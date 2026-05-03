# SDINT Project Development Timeline

This document outlines the stepwise procedure and evolutionary journey of the SDINT (Social Data Intelligence Platform) project, detailing how it grew from a foundational analytics tool to a robust OSINT investigation framework.

## Phase 1: Foundation & Infrastructure (Deploying Social Analytics Platform)
**Objective**: Build a full-stack platform capable of processing social data.
- **Backend Setup**: Developed a Flask-based backend architecture connecting to a MongoDB database to house social media data (posts, comments, trends).
- **Frontend Setup**: Built a responsive UI using React & Vite.
- **Deployment & Cloud Infrastructure**: Configured environment variables, resolved CORS issues, and orchestrated cloud deployment (Vercel for Frontend, Render for Backend) to ensure both modules communicated flawlessly in a production environment.

## Phase 2: Core AI Social Analytics Engine
**Objective**: Implement advanced analytical models on textual social media data.
- **Trend & Sentiment Analysis**: Built pipelines to track trending topics, generate text summaries, and analyze the sentiment distribution of posts.
- **Toxicity & Opinion Divergence**: Integrated NLP models to detect toxic comments and compute "opinion divergence" in ongoing discussions.
- **Echo Chamber Scoring**: Developed algorithms to measure and assign "echo chamber" scores to various subreddit communities.
- **Debugging & Polish**: Resolved data pipeline issues specifically targeting incident detection modules, ensuring the frontend accurately rendered real-time analytical metrics.

## Phase 3: The OSINT Evidence Engine (Module 1)
**Objective**: Transition from passive social analytics to active intelligence gathering.
- **Architecture Design**: Conceptualized the Evidence Engine—a system designed to ingest, validate, and store intelligence artifacts.
- **Entity Extraction**: Implemented SpaCy NLP to automatically extract primary targets, locations, DOBs, and context from descriptive user prompts.
- **Schema & Data Modeling**: Developed standard `EvidenceItem` models and a Mongo-backed Evidence Store to ensure unified data formats.
- **Integration Testing**: Executed extensive test suites to validate schema adherence and ensure the engine was ready for multi-source ingestion.

## Phase 4: The OSINT Connector Framework
**Objective**: Connect the application to real-world, open-source intelligence databases.
- **Platform Connectors**: Built concurrent connector classes (UsernameConnector, BreachConnector, GithubConnector) utilizing `aiohttp` for parallel execution.
- **Internal Integration**: Implemented `RedditLocalConnector` to leverage our existing, internal social media database as a high-confidence evidence source.
- **Smart Enumeration**: Developed logic to take NLP-extracted parameters (like DOB and Location) to generate highly probable username variants, supplementing standard exact-match searches.
- **Image Intelligence**: Integrated InsightFace (for 512-D facial embeddings) and Pillow (for EXIF data) to allow the system to ingest images and execute reverse image searches via SauceNAO.

## Phase 5: Identity Corroboration & Orchestration (Mastering the Framework)
**Objective**: Eliminate false positives and weave raw data into actionable, corroborated intelligence.
- **Investigation Orchestrator**: Developed `investigation_orchestrator.py` to act as the central brain—parsing prompts, spawning concurrent connector tasks, and routing evidence.
- **Identity Resolver**: Engineered an `IdentityResolver` module that cross-references evidence. Instead of listing raw data, it groups findings into canonical `ResolvedPerson` profiles.
- **Confidence Scoring Engine**: Implemented strict validation mechanics:
  - *Verification Logic*: Enforced logic to verify a target's name actually appears in the bio of HTTP 200 URLs, culling false positives.
  - *Dynamic Scoring*: Assigned dynamic confidence percentages (e.g., 90%+ requires email exact match + username match across 3+ platforms).
- **Executive Reporting**: Built modules to auto-generate PDF reports and interactive UI dashboards displaying entity networks, validation signals (green checkmarks/warnings), and intelligence timelines.

## Phase 6: Review & Finalization
**Objective**: Prepare the system for project review and production handover.
- **Technical Documentation**: Generated comprehensive documentation (`OSINT_IMPLEMENTATION.md`, `SOCIAL_DISCUSSION_IMPLEMENTATION.md`) explaining system flows, architecture, and deployment procedures.
- **Execution Simplification**: Created global launchers (`run_sdint.bat`) to automate dependency management and multi-server bootups, ensuring a seamless experience for evaluators and users.
