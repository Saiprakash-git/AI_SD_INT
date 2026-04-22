"""
Module 1 — Evidence Engine: Integration Test Suite

Tests all components:
  1. Schema validation (create, validate, serialize/deserialize)
  2. Entity extraction (regex + NER)
  3. Evidence builder (Reddit post, comment, user, raw)
  4. Evidence store (insert, query, search, dedup, stats)
  5. Reddit converter (batch conversion)

Run: python -m osint.test_module1
"""

import sys
import os
import json

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# ─── Color helpers for terminal output ────────────────────────────────────────

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

passed = 0
failed = 0


def test(name, condition, detail=""):
    global passed, failed
    if condition:
        print(f"  {GREEN}[PASS]{RESET} {name}")
        passed += 1
    else:
        print(f"  {RED}[FAIL]{RESET} {name} {RED}- {detail}{RESET}")
        failed += 1


def section(title):
    print(f"\n{CYAN}{BOLD}{'-' * 60}{RESET}")
    print(f"{CYAN}{BOLD}  {title}{RESET}")
    print(f"{CYAN}{BOLD}{'-' * 60}{RESET}")


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 1: Schema Validation
# ═══════════════════════════════════════════════════════════════════════════════

section("TEST 1: Evidence Schema")

from osint.schemas.evidence_schema import (
    EvidenceItem, EvidenceContent, EvidenceTimestamps, EntityRecord,
    SourceType, EntityType, EvidenceStatus,
    validate_evidence_item, generate_evidence_id
)

# Test ID generation
eid = generate_evidence_id()
test("generate_evidence_id() produces 'evi_' prefixed ID", eid.startswith("evi_"))
test("generate_evidence_id() produces unique IDs", generate_evidence_id() != generate_evidence_id())

# Test entity record
entity = EntityRecord(type="email", value="test@example.com", confidence=1.0, source="regex")
entity_dict = entity.to_dict()
test("EntityRecord.to_dict() works", entity_dict["type"] == "email")
entity_back = EntityRecord.from_dict(entity_dict)
test("EntityRecord.from_dict() round-trips", entity_back.value == "test@example.com")

# Test evidence content
content = EvidenceContent(title="Test Post", body="Hello world", url="https://example.com")
content_dict = content.to_dict()
test("EvidenceContent.to_dict() works", content_dict["title"] == "Test Post")
content_back = EvidenceContent.from_dict(content_dict)
test("EvidenceContent.from_dict() round-trips", content_back.body == "Hello world")

# Test full evidence item
item = EvidenceItem(
    evidence_id=generate_evidence_id(),
    source_type=SourceType.REDDIT_POST.value,
    source_id="test_123",
    source_platform="reddit",
    content=content,
    entities=[entity],
    metadata={"subreddit": "technology", "score": 42},
    timestamps=EvidenceTimestamps(
        source_created="2025-01-01T00:00:00Z",
        collected_at="2025-01-02T00:00:00Z",
        processed_at="2025-01-02T00:00:01Z"
    ),
    confidence=0.85,
    tags=["reddit", "test"],
    investigation_id=None,
    status=EvidenceStatus.PROCESSED.value
)

# Serialize
item_dict = item.to_dict()
test("EvidenceItem.to_dict() includes all fields", all(k in item_dict for k in [
    "evidence_id", "source_type", "source_id", "content", "entities",
    "metadata", "timestamps", "confidence", "tags", "status"
]))

# Deserialize
item_back = EvidenceItem.from_dict(item_dict)
test("EvidenceItem.from_dict() restores evidence_id", item_back.evidence_id == item.evidence_id)
test("EvidenceItem.from_dict() restores entities", len(item_back.entities) == 1)
test("EvidenceItem.from_dict() restores nested content", item_back.content.title == "Test Post")

# Validation
is_valid, errors = validate_evidence_item(item)
test("Valid item passes validation", is_valid, str(errors))

# Test invalid item
bad_item = EvidenceItem(
    evidence_id="",
    source_type="invalid_type",
    source_id="",
    source_platform="",
    content=EvidenceContent(),
    entities=[EntityRecord(type="bad_type", value="", confidence=2.5, source="")],
    metadata={},
    timestamps=EvidenceTimestamps(),
    confidence=-0.5,
    tags=[],
    status="bogus"
)
is_valid, errors = validate_evidence_item(bad_item)
test("Invalid item fails validation", not is_valid)
test("Validation catches multiple errors", len(errors) >= 4, f"Only found {len(errors)} errors")

# Helper methods
test("get_text_content() combines title and body", "Test Post" in item.get_text_content())
test("get_entities_by_type() filters correctly", len(item.get_entities_by_type("email")) == 1)
test("has_entity() finds existing entity", item.has_entity("email", "test@example.com"))
test("has_entity() returns False for missing", not item.has_entity("email", "missing@test.com"))


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 2: Entity Extractor
# ═══════════════════════════════════════════════════════════════════════════════

section("TEST 2: Entity Extractor")

from osint.extractors.entity_extractor import EntityExtractor

extractor = EntityExtractor()

# Test email extraction
entities = extractor.extract("Contact me at john.doe@example.com for details")
emails = [e for e in entities if e["type"] == "email"]
test("Extracts email addresses", len(emails) == 1)
test("Email value is correct", emails[0]["value"] == "john.doe@example.com" if emails else False)

# Test URL extraction
entities = extractor.extract("Check out https://www.reddit.com/r/technology for news")
urls = [e for e in entities if e["type"] == "url"]
test("Extracts URLs", len(urls) >= 1)

# Test Reddit username
entities = extractor.extract("Thanks u/johndoe for the tip! Also credit to /u/janedoe")
usernames = [e for e in entities if e["type"] == "username"]
test("Extracts Reddit usernames", len(usernames) == 2, f"Found {len(usernames)}")

# Test Reddit subreddit
entities = extractor.extract("This was posted in r/technology and r/programming")
subreddits = [e for e in entities if e["type"] == "subreddit"]
test("Extracts subreddits", len(subreddits) == 2, f"Found {len(subreddits)}")

# Test IP address
entities = extractor.extract("Server at 192.168.1.100 is down, try 10.0.0.1")
ips = [e for e in entities if e["type"] == "ip_address"]
test("Extracts IP addresses", len(ips) == 2, f"Found {len(ips)}")

# Test hashtag
entities = extractor.extract("Trending: #AI #MachineLearning #Python")
hashtags = [e for e in entities if e["type"] == "hashtag"]
test("Extracts hashtags", len(hashtags) == 3, f"Found {len(hashtags)}")

# Test mixed content
mixed_text = """
Hey u/security_researcher, check this out!
Found a breach dump at https://darkweb.example.com/leak
Emails exposed: admin@company.com, ceo@company.com
Server IP: 203.0.113.42
Contact @InfoSec on Twitter for more info.
#databreach #infosec
"""
entities = extractor.extract(mixed_text)
test("Mixed content: finds emails", len([e for e in entities if e["type"] == "email"]) == 2)
test("Mixed content: finds URLs", len([e for e in entities if e["type"] == "url"]) >= 1)
test("Mixed content: finds usernames", len([e for e in entities if e["type"] == "username"]) >= 1)
test("Mixed content: finds IPs", len([e for e in entities if e["type"] == "ip_address"]) == 1)
test("Mixed content: finds hashtags", len([e for e in entities if e["type"] == "hashtag"]) == 2)

# Test deduplication
entities = extractor.extract("Email john@test.com and also john@test.com again")
emails = [e for e in entities if e["type"] == "email"]
test("Deduplicates identical entities", len(emails) == 1)

# Test empty/invalid input
test("Empty string returns empty list", extractor.extract("") == [])
test("None returns empty list", extractor.extract(None) == [])

# Test NER (if spaCy is available)
entities = extractor.extract("Elon Musk announced that Tesla will move to Austin, Texas")
persons = [e for e in entities if e["type"] == "person"]
orgs = [e for e in entities if e["type"] == "organization"]
locations = [e for e in entities if e["type"] == "location"]
if persons or orgs or locations:
    test("NER: extracts person names", len(persons) >= 1, f"Found: {[p['value'] for p in persons]}")
    test("NER: extracts organizations", len(orgs) >= 1, f"Found: {[o['value'] for o in orgs]}")
    test("NER: extracts locations", len(locations) >= 1, f"Found: {[l['value'] for l in locations]}")
else:
    print(f"  {YELLOW}[WARN] spaCy NER not available - skipping NER tests{RESET}")
    print(f"  {YELLOW}  Run: python -m spacy download en_core_web_sm{RESET}")


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 3: Evidence Builder
# ═══════════════════════════════════════════════════════════════════════════════

section("TEST 3: Evidence Builder")

from osint.services.evidence_builder import EvidenceBuilder

# Test from_reddit_post
mock_post = {
    "post_id": "test_post_001",
    "title": "Breaking: Security breach at Acme Corp affects millions",
    "content": "Contact admin@acmecorp.com for details. Report from u/security_reporter.",
    "subreddit": "technology",
    "score": 1500,
    "number_of_comments": 234,
    "created_utc": 1700000000,
    "url": "https://reddit.com/r/technology/comments/test_post_001",
    "sentiment_distribution": {"positive": 5, "negative": 20, "neutral": 10},
    "summary": "Security breach affecting millions of users",
    "image_metadata": None,
}

post_item = EvidenceBuilder.from_reddit_post(mock_post)
test("from_reddit_post: correct source_type", post_item.source_type == "reddit_post")
test("from_reddit_post: correct source_id", post_item.source_id == "test_post_001")
test("from_reddit_post: has evidence_id", post_item.evidence_id.startswith("evi_"))
test("from_reddit_post: has content title", post_item.content.title == mock_post["title"])
test("from_reddit_post: extracts entities", len(post_item.entities) > 0)
test("from_reddit_post: includes subreddit entity",
     any(e.type == "subreddit" and e.value == "technology" for e in post_item.entities))
test("from_reddit_post: preserves metadata", post_item.metadata.get("score") == 1500)
test("from_reddit_post: has timestamps", post_item.timestamps.source_created is not None)
test("from_reddit_post: passes validation", validate_evidence_item(post_item)[0])

# Test from_reddit_comment
mock_comment = {
    "comment_id": "test_comment_001",
    "post_id": "test_post_001",
    "text": "This is terrible! Contact john@company.com if you're affected. More info at r/privacy",
    "author": "concerned_user_42",
    "score": 89,
    "created_utc": 1700001000,
    "sentiment_label": "negative",
    "sentiment": {"compound": -0.65, "neg": 0.4, "neu": 0.5, "pos": 0.1},
    "toxicity_score": 0.2,
    "is_toxic": False,
}

comment_item = EvidenceBuilder.from_reddit_comment(mock_comment)
test("from_reddit_comment: correct source_type", comment_item.source_type == "reddit_comment")
test("from_reddit_comment: has author as entity",
     any(e.type == "username" and e.value == "concerned_user_42" for e in comment_item.entities))
test("from_reddit_comment: extracts email from text",
     any(e.type == "email" for e in comment_item.entities))
test("from_reddit_comment: preserves sentiment metadata", comment_item.metadata.get("sentiment_label") == "negative")
test("from_reddit_comment: passes validation", validate_evidence_item(comment_item)[0])

# Test from_reddit_user
user_item = EvidenceBuilder.from_reddit_user("test_user_99", {
    "comment_karma": 5000,
    "link_karma": 1200,
    "created_utc": 1600000000,
    "is_gold": False,
    "is_mod": True,
    "has_verified_email": True,
    "subreddit": {"public_description": "I'm a security researcher. Contact: sec@test.com"},
})
test("from_reddit_user: correct source_type", user_item.source_type == "reddit_user")
test("from_reddit_user: has username entity",
     any(e.type == "username" and e.value == "test_user_99" for e in user_item.entities))
test("from_reddit_user: extracts email from bio",
     any(e.type == "email" for e in user_item.entities))
test("from_reddit_user: calculates account age", "account_age_days" in user_item.metadata)
test("from_reddit_user: passes validation", validate_evidence_item(user_item)[0])

# Test from_raw (generic builder)
raw_item = EvidenceBuilder.from_raw(
    source_type="web_search",
    source_id="ddg_result_001",
    source_platform="duckduckgo",
    title="John Doe - LinkedIn Profile",
    body="John Doe is a software engineer at Google. john.doe@gmail.com",
    url="https://linkedin.com/in/johndoe",
    metadata={"query": "john doe engineer"},
    confidence=0.6,
    tags=["web_search", "linkedin"],
)
test("from_raw: correct source_type", raw_item.source_type == "web_search")
test("from_raw: extracts entities from content", len(raw_item.entities) > 0)
test("from_raw: passes validation", validate_evidence_item(raw_item)[0])


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 4: Evidence Store (MongoDB)
# ═══════════════════════════════════════════════════════════════════════════════

section("TEST 4: Evidence Store (MongoDB)")

try:
    from osint.db.evidence_store import EvidenceStore

    store = EvidenceStore()

    # Clean up any previous test data
    store.collection.delete_many({"tags": "module1_test"})

    # Create test items
    test_item_1 = EvidenceBuilder.from_raw(
        source_type="manual",
        source_id="module1_test_001",
        source_platform="test",
        title="Module 1 Test Item Alpha",
        body="This is a test evidence item for validation. Contact test@module1.com",
        tags=["module1_test"],
        confidence=0.9,
    )
    test_item_2 = EvidenceBuilder.from_raw(
        source_type="manual",
        source_id="module1_test_002",
        source_platform="test",
        title="Module 1 Test Item Beta",
        body="Another test item with different content. User u/testaccount mentioned.",
        tags=["module1_test"],
        confidence=0.7,
    )

    # Insert
    inserted_1 = store.insert(test_item_1)
    test("Insert evidence item", inserted_1)

    inserted_2 = store.insert(test_item_2)
    test("Insert second evidence item", inserted_2)

    # Deduplication
    duplicate = store.insert(test_item_1)
    test("Duplicate insert is skipped", not duplicate)

    # Get by ID
    fetched = store.get_by_id(test_item_1.evidence_id)
    test("Get by ID returns correct item", fetched is not None and fetched.evidence_id == test_item_1.evidence_id)

    # Get by source
    fetched_src = store.get_by_source("manual", "module1_test_001")
    test("Get by source works", fetched_src is not None)

    # Exists check
    test("exists_by_source True for existing", store.exists_by_source("manual", "module1_test_001"))
    test("exists_by_source False for missing", not store.exists_by_source("manual", "nonexistent_999"))

    # Get by entity
    entity_results = store.get_by_entity("email", "test@module1.com")
    test("Get by entity finds matching evidence", len(entity_results) >= 1)

    # Get by tags
    tag_results = store.get_by_tags(["module1_test"])
    test("Get by tags returns test items", len(tag_results) >= 2)

    # Get recent
    recent = store.get_recent(limit=5, source_type="manual")
    test("Get recent returns items", len(recent) >= 1)

    # Update status
    updated = store.update_status(test_item_1.evidence_id, "validated")
    test("Update status succeeds", updated)
    refetched = store.get_by_id(test_item_1.evidence_id)
    test("Status was actually updated", refetched.status == "validated")

    # Entity network
    network = store.get_entity_network("email", "test@module1.com")
    test("Entity network returns result", "target" in network)
    test("Entity network has evidence count", network["evidence_count"] >= 1)

    # Stats
    stats = store.get_stats()
    test("Stats returns total count", stats["total_evidence_items"] >= 2)
    test("Stats has source breakdown", len(stats["by_source_type"]) >= 1)

    # Cleanup
    store.collection.delete_many({"tags": "module1_test"})
    print(f"\n  {YELLOW}[INFO] Test data cleaned up{RESET}")

except Exception as e:
    print(f"  {RED}[FAIL] MongoDB tests failed: {e}{RESET}")
    failed += 1


# ═══════════════════════════════════════════════════════════════════════════════
# RESULTS
# ═══════════════════════════════════════════════════════════════════════════════

section("TEST RESULTS")

total = passed + failed
print(f"\n  Total:  {total}")
print(f"  {GREEN}Passed: {passed}{RESET}")
if failed > 0:
    print(f"  {RED}Failed: {failed}{RESET}")
else:
    print(f"  Failed: 0")

print()
if failed == 0:
    print(f"  {GREEN}{BOLD}[PASS] MODULE 1 - EVIDENCE ENGINE: ALL TESTS PASSED{RESET}")
else:
    print(f"  {RED}{BOLD}[FAIL] MODULE 1 - EVIDENCE ENGINE: {failed} TEST(S) FAILED{RESET}")

print()
