"""
MODULE 1 — Evidence Engine Test Suite

Tests all components of the evidence engine:
- Schema validation
- Entity extraction (NER + regex)
- Evidence item creation
- Reddit conversion
- Database operations
"""

import sys
import os
import logging
from datetime import datetime, timezone

# Ensure imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from osint.schemas.evidence_schema import (
    EvidenceItem, EntityRecord, EvidenceContent, EvidenceTimestamps,
    SourceType, EntityType, EvidenceStatus, generate_evidence_id, validate_evidence_item
)
from osint.extractors.entity_extractor import EntityExtractor
from osint.services.evidence_builder import EvidenceBuilder
from osint.db.evidence_store import EvidenceStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestEvidenceEngine:
    """Comprehensive tests for Module 1."""
    
    def __init__(self):
        self.extractor = EntityExtractor()
        self.store = EvidenceStore()
        self.test_results = {"passed": 0, "failed": 0, "errors": []}
    
    def test_schema_generation(self):
        """Test evidence_id generation."""
        logger.info("TEST: Evidence ID generation...")
        try:
            id1 = generate_evidence_id()
            id2 = generate_evidence_id()
            
            assert id1.startswith("evi_"), "ID should start with 'evi_'"
            assert len(id1) == 24, f"ID should be 24 chars, got {len(id1)}"
            assert id1 != id2, "IDs should be unique"
            
            self.test_results["passed"] += 1
            logger.info("✓ Evidence ID generation passed")
        except Exception as e:
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"ID generation: {e}")
            logger.error(f"✗ Evidence ID generation failed: {e}")
    
    def test_entity_extraction_regex(self):
        """Test regex entity extraction."""
        logger.info("TEST: Entity extraction (regex)...")
        try:
            text = "Contact john@example.com or @johndoe on Twitter. Visit https://example.com. Bitcoin: 1A1z7agoat2SJVQWCVPEASSXXUAMNUHTH"
            entities = self.extractor.extract(text)
            
            assert len(entities) > 0, "Should extract entities"
            
            # Check for email
            emails = [e for e in entities if e["type"] == "email"]
            assert len(emails) > 0, "Should extract email"
            assert any(e["value"] == "john@example.com" for e in emails), "Should extract correct email"
            
            # Check for URL
            urls = [e for e in entities if e["type"] == "url"]
            assert len(urls) > 0, "Should extract URL"
            
            # Check for username
            usernames = [e for e in entities if e["type"] == "username"]
            assert len(usernames) > 0, "Should extract username"
            
            self.test_results["passed"] += 1
            logger.info(f"✓ Entity extraction (regex) passed - extracted {len(entities)} entities")
        except Exception as e:
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"Regex extraction: {e}")
            logger.error(f"✗ Entity extraction (regex) failed: {e}")
    
    def test_entity_extraction_ner(self):
        """Test NER entity extraction."""
        logger.info("TEST: Entity extraction (NER)...")
        try:
            text = "John Smith works at Google in San Francisco. The article was published on January 15, 2025."
            entities = self.extractor.extract(text)
            
            assert len(entities) > 0, "Should extract entities with NER"
            
            # Should extract persons, organizations, locations
            entity_types = {e["type"] for e in entities}
            logger.info(f"  Extracted entity types: {entity_types}")
            
            self.test_results["passed"] += 1
            logger.info(f"✓ Entity extraction (NER) passed - found types: {entity_types}")
        except Exception as e:
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"NER extraction: {e}")
            logger.error(f"✗ Entity extraction (NER) failed: {e}")
    
    def test_evidence_item_creation(self):
        """Test EvidenceItem creation and validation."""
        logger.info("TEST: Evidence item creation...")
        try:
            item = EvidenceItem(
                evidence_id=generate_evidence_id(),
                source_type=SourceType.WEB_SEARCH.value,
                source_id="search_001",
                source_platform="duckduckgo",
                content=EvidenceContent(
                    title="Test Search Result",
                    body="This is test content",
                    url="https://example.com"
                ),
                entities=[
                    EntityRecord(
                        type=EntityType.EMAIL.value,
                        value="test@example.com",
                        confidence=1.0,
                        source="regex"
                    )
                ],
                metadata={"search_query": "test"},
                timestamps=EvidenceTimestamps(
                    source_created=datetime.now(timezone.utc).isoformat(),
                    collected_at=datetime.now(timezone.utc).isoformat()
                ),
                confidence=0.85,
                tags=["test", "search"],
                status=EvidenceStatus.PROCESSED.value
            )
            
            # Validate
            is_valid, errors = validate_evidence_item(item)
            assert is_valid, f"Validation failed: {errors}"
            
            # Serialize/deserialize
            item_dict = item.to_dict()
            item_restored = EvidenceItem.from_dict(item_dict)
            assert item_restored.evidence_id == item.evidence_id, "Deserialization failed"
            
            self.test_results["passed"] += 1
            logger.info("✓ Evidence item creation passed")
        except Exception as e:
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"Item creation: {e}")
            logger.error(f"✗ Evidence item creation failed: {e}")
    
    def test_evidence_builder_raw(self):
        """Test EvidenceBuilder.from_raw factory method."""
        logger.info("TEST: Evidence builder (from_raw)...")
        try:
            item = EvidenceBuilder.from_raw(
                source_type=SourceType.WEB_SEARCH.value,
                source_id="ddg_001",
                source_platform="duckduckgo",
                title="Search Result",
                body="John Smith contacted jane@example.com about the project",
                url="https://example.com/result",
                metadata={"query": "contact info"},
                confidence=0.75,
                tags=["contact", "search"],
                extract_entities=True
            )
            
            assert item.evidence_id.startswith("evi_"), "Should generate ID"
            assert len(item.entities) > 0, "Should extract entities"
            assert any(e.type == EntityType.EMAIL.value for e in item.entities), "Should find email"
            
            # Validate
            is_valid, errors = validate_evidence_item(item)
            assert is_valid, f"Validation failed: {errors}"
            
            self.test_results["passed"] += 1
            logger.info(f"✓ Evidence builder (from_raw) passed - {len(item.entities)} entities extracted")
        except Exception as e:
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"Builder from_raw: {e}")
            logger.error(f"✗ Evidence builder (from_raw) failed: {e}")
    
    def test_evidence_store_dedup(self):
        """Test evidence store deduplication logic."""
        logger.info("TEST: Evidence store deduplication...")
        try:
            item1 = EvidenceBuilder.from_raw(
                source_type=SourceType.MANUAL.value,
                source_id="manual_001",
                source_platform="test",
                title="Test Item",
                body="Test content"
            )
            
            # Try to insert duplicate (should be skipped)
            item2 = EvidenceBuilder.from_raw(
                source_type=SourceType.MANUAL.value,
                source_id="manual_001",  # Same source ID
                source_platform="test",
                title="Different Title",
                body="Different content"
            )
            
            result1 = self.store.insert(item1)
            result2 = self.store.insert(item2)
            
            assert result1 == True, "First insert should succeed"
            assert result2 == False, "Duplicate insert should be skipped"
            
            self.test_results["passed"] += 1
            logger.info("✓ Evidence store deduplication passed")
        except Exception as e:
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"Store dedup: {e}")
            logger.error(f"✗ Evidence store deduplication failed: {e}")
            # Clean up
            self.store.collection.delete_one({"source_type": SourceType.MANUAL.value, "source_id": "manual_001"})
    
    def test_evidence_store_queries(self):
        """Test evidence store query operations."""
        logger.info("TEST: Evidence store queries...")
        try:
            # Create and insert test items
            items = [
                EvidenceBuilder.from_raw(
                    source_type=SourceType.WEB_SEARCH.value,
                    source_id=f"query_test_{i}",
                    source_platform="duckduckgo",
                    title=f"Result {i}",
                    body=f"Content {i} with email test{i}@example.com",
                    tags=["query_test"]
                )
                for i in range(3)
            ]
            
            for item in items:
                self.store.insert(item)
            
            # Test get_by_tags
            results = self.store.get_by_tags(["query_test"], limit=10)
            assert len(results) >= 3, "Should retrieve tagged items"
            
            # Test get_by_entity
            email_results = self.store.get_by_entity(EntityType.EMAIL.value, "test0@example.com")
            assert len(email_results) > 0, "Should find by entity"
            
            # Test search
            search_results = self.store.search("Content 1", limit=10)
            assert len(search_results) > 0, "Full-text search should work"
            
            self.test_results["passed"] += 1
            logger.info("✓ Evidence store queries passed")
        except Exception as e:
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"Store queries: {e}")
            logger.error(f"✗ Evidence store queries failed: {e}")
            # Clean up
            self.store.collection.delete_many({"tags": {"$in": ["query_test"]}})
    
    def test_evidence_store_stats(self):
        """Test evidence store statistics."""
        logger.info("TEST: Evidence store statistics...")
        try:
            stats = self.store.get_stats()
            
            assert "total_evidence_items" in stats, "Should have total count"
            assert "by_source_type" in stats, "Should have source type breakdown"
            assert "entity_type_distribution" in stats, "Should have entity distribution"
            
            logger.info(f"  Total items: {stats['total_evidence_items']}")
            logger.info(f"  Source types: {stats['by_source_type']}")
            
            self.test_results["passed"] += 1
            logger.info("✓ Evidence store statistics passed")
        except Exception as e:
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"Store stats: {e}")
            logger.error(f"✗ Evidence store statistics failed: {e}")
    
    def run_all_tests(self):
        """Run all tests."""
        logger.info("=" * 70)
        logger.info("MODULE 1 — EVIDENCE ENGINE TEST SUITE")
        logger.info("=" * 70)
        
        self.test_schema_generation()
        self.test_entity_extraction_regex()
        self.test_entity_extraction_ner()
        self.test_evidence_item_creation()
        self.test_evidence_builder_raw()
        self.test_evidence_store_dedup()
        self.test_evidence_store_queries()
        self.test_evidence_store_stats()
        
        logger.info("=" * 70)
        logger.info("TEST RESULTS")
        logger.info("=" * 70)
        logger.info(f"Passed: {self.test_results['passed']}")
        logger.info(f"Failed: {self.test_results['failed']}")
        
        if self.test_results["errors"]:
            logger.info("\nErrors:")
            for error in self.test_results["errors"]:
                logger.info(f"  - {error}")
        
        logger.info("=" * 70)
        
        return self.test_results["failed"] == 0


if __name__ == "__main__":
    suite = TestEvidenceEngine()
    success = suite.run_all_tests()
    sys.exit(0 if success else 1)
