"""
MODULE 4 — Visualization & API

REST API endpoints for investigation management and analysis.

Endpoints:
  POST   /api/investigations - Create new investigation
  GET    /api/investigations/{id} - Get investigation details
  POST   /api/investigations/{id}/evidence - Add evidence
  GET    /api/investigations/{id}/timeline - Get timeline
  GET    /api/investigations/{id}/entities - Get entities
  GET    /api/investigations/{id}/identities - Get resolved identities
  GET    /api/investigations/{id}/pivots - Get pivot suggestions
  GET    /api/investigations/{id}/summary - Get complete summary
  POST   /api/investigations/{id}/close - Close investigation
  GET    /api/search - Search across investigations
"""

import sys
sys.path.insert(0, '.')

from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from datetime import datetime, timezone
import os
import json
from bson import json_util

# Original app.py imports
try:
    from db.mongo_client import db
    from analysis.narrative_arc import compute_narrative_arc
    from analysis.opinion_divergence import compute_opinion_divergence
    from analysis.incident_detection import detect_incidents
    from analysis.narrative_search import construct_narrative
    from analysis.link_analyzer import run_link_analysis
    from osint.extractors.reddit_converter import RedditConverter
    import rss_collector
    has_legacy_features = True
except ImportError as e:
    logger_init = logging.getLogger(__name__)
    logger_init.info(f"Legacy features unavailable: {e}")
    has_legacy_features = False

from osint.db.evidence_store import EvidenceStore
from osint.intelligence import (
    IdentityResolver,
    EntityPivot,
    NarrativeBuilder,
    InvestigationManager,
)
from osint.connectors import (
    DuckDuckGoConnector,
    SherlockConnector,
    HIBPConnector,
    DomainIntelligenceConnector,
)


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # CORS enabled for all routes

# Initialize backend components
store = EvidenceStore()
inv_manager = InvestigationManager(store)
identity_resolver = IdentityResolver(store)
entity_pivot = EntityPivot(store)
narrative_builder = NarrativeBuilder(store)

# Connectors
ddg_connector = DuckDuckGoConnector()
sherlock_connector = SherlockConnector()
hibp_connector = HIBPConnector()
domain_connector = DomainIntelligenceConnector()


# ============================================================================
# Helper Functions
# ============================================================================

def parse_json(data):
    """Parse MongoDB BSON documents to JSON."""
    try:
        return json.loads(json_util.dumps(data))
    except:
        return data


# ============================================================================
# Legacy Endpoints (for frontend compatibility)
# ============================================================================

@app.route('/', methods=['GET'])
def root():
    return jsonify({"message": "SDINT API is running", "version": "2.0"})

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get system status - returns RSS collector status."""
    try:
        if has_legacy_features:
            status = db["rss_status"].find_one(sort=[("_id", -1)])
            if status:
                return jsonify(parse_json([status]))
        return jsonify([{
            "status": "operational",
            "last_poll_time": datetime.now(timezone.utc).isoformat(),
            "message": "System operational"
        }])
    except Exception as e:
        logger.error(f"Status endpoint error: {e}")
        return jsonify({
            "status": "operational",
            "last_poll_time": datetime.now(timezone.utc).isoformat(),
            "error": str(e)
        }), 200

@app.route('/api/posts', methods=['GET'])
def get_posts_by_topic():
    """Get posts by topic (legacy endpoint for frontend)."""
    try:
        if has_legacy_features:
            topic_id = request.args.get('topic_id')
            query = {}
            if topic_id is not None:
                query = {"topic_id": int(topic_id)}
            
            posts = list(db["posts"].find(query).sort("score", -1).limit(20))
            return jsonify(parse_json(posts))
        return jsonify([])
    except Exception as e:
        logger.error(f"Posts endpoint error: {e}")
        return jsonify({"error": str(e), "posts": []}), 200

@app.route('/api/posts/<post_id>/summary', methods=['GET'])
def get_post_summary(post_id):
    """Get post summary."""
    try:
        if has_legacy_features:
            post = db["posts"].find_one({"post_id": post_id}, {"summary": 1})
            if post and "summary" in post:
                return jsonify({"post_id": post_id, "summary": post["summary"]})
        return jsonify({"post_id": post_id, "summary": "Summary unavailable"}), 200
    except Exception as e:
        logger.error(f"Post summary error: {e}")
        return jsonify({"error": str(e)}), 200

@app.route('/api/posts/<post_id>/sentiment', methods=['GET'])
def get_post_sentiment(post_id):
    """Get post sentiment."""
    try:
        if has_legacy_features:
            post = db["posts"].find_one({"post_id": post_id}, {"sentiment_distribution": 1})
            if post and "sentiment_distribution" in post:
                return jsonify({"post_id": post_id, "sentiment": post["sentiment_distribution"]})
        return jsonify({"post_id": post_id, "sentiment": {}}), 200
    except Exception as e:
        logger.error(f"Post sentiment error: {e}")
        return jsonify({"error": str(e)}), 200


# ============================================================================
# Investigation Management Endpoints
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


@app.route('/api/investigations/<investigation_id>', methods=['GET'])
def get_investigation(investigation_id):
    """Get investigation summary."""
    try:
        summary = inv_manager.get_investigation_summary(investigation_id)
        
        return jsonify({
            "status": "success",
            "data": summary
        }), 200
    
    except ValueError:
        return jsonify({"error": "Investigation not found"}), 404
    except Exception as e:
        logger.error(f"Error fetching investigation: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/investigations/<investigation_id>/evidence', methods=['POST'])
def add_evidence(investigation_id):
    """Add evidence items to investigation."""
    try:
        data = request.get_json()
        evidence_ids = data.get('evidence_ids', [])
        
        if not evidence_ids:
            return jsonify({"error": "No evidence IDs provided"}), 400
        
        added = inv_manager.add_evidence_to_investigation(
            investigation_id,
            evidence_ids
        )
        
        return jsonify({
            "status": "success",
            "added": added
        }), 200
    
    except ValueError:
        return jsonify({"error": "Investigation not found"}), 404
    except Exception as e:
        logger.error(f"Error adding evidence: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/investigations/<investigation_id>/entities', methods=['GET'])
def get_investigation_entities(investigation_id):
    """Get all entities in investigation."""
    try:
        entities = inv_manager.get_investigation_entities(investigation_id)
        
        return jsonify({
            "status": "success",
            "entities": {
                entity_type: [
                    {
                        "value": e["value"],
                        "confidence": round(e.get("confidence", 0), 3),
                        "source": e.get("source", "unknown")
                    }
                    for e in entities_list
                ]
                for entity_type, entities_list in entities.items()
            }
        }), 200
    
    except ValueError:
        return jsonify({"error": "Investigation not found"}), 404
    except Exception as e:
        logger.error(f"Error fetching entities: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/investigations/<investigation_id>/identities', methods=['GET'])
def get_investigation_identities(investigation_id):
    """Get resolved identities for investigation."""
    try:
        identities = inv_manager.resolve_investigation_identities(investigation_id)
        
        return jsonify({
            "status": "success",
            "identities": [
                {
                    "identity_id": id_profile.identity_id,
                    "primary_entity": id_profile.primary_entity,
                    "equivalent_entities": id_profile.equivalent_entities[:10],
                    "entity_types": list(id_profile.entity_types),
                    "confidence": round(id_profile.confidence, 3),
                    "evidence_count": len(id_profile.evidence_ids)
                }
                for id_profile in identities
            ],
            "total": len(identities)
        }), 200
    
    except ValueError:
        return jsonify({"error": "Investigation not found"}), 404
    except Exception as e:
        logger.error(f"Error resolving identities: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/investigations/<investigation_id>/timeline', methods=['GET'])
def get_investigation_timeline(investigation_id):
    """Get timeline for investigation."""
    try:
        narrative = inv_manager.build_investigation_timeline(investigation_id)
        
        return jsonify({
            "status": "success",
            "timeline": {
                "narrative_id": narrative.narrative_id,
                "title": narrative.title,
                "events": [
                    {
                        "evidence_id": e.evidence_id,
                        "timestamp": e.timestamp,
                        "event_type": e.event_type,
                        "source_platform": e.source_platform,
                        "title": e.title,
                        "threat_level": e.threat_level,
                        "confidence": round(e.confidence, 3)
                    }
                    for e in narrative.timeline
                ],
                "pattern_type": narrative.pattern_type,
                "threat_assessment": narrative.threat_assessment,
                "entity_count": len(narrative.entities_involved)
            }
        }), 200
    
    except ValueError:
        return jsonify({"error": "Investigation not found"}), 404
    except Exception as e:
        logger.error(f"Error building timeline: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/investigations/<investigation_id>/pivots', methods=['GET'])
def get_investigation_pivots(investigation_id):
    """Get pivot suggestions for investigation entities."""
    try:
        entity_type = request.args.get('entity_type')
        entity_value = request.args.get('entity_value')
        
        if not entity_type or not entity_value:
            return jsonify({"error": "entity_type and entity_value required"}), 400
        
        pivots = inv_manager.find_investigation_pivots(
            investigation_id,
            entity_type,
            entity_value
        )
        
        return jsonify({
            "status": "success",
            "pivots": pivots[:10]
        }), 200
    
    except ValueError:
        return jsonify({"error": "Investigation not found"}), 404
    except Exception as e:
        logger.error(f"Error finding pivots: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/investigations/<investigation_id>/summary', methods=['GET'])
def get_investigation_summary_endpoint(investigation_id):
    """Get complete investigation summary."""
    try:
        summary = inv_manager.get_investigation_summary(investigation_id)
        
        return jsonify({
            "status": "success",
            "summary": summary
        }), 200
    
    except ValueError:
        return jsonify({"error": "Investigation not found"}), 404
    except Exception as e:
        logger.error(f"Error getting summary: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/investigations/<investigation_id>/close', methods=['POST'])
def close_investigation(investigation_id):
    """Close investigation."""
    try:
        data = request.get_json() or {}
        final_assessment = data.get('final_assessment')
        
        closed_inv = inv_manager.close_investigation(
            investigation_id,
            final_assessment
        )
        
        return jsonify({
            "status": "success",
            "investigation": closed_inv.to_dict()
        }), 200
    
    except ValueError:
        return jsonify({"error": "Investigation not found"}), 404
    except Exception as e:
        logger.error(f"Error closing investigation: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# Intelligence Endpoints
# ============================================================================

@app.route('/api/analyze/identity', methods=['POST'])
def analyze_identity():
    """Analyze and resolve identity."""
    try:
        data = request.get_json()
        entity_type = data.get('type')  # email, username, domain, person
        entity_value = data.get('value')
        
        if not entity_type or not entity_value:
            return jsonify({"error": "type and value required"}), 400
        
        if entity_type == "email":
            profile = identity_resolver.resolve_by_email(entity_value)
        elif entity_type == "username":
            profile = identity_resolver.resolve_by_username(entity_value)
        elif entity_type == "domain":
            profile = identity_resolver.resolve_by_domain(entity_value)
        elif entity_type == "person":
            profile = identity_resolver.resolve_by_person(entity_value)
        else:
            return jsonify({"error": f"Unknown entity type: {entity_type}"}), 400
        
        return jsonify({
            "status": "success",
            "profile": profile.to_dict()
        }), 200
    
    except Exception as e:
        logger.error(f"Error analyzing identity: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/analyze/pivot', methods=['POST'])
def analyze_pivot():
    """Find related entities and pivots."""
    try:
        data = request.get_json()
        entity_type = data.get('type')
        entity_value = data.get('value')
        
        if not entity_type or not entity_value:
            return jsonify({"error": "type and value required"}), 400
        
        entity = {"type": entity_type, "value": entity_value}
        
        # Get related entities
        related = entity_pivot.find_related_entities(entity)
        
        # Get suggestions
        suggestions = entity_pivot.suggest_pivots(entity)
        
        # Get graph data
        graph_data = entity_pivot.get_graph_data(entity, depth=2)
        
        return jsonify({
            "status": "success",
            "related_entities": [r.to_dict() for r in related[:10]],
            "suggestions": [
                {
                    "to_entity": s.to_entity,
                    "strength": round(s.strength, 3),
                    "justification": s.justification
                }
                for s in suggestions[:5]
            ],
            "graph": graph_data
        }), 200
    
    except Exception as e:
        logger.error(f"Error analyzing pivot: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/search/evidence', methods=['GET'])
def search_evidence():
    """Full-text search evidence."""
    try:
        query = request.args.get('q')
        limit = int(request.args.get('limit', 10))
        
        if not query:
            return jsonify({"error": "Query required"}), 400
        
        results = store.search(query, limit=limit)
        
        return jsonify({
            "status": "success",
            "query": query,
            "results": [
                {
                    "evidence_id": r.evidence_id,
                    "source_type": r.source_type,
                    "title": r.content.title if hasattr(r.content, 'title') else (r.content.get("title", "") if isinstance(r.content, dict) else ""),
                    "confidence": r.confidence,
                    "timestamp": r.timestamps.get("discovered", "") if isinstance(r.timestamps, dict) else getattr(r.timestamps, "discovered", "")
                }
                for r in results
            ],
            "total": len(results)
        }), 200
    
    except Exception as e:
        logger.error(f"Error searching evidence: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# Connector Endpoints
# ============================================================================

@app.route('/api/collect/web', methods=['POST'])
def collect_web():
    """Run web search via DuckDuckGo."""
    try:
        data = request.get_json()
        query = data.get('query')
        investigation_id = data.get('investigation_id')
        limit = data.get('limit', 5)
        
        if not query:
            return jsonify({"error": "Query required"}), 400
        
        results = ddg_connector.search(
            query,
            limit=limit,
            investigation_id=investigation_id,
            tags=data.get('tags', [])
        )
        
        # Store results
        for item in results:
            store.insert(item)
        
        return jsonify({
            "status": "success",
            "results": len(results),
            "investigation_id": investigation_id
        }), 200
    
    except Exception as e:
        logger.error(f"Error collecting web data: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/collect/breach', methods=['POST'])
def collect_breach():
    """Check for breach data via HIBP."""
    try:
        data = request.get_json()
        query = data.get('query')  # Email or domain
        investigation_id = data.get('investigation_id')
        
        if not query:
            return jsonify({"error": "Query required"}), 400
        
        results = hibp_connector.search(
            query,
            investigation_id=investigation_id,
            tags=data.get('tags', [])
        )
        
        # Store results
        for item in results:
            store.insert(item)
        
        return jsonify({
            "status": "success",
            "results": len(results),
            "investigation_id": investigation_id
        }), 200
    
    except Exception as e:
        logger.error(f"Error collecting breach data: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/collect/domain', methods=['POST'])
def collect_domain():
    """Gather domain intelligence."""
    try:
        data = request.get_json()
        domain = data.get('domain')
        investigation_id = data.get('investigation_id')
        
        if not domain:
            return jsonify({"error": "Domain required"}), 400
        
        results = domain_connector.search(
            domain,
            investigation_id=investigation_id,
            tags=data.get('tags', [])
        )
        
        # Store results
        for item in results:
            store.insert(item)
        
        return jsonify({
            "status": "success",
            "results": len(results),
            "investigation_id": investigation_id
        }), 200
    
    except Exception as e:
        logger.error(f"Error collecting domain data: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# Health & Status
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0"
    }), 200


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
                "investigations": len(inv_manager._investigations)
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    logger.info("Starting OSINT Platform API...")
    logger.info("Available endpoints:")
    logger.info("  POST   /api/investigations")
    logger.info("  GET    /api/investigations/<id>/summary")
    logger.info("  POST   /api/analyze/identity")
    logger.info("  POST   /api/analyze/pivot")
    logger.info("  GET    /api/health")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
