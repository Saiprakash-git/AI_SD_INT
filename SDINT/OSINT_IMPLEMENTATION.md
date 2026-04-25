# OSINT IDENTITY DISCOVERY FRAMEWORK - COMPLETE IMPLEMENTATION

## 📋 TABLE OF CONTENTS
1. [Project Overview](#project-overview)
2. [Complete Execution Flow](#complete-execution-flow)
3. [Architecture & Modules](#architecture--modules)
4. [Data Models](#data-models)
5. [Implementation Details](#implementation-details)
6. [Setup & Testing](#setup--testing)
7. [API Reference](#api-reference)

---

## PROJECT OVERVIEW

**Objective**: Query any identifier (email, username, domain, phone, name) → Correlate evidence from 10+ free data sources → Resolve canonical identity → Generate intelligence report

**Tech Stack**:
- Backend: Flask 3.0.0 + Python 3.10+
- Frontend: React 19 + Vite 7.3
- Database: MongoDB 5.0+
- Data Sources: 100% FREE (no paid APIs)

**Supported Query Types**:
- Email: `john@example.com`
- Username: `@john_doe` or `john_doe`
- Domain: `example.com`
- Phone: `+1-555-0123`
- Name: `John Doe`

**Output**: Dossier with risk score, confidence meter, timeline, platform breakdown, entity network

---

## COMPLETE EXECUTION FLOW

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER QUERY                              │
│                    "john_doe@example.com"                       │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              [STEP 1] FRONTEND: HTTP REQUEST                    │
│                POST /api/osint/investigate                      │
│                {query: "john_doe@example.com"}                  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│               [STEP 2] BACKEND: CREATE SESSION                  │
│  File: app.py → start_investigation()                          │
│  Action: Insert into MongoDB.investigation_sessions            │
│  Fields: session_id, query, status="queued"                    │
│  Return: {session_id: "uuid1", task_id: "uuid2"}              │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│            [STEP 3] QUEUE BACKGROUND JOB                        │
│  File: task_queue.py → TaskQueue.submit()                      │
│  Action: ThreadPoolExecutor adds investigation to queue        │
│  Function: run_full_investigation(session_id, query, db)       │
│  Purpose: Long operation (10-30 sec) shouldn't block API       │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│         [STEP 4] PARSE QUERY → DETERMINE PIVOT TYPE             │
│  File: investigation_orchestrator.py → parse_pivot()            │
│  Input: "john_doe@example.com"                                  │
│  Logic:                                                          │
│    if matches email regex: type = "email"                       │
│    if matches phone regex: type = "phone"                       │
│    if no spaces + alphanumeric: type = "username"              │
│    if domain pattern: type = "domain"                           │
│    else: type = "name"                                          │
│  Output: {type: "email", value: "john_doe@example.com"}        │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│        [STEP 5] INITIALIZE RATE SCHEDULER                        │
│  File: rate_scheduler.py → RateScheduler.get()                  │
│  Purpose: Prevent IP bans by tracking per-source cooldowns      │
│  Configured Limits:                                              │
│    - DuckDuckGo: 1 second between requests                       │
│    - Nitter: 3 seconds                                           │
│    - Instagram: 10 seconds                                       │
│    - GitHub: 0 seconds (hour-based rate limit)                  │
│    - HackerNews: 0 seconds (unlimited for API)                  │
└──────────────────────────┬───────────────────────────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
         ▼                 ▼                 ▼
    ┌─────────┐        ┌─────────┐      ┌─────────┐
    │ Username│        │ Breach  │      │ GitHub  │  
    │Connector│        │Connector│      │Connector│
    └────┬────┘        └────┬────┘      └────┬────┘
         │                 │                 │
         │ [PARALLEL EXECUTION BEGINS]      │
         │                                  │

┌─────────────────────────────────────────────────────────────────┐
│        [STEP 6A] USERNAME CONNECTOR (20+ Platforms)             │
│  File: osint/connectors/username_connector.py                  │
│  Method: run(pivot={type: "email", value: "john_doe@ex.com"}) │
│  Searches:                                                       │
│    1. Extract username from email: "john_doe"                   │
│    2. Check 20+ platforms asynchronously:                       │
│       ✓ GitHub: HTTP GET /users/john_doe                        │
│       ✓ Reddit: HTTP GET /user/john_doe/about                   │
│       ✓ HackerNews: hn.algolia.com search                       │
│       ✓ GitLab, PyPI, npm, Keybase, Telegram, Dev.to, etc.     │
│    3. For each platform, try exact match + variations           │
│  Output: [{platform: "github", url: "...", confidence: 0.95}]  │
│  Storage: Each item saved to MongoDB immediately               │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│        [STEP 6B] BREACH CONNECTOR (5 Free Sources)              │
│  File: osint/connectors/breach_connector.py                    │
│  Method: run(pivot={type: "email", value: "john_doe@ex.com"}) │
│  Searches:                                                       │
│    1. psbdmp.ws Pastebin: Search for email                      │
│    2. LeakCheck.io API: Check email in database                │
│    3. BreachDirectory.org: Query breach index                   │
│    4. HIBP k-anonymity: Check password hash prefix              │
│    5. SauceNAO: Reverse search image database                   │
│  Output: [{source: "psbdmp", severity: "HIGH", date: "2023"}]  │
│  Risk Assessment: Count breaches, assign severity               │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│         [STEP 6C] GITHUB CONNECTOR (Profile Enrichment)         │
│  File: osint/connectors/github_connector.py                    │
│  Method: run(pivot={type: "username", value: "john_doe"})      │
│  API Calls (GitHub REST API - 60 req/hr free):                 │
│    1. GET /users/john_doe → Profile info                       │
│       └─ Bio, location, company, public_repos, followers       │
│    2. Extract emails from public gists/repos                   │
│    3. Get followers/following data                              │
│    4. Scan repositories for additional email patterns          │
│  Output: [{platform: "github", email: "...", repos: 45, ...}]  │
│  Rate Limit: 60 requests per hour (tracked)                    │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│     [STEP 6D] HACKERNEWS CONNECTOR (Profile Discovery)          │
│  File: osint/connectors/hackernews_connector.py                │
│  Method: run(pivot={type: "username", value: "john_doe"})      │
│  API Calls (HN API - unlimited free):                          │
│    1. GET /user/john_doe → Profile info                        │
│       └─ Karma, about, created timestamp                       │
│    2. GET /user/john_doe/submissions → Recent activity         │
│    3. Parse bios for email/website mentions                    │
│  Output: [{platform: "hackernews", karma: 5000, ...}]          │
│  Rate Limit: None (public API)                                 │
└─────────────────────────────────────────────────────────────────┘
         │                 │                 │
         └─────────────────┼─────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│        [STEP 7] AGGREGATE ALL EVIDENCE                           │
│  Timing: All 4+ connectors run in parallel (5-10 seconds)       │
│  Total Evidence Items Collected: 15-50 items                    │
│  Each item: {source, type, fields, timestamp, confidence}      │
│  Action: All items inserted into MongoDB.evidence_items        │
│  Example Aggregation:                                           │
│    - Username matches: 8 items (GitHub, Reddit, HN, etc)       │
│    - Breach findings: 3 items (2 breaches detected)             │
│    - Email extractions: 4 items (multiple emails found)         │
│    - Profile enrichments: 5 items (followers, karma, etc)       │
│  MongoDB Query:                                                 │
│    db.evidence_items.find({session_id: "uuid1"})               │
│    → returns all 20 evidence items                              │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│          [STEP 8] IDENTITY RESOLUTION & MERGING                 │
│  File: osint/services/identity_resolver.py                     │
│  Class: IdentityResolver.resolve()                             │
│                                                                  │
│  [8.1] EXTRACT ENTITIES FROM EVIDENCE                           │
│    - emails: ["john@example.com", "j.doe@company.com"]         │
│    - usernames: ["john_doe", "johndoe", "jdoe"]                │
│    - phones: ["+1-555-0123"]                                    │
│    - domains: ["example.com", "github.com"]                    │
│    - locations: ["New York, NY"]                               │
│    - organizations: ["Company Inc"]                             │
│                                                                  │
│  [8.2] DEDUPLICATE USING SIMILARITY SCORING                    │
│    Algorithm: Jaro-Winkler string similarity (0-1)             │
│    Example:                                                     │
│      - "john_doe" vs "johndoe": 0.95 similarity                │
│      - → Merge into single canonical: "john_doe"               │
│      - "john@example.com" vs "john@example.com": 1.0           │
│      - → Keep both (different domains still linked)            │
│                                                                  │
│  [8.3] CALCULATE MATCH CONFIDENCE (0-1 scale)                 │
│    Scoring Logic:                                               │
│      - Same email on GitHub + Reddit: +0.25                    │
│      - Same username on 3+ platforms: +0.20                    │
│      - Similar name variations: +0.10                          │
│      - Breach exposure confirms ID: +0.15                      │
│      - Location consistency: +0.10                              │
│      - Total = 0.0 to 1.0                                       │
│    Example: 0.92 confidence                                    │
│                                                                  │
│  [8.4] ASSESS RISK LEVEL (CRITICAL|HIGH|MEDIUM|LOW)           │
│    Criteria:                                                    │
│      - CRITICAL: >3 breaches OR major platform breach          │
│      - HIGH: 2-3 breaches OR credentials leaked                │
│      - MEDIUM: 1 breach OR scattered evidence                  │
│      - LOW: No breaches + minimal evidence                     │
│    Example Risk: HIGH (2 breaches detected)                    │
│                                                                  │
│  [8.5] GENERATE INTELLIGENCE SUMMARY (Human-Readable)          │
│    Template:                                                    │
│      "John Doe identified across GitHub (john_doe), Reddit     │
│       (johndoe), and HackerNews with 92% confidence.           │
│       Email john@example.com found in 2 public breaches.       │
│       Risk Level: HIGH due to breach exposure."                │
│                                                                  │
│  Output: ResolvedPerson Object                                 │
│    {                                                            │
│      session_id: "uuid1",                                      │
│      canonical_name: "John Doe",                               │
│      emails: ["john@example.com", "j.doe@company.com"],        │
│      usernames: ["john_doe", "johndoe"],                       │
│      phones: ["+1-555-0123"],                                  │
│      risk_level: "HIGH",                                       │
│      risk_score: 0.75,                                         │
│      match_confidence: 0.92,                                   │
│      breach_findings: [                                        │
│        {source: "psbdmp", email: "john@ex.com", date: "2023"}  │
│      ],                                                         │
│      summary: "John Doe identified across..."                  │
│    }                                                            │
│                                                                  │
│  MongoDB Action: resolved_persons.insert_one(person)           │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│         [STEP 9] BUILD NARRATIVE & VISUALIZATIONS              │
│  File: osint/services/narrative_builder.py                     │
│  Class: NarrativeBuilder                                        │
│                                                                  │
│  [9.1] BUILD TIMELINE (Chronological Events)                   │
│    Process:                                                     │
│      1. Sort all evidence by timestamp (newest first)          │
│      2. Classify by type:                                      │
│         - breach: Email found in database dump                 │
│         - profile: Active account discovered                   │
│         - domain: Website registration                         │
│         - mention: Reference in forum/post                     │
│         - archive: Historical web archive                      │
│      3. Assign severity: CRITICAL|HIGH|MEDIUM|LOW              │
│                                                                  │
│    Output:                                                      │
│    [                                                            │
│      {                                                          │
│        timestamp: "2024-01-15T10:30:00Z",                      │
│        type: "breach",                                         │
│        platform: "psbdmp",                                     │
│        title: "Email found in Pastebin breach",               │
│        severity: "HIGH",                                       │
│        url: "https://..."                                      │
│      },                                                         │
│      {                                                          │
│        timestamp: "2024-02-20T14:22:00Z",                      │
│        type: "profile",                                        │
│        platform: "GitHub",                                     │
│        title: "GitHub profile discovered",                    │
│        severity: "LOW"                                         │
│      },                                                         │
│      ...                                                        │
│    ]                                                            │
│                                                                  │
│  [9.2] BUILD PLATFORM SUMMARY (Aggregated by Source)           │
│    Process:                                                     │
│      1. Group evidence by platform (GitHub, Reddit, etc)      │
│      2. Count evidence items per platform                      │
│      3. Extract usernames, URLs, last_seen date               │
│      4. Aggregate profile data (followers, karma, etc)         │
│                                                                  │
│    Output:                                                      │
│    [                                                            │
│      {                                                          │
│        platform: "GitHub",                                     │
│        evidence_count: 5,                                      │
│        usernames: ["john_doe"],                                │
│        urls: ["https://github.com/john_doe"],                 │
│        last_seen: "2024-02-20",                               │
│        profile_data: {followers: 234, repos: 45}              │
│      },                                                         │
│      {                                                          │
│        platform: "Reddit",                                     │
│        evidence_count: 3,                                      │
│        usernames: ["johndoe"],                                 │
│        urls: ["https://reddit.com/user/johndoe"],             │
│        last_seen: "2024-02-15"                                │
│      },                                                         │
│      ...                                                        │
│    ]                                                            │
│                                                                  │
│  [9.3] BUILD ENTITY NETWORK (Graph for Visualization)          │
│    Purpose: Create vis-network compatible graph for UI         │
│    Process:                                                     │
│      1. Create nodes for each entity:                          │
│         - person (central): "john_doe"                         │
│         - emails: "john@example.com", "j.doe@company.com"      │
│         - usernames: "john_doe", "johndoe"                     │
│         - platforms: "GitHub", "Reddit", "HN"                  │
│         - domains: "example.com"                               │
│      2. Create edges between related nodes:                    │
│         - person → email (has email)                           │
│         - person → username (has username)                     │
│         - person → platform (has profile)                      │
│                                                                  │
│    Output:                                                      │
│    {                                                            │
│      nodes: [                                                   │
│        {id: "john_doe", label: "john_doe", type: "person"},   │
│        {id: "john@ex.com", label: "john@ex.com", type: "email"},│
│        {id: "github", label: "GitHub", type: "platform"},     │
│        ...                                                      │
│      ],                                                         │
│      edges: [                                                   │
│        {from: "john_doe", to: "john@ex.com", type: "has_email"},│
│        {from: "john_doe", to: "github", type: "has_profile"},  │
│        ...                                                      │
│      ]                                                          │
│    }                                                            │
│                                                                  │
│  MongoDB Action:                                                │
│    narrative_artifacts.insert_one({                            │
│      session_id: "uuid1",                                      │
│      timeline: [...],                                          │
│      platform_summary: [...],                                  │
│      network_graph: {...}                                      │
│    })                                                           │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│         [STEP 10] UPDATE SESSION STATUS                         │
│  Action: Mark investigation as "complete"                      │
│  MongoDB Update:                                                │
│    investigation_sessions.update_one({session_id: "uuid1"}, {   │
│      status: "complete",                                        │
│      completed_at: "2024-02-20T14:35:00Z",                     │
│      evidence_count: 20,                                        │
│      canonical_name: "John Doe",                               │
│      risk_level: "HIGH",                                        │
│      match_confidence: 0.92                                     │
│    })                                                           │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│      [STEP 11] FRONTEND POLLING (Get Results)                   │
│  File: InvestigationMode.jsx → polling loop                    │
│  Loop:                                                          │
│    Every 2 seconds → GET /api/osint/tasks/<task_id>            │
│    Check status: "pending" | "running" | "complete" | "failed" │
│    When complete:                                               │
│      → GET /api/osint/session/<session_id>                     │
│      → Fetch full results                                      │
│      → Stop polling                                            │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│           [STEP 12] DISPLAY RESULTS TO USER                     │
│  Frontend Renders:                                              │
│    1. DOSSIER SIDEBAR                                           │
│       - Canonical Name: "John Doe"                              │
│       - Risk Badge: "HIGH" (color: orange)                      │
│       - Confidence Meter: 92% (visual bar)                      │
│       - Evidence Count: "20 items"                              │
│       - Breach Exposure: "⚠️ 2 breaches detected"              │
│       - Usernames: ["john_doe", "johndoe"]                     │
│       - Emails: ["john@example.com", "j.doe@company.com"]      │
│                                                                  │
│    2. TABBED INTERFACE                                          │
│       [Overview]  [Timeline]  [Platforms]  [Evidence]          │
│                                                                  │
│       Overview Tab: Raw query, pivot type, summary             │
│       Timeline Tab: 20 chronological events                    │
│       Platforms Tab: 6 sources with evidence count             │
│       Evidence Tab: Raw JSON export                            │
│                                                                  │
│    3. TIMELINE VISUALIZATION                                   │
│       - Chronological list with timestamps                     │
│       - Event type indicators (breach, profile, etc)           │
│       - Severity color coding                                  │
│       - Platform badges                                        │
│                                                                  │
│    4. PLATFORM BREAKDOWN                                        │
│       - Grid of platform cards                                 │
│       - Evidence count per platform                            │
│       - Links to profiles                                      │
│       - Last seen date                                         │
│                                                                  │
│    5. NETWORK GRAPH (Optional)                                 │
│       - Interactive vis-network graph                          │
│       - Central person node connected to emails/platforms      │
│       - Hover for details                                      │
│       - Click to expand                                        │
└──────────────────────────────────────────────────────────────────┘

TOTAL EXECUTION TIME: 10-30 seconds
EVIDENCE ITEMS: 15-50
PLATFORMS SEARCHED: 25+
CONFIDENCE: 0-1 (0.92 in example)
RISK LEVEL: CRITICAL|HIGH|MEDIUM|LOW
```

---

## ARCHITECTURE & MODULES

### **Backend Architecture (9 Core Components)**

#### **1. Flask API Layer** (`app.py`)
```python
# 5 REST Endpoints
POST /api/osint/investigate
  ├─ Input: {query: "john_doe"}
  ├─ Process: Create session, queue task
  └─ Output: {session_id, task_id, status}

GET /api/osint/session/<session_id>
  ├─ Process: Fetch from MongoDB
  └─ Output: {session, person, artifacts}

GET /api/osint/tasks/<task_id>
  ├─ Process: Check task queue status
  └─ Output: {task_id, status, result, error}

GET /api/osint/sessions
  └─ Output: All investigations (paginated)

GET /api/osint/evidence?session_id=...
  └─ Output: Raw evidence items
```

#### **2. Task Queue** (`task_queue.py`)
```python
# Background job processing (ThreadPoolExecutor)
ThreadPoolExecutor(max_workers=5)
├─ Purpose: Handle long-running investigations without blocking API
├─ Storage: In-memory + MongoDB persistence
├─ Status: pending → running → complete/failed
├─ Methods:
│  ├─ submit(func, *args) → task_id
│  ├─ get_status(task_id) → {status, result, error}
│  └─ list_tasks() → all tasks
└─ MongoDB Collections:
   └─ task_status (tracks all background jobs)
```

#### **3. Investigation Orchestrator** (`investigation_orchestrator.py`)
```python
# Master pipeline that coordinates everything
run_full_investigation(session_id, query, db)
├─ [1] parse_pivot(query)
│  └─ Auto-detect: email|username|domain|phone|name
├─ [2] Initialize RateScheduler
├─ [3] Run connectors in parallel:
│  ├─ UsernameConnector
│  ├─ BreachConnector
│  ├─ GitHubConnector
│  └─ HackerNewsConnector
├─ [4] Aggregate evidence (MongoDB)
├─ [5] Call IdentityResolver.resolve()
├─ [6] Call NarrativeBuilder.build_narrative()
└─ [7] Update session status (complete)
```

#### **4. Connectors (4 Parallel Data Sources)**

##### **4A. UsernameConnector** (`username_connector.py`)
```python
Checks 20+ Platforms:
├─ Development: GitHub, GitLab, PyPI, npm, Keybase
├─ Social: Reddit, Twitter (via Nitter), Mastodon
├─ Code: StackOverflow, CodePen, Replit, Dev.to, Hashnode
├─ Web: Medium, Pastebin, Docker Hub, Gravatar
└─ Other: Telegram, Signal, Keybase, etc.

Implementation:
├─ Async I/O with aiohttp (concurrent HTTP requests)
├─ For each platform:
│  ├─ Check exact username match
│  ├─ Try common variations (john_doe, johndoe, j_doe)
│  ├─ Extract profile data if match found
│  └─ Assign confidence score
├─ Returns: List of EvidenceItem objects
└─ Example Output:
   {
     source: "github",
     platform: "GitHub",
     username: "john_doe",
     url: "https://github.com/john_doe",
     confidence: 0.95
   }
```

##### **4B. BreachConnector** (`breach_connector.py`)
```python
Checks 5 Free Breach Databases:
├─ psbdmp.ws (Pastebin search via web scrape)
├─ LeakCheck.io (Public API - no key required)
├─ BreachDirectory.org (Public API)
├─ HIBP k-anonymity (SHA-1 hash prefix check)
└─ SauceNAO (Image reverse search - 100/day free)

Implementation:
├─ Query each database for email/phone
├─ Extract breach metadata: date, source, severity
├─ Assign risk: CRITICAL if major platform, HIGH if scattered
├─ Returns: List of EvidenceItem objects
└─ Example Output:
   {
     source: "psbdmp",
     type: "breach",
     email: "john@example.com",
     date: "2023-01-15",
     severity: "HIGH"
   }
```

##### **4C. GitHubConnector** (`github_connector.py`)
```python
GitHub API V3 (REST API - 60 req/hr free)

Implementation:
├─ Calls:
│  ├─ GET /users/{username} → Profile data
│  ├─ GET /users/{username}/repos → Repositories
│  ├─ GET /users/{username}/followers → Social graph
│  └─ Scrape gists/repos for email patterns
├─ Extract fields: email, followers, public_repos, bio, location
├─ Returns: List of EvidenceItem objects
└─ Example Output:
   {
     source: "github",
     username: "john_doe",
     email: "john.doe@company.com",
     followers: 234,
     public_repos: 45
   }
```

##### **4D. HackerNewsConnector** (`hackernews_connector.py`)
```python
HackerNews API (Unlimited free)

Implementation:
├─ Calls:
│  ├─ GET /user/{username} → Profile data
│  ├─ Parse user submissions/comments
│  └─ Extract email/website from bio
├─ Extract fields: karma, about, created, activity
├─ Returns: List of EvidenceItem objects
└─ Example Output:
   {
     source: "hackernews",
     username: "john_doe",
     karma: 5000,
     about: "Developer and researcher"
   }
```

#### **5. Identity Resolver** (`identity_resolver.py`)
```python
Merge evidence into canonical person

Algorithm:
├─ [1] Extract all entities from evidence:
│  ├─ emails: ["john@ex.com", "j.doe@co.com"]
│  ├─ usernames: ["john_doe", "johndoe", "jdoe"]
│  ├─ phones: ["+1-555-0123"]
│  └─ domains: ["example.com"]
│
├─ [2] Deduplicate using Jaro-Winkler similarity:
│  ├─ String similarity (0-1): "john_doe" vs "johndoe" = 0.95
│  ├─ If >0.85: merge into canonical form
│  └─ Consolidate emails with same person
│
├─ [3] Calculate confidence (0-1):
│  ├─ Multiple platforms same username: +0.25
│  ├─ Same email across sources: +0.25
│  ├─ Name variations match: +0.15
│  ├─ Breach confirms identity: +0.15
│  └─ Total: 0.0 - 1.0
│
├─ [4] Calculate risk (CRITICAL|HIGH|MEDIUM|LOW):
│  ├─ CRITICAL: >3 breaches OR major platform compromised
│  ├─ HIGH: 2-3 breaches OR credentials leaked
│  ├─ MEDIUM: 1 breach OR scattered evidence
│  └─ LOW: No breaches
│
└─ [5] Generate summary (human-readable)
   └─ "John Doe identified across GitHub, Reddit, HN with 92% confidence"

Output: ResolvedPerson object
```

#### **6. Narrative Builder** (`narrative_builder.py`)
```python
Create timeline, platform summary, entity network

Methods:

build_timeline(evidence_items):
├─ Sort by timestamp (newest first)
├─ Classify: breach|profile|domain|mention|archive
├─ Assign severity: CRITICAL|HIGH|MEDIUM|LOW
└─ Returns: [{timestamp, type, platform, title, severity}, ...]

build_platform_summary(evidence_items):
├─ Group by platform
├─ Count evidence per platform
├─ Extract usernames, URLs, last_seen
└─ Returns: [{platform, count, usernames, urls}, ...]

build_entity_network(evidence_items):
├─ Create nodes: person, emails, usernames, platforms
├─ Create edges: relationships
└─ Returns: {nodes: [...], edges: [...]} (vis-network format)
```

#### **7. Rate Scheduler** (`rate_scheduler.py`)
```python
Per-source rate limiting

Configuration:
├─ DuckDuckGo: 1 second between requests
├─ Nitter (Twitter): 3 seconds
├─ Instagram: 10 seconds
├─ GitHub: 0 seconds (hourly quota)
└─ HackerNews: 0 seconds

Purpose: Prevent IP bans, respect API limits
Method: wait_for(connector_name) → sleeps if needed
```

### **Frontend Architecture (React Component)**

#### **InvestigationMode.jsx**
```jsx
Main OSINT UI Component

Features:
├─ Query input with auto-detection
├─ Real-time polling (2-second intervals)
├─ Tabbed interface: Overview | Timeline | Platforms | Evidence
├─ Dossier sidebar with:
│  ├─ Canonical name
│  ├─ Risk badge (color-coded)
│  ├─ Confidence meter (visual bar)
│  ├─ Evidence count
│  ├─ Breach exposure
│  └─ Extracted identifiers
├─ Timeline visualization
├─ Platform breakdown
└─ Raw JSON export

Polling Loop:
├─ User submits query
├─ GET /api/osint/investigate
├─ Receives: session_id, task_id
├─ Every 2 seconds: GET /api/osint/tasks/<task_id>
├─ When complete: GET /api/osint/session/<session_id>
└─ Display full results
```

---

## DATA MODELS

### **1. EvidenceItem** (Raw Evidence)
```json
{
  "session_id": "uuid",
  "source": "github",
  "evidence_type": "profile",
  "extracted_fields": {
    "username": "john_doe",
    "platform": "GitHub",
    "url": "https://github.com/john_doe",
    "email": "john@example.com",
    "followers": 234
  },
  "timestamp": "2024-02-20T14:22:00Z",
  "confidence": 0.95,
  "severity": "LOW"
}
```

### **2. ResolvedPerson** (Merged Identity)
```json
{
  "session_id": "uuid",
  "canonical_name": "John Doe",
  "emails": ["john@example.com", "j.doe@company.com"],
  "usernames": ["john_doe", "johndoe"],
  "phones": ["+1-555-0123"],
  "domains": ["example.com"],
  "risk_level": "HIGH",
  "risk_score": 0.75,
  "match_confidence": 0.92,
  "breach_findings": [
    {
      "source": "psbdmp",
      "email": "john@example.com",
      "date": "2023-01-15",
      "severity": "HIGH"
    }
  ],
  "summary": "John Doe identified across GitHub, Reddit, HackerNews..."
}
```

### **3. Timeline Event**
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "type": "breach",
  "platform": "psbdmp",
  "title": "Email found in Pastebin breach",
  "severity": "HIGH",
  "url": "https://..."
}
```

### **4. Platform Summary**
```json
{
  "platform": "GitHub",
  "evidence_count": 5,
  "usernames": ["john_doe"],
  "urls": ["https://github.com/john_doe"],
  "last_seen": "2024-02-20",
  "profile_data": {
    "followers": 234,
    "public_repos": 45
  }
}
```

---

## IMPLEMENTATION DETAILS

### **Technology Stack**

**Backend**:
- Flask 3.0.0 (Lightweight HTTP framework)
- Python 3.10+ (Async/await support)
- aiohttp (Async HTTP client for parallel requests)
- pymongo (MongoDB driver)
- APScheduler (Scheduled background jobs)

**Frontend**:
- React 19 (Functional components + hooks)
- Vite 7.3 (Fast build tool)
- Axios (HTTP client)
- Lucide icons (UI icons)

**Database**:
- MongoDB 5.0+ (Document storage)
- Collections:
  - investigation_sessions
  - evidence_items
  - resolved_persons
  - narrative_artifacts
  - task_status

**Data Sources (100% FREE)**:
- 20+ username platforms (direct HTTP checks)
- 5 breach databases (free APIs + web scraping)
- GitHub API (60 req/hr free tier)
- HackerNews API (unlimited free)

### **Deployment**

**Backend**:
```bash
cd backend
pip install -r requirements.txt
python app.py
# Runs on http://localhost:5000
```

**Frontend**:
```bash
cd frontend
npm install
npm run dev
# Runs on http://localhost:5175
```

**Database**:
```bash
mongod
# Runs on mongodb://localhost:27017
```

---

## SETUP & TESTING

### **Quick Start (5 Minutes)**

Terminal 1 - MongoDB:
```bash
mongod
# Output: Waiting for connections on port 27017
```

Terminal 2 - Backend:
```bash
cd backend
python app.py
# Output: Running on http://127.0.0.1:5000
```

Terminal 3 - Frontend:
```bash
cd frontend
npm run dev
# Output: VITE ready at http://localhost:5175
```

### **Test Investigation**

1. Open browser: http://localhost:5175
2. Click "Crawl Mode" → "Identity Discovery"
3. Enter query: `github_username` or `email@example.com`
4. Click "Start Investigation"
5. Wait 5-30 seconds
6. View timeline, platforms, dossier

---

## API REFERENCE

### **POST /api/osint/investigate**
Start new investigation
```json
Request:
{
  "query": "john_doe@example.com"
}

Response (202 Accepted):
{
  "status": "queued",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "task_id": "550e8400-e29b-41d4-a716-446655440001",
  "pivot_type": "email",
  "query": "john_doe@example.com"
}
```

### **GET /api/osint/session/<session_id>**
Get investigation results
```json
Response (200 OK):
{
  "session": {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "complete",
    "evidence_count": 20,
    "canonical_name": "John Doe",
    "risk_level": "HIGH",
    "match_confidence": 0.92
  },
  "person": {
    "canonical_name": "John Doe",
    "emails": ["john@example.com"],
    "usernames": ["john_doe"],
    "risk_level": "HIGH",
    "breach_findings": [...]
  },
  "artifacts": {
    "timeline": [...],
    "platform_summary": [...],
    "network_graph": {...}
  }
}
```

### **GET /api/osint/tasks/<task_id>**
Check task status
```json
Response (200 OK - Running):
{
  "task_id": "550e8400-e29b-41d4-a716-446655440001",
  "status": "running",
  "result": null
}

Response (200 OK - Complete):
{
  "task_id": "550e8400-e29b-41d4-a716-446655440001",
  "status": "complete",
  "result": {
    "evidence_count": 20,
    "canonical_name": "John Doe",
    "risk_level": "HIGH"
  }
}
```

---

**COMPLETE OSINT FRAMEWORK IMPLEMENTATION - READY FOR PRODUCTION**
