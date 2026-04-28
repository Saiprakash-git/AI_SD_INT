# OSINT IDENTITY DISCOVERY FRAMEWORK - COMPLETE IMPLEMENTATION

## 📋 TABLE OF CONTENTS
1. [Project Overview](#project-overview)
2. [Complete Execution Flow](#complete-execution-flow)
3. [Architecture & Modules](#architecture--modules)
4. [Data Models](#data-models)
5. [Implementation Details](#implementation-details)
6. [Image Intelligence Pipeline](#image-intelligence-pipeline)
7. [Identity Resolution & Corroboration](#identity-resolution--corroboration)
8. [Setup & Testing](#setup--testing)

---

## PROJECT OVERVIEW

**Objective**: Take complex, descriptive user prompts (including images, names, locations, and DOBs) → Extract context using NLP → Correlate evidence across 15+ free data sources, internal databases, and reverse image searches → Resolve canonical identity with verifiable corroboration signals → Generate an intelligence report.

**Tech Stack**:
- Backend: Flask 3.0.0 + Python 3.10+
- Frontend: React 19 + Vite
- Database: MongoDB 5.0+
- Machine Learning: SpaCy (NLP extraction), InsightFace (Facial Recognition embeddings)
- Data Sources: 100% FREE (No paid API keys needed)

**Supported Inputs (Unified Descriptive Prompt)**:
- "Find John Doe. He is from New York, born in 1990."
- "Trace the digital footprint of this image." (With image file upload)
- "Investigate satoshin@gmx.com. Associated with cryptocurrency."

**Output**: Executive Dossier with Corroboration Signals, meaningful Confidence Metrics, Image Footprint mappings, Timeline, Platform Breakdown, and Entity Network Graph.

---

## COMPLETE EXECUTION FLOW

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER DESCRIPTIVE PROMPT                      │
│ "Find David. Born 1995 in Delhi. Attached: target.jpg"          │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              [STEP 1] NLP ENTITY EXTRACTION                     │
│  File: app.py & entity_extractor.py                             │
│  Action: Extracts primary target ("David"), DOB (1995),         │
│          Location ("Delhi"), and saves image.                   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              [STEP 2] IMAGE DEEP ANALYSIS                       │
│  File: image_analyzer.py                                        │
│  Action: Extracts EXIF (GPS, Camera data). Analyzes face with   │
│          InsightFace to generate 512-D embeddings.              │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│          [STEP 3] SMART ENUMERATION & SEED DISCOVERY            │
│  File: username_connector.py                                    │
│  Action: Uses DuckDuckGo HTML to search "David (twitter OR...)" │
│          to extract actual @handles used. Generates variants    │
│          using DOB/Location (e.g., david1995, david_delhi).     │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│         [STEP 4] CONCURRENT PARALLEL CONNECTORS                 │
│  Execution: investigation_orchestrator.py                       │
│  Sources:                                                       │
│    - Username validation (HTTP 200 + bio text matching)         │
│    - Breach databases (HIBP, LeakCheck)                         │
│    - Internal DB (RedditLocalConnector & Image mappings)        │
│    - Reverse Image Search (SauceNaoConnector)                   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│      [STEP 5] IDENTITY RESOLUTION & CORROBORATION               │
│  File: identity_resolver.py                                     │
│  Action: Merges evidence. Calculates meaningful confidence      │
│          (90% = Exact match across 3+ sources). Generates       │
│          green ✓ validation signals for the dossier.            │
└─────────────────────────────────────────────────────────────────┘
```

---

## ARCHITECTURE & MODULES

### 1. The Connector Engine
Connectors are modular python classes implementing a `run(pivot: dict) -> list[EvidenceItem]` interface.

- **UsernameConnector**: Checks 20+ platforms (GitHub, Keybase, Medium, Replit, etc.). Uses `aiohttp` for concurrency. Validates true matches by parsing the page content and verifying the target's name appears on the profile (prevents false positive HTTP 200s).
- **RedditLocalConnector**: Queries your existing MongoDB `posts` and `comments` collections. It uses the variants generated from the `UsernameConnector` to search the `author` field, turning your internal DB into a high-confidence OSINT source.
- **SauceNaoConnector**: Uploads images to SauceNAO's free tier for reverse image matching against Pixiv, Twitter, and anime databases.
- **ImageConnector**: Queries the internal MongoDB `image_mappings` collection to see if an uploaded image's face embedding or hash matches past investigations.
- **BreachConnector**: Scans Pastebin dumps and LeakCheck free tiers for exposed emails.
- **NewsConnector (GDELT)**: Finds news articles related to the identity.

### 2. The Orchestrator
`investigation_orchestrator.py`
The brain of the operation. It receives the NLP context, sets up the `RateScheduler`, spawns the connectors, normalizes all outputs into standard `EvidenceItem` models, and fires off the `IdentityResolver`.

---

## IMPLEMENTATION DETAILS: RECENT FIXES & UPGRADES

### 1. Prompt-Based NLP Engine
Instead of rigid input boxes, the framework uses SpaCy in `EntityExtractor`. It dynamically classifies whether the query is focusing on an email, phone, domain, or person. It isolates the DOB, location, and bio, injecting them into the `context` dictionary passed to the orchestrator.

### 2. Context-Aware Variant Generation
Traditional OSINT tools fail when searching common names because they only test exact string matches. Our `generate_username_variants` uses the extracted DOB and Location to generate high-probability handles like `[firstname][lastname][birth_year]` and `[firstname]_[location_code]`. 

### 3. Dynamic Seed Harvesting (Bug 2 Fix)
Before blindly generating usernames, `UsernameConnector.extract_handles_from_search()` performs a quick, lightweight DuckDuckGo HTML search. It uses Regex to pull actual `@handles` and profile URLs from the search snippets, injecting real ground-truth handles into the enumeration list.

### 4. Strict Validation (Bug 1 & 3 Fix)
Previously, a HTTP 200 response on `github.com/levels` marked "levels" as found, leading to garbage data. The `check_platform` logic now pulls the raw text of the HTTP 200 response and validates that the original query name tokens actually appear inside the profile bio/HTML. If they don't, it is silently discarded, ensuring the "Evidence Count" only displays verified facts.

---

## IMAGE INTELLIGENCE PIPELINE

The image module was fully built from scratch to support deep visual footprinting:

1. **Flask Upload Endpoint**: `app.py` accepts `multipart/form-data` image uploads, saving them locally and triggering immediate initial analysis.
2. **EXIF Extractor**: Parses the raw byte headers using `Pillow` to extract Camera models, timestamps, and converts raw GPS coordinates into decimal Latitude/Longitude pairs.
3. **InsightFace Wiring**: Loads the `buffalo_l` model (CPU optimized). Detects bounding boxes and extracts 512-dimensional facial embeddings for identity matching. 
4. **Reverse Web Search**: Connects to the public web via `SauceNaoConnector`.
5. **Dossier Integration**: Results are uniquely categorized in the UI under **Photos & Media** and **Reverse Image Matches**.

---

## IDENTITY RESOLUTION & CORROBORATION

The `IdentityResolver` (`identity_resolver.py`) merges raw evidence into a canonical `ResolvedPerson` object.

### Corroboration Signals (Fix 1)
Instead of just presenting a list of links, the resolver tracks *why* it linked them together. It generates an array of explicit reasons (e.g., `✓ Email verified in evidence`, `✓ Consistent username pattern matched across 3 platforms`, `⚠ Name match only — high chance of false positive`). These are displayed directly on the React Dashboard.

### Meaningful Confidence Scoring (Fix 2)
The `match_confidence` score is strictly computed:
- **90%+**: Email exact match + username match across 3+ platforms.
- **70–90%**: Username pattern match + Location consistent.
- **50–70%**: Name match only, unverified context.
- **<50%**: Possible match, low corroboration.

---

## SETUP & TESTING

### Prerequisites
- Python 3.10+
- Node.js 18+
- MongoDB instance running locally (or Atlas)
- Ensure `spacy` models are installed: `python -m spacy download en_core_web_sm`
- Ensure `insightface` and `onnxruntime` are installed for facial recognition.

### Running the application
**Backend:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

### How to Test the Upgrades
1. Go to the Investigation tab.
2. Click **Upload Target Image** and select a photo.
3. Type: *"Investigate this footprint. Look for history on Reddit."*
4. Click Start. Watch the backend terminal spawn 15+ concurrent requests, filter out false positives based on bio text, run the image through SauceNAO, and render the corroboration logic in the dashboard.
