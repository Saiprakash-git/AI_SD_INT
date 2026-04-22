"""
Evidence Store — MongoDB CRUD operations for evidence items.

Handles all database interactions for the evidence_items collection:
  - Insert with deduplication
  - Query by ID, source, entity, investigation
  - Full-text search across content
  - Statistics and aggregation
  - Index management

All methods work with EvidenceItem dataclass objects, handling
serialization/deserialization transparently.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone

import sys
import os

backend_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
project_root = os.path.dirname(backend_root)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.db.mongo_client import db
from osint.schemas.evidence_schema import (
    EvidenceItem,
    EvidenceStatus,
    validate_evidence_item,
)

logger = logging.getLogger(__name__)

# MongoDB collection for evidence items
evidence_collection = db["evidence_items"]


class EvidenceStore:
    """
    Data access layer for evidence items in MongoDB.
    
    Usage:
        store = EvidenceStore()
        store.insert(evidence_item)
        results = store.search("john doe")
        by_entity = store.get_by_entity("email", "john@example.com")
    """

    def __init__(self):
        self.collection = evidence_collection
        self._ensure_indexes()

    def _ensure_indexes(self):
        """Create MongoDB indexes for optimal query performance."""
        try:
            # Unique constraint on evidence_id
            self.collection.create_index("evidence_id", unique=True)

            # Common query patterns
            self.collection.create_index("source_type")
            self.collection.create_index("source_id")
            self.collection.create_index("source_platform")
            self.collection.create_index("status")
            self.collection.create_index("investigation_id")
            self.collection.create_index("confidence")

            # Entity-based queries (compound index on nested array fields)
            self.collection.create_index("entities.type")
            self.collection.create_index("entities.value")
            self.collection.create_index([("entities.type", 1), ("entities.value", 1)])

            # Tag-based queries
            self.collection.create_index("tags")

            # Full-text search on content fields
            self.collection.create_index(
                [("content.title", "text"), ("content.body", "text")],
                name="content_text_index",
                default_language="english",
            )

            # Timestamp-based sorting
            self.collection.create_index("timestamps.collected_at")
            self.collection.create_index("timestamps.source_created")

            # Dedup index: prevent duplicate source items
            self.collection.create_index(
                [("source_type", 1), ("source_id", 1)],
                unique=True,
                name="source_dedup_index",
            )

            logger.info("Evidence store indexes created/verified.")
        except Exception as e:
            # Indexes may already exist — log but don't crash
            logger.debug(f"Index creation note: {e}")

    # ─── Insert Operations ────────────────────────────────────────────────

    def insert(self, item: EvidenceItem) -> bool:
        """
        Insert an evidence item into the store.
        Skips duplicates based on (source_type, source_id).
        
        Returns:
            True if inserted, False if skipped (duplicate)
        """
        # Validate before insert
        is_valid, errors = validate_evidence_item(item)
        if not is_valid:
            logger.warning(f"Invalid evidence item {item.evidence_id}: {errors}")
            return False

        try:
            self.collection.insert_one(item.to_dict())
            return True
        except Exception as e:
            if "duplicate key" in str(e).lower() or "E11000" in str(e):
                logger.debug(f"Duplicate evidence skipped: {item.source_type}/{item.source_id}")
                return False
            logger.error(f"Failed to insert evidence {item.evidence_id}: {e}")
            raise

    def insert_many(self, items: List[EvidenceItem]) -> Dict[str, int]:
        """
        Bulk insert evidence items, skipping duplicates.
        
        Returns:
            {"inserted": N, "skipped": M, "errors": E}
        """
        stats = {"inserted": 0, "skipped": 0, "errors": 0}

        for item in items:
            try:
                if self.insert(item):
                    stats["inserted"] += 1
                else:
                    stats["skipped"] += 1
            except Exception:
                stats["errors"] += 1

        return stats

    # ─── Query Operations ─────────────────────────────────────────────────

    def get_by_id(self, evidence_id: str) -> Optional[EvidenceItem]:
        """Fetch a single evidence item by its unique ID."""
        doc = self.collection.find_one({"evidence_id": evidence_id})
        if doc:
            return EvidenceItem.from_dict(doc)
        return None

    def get_by_source(self, source_type: str, source_id: str) -> Optional[EvidenceItem]:
        """Fetch evidence by its original source identifiers."""
        doc = self.collection.find_one({"source_type": source_type, "source_id": source_id})
        if doc:
            return EvidenceItem.from_dict(doc)
        return None

    def exists_by_source(self, source_type: str, source_id: str) -> bool:
        """Check if evidence from a specific source already exists."""
        return self.collection.count_documents(
            {"source_type": source_type, "source_id": source_id},
            limit=1
        ) > 0

    def get_by_entity(self, entity_type: str, entity_value: str,
                      limit: int = 50) -> List[EvidenceItem]:
        """
        Find all evidence containing a specific entity.
        
        Args:
            entity_type: EntityType value (e.g., "email", "username")
            entity_value: The entity value to search for
            limit: Max results
            
        Returns:
            List of matching EvidenceItem objects
        """
        # Case-insensitive search on entity value
        query = {
            "entities": {
                "$elemMatch": {
                    "type": entity_type,
                    "value": {"$regex": f"^{entity_value}$", "$options": "i"}
                }
            }
        }
        docs = list(self.collection.find(query).limit(limit))
        return [EvidenceItem.from_dict(d) for d in docs]

    def search(self, query_text: str, limit: int = 50,
               source_type: Optional[str] = None) -> List[EvidenceItem]:
        """
        Full-text search across evidence content.
        
        Args:
            query_text: Search query
            limit: Max results
            source_type: Optional filter by source type
            
        Returns:
            List of matching EvidenceItem objects sorted by relevance
        """
        search_query = {"$text": {"$search": query_text}}
        if source_type:
            search_query["source_type"] = source_type

        docs = list(
            self.collection.find(
                search_query,
                {"score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"})]).limit(limit)
        )
        return [EvidenceItem.from_dict(d) for d in docs]

    def get_by_investigation(self, investigation_id: str,
                             limit: int = 200) -> List[EvidenceItem]:
        """Get all evidence linked to a specific investigation."""
        docs = list(
            self.collection.find({"investigation_id": investigation_id})
            .sort("timestamps.collected_at", -1)
            .limit(limit)
        )
        return [EvidenceItem.from_dict(d) for d in docs]

    def get_by_tags(self, tags: List[str], limit: int = 50) -> List[EvidenceItem]:
        """Get evidence matching any of the specified tags."""
        docs = list(
            self.collection.find({"tags": {"$in": tags}})
            .sort("timestamps.collected_at", -1)
            .limit(limit)
        )
        return [EvidenceItem.from_dict(d) for d in docs]

    def get_recent(self, limit: int = 20,
                   source_type: Optional[str] = None) -> List[EvidenceItem]:
        """Get the most recently collected evidence items."""
        query = {}
        if source_type:
            query["source_type"] = source_type

        docs = list(
            self.collection.find(query)
            .sort("timestamps.collected_at", -1)
            .limit(limit)
        )
        return [EvidenceItem.from_dict(d) for d in docs]

    # ─── Update Operations ────────────────────────────────────────────────

    def update_status(self, evidence_id: str, new_status: str) -> bool:
        """Update the status of an evidence item."""
        if new_status not in [s.value for s in EvidenceStatus]:
            logger.warning(f"Invalid status: {new_status}")
            return False

        result = self.collection.update_one(
            {"evidence_id": evidence_id},
            {"$set": {"status": new_status}}
        )
        return result.modified_count > 0

    def add_entities(self, evidence_id: str, entities: List[Dict[str, Any]]) -> bool:
        """Append new entities to an existing evidence item."""
        result = self.collection.update_one(
            {"evidence_id": evidence_id},
            {
                "$push": {"entities": {"$each": entities}},
                "$set": {"timestamps.processed_at": datetime.now(timezone.utc).isoformat()}
            }
        )
        return result.modified_count > 0

    def link_to_investigation(self, evidence_id: str, investigation_id: str) -> bool:
        """Link an evidence item to an investigation."""
        result = self.collection.update_one(
            {"evidence_id": evidence_id},
            {"$set": {"investigation_id": investigation_id}}
        )
        return result.modified_count > 0

    # ─── Aggregation / Statistics ─────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        """Get overall evidence store statistics."""
        total = self.collection.count_documents({})

        # Count by source type
        source_pipeline = [
            {"$group": {"_id": "$source_type", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        by_source = {doc["_id"]: doc["count"] for doc in self.collection.aggregate(source_pipeline)}

        # Count by status
        status_pipeline = [
            {"$group": {"_id": "$status", "count": {"$sum": 1}}}
        ]
        by_status = {doc["_id"]: doc["count"] for doc in self.collection.aggregate(status_pipeline)}

        # Entity type distribution
        entity_pipeline = [
            {"$unwind": "$entities"},
            {"$group": {"_id": "$entities.type", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        by_entity_type = {doc["_id"]: doc["count"] for doc in self.collection.aggregate(entity_pipeline)}

        # Top entities by frequency
        top_entities_pipeline = [
            {"$unwind": "$entities"},
            {"$group": {"_id": {"type": "$entities.type", "value": "$entities.value"}, "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 20}
        ]
        top_entities = [
            {"type": doc["_id"]["type"], "value": doc["_id"]["value"], "count": doc["count"]}
            for doc in self.collection.aggregate(top_entities_pipeline)
        ]

        return {
            "total_evidence_items": total,
            "by_source_type": by_source,
            "by_status": by_status,
            "entity_type_distribution": by_entity_type,
            "top_entities": top_entities,
        }

    def get_entity_network(self, entity_type: str, entity_value: str) -> Dict[str, Any]:
        """
        Get the co-occurrence network for a specific entity.
        Returns other entities that appear alongside the target entity.
        Useful for Module 3 (identity resolution) and Module 4 (graph building).
        """
        # Find all evidence containing this entity
        matching_docs = list(self.collection.find(
            {"entities": {"$elemMatch": {"type": entity_type, "value": {"$regex": f"^{entity_value}$", "$options": "i"}}}},
            {"entities": 1, "source_type": 1}
        ).limit(100))

        # Aggregate co-occurring entities
        co_occurring = {}
        for doc in matching_docs:
            for entity in doc.get("entities", []):
                key = f"{entity['type']}:{entity['value']}"
                if entity["type"] == entity_type and entity["value"].lower() == entity_value.lower():
                    continue  # Skip self
                if key not in co_occurring:
                    co_occurring[key] = {
                        "type": entity["type"],
                        "value": entity["value"],
                        "co_occurrence_count": 0,
                        "sources": set()
                    }
                co_occurring[key]["co_occurrence_count"] += 1
                co_occurring[key]["sources"].add(doc.get("source_type", ""))

        # Convert sets to lists for JSON serialization
        network = []
        for key, data in co_occurring.items():
            data["sources"] = list(data["sources"])
            network.append(data)

        network.sort(key=lambda x: x["co_occurrence_count"], reverse=True)

        return {
            "target": {"type": entity_type, "value": entity_value},
            "evidence_count": len(matching_docs),
            "co_occurring_entities": network[:50],
        }
