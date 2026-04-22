"""
MODULE 1 — Evidence Engine Usage Examples

Practical examples for common OSINT workflows.
"""

# ============================================================================
# EXAMPLE 1: Simple Entity Extraction
# ============================================================================

from osint import EntityExtractor

extractor = EntityExtractor()

text = """
Contact me at john.smith@example.com or @johnsmith on Twitter.
Visit my website: https://johnsmith.dev
Bitcoin wallet: 1A1z7agoat2SJVQWCVPEASSXXUAMNUHTH
Located in San Francisco, CA
"""

entities = extractor.extract(text)

print("Extracted Entities:")
for entity in entities:
    print(f"  {entity['type']:15} | {entity['value']:30} | confidence: {entity['confidence']}")

# Output:
# email           | john.smith@example.com         | confidence: 1.0
# username        | johnsmith                      | confidence: 0.9
# url             | https://johnsmith.dev         | confidence: 1.0
# crypto_wallet   | 1A1z7agoat2SJVQWCVPEASSXXUMAN... | confidence: 0.8
# location        | San Francisco, CA             | confidence: 0.75


# ============================================================================
# EXAMPLE 2: Create Evidence from Web Search
# ============================================================================

from osint import EvidenceBuilder, EvidenceFactory, EvidenceStore

# Option A: Using factory (simpler)
item = EvidenceFactory.from_web_search(
    query="john smith email",
    result_title="John Smith - Contact Info",
    result_body="John Smith can be reached at john@example.com for consulting",
    result_url="https://example.com/contact",
    source="duckduckgo"
)

# Option B: Using builder (more control)
item = EvidenceBuilder.from_raw(
    source_type="web_search",
    source_id="ddg_search_001",
    source_platform="duckduckgo",
    title="John Smith - Contact Info",
    body="John Smith can be reached at john@example.com for consulting",
    url="https://example.com/contact",
    metadata={"search_query": "john smith email"},
    confidence=0.70,
    tags=["web_search", "contact_info"],
    extract_entities=True
)

# Store in MongoDB
store = EvidenceStore()
store.insert(item)

print(f"Created evidence item: {item.evidence_id}")
print(f"Extracted {len(item.entities)} entities:")
for entity in item.entities:
    print(f"  - {entity.type}: {entity.value}")


# ============================================================================
# EXAMPLE 3: Query Evidence by Entity
# ============================================================================

from osint import EvidenceQuery, EvidenceNormalizer

query = EvidenceQuery()

# Find all evidence containing a specific email
email_evidence = query.find_by_email("john@example.com")
print(f"Found {len(email_evidence)} evidence items for john@example.com:")
for item in email_evidence[:3]:
    print(f"  - {item.source_type}: {item.content.title}")

# Find all evidence containing a username
username_evidence = query.find_by_username("johndoe")
print(f"Found {len(username_evidence)} evidence items for username 'johndoe'")

# Find all evidence for a domain
domain_evidence = query.find_by_domain("example.com")
print(f"Found {len(domain_evidence)} evidence items for domain 'example.com'")


# ============================================================================
# EXAMPLE 4: Identity Bundle - Comprehensive Search
# ============================================================================

# Find ALL related evidence for an identifier (email, username, domain, person name)
bundle = query.find_identity_bundle("john@example.com", identifier_type="auto")

print("Identity Bundle for john@example.com:")
for entity_type, items in bundle.items():
    print(f"\n  {entity_type}: {len(items)} items")
    for item in items[:2]:
        print(f"    - {item.source_platform}: {item.content.title}")


# ============================================================================
# EXAMPLE 5: Entity Pivot Network
# ============================================================================

# Discover related entities (co-occurrence)
network = query.get_entity_pivots("email", "john@example.com", depth=1)

print(f"\nPivot Network for john@example.com:")
print(f"  Evidence items: {network['evidence_count']}")
print(f"  Related entities: {len(network['related_entities'])}")

for related in network['related_entities'][:5]:
    print(f"    - {related['type']:15} | {related['value']:30} | seen {related['co_occurrence_count']} times")


# ============================================================================
# EXAMPLE 6: Batch Processing
# ============================================================================

from osint import EvidenceBatch

# Option A: Manual batch
batch = EvidenceBatch()
batch.add(EvidenceFactory.from_web_search("query1", "Title1", "Body1", "url1"))
batch.add(EvidenceFactory.from_web_search("query2", "Title2", "Body2", "url2"))
batch.add(EvidenceFactory.from_web_search("query3", "Title3", "Body3", "url3"))

stats = batch.commit()
print(f"Batch inserted: {stats['inserted']}, skipped: {stats['skipped']}")

# Option B: Context manager (auto-commit)
with EvidenceBatch() as batch:
    for i in range(10):
        batch.add_raw(
            source_type="manual",
            source_id=f"batch_item_{i}",
            source_platform="test",
            title=f"Item {i}",
            body=f"Test content {i}",
            extract_entities=True
        )


# ============================================================================
# EXAMPLE 7: Reddit Integration
# ============================================================================

from osint.extractors.reddit_converter import RedditConverter

# Convert existing Reddit data to evidence items
converter = RedditConverter(investigation_id="investigation_001")

# Convert all or selective
stats = converter.convert_posts(limit=500)
print(f"Converted {stats['posts_converted']} posts")

stats = converter.convert_comments(limit=2000)
print(f"Converted {stats['comments_converted']} comments")

# Query Reddit evidence
store = EvidenceStore()
reddit_items = store.get_by_tags(["reddit"], limit=50)
print(f"Found {len(reddit_items)} Reddit evidence items")


# ============================================================================
# EXAMPLE 8: Investigation Tracking
# ============================================================================

# Create evidence linked to an investigation
investigation_id = "inv_2024_suspect_001"

item = EvidenceBuilder.from_raw(
    source_type="web_search",
    source_id="search_suspect_001",
    source_platform="duckduckgo",
    title="Suspect Online Presence",
    body="User found on multiple platforms",
    url="",
    metadata={"notes": "Cross-referenced from Reddit"},
    investigation_id=investigation_id,
    extract_entities=True
)

store.insert(item)

# Later: retrieve all evidence for this investigation
investigation_evidence = store.get_by_investigation(investigation_id)
print(f"Investigation has {len(investigation_evidence)} evidence items")


# ============================================================================
# EXAMPLE 9: Entity Normalization
# ============================================================================

from osint import EvidenceNormalizer

normalizer = EvidenceNormalizer()

# Normalize various entity formats
emails = ["John@Example.COM", "jane@EXAMPLE.com", "admin@Test.com"]
normalized_emails = [normalizer.normalize_email(e) for e in emails]
print("Normalized emails:", normalized_emails)

usernames = ["@johndoe", "u/johndoe", "johndoe"]
normalized_usernames = [normalizer.normalize_username(u) for u in usernames]
print("Normalized usernames:", normalized_usernames)

domains = ["https://example.com", "www.example.com", "EXAMPLE.COM"]
normalized_domains = [normalizer.normalize_domain(d) for d in domains]
print("Normalized domains:", normalized_domains)


# ============================================================================
# EXAMPLE 10: Statistics & Monitoring
# ============================================================================

store = EvidenceStore()
stats = store.get_stats()

print("\n=== Evidence Store Statistics ===")
print(f"Total items: {stats['total_evidence_items']}")
print(f"\nBy Source Type:")
for source, count in sorted(stats['by_source_type'].items(), key=lambda x: x[1], reverse=True):
    print(f"  {source:20} | {count:6} items")

print(f"\nBy Status:")
for status, count in sorted(stats['by_status'].items(), key=lambda x: x[1], reverse=True):
    print(f"  {status:20} | {count:6} items")

print(f"\nEntity Types:")
for entity_type, count in sorted(stats['entity_type_distribution'].items(), key=lambda x: x[1], reverse=True)[:10]:
    print(f"  {entity_type:20} | {count:6} entities")

print(f"\nTop Entities:")
for entity in stats['top_entities'][:5]:
    print(f"  {entity['type']:15} | {entity['value']:30} | {entity['count']} mentions")


# ============================================================================
# EXAMPLE 11: Complex Investigation Scenario
# ============================================================================

# Scenario: Tracking a suspect across multiple platforms

investigation_id = "investigation_2024_phishing"
suspect_identifiers = {
    "emails": ["suspect@gmail.com", "alert@suspicious.net"],
    "usernames": ["hacker123", "phish_master", "anon_attacker"],
    "domains": ["suspicious.net", "fake-bank.com"]
}

# Phase 1: Create evidence items for each identifier
with EvidenceBatch() as batch:
    for email in suspect_identifiers["emails"]:
        batch.add(EvidenceFactory.from_breach_data(
            email=email,
            breach_name="known_phishing_ring",
            metadata={"investigation_id": investigation_id}
        ))
    
    for username in suspect_identifiers["usernames"]:
        batch.add(EvidenceFactory.from_username_search(
            username=username,
            platform="twitter",
            profile_url=f"https://twitter.com/{username}",
            metadata={"investigation_id": investigation_id}
        ))

print(f"Created initial evidence for investigation {investigation_id}")

# Phase 2: Query all related evidence
store = EvidenceStore()
all_evidence = store.get_by_investigation(investigation_id)
print(f"Total evidence: {len(all_evidence)}")

# Phase 3: Discover connections via pivots
query = EvidenceQuery()
for email in suspect_identifiers["emails"]:
    pivot_network = query.get_entity_pivots("email", email, depth=1)
    print(f"\nRelated to {email}:")
    for related in pivot_network['related_entities'][:3]:
        print(f"  - {related['type']}: {related['value']}")


print("\n" + "="*70)
print("MODULE 1 Examples Complete")
print("="*70)
