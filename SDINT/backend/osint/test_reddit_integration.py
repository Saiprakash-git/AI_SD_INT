"""
MODULE 1 — Reddit Integration Test

Tests Reddit data conversion to evidence items.
Validates that all Reddit data types (posts, comments, users)
correctly map to the evidence schema.
"""

import sys
import os
import logging
from datetime import datetime, timedelta
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.mongo_client import db, posts_collection, comments_collection
from osint.extractors.reddit_converter import RedditConverter
from osint.db.evidence_store import EvidenceStore
from osint.schemas.evidence_schema import SourceType, EntityType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestRedditIntegration:
    """Test Reddit → Evidence conversion pipeline."""
    
    def __init__(self):
        self.store = EvidenceStore()
        self.converter = RedditConverter()
        self.test_results = {"passed": 0, "failed": 0, "errors": []}
    
    def setup_test_data(self):
        """Create test Reddit data in MongoDB."""
        logger.info("Setting up test Reddit data...")
        
        # Clear test data
        posts_collection.delete_many({"_test": True})
        comments_collection.delete_many({"_test": True})
        
        base_time = datetime.utcnow()
        
        # Create test posts
        posts = [
            {
                "_test": True,
                "post_id": "test_post_1",
                "title": "John Smith discusses new AI framework at Google",
                "content": "Check out my research at https://github.com/example. Contact me at john.smith@example.com or @johnsmith on Twitter.",
                "subreddit": "MachineLearning",
                "score": 100,
                "number_of_comments": 5,
                "timestamp": base_time,
                "created_utc": base_time.timestamp()
            },
            {
                "_test": True,
                "post_id": "test_post_2",
                "title": "Discussion about cybersecurity",
                "content": "Recent breach: example.com was compromised. More info at https://security-news.com",
                "subreddit": "cybersecurity",
                "score": 50,
                "number_of_comments": 3,
                "timestamp": base_time - timedelta(hours=1),
                "created_utc": (base_time - timedelta(hours=1)).timestamp()
            }
        ]
        
        posts_collection.insert_many(posts)
        
        # Create test comments
        comments = [
            {
                "_test": True,
                "comment_id": "test_comment_1",
                "post_id": "test_post_1",
                "text": "Great article! Similar work by jane_doe@research.org",
                "author": "tech_enthusiast",
                "score": 20,
                "timestamp": base_time,
                "created_utc": base_time.timestamp()
            },
            {
                "_test": True,
                "comment_id": "test_comment_2",
                "post_id": "test_post_1",
                "text": "Check my profile: https://johndoe.dev - we should collaborate!",
                "author": "johndoe",
                "score": 15,
                "timestamp": base_time + timedelta(minutes=10),
                "created_utc": (base_time + timedelta(minutes=10)).timestamp()
            },
            {
                "_test": True,
                "comment_id": "test_comment_3",
                "post_id": "test_post_2",
                "text": "I got my data from a breach. Email: leaked_account@gmail.com",
                "author": "anonymous_user",
                "score": 5,
                "timestamp": base_time - timedelta(minutes=30),
                "created_utc": (base_time - timedelta(minutes=30)).timestamp()
            }
        ]
        
        comments_collection.insert_many(comments)
        logger.info(f"Created {len(posts)} test posts and {len(comments)} test comments")
    
    def test_reddit_post_conversion(self):
        """Test Reddit post → evidence conversion."""
        logger.info("TEST: Reddit post conversion...")
        try:
            # Get test post
            post = posts_collection.find_one({"_test": True, "post_id": "test_post_1"})
            assert post is not None, "Test post not found"
            
            # Convert
            from osint.services.evidence_builder import EvidenceBuilder
            item = EvidenceBuilder.from_reddit_post(post)
            
            assert item.source_type == SourceType.REDDIT_POST.value, "Wrong source type"
            assert item.source_platform == "reddit", "Wrong platform"
            assert item.source_id == "test_post_1", "Wrong source ID"
            assert len(item.entities) > 0, "Should extract entities from post"
            
            # Check extracted entities
            emails = [e for e in item.entities if e.type == EntityType.EMAIL.value]
            urls = [e for e in item.entities if e.type == EntityType.URL.value]
            usernames = [e for e in item.entities if e.type == EntityType.USERNAME.value]
            
            logger.info(f"  Emails: {len(emails)}, URLs: {len(urls)}, Usernames: {len(usernames)}")
            
            assert len(emails) > 0, "Should extract email"
            assert len(urls) > 0, "Should extract URL"
            
            # Check metadata
            assert item.metadata.get("subreddit") == "MachineLearning", "Metadata not captured"
            assert item.metadata.get("score") == 100, "Score not captured"
            
            self.test_results["passed"] += 1
            logger.info("✓ Reddit post conversion passed")
        except Exception as e:
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"Post conversion: {e}")
            logger.error(f"✗ Reddit post conversion failed: {e}")
    
    def test_reddit_comment_conversion(self):
        """Test Reddit comment → evidence conversion."""
        logger.info("TEST: Reddit comment conversion...")
        try:
            # Get test comment
            comment = comments_collection.find_one({"_test": True, "comment_id": "test_comment_1"})
            assert comment is not None, "Test comment not found"
            
            # Convert
            from osint.services.evidence_builder import EvidenceBuilder
            item = EvidenceBuilder.from_reddit_comment(comment)
            
            assert item.source_type == SourceType.REDDIT_COMMENT.value, "Wrong source type"
            assert item.source_platform == "reddit", "Wrong platform"
            assert len(item.entities) > 0, "Should extract entities from comment"
            
            # Should have author as username entity
            author_entities = [e for e in item.entities if e.type == EntityType.USERNAME.value and e.value == "tech_enthusiast"]
            assert len(author_entities) > 0, "Should extract author as username"
            
            self.test_results["passed"] += 1
            logger.info("✓ Reddit comment conversion passed")
        except Exception as e:
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"Comment conversion: {e}")
            logger.error(f"✗ Reddit comment conversion failed: {e}")
    
    def test_reddit_converter_batch(self):
        """Test batch Reddit → Evidence conversion."""
        logger.info("TEST: Batch Reddit conversion...")
        try:
            # Clear evidence store (test data)
            self.store.collection.delete_many({"investigation_id": "test_reddit_batch"})
            
            # Set investigation ID
            converter = RedditConverter(investigation_id="test_reddit_batch")
            
            # Convert only test data
            stats = converter.convert_posts(limit=10)
            
            logger.info(f"  Posts converted: {stats['posts_converted']}, skipped: {stats['posts_skipped']}")
            
            # Verify items in store
            test_items = list(self.store.collection.find({"investigation_id": "test_reddit_batch"}))
            logger.info(f"  Items in store: {len(test_items)}")
            
            assert len(test_items) > 0, "Should have converted items"
            
            # Check for email extraction
            email_results = self.store.get_by_entity(EntityType.EMAIL.value, "john.smith@example.com")
            email_count = len(email_results)
            logger.info(f"  Email mentions: {email_count}")
            
            self.test_results["passed"] += 1
            logger.info("✓ Batch Reddit conversion passed")
        except Exception as e:
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"Batch conversion: {e}")
            logger.error(f"✗ Batch Reddit conversion failed: {e}")
        finally:
            # Clean up test evidence
            self.store.collection.delete_many({"investigation_id": "test_reddit_batch"})
    
    def test_reddit_to_evidence_entity_extraction(self):
        """Test entity extraction quality in Reddit → Evidence."""
        logger.info("TEST: Reddit → Evidence entity extraction...")
        try:
            # Get a complex post with multiple entity types
            post = posts_collection.find_one({"_test": True, "post_id": "test_post_1"})
            
            from osint.services.evidence_builder import EvidenceBuilder
            item = EvidenceBuilder.from_reddit_post(post)
            
            # Count entities by type
            entity_summary = {}
            for entity in item.entities:
                entity_type = entity.type
                entity_summary[entity_type] = entity_summary.get(entity_type, 0) + 1
            
            logger.info(f"  Entity distribution: {entity_summary}")
            
            # Validate confidence scores
            for entity in item.entities:
                assert 0.0 <= entity.confidence <= 1.0, f"Invalid confidence: {entity.confidence}"
            
            # Check source attribution
            for entity in item.entities:
                assert entity.source in ["ner", "regex", "structural"], f"Invalid source: {entity.source}"
            
            self.test_results["passed"] += 1
            logger.info("✓ Reddit → Evidence entity extraction passed")
        except Exception as e:
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"Entity extraction: {e}")
            logger.error(f"✗ Reddit → Evidence entity extraction failed: {e}")
    
    def cleanup(self):
        """Clean up test data."""
        logger.info("Cleaning up test data...")
        posts_collection.delete_many({"_test": True})
        comments_collection.delete_many({"_test": True})
        logger.info("Test data cleaned up")
    
    def run_all_tests(self):
        """Run all integration tests."""
        logger.info("=" * 70)
        logger.info("MODULE 1 — REDDIT INTEGRATION TEST")
        logger.info("=" * 70)
        
        try:
            self.setup_test_data()
            
            self.test_reddit_post_conversion()
            self.test_reddit_comment_conversion()
            self.test_reddit_to_evidence_entity_extraction()
            self.test_reddit_converter_batch()
            
        finally:
            self.cleanup()
        
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
    suite = TestRedditIntegration()
    success = suite.run_all_tests()
    sys.exit(0 if success else 1)
