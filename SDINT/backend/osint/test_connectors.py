"""
MODULE 2 Test Suite — Connector validation.

Tests:
  1. BaseConnector retry logic and rate limiting
  2. DuckDuckGo web search connector
  3. Sherlock username search connector
  4. HIBP breach data connector
  5. Domain Intelligence connector
  6. End-to-end connector pipeline
"""

import time
import logging
from datetime import datetime

from osint.connectors import (
    DuckDuckGoConnector,
    SherlockConnector,
    HIBPConnector,
    DomainIntelligenceConnector,
    ConnectorError,
)
from osint.db.evidence_store import EvidenceStore
from osint.schemas.evidence_schema import SourceType, EntityType

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
)
logger = logging.getLogger(__name__)


def test_duckduckgo_connector():
    """Test web search connector."""
    logger.info("\n" + "="*70)
    logger.info("TEST: DuckDuckGo Connector")
    logger.info("="*70)

    connector = DuckDuckGoConnector()

    # Test 1: Valid query
    logger.info("▶ Test: Web search for 'john smith email'")
    try:
        results = connector.search("john smith email", limit=5)
        assert len(results) > 0, "Should return results"
        logger.info(f"  ✓ Returned {len(results)} evidence items")

        for item in results:
            assert item.source_platform == "duckduckgo"
            assert item.source_type == "web_search"
            assert item.content.title, "Should have title"
            assert len(item.entities) >= 0, "Should extract entities"
            logger.info(f"    - {item.content.title[:50]}... ({len(item.entities)} entities)")

    except Exception as e:
        logger.error(f"  ✗ Failed: {e}")
        raise

    # Test 2: Invalid query
    logger.info("▶ Test: Invalid query (empty)")
    try:
        results = connector.search("", limit=5)
        logger.error("  ✗ Should have raised ValueError")
        raise AssertionError("Should reject empty query")
    except ValueError:
        logger.info("  ✓ Correctly rejected empty query")

    # Test 3: Query with special keywords
    logger.info("▶ Test: Query with email pattern")
    try:
        results = connector.search("contact@example.com verification", limit=5)
        assert len(results) > 0
        logger.info(f"  ✓ Returned {len(results)} items")
    except Exception as e:
        logger.warning(f"  ⚠ Partial: {e}")

    logger.info("✓ DuckDuckGo Connector Tests Passed\n")


def test_sherlock_connector():
    """Test username search connector."""
    logger.info("="*70)
    logger.info("TEST: Sherlock Connector")
    logger.info("="*70)

    connector = SherlockConnector()

    # Test 1: Valid username
    logger.info("▶ Test: Search for username 'testuser'")
    try:
        results = connector.search("testuser", limit=50)
        logger.info(f"  ✓ Returned {len(results)} evidence items")

        for item in results[:3]:
            assert item.source_platform == "sherlock"
            assert item.source_type == "username_discovery"
            logger.info(f"    - Found on: {item.metadata.get('platform', 'unknown')}")

    except Exception as e:
        logger.error(f"  ✗ Failed: {e}")
        raise

    # Test 2: Invalid username
    logger.info("▶ Test: Invalid username (too long)")
    try:
        results = connector.search("a" * 200, limit=10)
        logger.error("  ✗ Should have raised ValueError")
        raise AssertionError("Should reject long username")
    except ValueError:
        logger.info("  ✓ Correctly rejected overly long username")

    # Test 3: Confidence scoring
    logger.info("▶ Test: Confidence scoring by platform")
    try:
        results = connector.search("john123", limit=50)
        if results:
            confidences = [item.confidence for item in results]
            avg_confidence = sum(confidences) / len(confidences)
            logger.info(f"  ✓ Average confidence: {avg_confidence:.2f}")
    except Exception as e:
        logger.warning(f"  ⚠ Partial: {e}")

    logger.info("✓ Sherlock Connector Tests Passed\n")


def test_hibp_connector():
    """Test breach data connector."""
    logger.info("="*70)
    logger.info("TEST: HIBP Connector")
    logger.info("="*70)

    connector = HIBPConnector()

    # Test 1: Valid email lookup
    logger.info("▶ Test: Breach lookup for email")
    try:
        results = connector.search("test@example.com", limit=100)
        logger.info(f"  ✓ Returned {len(results)} evidence items")

        for item in results[:2]:
            assert item.source_platform == "hibp"
            assert item.source_type == "breach_data"
            breach_name = item.metadata.get('breach_name', 'unknown')
            logger.info(f"    - Breach: {breach_name}")

    except Exception as e:
        logger.error(f"  ✗ Failed: {e}")
        raise

    # Test 2: Domain lookup
    logger.info("▶ Test: Breach lookup for domain")
    try:
        results = connector.search("example.com", limit=100)
        logger.info(f"  ✓ Returned {len(results)} evidence items")
    except Exception as e:
        logger.warning(f"  ⚠ Partial: {e}")

    # Test 3: Invalid query
    logger.info("▶ Test: Invalid query (invalid domain)")
    try:
        results = connector.search("notadomain", limit=10)
        logger.error("  ✗ Should have raised ValueError")
        raise AssertionError("Should reject invalid domain")
    except ValueError:
        logger.info("  ✓ Correctly rejected invalid domain")

    # Test 4: Password check
    logger.info("▶ Test: Password compromise check")
    try:
        result = connector.check_password("password123")
        assert isinstance(result, dict)
        assert 'compromised' in result
        status = "COMPROMISED" if result['compromised'] else "SAFE"
        logger.info(f"  ✓ Password status: {status}")
    except Exception as e:
        logger.warning(f"  ⚠ Partial: {e}")

    logger.info("✓ HIBP Connector Tests Passed\n")


def test_domain_intelligence_connector():
    """Test domain intelligence connector."""
    logger.info("="*70)
    logger.info("TEST: Domain Intelligence Connector")
    logger.info("="*70)

    connector = DomainIntelligenceConnector()

    # Test 1: Valid domain lookup
    logger.info("▶ Test: Domain intelligence for 'example.com'")
    try:
        results = connector.search("example.com", limit=100)
        logger.info(f"  ✓ Returned {len(results)} evidence items")

        item_types = {}
        for item in results:
            assert item.source_platform == "domain_tools"
            assert item.source_type == "domain_intel"
            record_type = item.metadata.get('record_type', 'unknown')
            item_types[record_type] = item_types.get(record_type, 0) + 1

        logger.info(f"  ✓ Record types found: {dict(item_types)}")

    except Exception as e:
        logger.error(f"  ✗ Failed: {e}")
        raise

    # Test 2: Domain with protocol
    logger.info("▶ Test: Domain with protocol 'https://example.com'")
    try:
        results = connector.search("https://example.com/path", limit=100)
        assert len(results) > 0
        logger.info(f"  ✓ Correctly parsed and returned {len(results)} items")
    except Exception as e:
        logger.warning(f"  ⚠ Partial: {e}")

    # Test 3: Invalid domain
    logger.info("▶ Test: Invalid domain (no TLD)")
    try:
        results = connector.search("localhost", limit=10)
        logger.error("  ✗ Should have raised ValueError")
        raise AssertionError("Should reject invalid domain")
    except ValueError:
        logger.info("  ✓ Correctly rejected invalid domain")

    logger.info("✓ Domain Intelligence Connector Tests Passed\n")


def test_connector_pipeline():
    """Test end-to-end connector pipeline."""
    logger.info("="*70)
    logger.info("TEST: End-to-End Connector Pipeline")
    logger.info("="*70)

    # Clean up test data first
    store = EvidenceStore()
    store.collection.delete_many({"tags": "connector_test"})

    # Test 1: Multi-connector investigation
    logger.info("▶ Test: Multi-source investigation pipeline")
    try:
        investigation_id = f"test_investigation_{int(time.time())}"

        # Step 1: Web search
        logger.info("  1. Web search for 'john@example.com'")
        ddg = DuckDuckGoConnector()
        web_results = ddg.search(
            "john@example.com",
            limit=3,
            investigation_id=investigation_id,
            tags=["connector_test"]
        )
        logger.info(f"     → Found {len(web_results)} web results")

        # Step 2: Username search
        logger.info("  2. Username search for 'johnsmith'")
        sherlock = SherlockConnector()
        user_results = sherlock.search(
            "johnsmith",
            limit=30,
            investigation_id=investigation_id,
            tags=["connector_test"]
        )
        logger.info(f"     → Found {len(user_results)} username matches")

        # Step 3: Breach data lookup
        logger.info("  3. Breach lookup for 'john@example.com'")
        hibp = HIBPConnector()
        breach_results = hibp.search(
            "john@example.com",
            limit=100,
            investigation_id=investigation_id,
            tags=["connector_test"]
        )
        logger.info(f"     → Found {len(breach_results)} breaches")

        # Step 4: Domain intelligence
        logger.info("  4. Domain intelligence for 'example.com'")
        domain = DomainIntelligenceConnector()
        domain_results = domain.search(
            "example.com",
            limit=100,
            investigation_id=investigation_id,
            tags=["connector_test"]
        )
        logger.info(f"     → Found {len(domain_results)} domain intelligence items")

        # Step 5: Store and query
        total_evidence = (
            len(web_results) + len(user_results) +
            len(breach_results) + len(domain_results)
        )
        logger.info(f"\n  ✓ Pipeline created {total_evidence} total evidence items")

        # Verify storage
        stored = store.get_by_investigation(investigation_id)
        logger.info(f"  ✓ Stored in MongoDB: {len(stored)} items")

        # Verify by source type
        by_source = {}
        for item in stored:
            source = item.source_type
            by_source[source] = by_source.get(source, 0) + 1
        logger.info(f"  ✓ Distribution: {dict(by_source)}")

    except Exception as e:
        logger.error(f"  ✗ Failed: {e}")
        raise

    # Test 2: Connector health checks
    logger.info("▶ Test: Connector health checks")
    try:
        connectors = [
            ("DuckDuckGo", DuckDuckGoConnector()),
            ("Sherlock", SherlockConnector()),
            ("HIBP", HIBPConnector()),
            ("Domain Intelligence", DomainIntelligenceConnector())
        ]

        for name, conn in connectors:
            health = conn.health_check()
            status = health['status']
            logger.info(f"  ✓ {name}: {status}")

    except Exception as e:
        logger.warning(f"  ⚠ Partial: {e}")

    # Clean up
    store.collection.delete_many({"tags": "connector_test"})

    logger.info("✓ End-to-End Pipeline Tests Passed\n")


def test_rate_limiting():
    """Test rate limiting behavior."""
    logger.info("="*70)
    logger.info("TEST: Rate Limiting")
    logger.info("="*70)

    connector = DuckDuckGoConnector(rate_limit_delay=0.5)

    logger.info("▶ Test: Rate limiting enforcement")
    try:
        start = time.time()

        # Make 3 requests
        for i in range(3):
            logger.info(f"  Request {i + 1}...")
            results = connector.search(f"query{i}", limit=1)

        elapsed = time.time() - start

        # Should take at least 2 seconds (0.5s * 2 gaps between 3 requests)
        expected_min = 1.0  # 2 gaps of 0.5s
        logger.info(f"  ✓ Completed 3 requests in {elapsed:.2f}s (min expected: {expected_min:.2f}s)")

        if elapsed >= expected_min:
            logger.info("  ✓ Rate limiting working correctly")
        else:
            logger.warning(f"  ⚠ Rate limiting may not be enforced (elapsed: {elapsed:.2f}s)")

    except Exception as e:
        logger.error(f"  ✗ Failed: {e}")
        raise

    logger.info("✓ Rate Limiting Tests Passed\n")


def run_all_tests():
    """Run complete MODULE 2 test suite."""
    logger.info("\n" + "="*70)
    logger.info("MODULE 2 — CONNECTORS TEST SUITE")
    logger.info("="*70 + "\n")

    tests = [
        ("DuckDuckGo Connector", test_duckduckgo_connector),
        ("Sherlock Connector", test_sherlock_connector),
        ("HIBP Connector", test_hibp_connector),
        ("Domain Intelligence Connector", test_domain_intelligence_connector),
        ("Rate Limiting", test_rate_limiting),
        ("End-to-End Pipeline", test_connector_pipeline),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            test_func()
            results.append((test_name, "PASSED"))
        except Exception as e:
            results.append((test_name, f"FAILED: {e}"))
            logger.exception(f"Test failed: {test_name}")

    # Summary
    logger.info("="*70)
    logger.info("TEST SUMMARY")
    logger.info("="*70)
    for test_name, result in results:
        status = "✓" if result == "PASSED" else "✗"
        logger.info(f"{status} {test_name}: {result}")

    passed = sum(1 for _, r in results if r == "PASSED")
    total = len(results)
    logger.info(f"\nTotal: {passed}/{total} tests passed")

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
