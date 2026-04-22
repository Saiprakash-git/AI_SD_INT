## MODULE 1 — Evidence Engine

**Status: COMPLETE ✓**

The Evidence Engine is the foundational layer of the OSINT platform. It provides a unified, source-agnostic system for collecting, extracting, storing, and querying intelligence data.

---

### 📋 Overview

**Purpose**: Normalize diverse OSINT data sources into a single intelligence format.

**Pipeline**:
```
Raw Input 
  ↓ (Entity Extraction)
Entity Records
  ↓ (Evidence Builder)
Evidence Items
  ↓ (Storage)
MongoDB (evidence_items)
  ↓ (Query/Pivot)
Intelligence Analysis
```

**Sources Supported**:
- Reddit (posts, comments, users)
- Web Search (DuckDuckGo, etc.)
- Username Discovery (Sherlock)
- Breach Data (HIBP)
- Domain Intelligence (WHOIS, DNS, crt.sh)
- Manual Entry

---

### 🏗️ Architecture

#### Schema (`evidence_schema.py`)
Universal data format for all intelligence:

```python
EvidenceItem:
  - evidence_id: str           # Unique ID (evi_xxxxxxxxxxxx)
  - source_type: str           # reddit_post, web_search, etc.
  - source_id: str             # Original ID from source
  - source_platform: str       # reddit, duckduckgo, etc.
  - content: EvidenceContent   # title, body, url
  - entities: [EntityRecord]   # Extracted entities
  - metadata: Dict             # Source-specific fields
  - timestamps: EvidenceTimestamps
  - confidence: float          # 0.0-1.0 reliability score
  - tags: [str]               # Classification tags
  - status: str               # raw, processed, validated, archived
```

**Entity Types**:
- Email, Username, URL, Phone, Domain, Person, Organization
- Location, IP_ADDRESS, Date, Hashtag, Subreddit, Crypto Wallet

#### Entity Extraction (`entity_extractor.py`)
Hybrid entity extraction using:
1. **Regex Patterns** (12 types, deterministic, high-precision):
   - Email, URL, Phone, IP Address, Domain
   - Reddit username/subreddit, Twitter handle, Hashtag
   - Crypto wallets (BTC, ETH)

2. **spaCy NER** (contextual, high-recall):
   - Person, Organization, Location, Date

**Confidence Scores**:
- Regex patterns: 0.8-1.0 (deterministic)
- NER entities: 0.75-0.85 (model-dependent)
- Structural: 1.0 (metadata-based)

#### Evidence Builder (`evidence_builder.py`)
Factory methods for creating validated evidence items:

```python
# From Reddit post
item = EvidenceBuilder.from_reddit_post(post_doc, investigation_id)

# From Reddit comment
item = EvidenceBuilder.from_reddit_comment(comment_doc, investigation_id)

# From Reddit user
item = EvidenceBuilder.from_reddit_user(username, user_data, investigation_id)

# From any source (generic)
item = EvidenceBuilder.from_raw(
    source_type="web_search",
    source_id="ddg_001",
    source_platform="duckduckgo",
    title="Search Result",
    body="Content with email@example.com",
    url="https://...",
    metadata={...},
    confidence=0.75,
    tags=["search"],
    extract_entities=True
)
```

#### Evidence Store (`evidence_store.py`)
MongoDB-backed data access layer with optimizations:

**Indexes**:
- Deduplication: `(source_type, source_id)` UNIQUE
- Full-text search: `content.title, content.body`
- Entity queries: `entities.type, entities.value`
- Investigation: `investigation_id, status`
- Timestamps: `timestamps.collected_at`

**Operations**:
```python
store = EvidenceStore()

# Insert (with dedup)
store.insert(item)

# Query by entity
store.get_by_entity("email", "john@example.com")

# Search
store.search("john smith", limit=50)

# By investigation
store.get_by_investigation(investigation_id)

# Entity network (co-occurrence)
network = store.get_entity_network("email", "john@example.com")

# Statistics
stats = store.get_stats()
```

---

### 🎯 Quick Start

#### Installation
```bash
# Install dependencies
pip install pymongo spacy transformers vaderSentiment

# Download spaCy model
python -m spacy download en_core_web_sm
```

#### Basic Usage

```python
from osint import (
    EvidenceBuilder, EvidenceStore, EntityExtractor,
    EvidenceNormalizer, EvidenceQuery
)

# 1. Extract entities from text
extractor = EntityExtractor()
entities = extractor.extract("Contact john@example.com or @johndoe")
# → [{"type": "email", "value": "john@example.com", ...}, ...]

# 2. Create evidence item
item = EvidenceBuilder.from_raw(
    source_type="web_search",
    source_id="search_001",
    source_platform="duckduckgo",
    title="Search Result",
    body="Email: john@example.com",
    extract_entities=True
)

# 3. Store in MongoDB
store = EvidenceStore()
store.insert(item)

# 4. Query
emails = store.get_by_entity("email", "john@example.com")
print(f"Found {len(emails)} evidence items")

# 5. Find relationships (pivot)
query = EvidenceQuery()
bundle = query.find_identity_bundle("john@example.com", "auto")
# → {emails: [...], domains: [...], usernames: [...]}
```

#### Reddit Conversion

```python
from osint.extractors.reddit_converter import RedditConverter

# Convert all Reddit data to evidence
converter = RedditConverter(investigation_id="investigation_001")
stats = converter.convert_all(limit=1000)
print(stats)
# → {posts_converted: 150, comments_converted: 1200, users_extracted: 85, ...}

# Or selective conversion
converter.convert_posts(limit=500)
converter.convert_comments(limit=2000)
```

---

### 📊 Data Flow Examples

#### Example 1: Web Search Result
```
Input:
  "Contact john@example.com for more info"
  
↓ Entity Extraction:
  - email: john@example.com (confidence 1.0)
  - url: (if present)

↓ Evidence Builder:
  EvidenceItem(
    source_type="web_search",
    source_id="search_123",
    entities=[EntityRecord("email", "john@example.com", ...)]
  )

↓ Storage:
  MongoDB evidence_items collection
  
↓ Query:
  store.get_by_entity("email", "john@example.com")
  → Returns all evidence mentioning this email
```

#### Example 2: Reddit Post
```
Input:
  Post by u/johndoe in r/MachineLearning
  Content: "See my research at github.com/john/project"
  
↓ Entity Extraction:
  - username: johndoe
  - subreddit: MachineLearning
  - url: github.com/john/project
  - person: john (from NER)

↓ Evidence Builder:
  EvidenceBuilder.from_reddit_post(post_dict)
  
↓ Storage:
  MongoDB with source dedup: ("reddit_post", post_id)
  
↓ Query:
  query.find_identity_bundle("johndoe", "username")
  → Returns all evidence for this user identity
```

#### Example 3: Identity Resolution (Module 3 Preview)
```
Input:
  User identifier: "john@example.com"

↓ Evidence Query:
  bundle = query.find_identity_bundle("john@example.com", "auto")
  
↓ Results grouped by type:
  {
    "emails": [...],           # All email mentions
    "domains": [...],          # Associated domains
    "usernames": [...],        # Associated usernames
    "persons": [...]           # Person entity matches
  }

↓ Pivot Network:
  network = store.get_entity_network("email", "john@example.com")
  → Co-occurring entities: twitter handles, domains, etc.
```

---

### 🧪 Testing

#### Unit Tests
```bash
cd backend/osint
python test_evidence_engine.py
# Tests: ID generation, extraction, creation, validation, storage

# Expected output:
# ✓ Evidence ID generation passed
# ✓ Entity extraction (regex) passed
# ✓ Entity extraction (NER) passed
# ✓ Evidence item creation passed
# ✓ Evidence builder (from_raw) passed
# ✓ Evidence store deduplication passed
# ✓ Evidence store queries passed
# ✓ Evidence store statistics passed
```

#### Integration Tests
```bash
python test_reddit_integration.py
# Tests: Reddit post/comment/user conversion, batch operations

# Expected output:
# ✓ Reddit post conversion passed
# ✓ Reddit comment conversion passed
# ✓ Reddit → Evidence entity extraction passed
# ✓ Batch Reddit conversion passed
```

---

### 📈 Statistics & Monitoring

```python
# Get comprehensive stats
stats = store.get_stats()

print(f"Total evidence items: {stats['total_evidence_items']}")
# → 15,234

print(f"By source type: {stats['by_source_type']}")
# → {'reddit_post': 8234, 'web_search': 5421, 'breach_data': 1579}

print(f"By status: {stats['by_status']}")
# → {'processed': 12000, 'raw': 3000, 'validated': 234}

print(f"Entity distribution: {stats['entity_type_distribution']}")
# → {'email': 4521, 'username': 3234, 'url': 8900, ...}

print(f"Top entities: {stats['top_entities']}")
# → [{'type': 'email', 'value': 'common@example.com', 'count': 12}, ...]
```

---

### 🔗 Ready for Module 2

The Evidence Engine is production-ready for:
- ✓ Multi-source data ingestion
- ✓ Entity extraction at scale
- ✓ Deduplication
- ✓ Fast queries
- ✓ Investigation tracking

**Next**: MODULE 2 — Connectors
- DuckDuckGo Web Search
- Sherlock Username Search
- HIBP Breach Lookup
- WHOIS/DNS Domain Intelligence

---

### 📚 API Reference

#### Core Classes

```python
# Schema
EvidenceItem              # Main intelligence atom
EntityRecord             # Single extracted entity
EvidenceContent          # Content container
EvidenceTimestamps       # Temporal tracking

# Extraction
EntityExtractor          # Hybrid NER + regex
  .extract(text, include_context=True)

# Building
EvidenceBuilder          # Factory methods
  .from_reddit_post()
  .from_reddit_comment()
  .from_reddit_user()
  .from_raw()

EvidenceFactory          # Convenience shortcuts
  .from_web_search()
  .from_username_search()
  .from_breach_data()

# Storage
EvidenceStore            # MongoDB operations
  .insert()
  .get_by_id()
  .get_by_entity()
  .search()
  .get_entity_network()
  .get_stats()

EvidenceBatch            # Bulk operations
  .add()
  .commit()

# Utils
EvidenceNormalizer       # Entity normalization
EvidenceQuery            # Query builder
  .find_by_email()
  .find_by_username()
  .find_identity_bundle()
  .get_entity_pivots()
```

---

### ⚙️ Configuration

MongoDB collections and indexes are automatically created on first access:

```python
# Indexes created by EvidenceStore:
# - Deduplication: (source_type, source_id) unique
# - Full-text: content.title, content.body
# - Entity queries: entities.type, entities.value
# - And 10+ more for optimization
```

---

### 📝 Notes

- All timestamps are UTC ISO format
- Entity confidence ranges from 0.0-1.0
- Deduplication is at source level: duplicate (source_type, source_id) is skipped
- Investigation linking allows grouping evidence by case/investigation
- Status workflow: RAW → PROCESSED → VALIDATED → ARCHIVED

---

**Module 1 Complete** ✓  
Ready to advance to Module 2: Connectors
