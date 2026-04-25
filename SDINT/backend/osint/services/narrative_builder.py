"""
Narrative builder - creates timeline, platform summary, and entity network
for visualization in React components.
"""

from collections import defaultdict
from datetime import datetime, timezone


class NarrativeBuilder:
    """Build structured timeline and narrative from evidence."""

    def build_timeline(self, evidence_items: list, person: dict) -> list:
        """Returns timeline events sorted chronologically."""
        events = []
        
        for ev in evidence_items:
            # Handle both dict and object
            ev_dict = ev.__dict__ if hasattr(ev, '__dict__') else ev
            fields = ev_dict.get("extracted_fields", {})
            connector = ev_dict.get("connector_name", "")
            
            # Parse timestamp
            ts = ev_dict.get("collected_at")
            if isinstance(ts, str):
                try:
                    ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                except:
                    ts = datetime.now(timezone.utc)
            
            event_type = self._classify_event_type(connector, fields)
            platform = fields.get("platform", self._connector_to_platform(connector))
            
            events.append({
                "id": str(ev_dict.get("_id", "")),
                "timestamp": ts.isoformat() if ts else None,
                "timestamp_ms": int(ts.timestamp() * 1000) if ts else 0,
                "type": event_type,
                "platform": platform,
                "connector": connector,
                "title": self._make_event_title(connector, fields, ev_dict),
                "description": ev_dict.get("raw_text", "")[:300],
                "source_url": ev_dict.get("source_url", ""),
                "confidence": ev_dict.get("confidence", 0.5),
                "severity": self._get_severity(event_type, fields),
            })
        
        # Sort ascending
        events.sort(key=lambda e: e["timestamp_ms"])
        return events

    def build_platform_summary(self, evidence_items: list) -> list:
        """Aggregate evidence by platform."""
        platform_data = defaultdict(lambda: {
            "count": 0, "urls": [], "usernames": set(), "last_seen": None
        })
        
        for ev in evidence_items:
            ev_dict = ev.__dict__ if hasattr(ev, '__dict__') else ev
            fields = ev_dict.get("extracted_fields", {})
            platform = fields.get("platform") or self._connector_to_platform(ev_dict.get("connector_name", ""))
            
            platform_data[platform]["count"] += 1
            if ev_dict.get("source_url"):
                platform_data[platform]["urls"].append(ev_dict["source_url"])
            if fields.get("username"):
                platform_data[platform]["usernames"].add(fields["username"])
            ts = ev_dict.get("collected_at")
            if ts:
                platform_data[platform]["last_seen"] = str(ts)
        
        result = []
        for platform, data in platform_data.items():
            if platform and platform != "unknown":
                result.append({
                    "platform": platform,
                    "evidence_count": data["count"],
                    "profile_urls": list(set(data["urls"]))[:3],
                    "usernames": list(data["usernames"])[:5],
                    "last_seen": data["last_seen"],
                })
        
        return sorted(result, key=lambda x: x["evidence_count"], reverse=True)

    def build_entity_network(self, evidence_items: list) -> dict:
        """Build nodes+edges for network visualization."""
        nodes = {}
        edges = []
        edge_id = 0
        
        # Central target node
        nodes["target"] = {
            "id": "target",
            "label": "TARGET",
            "group": "person",
            "size": 30,
            "color": "#7F77DD",
        }
        
        for ev in evidence_items:
            ev_dict = ev.__dict__ if hasattr(ev, '__dict__') else ev
            fields = ev_dict.get("extracted_fields", {})
            
            # Username nodes
            if fields.get("username") and fields.get("platform"):
                node_id = f"u_{fields['username']}_{fields['platform']}"
                if node_id not in nodes and len(nodes) < 50:
                    nodes[node_id] = {
                        "id": node_id,
                        "label": f"@{fields['username']}\n({fields['platform']})",
                        "group": "username",
                        "color": "#1D9E75",
                    }
                    edges.append({"id": edge_id, "from": "target", "to": node_id, "label": "uses"})
                    edge_id += 1
            
            # Email nodes
            for email in fields.get("emails", []):
                node_id = f"e_{email}"
                if node_id not in nodes and len(nodes) < 50:
                    nodes[node_id] = {
                        "id": node_id,
                        "label": email,
                        "group": "email",
                        "color": "#EF9F27",
                    }
                    edges.append({"id": edge_id, "from": "target", "to": node_id, "label": "owns"})
                    edge_id += 1
            
            # Domain nodes
            for domain in fields.get("domains", []):
                node_id = f"d_{domain}"
                if node_id not in nodes and len(nodes) < 50:
                    nodes[node_id] = {
                        "id": node_id,
                        "label": domain,
                        "group": "domain",
                        "color": "#185FA5",
                    }
                    edges.append({"id": edge_id, "from": "target", "to": node_id, "label": "linked"})
                    edge_id += 1
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges[:100],
        }

    def _classify_event_type(self, connector: str, fields: dict) -> str:
        if "breach" in connector or fields.get("breach_type"):
            return "breach"
        if "username" in connector or fields.get("platform"):
            return "profile"
        if "domain" in connector:
            return "domain"
        if "search" in connector:
            return "mention"
        return "general"

    def _connector_to_platform(self, connector: str) -> str:
        mapping = {
            "web_search": "Web",
            "domain_intel": "WHOIS",
            "username_lookup": "Multi-Platform",
            "breach_check": "Breach DB",
            "github": "GitHub",
            "hackernews": "HackerNews",
        }
        for key, val in mapping.items():
            if key in connector.lower():
                return val
        return connector

    def _make_event_title(self, connector: str, fields: dict, ev: dict) -> str:
        if fields.get("platform") and fields.get("username"):
            return f"@{fields['username']} on {fields['platform']}"
        if fields.get("breach_type"):
            return f"Breach: {fields['breach_type']}"
        if fields.get("domain"):
            return f"Domain: {fields['domain']}"
        source = ev.get("source_url", "")
        if source:
            from urllib.parse import urlparse
            domain = urlparse(source).netloc
            return f"Evidence from {domain}"
        return f"Evidence via {connector}"

    def _get_severity(self, event_type: str, fields: dict) -> str:
        if event_type == "breach":
            return "HIGH"
        if event_type == "profile":
            return "MEDIUM"
        return "LOW"
