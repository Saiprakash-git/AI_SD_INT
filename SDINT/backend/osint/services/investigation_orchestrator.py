"""
Investigation Orchestrator - Main OSINT pipeline orchestrator.
Runs all connectors, resolves identity, builds narrative.
CORE TO THE OSINT FRAMEWORK - FOCUSES ON IDENTITY DISCOVERY.
"""

import re
import uuid
from datetime import datetime, timezone

from osint.connectors.username_connector import UsernameConnector
from osint.connectors.breach_connector import BreachConnector
from osint.connectors.hackernews_connector import HackerNewsConnector
from osint.connectors.github_connector import GitHubConnector
from osint.connectors.nitter_connector import NitterConnector
from osint.connectors.instagram_connector import InstagramConnector
from osint.connectors.crtsh_connector import CrtShConnector
from osint.connectors.wayback_connector import WaybackConnector
from osint.connectors.google_dork_connector import GoogleDorkConnector
from osint.connectors.reddit_local_connector import RedditLocalConnector
from osint.connectors.news_connector import NewsConnector
from osint.services.identity_resolver import IdentityResolver
from osint.services.narrative_builder import NarrativeBuilder
from osint.services.rate_scheduler import RateScheduler
from osint.services.source_credibility import SourceCredibility
from osint.services.content_analyzer import ContentAnalyzer


def _connector_source_type(connector_name: str) -> str:
    """Map connector to a stable source_type used by downstream UI/API."""
    mapping = {
        "username_lookup": "username_discovery",
        "breach_check": "breach_data",
        "github": "web_search",
        "hackernews": "web_search",
        "nitter_twitter": "web_search",
        "instagram_public": "web_search",
        "crtsh": "domain_intel",
        "wayback_cdx": "web_archive",
        "google_dork": "web_search",
        "reddit_local": "reddit_post",
        "gdelt_news": "news_article",
    }
    return mapping.get(connector_name, "web_search")


def _normalize_item(
    item: dict,
    pivot: dict,
    session_id: str,
    connector_name: str,
    custom_weights: dict = None
) -> dict:
    """
    Normalize connector output to a consistent shape while preserving original fields.
    """
    extracted_fields = item.get("extracted_fields", {}) or {}
    source_url = item.get("source_url", "") or extracted_fields.get("profile_url", "")
    title = extracted_fields.get("title") or extracted_fields.get("platform") or connector_name
    body = item.get("raw_text", "") or ""
    collected_at = item.get("collected_at")
    if hasattr(collected_at, "isoformat"):
        collected_at = collected_at.isoformat()

    source_credibility = SourceCredibility.score(connector_name, item, custom_weights=custom_weights)

    return {
        "evidence_id": f"evi_{uuid.uuid4().hex[:16]}",
        "source_id": f"src_{uuid.uuid4().hex[:16]}",
        # Session pipeline fields
        "session_id": session_id,
        "connector_name": connector_name,
        "source_url": source_url,
        "queried_value": item.get("queried_value", pivot.get("value", "")),
        "queried_type": item.get("queried_type", pivot.get("type", "")),
        "raw_text": body,
        "extracted_fields": extracted_fields,
        "collected_at": collected_at or datetime.now(timezone.utc).isoformat(),
        "confidence": float(item.get("confidence", 0.5)),
        "source_credibility": source_credibility,
        "license_note": item.get("license_note", ""),
        # Compatibility fields for evidence explorer/search screens
        "source_type": _connector_source_type(connector_name),
        "source_platform": extracted_fields.get("platform", connector_name),
        "content": {
            "title": title,
            "body": body,
            "url": source_url,
        },
        "timestamps": {
            "collected_at": collected_at or datetime.now(timezone.utc).isoformat(),
        },
    }


def parse_pivot(raw_query: str) -> dict:
    """Classify query into structured pivot type."""
    q = raw_query.strip()
    
    # Email
    if re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', q):
        return {"type": "email", "value": q}
    
    # Phone
    if re.match(r'^[+\d\s\-().]{8,15}$', q.replace(" ", "")):
        return {"type": "phone", "value": q}
    
    # Username
    if re.match(r'^@?[\w]{2,30}$', q) and " " not in q:
        return {"type": "username", "value": q.lstrip("@")}
    
    # Domain
    if re.match(r'^[a-z0-9\-]+\.[a-z]{2,}$', q.lower()):
        return {"type": "domain", "value": q}
    
    # Default: name
    return {"type": "name", "value": q}


def _collect_external_links(evidence_items: list) -> list:
    links = {}
    for ev in evidence_items:
        fields = ev.get("extracted_fields", {}) or {}
        candidates = [
            ev.get("source_url"),
            fields.get("profile_url"),
        ]
        candidates.extend(fields.get("urls", []) if isinstance(fields.get("urls"), list) else [])
        candidates.extend(fields.get("domains", []) if isinstance(fields.get("domains"), list) else [])
        for url in candidates:
            if not url or not isinstance(url, str):
                continue
            href = url if url.startswith(("http://", "https://")) else f"https://{url}"
            links[href] = {
                "url": href,
                "connector": ev.get("connector_name", ""),
                "platform": fields.get("platform") or ev.get("source_platform") or "",
                "title": (ev.get("content") or {}).get("title") or fields.get("title") or href,
            }
    return list(links.values())[:200]


def run_full_investigation(session_id: str, raw_query: str, db, context: dict = None) -> dict:
    """
    Complete OSINT investigation pipeline:
    1. Parse query
    2. Run all connectors
    3. Resolve identity
    4. Build narrative
    5. Save results
    """
    try:
        pivot = parse_pivot(raw_query)
        pivot["session_id"] = session_id
        pivot["context"] = context or {}
        pivot["db"] = db
        session_doc = db.investigation_sessions.find_one({"session_id": session_id}, {"_id": 0}) or {}
        credibility_weights = (
            session_doc.get("credibility_weights")
            or (db.osint_settings.find_one({"_id": "credibility_weights"}) or {}).get("weights")
            or {}
        )
        
        # Update session status
        db.investigation_sessions.update_one(
            {"session_id": session_id},
            {"$set": {
                "status": "running",
                "pivot_type": pivot["type"],
                "started_at": datetime.now(timezone.utc).isoformat()
            }},
            upsert=True
        )
        
        all_evidence = []
        connector_runs = []
        rate_limiter = RateScheduler.get()
        
        # Pipeline: run connectors based on pivot type
        connectors = []
        
        # Always run these
        connectors.append(UsernameConnector())
        connectors.append(BreachConnector())
        connectors.append(HackerNewsConnector())
        connectors.append(GitHubConnector())
        connectors.append(NitterConnector())
        connectors.append(InstagramConnector())
        connectors.append(CrtShConnector())
        connectors.append(WaybackConnector())
        connectors.append(GoogleDorkConnector())
        connectors.append(RedditLocalConnector())
        connectors.append(NewsConnector())
        
        # If we have existing web search or domain connectors, add them
        # connectors.append(WebSearchConnector())
        # connectors.append(DomainIntelConnector())
        
        # Run each connector
        print(f"Running {len(connectors)} connectors...")
        for connector in connectors:
            if connector.supports_types and pivot["type"] in connector.supports_types:
                connector_start = datetime.now(timezone.utc)
                try:
                    # Rate limit
                    rate_limiter.wait_for(connector.name)
                    
                    print(f"  Running {connector.name}...")
                    items = connector.run(pivot)
                    
                    # Convert and save evidence
                    for item in items:
                        item_dict = item.__dict__ if hasattr(item, '__dict__') else dict(item)
                        normalized = _normalize_item(
                            item_dict,
                            pivot,
                            session_id,
                            connector.name,
                            custom_weights=credibility_weights,
                        )
                        db.evidence_items.insert_one(normalized)
                        all_evidence.append(normalized)
                    
                    print(f"    [INFO] {len(items)} evidence items")
                    run_doc = {
                        "session_id": session_id,
                        "connector": connector.name,
                        "status": "success",
                        "item_count": len(items),
                        "started_at": connector_start.isoformat(),
                        "completed_at": datetime.now(timezone.utc).isoformat(),
                    }
                    connector_runs.append(run_doc)
                    db.connector_runs.insert_one(run_doc)
                    run_doc.pop("_id", None)
                except Exception as e:
                    print(f"  [FAIL] {connector.name} failed: {e}")
                    run_doc = {
                        "session_id": session_id,
                        "connector": connector.name,
                        "status": "failed",
                        "item_count": 0,
                        "error": str(e),
                        "started_at": connector_start.isoformat(),
                        "completed_at": datetime.now(timezone.utc).isoformat(),
                    }
                    connector_runs.append(run_doc)
                    db.connector_runs.insert_one(run_doc)
                    run_doc.pop("_id", None)
        
        print(f"\nTotal evidence: {len(all_evidence)} items")
        
        # Identity resolution
        print("Resolving identity...")
        resolver = IdentityResolver()
        person = resolver.resolve(all_evidence, session_id, raw_query)
        resolver.save_to_db(person, db)
        print(f"  [INFO] Resolved as: {person.canonical_name or 'UNKNOWN'}")
        
        # Narrative building
        print("Building narrative...")
        builder = NarrativeBuilder()
        timeline = builder.build_timeline(all_evidence, {})
        platform_summary = builder.build_platform_summary(all_evidence)
        network_graph = builder.build_entity_network(all_evidence)
        content_analysis = ContentAnalyzer().analyze(all_evidence, raw_query)
        external_links = _collect_external_links(all_evidence)
        
        # Save session complete with results
        session_result = {
            "session_id": session_id,
            "raw_query": raw_query,
            "pivot_type": pivot["type"],
            "status": "complete",
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "evidence_count": len(all_evidence),
            "person_id": person.id,
            "canonical_name": person.canonical_name,
            "risk_level": person.risk_level,
            "risk_score": person.risk_score,
            "match_confidence": person.match_confidence,
            "timeline_count": len(timeline),
            "platform_count": len(platform_summary),
            "connector_runs": connector_runs,
            "connector_success": sum(1 for r in connector_runs if r["status"] == "success"),
            "connector_failures": sum(1 for r in connector_runs if r["status"] == "failed"),
            "avg_source_credibility": round(
                (
                    sum(float(e.get("source_credibility", 0.0)) for e in all_evidence)
                    / len(all_evidence)
                ) if all_evidence else 0.0,
                2
            ),
            "misinformation_risk": content_analysis.get("misinformation_risk", 0.0),
            "context": context or {},
        }
        
        db.investigation_sessions.update_one(
            {"session_id": session_id},
            {"$set": session_result},
            upsert=True
        )
        
        # Cache narrative artifacts
        db.narrative_artifacts.update_one(
            {"session_id": session_id},
            {"$set": {
                "timeline": timeline[:50],
                "platform_summary": platform_summary,
                "network_graph": network_graph,
                "open_source_analysis": content_analysis,
                "external_links": external_links,
            }},
            upsert=True
        )
        
        print(f"\n[OK] Investigation complete!")
        print(f"  Identity: {person.canonical_name}")
        print(f"  Risk Level: {person.risk_level}")
        print(f"  Confidence: {int(person.match_confidence*100)}%")
        print(f"  Breach Findings: {len(person.breach_findings)}")
        
        return session_result
    
    except Exception as e:
        print(f"Investigation failed: {e}")
        db.investigation_sessions.update_one(
            {"session_id": session_id},
            {"$set": {
                "status": "failed",
                "error": str(e),
                "completed_at": datetime.now(timezone.utc).isoformat()
            }},
            upsert=True
        )
        raise
