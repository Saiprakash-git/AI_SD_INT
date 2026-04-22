from flask import Flask, jsonify, request
from flask_cors import CORS
from bson import json_util
import json
import os
import sys
import logging
from datetime import datetime, timezone

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from apscheduler.schedulers.background import BackgroundScheduler
from db.mongo_client import db
from analysis.narrative_arc import compute_narrative_arc
from analysis.opinion_divergence import compute_opinion_divergence
from analysis.incident_detection import detect_incidents
from analysis.narrative_search import construct_narrative
from analysis.link_analyzer import run_link_analysis
import rss_collector

# OSINT Evidence Engine imports
from osint.db.evidence_store import EvidenceStore
from osint.extractors.reddit_converter import RedditConverter
from osint.extractors.entity_extractor import EntityExtractor
from osint.services.evidence_builder import EvidenceBuilder

# OSINT Intelligence imports
from osint.intelligence import (
    IdentityResolver,
    EntityPivot,
    NarrativeBuilder,
    InvestigationManager,
)

# OSINT Connector imports
from osint.connectors import (
    DuckDuckGoConnector,
    SherlockConnector,
    HIBPConnector,
    DomainIntelligenceConnector,
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

def parse_json(data):
    return json.loads(json_util.dumps(data))

# Scheduler Setup
scheduler = BackgroundScheduler()
scheduler.add_job(func=rss_collector.fetch_rss_live_data, trigger="interval", minutes=3)
scheduler.add_job(func=rss_collector.compute_all_echo_chambers, trigger="interval", minutes=30)
scheduler.start()

# Initialize OSINT backend components
store = EvidenceStore()
inv_manager = InvestigationManager(store)
identity_resolver = IdentityResolver(store)
entity_pivot = EntityPivot(store)
narrative_builder = NarrativeBuilder(store)
evidence_store = store

# Connectors
ddg_connector = DuckDuckGoConnector()
sherlock_connector = SherlockConnector()
hibp_connector = HIBPConnector()
domain_connector = DomainIntelligenceConnector()


# ============================================================================
# Core Health & Status
# ============================================================================

@app.route('/', methods=['GET'])
def root():
    return jsonify({
        "message": "SDINT - Social Data Intelligence Platform",
        "version": "2.0",
        "status": "operational"
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "ok",
        "message": "SDINT API is running",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "2.0"
    })

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get system status - returns RSS collector status."""
    try:
        status = db["rss_status"].find_one(sort=[("_id", -1)])
        if status:
            return jsonify(parse_json([status]))
    except Exception as e:
        logger.error(f"Status endpoint error: {e}")
    
    return jsonify([{
        "status": "operational",
        "last_poll_time": datetime.now(timezone.utc).isoformat(),
        "message": "System operational"
    }])


# ============================================================================
# Legacy Social Analysis Features (Existing)
# ============================================================================

@app.route('/api/topics/trending', methods=['GET'])
def get_trending_topics():
    trends = list(db["trends"].find().sort("frequency", -1))
    return jsonify(parse_json(trends))

@app.route('/api/trends/<topic_id>/analytics', methods=['GET'])
def get_trend_analytics(topic_id):
    posts = list(db["posts"].find({"topic_id": int(topic_id)}).sort("created_utc", 1))
    
    timeline_dict = {}
    total_running = 0
    for p in posts:
        total_running += 1
        ts = p.get("created_utc", 0)
        dt_str = datetime.fromtimestamp(ts).strftime('%m/%d/%Y %H:00')
        timeline_dict[dt_str] = total_running
    
    timeline = [{"time": k, "mentions": v} for k, v in timeline_dict.items()]
    
    origin_post = posts[0] if posts else None
    origin = {
        "title": origin_post.get("title", "Unknown Origin") if origin_post else "Unknown Origin",
        "date": datetime.fromtimestamp(origin_post["created_utc"]).strftime('%m/%d/%Y %H:%M') if origin_post else "Unknown"
    } if origin_post else None
    
    return jsonify({"timeline": timeline, "origin": origin})

@app.route('/api/posts', methods=['GET'])
def get_posts_by_topic():
    topic_id = request.args.get('topic_id')
    query = {}
    if topic_id is not None:
        query = {"topic_id": int(topic_id)}
    
    posts = list(db["posts"].find(query).sort("score", -1).limit(20))
    return jsonify(parse_json(posts))

@app.route('/api/posts/<post_id>/summary', methods=['GET'])
def get_post_summary(post_id):
    post = db["posts"].find_one({"post_id": post_id}, {"summary": 1})
    if post and "summary" in post:
        return jsonify({"post_id": post_id, "summary": post["summary"]})
    return jsonify({"error": "Summary not found"}), 404

@app.route('/api/posts/<post_id>/sentiment', methods=['GET'])
def get_post_sentiment(post_id):
    post = db["posts"].find_one({"post_id": post_id}, {"sentiment_distribution": 1})
    if post and "sentiment_distribution" in post:
        return jsonify({"post_id": post_id, "sentiment": post["sentiment_distribution"]})
    return jsonify({"error": "Sentiment data not found"}), 404

@app.route('/api/comments/toxic', methods=['GET'])
def get_toxic_comments():
    comments = list(db["comments"].find({"is_toxic": True}).sort("toxicity_score", -1).limit(50))
    return jsonify(parse_json(comments))

@app.route('/api/posts/<post_id>/comments', methods=['GET'])
def get_post_comments(post_id):
    comments = list(db["comments"].find({"post_id": post_id}).sort("score", -1).limit(100))
    return jsonify(parse_json(comments))

@app.route('/api/posts/<post_id>/narrative-arc', methods=['GET'])
def get_narrative_arc(post_id):
    post = db["posts"].find_one({"post_id": post_id}, {"narrative_arc": 1})
    if post and "narrative_arc" in post and post["narrative_arc"]:
        return jsonify(parse_json(post["narrative_arc"]))
    res = compute_narrative_arc(post_id)
    return jsonify(parse_json(res))

@app.route('/api/posts/<post_id>/opinion-divergence', methods=['GET'])
def get_opinion_divergence(post_id):
    post = db["posts"].find_one({"post_id": post_id}, {"opinion_divergence": 1})
    if post and "opinion_divergence" in post and post["opinion_divergence"]:
        return jsonify(parse_json(post["opinion_divergence"]))
    res = compute_opinion_divergence(post_id)
    return jsonify(parse_json(res))

@app.route('/api/subreddits/echo-chamber', methods=['GET'])
def get_all_echo_chambers():
    scores = list(db["subreddit_metrics"].find().sort("echo_chamber_score", -1))
    return jsonify(parse_json(scores))

@app.route('/api/subreddits/<subreddit>/echo-chamber', methods=['GET'])
def get_echo_chamber(subreddit):
    doc = db["subreddit_metrics"].find_one({"subreddit": subreddit})
    return jsonify(parse_json(doc))

@app.route('/api/incidents', methods=['GET'])
def get_incidents_api():
    return jsonify(parse_json(detect_incidents()))

@app.route('/api/search/narrative', methods=['GET'])
def search_narrative_api():
    q = request.args.get('q', '')
    if not q:
        return jsonify({"error": "No query"})
    return jsonify(parse_json(construct_narrative(q)))

@app.route('/api/analyze-link', methods=['POST'])
def analyze_link_api():
    data = request.json or {}
    url = data.get('url', '')
    if not url:
        return jsonify({"error": "No url"})
    return jsonify(parse_json(run_link_analysis(url)))


# ============================================================================
# OSINT Evidence Engine Endpoints
# ============================================================================

@app.route('/api/osint/evidence', methods=['GET'])
def get_evidence():
    """Get evidence items with optional filters."""
    source_type = request.args.get('source_type')
    limit = int(request.args.get('limit', 20))
    items = evidence_store.get_recent(limit=limit, source_type=source_type)
    return jsonify(parse_json([item.to_dict() for item in items]))

@app.route('/api/osint/evidence/<evidence_id>', methods=['GET'])
def get_evidence_by_id(evidence_id):
    """Get a single evidence item by ID."""
    item = evidence_store.get_by_id(evidence_id)
    if not item:
        return jsonify({"error": "Evidence item not found"}), 404
    return jsonify(parse_json(item.to_dict()))

@app.route('/api/osint/evidence/search', methods=['GET'])
def search_evidence():
    """Full-text search across evidence items."""
    q = request.args.get('q', '')
    source_type = request.args.get('source_type')
    limit = int(request.args.get('limit', 50))
    if not q:
        return jsonify({"error": "Query parameter 'q' is required"}), 400
    items = evidence_store.search(q, limit=limit, source_type=source_type)
    return jsonify(parse_json([item.to_dict() for item in items]))

@app.route('/api/osint/evidence/by-entity', methods=['GET'])
def get_evidence_by_entity():
    """Find evidence containing a specific entity."""
    entity_type = request.args.get('type', '')
    entity_value = request.args.get('value', '')
    limit = int(request.args.get('limit', 50))
    if not entity_type or not entity_value:
        return jsonify({"error": "Both 'type' and 'value' params required"}), 400
    items = evidence_store.get_by_entity(entity_type, entity_value, limit=limit)
    return jsonify(parse_json([item.to_dict() for item in items]))

@app.route('/api/osint/evidence/entity-network', methods=['GET'])
def get_entity_network():
    """Get co-occurrence network for an entity."""
    entity_type = request.args.get('type', '')
    entity_value = request.args.get('value', '')
    if not entity_type or not entity_value:
        return jsonify({"error": "Both 'type' and 'value' params required"}), 400
    network = evidence_store.get_entity_network(entity_type, entity_value)
    return jsonify(parse_json(network))

@app.route('/api/osint/evidence/stats', methods=['GET'])
def get_evidence_stats():
    """Get evidence store statistics."""
    stats = evidence_store.get_stats()
    return jsonify(parse_json(stats))

@app.route('/api/osint/evidence/convert-reddit', methods=['POST'])
def convert_reddit_to_evidence():
    """Convert existing Reddit data into evidence items."""
    data = request.json or {}
    limit = data.get('limit')
    investigation_id = data.get('investigation_id')
    
    converter = RedditConverter(investigation_id=investigation_id)
    stats = converter.convert_all(limit=limit)
    return jsonify({"status": "completed", "stats": stats})

@app.route('/api/osint/evidence/extract-entities', methods=['POST'])
def extract_entities_from_text():
    """Extract entities from arbitrary text."""
    data = request.json or {}
    text = data.get('text', '')
    if not text:
        return jsonify({"error": "'text' field required"}), 400
    extractor = EntityExtractor()
    entities = extractor.extract(text)
    return jsonify({"text_length": len(text), "entities_found": len(entities), "entities": entities})


# ============================================================================
# OSINT Investigation Management (NEW)
# ============================================================================

@app.route('/api/investigations', methods=['POST'])
def create_investigation():
    """Create new investigation."""
    try:
        data = request.get_json()
        
        if not data.get('title'):
            return jsonify({"error": "Title required"}), 400
        
        investigation = inv_manager.create_investigation(
            title=data['title'],
            description=data.get('description', ''),
            investigator=data.get('investigator', ''),
            priority=data.get('priority', 'medium'),
            tags=data.get('tags', [])
        )
        
        return jsonify({
            "status": "success",
            "investigation": investigation.to_dict()
        }), 201
    
    except Exception as e:
        logger.error(f"Error creating investigation: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/investigations/<inv_id>', methods=['GET'])
def get_investigation(inv_id):
    """Get investigation details."""
    try:
        investigation = inv_manager.get_investigation(inv_id)
        if not investigation:
            return jsonify({"error": "Investigation not found"}), 404
        
        return jsonify({
            "status": "success",
            "investigation": investigation.to_dict()
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting investigation: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/investigations/<inv_id>/summary', methods=['GET'])
def get_investigation_summary(inv_id):
    """Get investigation summary."""
    try:
        summary = inv_manager.get_investigation_summary(inv_id)
        
        return jsonify({
            "status": "success",
            "summary": summary
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting summary: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/investigations/<inv_id>/evidence', methods=['POST'])
def add_evidence_to_investigation(inv_id):
    """Add evidence to investigation."""
    try:
        data = request.get_json()
        evidence_ids = data.get('evidence_ids', [])
        
        for evi_id in evidence_ids:
            inv_manager.add_evidence_to_investigation(inv_id, evi_id)
        
        return jsonify({
            "status": "success",
            "message": f"Added {len(evidence_ids)} evidence items"
        }), 200
    
    except Exception as e:
        logger.error(f"Error adding evidence: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/investigations/<inv_id>/entities', methods=['GET'])
def get_investigation_entities(inv_id):
    """Get entities in investigation."""
    try:
        entities = inv_manager.get_investigation_entities(inv_id)
        
        return jsonify({
            "status": "success",
            "entities": entities
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting entities: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/investigations/<inv_id>/identities', methods=['GET'])
def get_investigation_identities(inv_id):
    """Get resolved identities in investigation."""
    try:
        identities = inv_manager.resolve_investigation_identities(inv_id)
        
        return jsonify({
            "status": "success",
            "identities": [
                {
                    "identity_id": i.identity_id,
                    "primary_entity": i.primary_entity,
                    "confidence": i.confidence,
                    "entity_types": i.entity_types,
                    "equivalent_entities": [
                        {"entity_id": e.entity_id, "value": e.value, "type": e.type, "confidence": e.confidence}
                        for e in i.equivalent_entities
                    ]
                }
                for i in identities
            ]
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting identities: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/investigations/<inv_id>/timeline', methods=['GET'])
def get_investigation_timeline(inv_id):
    """Get investigation timeline."""
    try:
        timeline, threat_level = inv_manager.build_investigation_timeline(inv_id)
        
        return jsonify({
            "status": "success",
            "timeline": [
                {
                    "evidence_id": e.evidence_id,
                    "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                    "event_type": e.event_type,
                    "source_platform": e.source_platform,
                    "title": e.title,
                    "description": e.description,
                    "threat_level": e.threat_level,
                    "confidence": e.confidence
                }
                for e in timeline
            ],
            "threat_assessment": threat_level
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting timeline: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/investigations/<inv_id>/pivots', methods=['GET'])
def get_investigation_pivots(inv_id):
    """Get pivot suggestions for investigation."""
    try:
        investigation = inv_manager.get_investigation(inv_id)
        if not investigation:
            return jsonify({"error": "Investigation not found"}), 404
        
        pivots = inv_manager.find_investigation_pivots(inv_id)
        
        return jsonify({
            "status": "success",
            "pivots": [
                {
                    "from_entity": p.from_entity,
                    "to_entity": p.to_entity,
                    "strength": p.strength,
                    "justification": p.justification,
                    "next_steps": p.next_steps
                }
                for p in pivots
            ]
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting pivots: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/investigations/<inv_id>/close', methods=['POST'])
def close_investigation(inv_id):
    """Close investigation."""
    try:
        data = request.get_json() or {}
        findings = data.get('findings', '')
        
        inv_manager.close_investigation(inv_id, findings=findings)
        
        return jsonify({
            "status": "success",
            "message": "Investigation closed"
        }), 200
    
    except Exception as e:
        logger.error(f"Error closing investigation: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# OSINT Intelligence Analysis
# ============================================================================

@app.route('/api/analyze/identity', methods=['POST'])
def analyze_identity():
    """Analyze identity (resolve by email, username, domain, or person)."""
    try:
        data = request.get_json()
        entity_type = data.get('type', '')  # email, username, domain, person
        entity_value = data.get('value', '')
        
        if not entity_type or not entity_value:
            return jsonify({"error": "type and value required"}), 400
        
        if entity_type == 'email':
            profile = identity_resolver.resolve_by_email(entity_value)
        elif entity_type == 'username':
            profile = identity_resolver.resolve_by_username(entity_value)
        elif entity_type == 'domain':
            profile = identity_resolver.resolve_by_domain(entity_value)
        elif entity_type == 'person':
            profile = identity_resolver.resolve_by_person(entity_value)
        else:
            return jsonify({"error": "Invalid entity type"}), 400
        
        return jsonify({
            "status": "success",
            "profile": {
                "identity_id": profile.identity_id,
                "primary_entity": profile.primary_entity,
                "confidence": profile.confidence,
                "entity_types": profile.entity_types,
                "equivalent_entities": len(profile.equivalent_entities)
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error analyzing identity: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/analyze/pivot', methods=['POST'])
def analyze_pivot():
    """Find related entities (pivot discovery)."""
    try:
        data = request.get_json()
        entity_type = data.get('type', '')
        entity_value = data.get('value', '')
        depth = data.get('depth', 1)
        
        if not entity_type or not entity_value:
            return jsonify({"error": "type and value required"}), 400
        
        related = entity_pivot.find_related_entities(entity_type, entity_value)
        network = entity_pivot.build_pivot_network(entity_type, entity_value, depth=depth)
        suggestions = entity_pivot.suggest_pivots(entity_type, entity_value)
        
        return jsonify({
            "status": "success",
            "related_entities": len(related),
            "network_depth": depth,
            "suggestions": [
                {
                    "from_entity": s.from_entity,
                    "to_entity": s.to_entity,
                    "strength": s.strength,
                    "justification": s.justification
                }
                for s in suggestions[:5]
            ]
        }), 200
    
    except Exception as e:
        logger.error(f"Error analyzing pivot: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# OSINT Data Collection
# ============================================================================

@app.route('/api/collect/web', methods=['POST'])
def collect_web_search():
    """Run web search via DuckDuckGo."""
    try:
        data = request.get_json()
        query = data.get('query', '')
        investigation_id = data.get('investigation_id')
        
        if not query:
            return jsonify({"error": "query required"}), 400
        
        results = ddg_connector.search(query)
        
        return jsonify({
            "status": "success",
            "query": query,
            "results_count": len(results),
            "results": results[:10]
        }), 200
    
    except Exception as e:
        logger.error(f"Error in web search: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/collect/breach', methods=['POST'])
def collect_breach_data():
    """Check breach data via HIBP."""
    try:
        data = request.get_json()
        query = data.get('query', '')
        investigation_id = data.get('investigation_id')
        
        if not query:
            return jsonify({"error": "query required"}), 400
        
        results = hibp_connector.search(query)
        
        return jsonify({
            "status": "success",
            "query": query,
            "breaches_found": len(results),
            "results": results
        }), 200
    
    except Exception as e:
        logger.error(f"Error in breach search: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/collect/username', methods=['POST'])
def collect_username_search():
    """Search username across platforms."""
    try:
        data = request.get_json()
        username = data.get('username', '')
        investigation_id = data.get('investigation_id')
        
        if not username:
            return jsonify({"error": "username required"}), 400
        
        results = sherlock_connector.search(username)
        
        return jsonify({
            "status": "success",
            "username": username,
            "platforms_found": len(results),
            "results": results
        }), 200
    
    except Exception as e:
        logger.error(f"Error in username search: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/collect/domain', methods=['POST'])
def collect_domain_intel():
    """Get domain intelligence (WHOIS, DNS, SSL, subdomains)."""
    try:
        data = request.get_json()
        domain = data.get('domain', '')
        investigation_id = data.get('investigation_id')
        
        if not domain:
            return jsonify({"error": "domain required"}), 400
        
        results = domain_connector.search(domain)
        
        return jsonify({
            "status": "success",
            "domain": domain,
            "intel_items": len(results),
            "results": results
        }), 200
    
    except Exception as e:
        logger.error(f"Error in domain intelligence: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# Search & Statistics
# ============================================================================

@app.route('/api/search/evidence', methods=['GET'])
def search_evidence_api():
    """Full-text search across all evidence."""
    try:
        q = request.args.get('q', '')
        limit = int(request.args.get('limit', 50))
        
        if not q:
            return jsonify({"error": "query required"}), 400
        
        results = store.search(q, limit=limit)
        
        return jsonify({
            "status": "success",
            "query": q,
            "results_count": len(results),
            "results": [r.to_dict() for r in results] if results else []
        }), 200
    
    except Exception as e:
        logger.error(f"Error in search: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get system statistics."""
    try:
        stats = store.get_stats()
        
        return jsonify({
            "status": "success",
            "stats": {
                "total_evidence": stats.get("total_count", 0),
                "by_source": stats.get("by_source_type", {}),
                "investigations": len(inv_manager._investigations) if hasattr(inv_manager, '_investigations') else 0,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    logger.info("="*70)
    logger.info("Starting SDINT - Social Data Intelligence Platform")
    logger.info("="*70)
    logger.info("\n📊 Social Analysis Features:")
    logger.info("  • Real-time trend analysis")
    logger.info("  • Echo chamber detection")
    logger.info("  • Toxic comment analysis")
    logger.info("  • Narrative arc computation")
    logger.info("\n🕵️  OSINT Investigation Framework:")
    logger.info("  • Evidence collection & storage")
    logger.info("  • Entity extraction & linking")
    logger.info("  • Identity resolution")
    logger.info("  • Relationship discovery")
    logger.info("  • Timeline & threat assessment")
    logger.info("\n📡 Data Collection:")
    logger.info("  • Web search (DuckDuckGo)")
    logger.info("  • Breach data (HIBP)")
    logger.info("  • Username discovery (Sherlock)")
    logger.info("  • Domain intelligence (WHOIS/DNS/SSL)")
    logger.info("\nStarting on http://localhost:5000")
    logger.info("="*70 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
