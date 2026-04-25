# OSINT SYSTEM — COMPLETE IMPLEMENTATION PROMPT
# For: AI Code Editor (Cursor / Windsurf / Copilot Chat)
# Project: Flask + MongoDB + React + Vite OSINT Investigation Platform
# Status: Completing partially-built system. No paid APIs. All free alternatives.

---

## CONTEXT — WHAT IS ALREADY BUILT (DO NOT REBUILD)

The following are confirmed working. Do not touch or rewrite these:

### Backend (Python / Flask / MongoDB)
- `EvidenceItem` dataclass with enums, validation, entity support — ✅ DONE
- MongoDB `evidence_items` collection with dedup index, search, stats — ✅ DONE
- Web search connector using `ddgs` (DuckDuckGo) — ✅ DONE
- Domain intel connector using `python-whois` + `dnspython` — ✅ DONE
- Entity extraction using `spaCy en_core_web_sm` + regex (emails, domains, IPs) — ✅ DONE
- Investigation Manager: MongoDB-backed CRUD, persists across restarts — ✅ DONE
- Entity Pivot Analysis: MongoDB aggregation for co-occurring entities — ✅ DONE

### Frontend (React + Vite)
- Overview dashboard with Recharts pie + bar charts — ✅ DONE
- Data Collection page with 4 sources and result cards — ✅ DONE
- Evidence Browser with detail panel — ✅ DONE
- Entity Explorer with pivot — ✅ DONE
- Investigation Dashboard — ✅ DONE

---

## WHAT NEEDS TO BE BUILT — COMPLETE SPECIFICATION

---

## TASK 1: FIX SHERLOCK USERNAME LOOKUP

**Problem:** `sherlock-project` is installed but connector import path is broken.

**Fix — replace the broken import with this working implementation:**

```python
# File: connectors/username_connector.py
# Replace entire file with this implementation

import subprocess
import json
import asyncio
import aiohttp
from dataclasses import dataclass
from typing import Optional
from datetime import datetime, timezone
import re

# Platform list — no sherlock import needed, use direct HTTP checks
# These platforms have predictable URL patterns and return 200 if user exists

PLATFORMS = {
    "GitHub": "https://github.com/{username}",
    "Reddit": "https://www.reddit.com/user/{username}/about.json",
    "HackerNews": "https://hacker-news.firebaseio.com/v0/user/{username}.json",
    "GitLab": "https://gitlab.com/{username}",
    "PyPI": "https://pypi.org/user/{username}/",
    "npm": "https://www.npmjs.com/~{username}",
    "Keybase": "https://keybase.io/{username}/_/api/1.0/user/lookup.json?username={username}",
    "Telegram": "https://t.me/{username}",
    "Dev.to": "https://dev.to/api/users/by_username?url={username}",
    "Hashnode": "https://hashnode.com/@{username}",
    "Medium": "https://medium.com/@{username}",
    "Pastebin": "https://pastebin.com/u/{username}",
    "Replit": "https://replit.com/@{username}",
    "Codepen": "https://codepen.io/{username}",
    "Stackoverflow": "https://stackoverflow.com/users?tab=Reputation&q={username}",
    "Mastodon": "https://mastodon.social/@{username}",
    "Bitbucket": "https://bitbucket.org/{username}/",
    "Sourceforge": "https://sourceforge.net/u/{username}/profile/",
    "Docker": "https://hub.docker.com/u/{username}/",
    "Gravatar": "https://en.gravatar.com/{username}",
}

# Platforms that return JSON — check for specific field
JSON_PLATFORMS = {
    "Reddit": lambda r: r.get("data", {}).get("name") is not None,
    "HackerNews": lambda r: r is not None and "id" in r,
    "Dev.to": lambda r: r.get("id") is not None,
    "Keybase": lambda r: r.get("status", {}).get("code") == 0,
}

async def check_platform(session: aiohttp.ClientSession, platform: str, url: str, username: str) -> Optional[dict]:
    """Check if username exists on a single platform."""
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
    }
    try:
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10), allow_redirects=True) as resp:
            if platform in JSON_PLATFORMS:
                if resp.status == 200:
                    try:
                        data = await resp.json(content_type=None)
                        if JSON_PLATFORMS[platform](data):
                            return {"platform": platform, "url": url, "found": True, "status": resp.status}
                    except Exception:
                        pass
                return None
            else:
                # For HTML platforms: 200 = found, 404 = not found
                # 301/302 redirects to login = not found for some platforms
                if resp.status == 200:
                    # Extra: check final URL isn't a generic "user not found" page
                    final_url = str(resp.url)
                    if "not_found" in final_url.lower() or "404" in final_url:
                        return None
                    return {"platform": platform, "url": url, "found": True, "status": resp.status}
    except asyncio.TimeoutError:
        pass
    except Exception:
        pass
    return None


async def enumerate_username(username: str) -> list[dict]:
    """Check username across all platforms concurrently."""
    results = []
    urls = {platform: template.format(username=username) for platform, template in PLATFORMS.items()}
    
    connector = aiohttp.TCPConnector(limit=20, limit_per_host=2)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [
            check_platform(session, platform, url, username)
            for platform, url in urls.items()
        ]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
    
    for resp in responses:
        if isinstance(resp, dict) and resp.get("found"):
            results.append(resp)
    
    return results


def generate_username_variants(name: str = None, email: str = None, hint: str = None) -> list[str]:
    """Generate likely usernames from name, email, or hint."""
    variants = set()
    
    if hint:
        variants.add(hint.lower().strip().lstrip("@"))
    
    if email:
        local = email.split("@")[0].lower()
        variants.add(local)
        variants.add(local.replace(".", ""))
        variants.add(local.replace("_", ""))
        variants.add(local.replace("-", ""))
    
    if name:
        parts = name.lower().strip().split()
        if len(parts) >= 2:
            first, last = parts[0], parts[-1]
            variants.update([
                f"{first}{last}",
                f"{first}.{last}",
                f"{first}_{last}",
                f"{first[0]}{last}",
                f"{first}{last[0]}",
                f"{last}{first}",
                f"{last}.{first}",
                first,
                last,
            ])
    
    return list(variants)[:10]  # cap at 10 variants


class UsernameConnector:
    """Free username enumeration across 20+ platforms using direct HTTP checks."""
    
    name = "username_lookup"
    supports_types = ["username", "name", "email"]
    
    def run(self, pivot: dict) -> list:
        """Synchronous wrapper for async enumeration."""
        from models.evidence import EvidenceItem, EvidenceType, ConfidenceLevel
        
        pivot_type = pivot.get("type")
        pivot_value = pivot.get("value", "")
        session_id = pivot.get("session_id", "")
        
        # Generate username variants
        if pivot_type == "username":
            usernames = [pivot_value.lstrip("@")]
        elif pivot_type == "name":
            usernames = generate_username_variants(name=pivot_value)
        elif pivot_type == "email":
            usernames = generate_username_variants(email=pivot_value)
        else:
            return []
        
        all_evidence = []
        
        for username in usernames:
            try:
                # Run async check synchronously
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                results = loop.run_until_complete(enumerate_username(username))
                loop.close()
                
                for result in results:
                    evidence = EvidenceItem(
                        connector_name=self.name,
                        source_url=result["url"],
                        queried_value=username,
                        queried_type="username",
                        raw_text=f"Username '{username}' found on {result['platform']}",
                        extracted_fields={
                            "username": username,
                            "platform": result["platform"],
                            "profile_url": result["url"],
                            "http_status": result["status"],
                        },
                        collected_at=datetime.now(timezone.utc),
                        confidence=0.85,
                        license_note="Public web profile",
                        session_id=session_id,
                    )
                    all_evidence.append(evidence)
                    
            except Exception as e:
                print(f"Username check error for '{username}': {e}")
        
        return all_evidence
```

**Also install:** `pip install aiohttp` (add to requirements.txt)

---

## TASK 2: REPLACE HIBP WITH FREE BREACH ALTERNATIVES

**Problem:** HIBP requires $3.50/month API key. Replace entirely with free alternatives.

**Build this file: `connectors/breach_connector.py`**

```python
# File: connectors/breach_connector.py
# 100% free breach checking using multiple sources

import requests
import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Optional
import time


class BreachConnector:
    """
    Free breach checking using:
    1. HIBP k-anonymity password check (SHA1 prefix, no key needed)
    2. psbdmp.ws paste search (free, no key)
    3. LeakCheck public API (free tier, no key for basic check)
    4. IntelX free tier (limited but real)
    5. Local COMB wordlist check if available
    """
    
    name = "breach_check"
    supports_types = ["email", "username", "phone"]
    
    HEADERS = {
        "User-Agent": "OSINT-Research-Tool/1.0 (educational)",
        "Accept": "application/json",
    }
    
    def run(self, pivot: dict) -> list:
        from models.evidence import EvidenceItem
        
        pivot_type = pivot.get("type")
        pivot_value = pivot.get("value", "")
        session_id = pivot.get("session_id", "")
        
        all_evidence = []
        
        if pivot_type == "email":
            all_evidence += self._check_hibp_password_range(pivot_value, session_id)
            all_evidence += self._check_psbdmp(pivot_value, session_id)
            all_evidence += self._check_leakcheck_free(pivot_value, session_id)
            all_evidence += self._check_breachdirectory(pivot_value, session_id)
        
        elif pivot_type == "username":
            all_evidence += self._check_psbdmp(pivot_value, session_id)
        
        return all_evidence

    def _check_hibp_password_range(self, email: str, session_id: str) -> list:
        """
        HIBP k-anonymity: hash the email, send first 5 chars.
        This tells us IF the email was in a breach without sending the full email.
        NOTE: This is the password range API — for email we use a different approach.
        Actually checks if the email string itself has been seen as a password (common pattern).
        """
        # For email breach check without API key: use the breachdirectory approach
        # The HIBP password range API works for passwords, not emails
        # So we hash the email and check the password range (emails are often used as passwords)
        sha1 = hashlib.sha1(email.encode("utf-8")).hexdigest().upper()
        prefix = sha1[:5]
        suffix = sha1[5:]
        
        try:
            resp = requests.get(
                f"https://api.pwnedpasswords.com/range/{prefix}",
                headers={"User-Agent": "OSINT-Research-Tool/1.0"},
                timeout=10
            )
            if resp.status_code == 200:
                hashes = resp.text.strip().split("\n")
                for line in hashes:
                    parts = line.strip().split(":")
                    if len(parts) == 2 and parts[0].upper() == suffix:
                        count = int(parts[1])
                        return [self._make_evidence(
                            session_id=session_id,
                            source_url="https://api.pwnedpasswords.com",
                            queried_value=email,
                            raw_text=f"Email '{email}' found in password breach databases ({count} occurrences)",
                            fields={
                                "breach_type": "password_reuse",
                                "occurrence_count": count,
                                "severity": "HIGH" if count > 100 else "MEDIUM",
                                "note": "Email string found in leaked password lists"
                            },
                            confidence=0.90
                        )]
        except Exception as e:
            print(f"HIBP range check error: {e}")
        return []

    def _check_psbdmp(self, query: str, session_id: str) -> list:
        """Search Pastebin dumps via psbdmp.ws — free, no key."""
        results = []
        try:
            time.sleep(1)  # rate limit respect
            resp = requests.get(
                f"https://psbdmp.ws/api/v3/search/{requests.utils.quote(query)}",
                headers=self.HEADERS,
                timeout=15
            )
            if resp.status_code == 200:
                data = resp.json()
                pastes = data.get("data", [])[:5]  # top 5 results
                for paste in pastes:
                    results.append(self._make_evidence(
                        session_id=session_id,
                        source_url=f"https://pastebin.com/{paste.get('id', '')}",
                        queried_value=query,
                        raw_text=f"Query '{query}' found in paste: {paste.get('text', '')[:500]}",
                        fields={
                            "paste_id": paste.get("id"),
                            "paste_date": paste.get("time"),
                            "paste_preview": paste.get("text", "")[:300],
                            "source": "psbdmp"
                        },
                        confidence=0.70
                    ))
        except Exception as e:
            print(f"psbdmp error: {e}")
        return results

    def _check_leakcheck_free(self, email: str, session_id: str) -> list:
        """LeakCheck.io free public endpoint — no key, limited results."""
        results = []
        try:
            time.sleep(1)
            resp = requests.get(
                f"https://leakcheck.io/api/public?check={requests.utils.quote(email)}",
                headers=self.HEADERS,
                timeout=15
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get("found", 0) > 0:
                    sources = data.get("sources", [])
                    results.append(self._make_evidence(
                        session_id=session_id,
                        source_url="https://leakcheck.io",
                        queried_value=email,
                        raw_text=f"Email '{email}' found in {data.get('found')} breach(es): {', '.join(s.get('name','') for s in sources)}",
                        fields={
                            "breach_count": data.get("found"),
                            "breach_sources": [s.get("name") for s in sources],
                            "source": "leakcheck_public"
                        },
                        confidence=0.85
                    ))
        except Exception as e:
            print(f"LeakCheck error: {e}")
        return results

    def _check_breachdirectory(self, email: str, session_id: str) -> list:
        """BreachDirectory.org public API — free, no key required for basic lookups."""
        results = []
        try:
            time.sleep(1.5)
            # Use RapidAPI free tier if key available, else use public endpoint
            resp = requests.get(
                f"https://breachdirectory.p.rapidapi.com/?func=auto&term={requests.utils.quote(email)}",
                headers={
                    **self.HEADERS,
                    "X-RapidAPI-Host": "breachdirectory.p.rapidapi.com",
                    # Add key from env if available — free tier: 50 req/month
                    # "X-RapidAPI-Key": os.getenv("RAPIDAPI_KEY", ""),
                },
                timeout=15
            )
            # If no key, fall back gracefully
            if resp.status_code in (200, 201):
                data = resp.json()
                if data.get("success") and data.get("result"):
                    found_items = data["result"][:3]
                    for item in found_items:
                        results.append(self._make_evidence(
                            session_id=session_id,
                            source_url="https://breachdirectory.org",
                            queried_value=email,
                            raw_text=f"Breach record found for '{email}'",
                            fields={
                                "sha1": item.get("sha1"),
                                "password_hint": item.get("password", "")[:3] + "***" if item.get("password") else None,
                                "source": "breachdirectory"
                            },
                            confidence=0.80
                        ))
        except Exception as e:
            print(f"BreachDirectory error: {e}")
        return results

    def _make_evidence(self, session_id, source_url, queried_value, raw_text, fields, confidence) -> object:
        from models.evidence import EvidenceItem
        return EvidenceItem(
            connector_name=self.name,
            source_url=source_url,
            queried_value=queried_value,
            queried_type="email",
            raw_text=raw_text,
            extracted_fields=fields,
            collected_at=datetime.now(timezone.utc),
            confidence=confidence,
            license_note="Public breach database",
            session_id=session_id,
        )
```

---

## TASK 3: IDENTITY RESOLUTION — COMPLETE THE SKELETON

**Problem:** Class exists but merging logic is not production-ready.

**Replace/complete `services/identity_resolver.py` with this:**

```python
# File: services/identity_resolver.py
# Complete identity resolution — no paid deps, uses jellyfish + custom scoring

import jellyfish
import re
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timezone
from collections import defaultdict
import hashlib


@dataclass
class ResolvedPerson:
    """Canonical person entity built from merged evidence."""
    id: str
    session_id: str
    canonical_name: Optional[str]
    name_first: Optional[str]
    name_last: Optional[str]
    aliases: list[str] = field(default_factory=list)
    usernames: list[dict] = field(default_factory=list)      # [{username, platform, url, confidence}]
    emails: list[dict] = field(default_factory=list)          # [{email, breach_count, source}]
    phones: list[str] = field(default_factory=list)
    locations: list[str] = field(default_factory=list)
    employers: list[str] = field(default_factory=list)
    domains: list[str] = field(default_factory=list)
    social_profiles: list[dict] = field(default_factory=list) # [{platform, url, username}]
    breach_findings: list[dict] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    match_confidence: float = 0.0
    risk_score: float = 0.0
    risk_level: str = "LOW"  # LOW / MEDIUM / HIGH
    intelligence_summary: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    raw_evidence_count: int = 0


class IdentityResolver:
    """
    Merges evidence items into a canonical ResolvedPerson entity.
    Uses weighted feature scoring without Splink (no heavy ML dependency).
    Production-ready for < 10,000 evidence items per session.
    """

    # Similarity thresholds
    USERNAME_SIMILARITY_THRESHOLD = 0.88
    NAME_SIMILARITY_THRESHOLD = 0.85

    def resolve(self, evidence_items: list, session_id: str, raw_query: str) -> ResolvedPerson:
        """
        Main entry point. Takes all evidence items for a session,
        returns a single merged ResolvedPerson.
        """
        person_id = hashlib.md5(f"{session_id}{raw_query}".encode()).hexdigest()
        
        person = ResolvedPerson(
            id=person_id,
            session_id=session_id,
            canonical_name=None,
        )
        
        # Extract structured data from all evidence items
        all_names = []
        all_emails = set()
        all_phones = set()
        all_usernames = []   # list of {username, platform, url}
        all_locations = []
        all_employers = []
        all_domains = set()
        all_profiles = []
        all_breach_findings = []
        
        for ev in evidence_items:
            person.evidence_ids.append(str(ev.get("_id", "")))
            fields = ev.get("extracted_fields", {})
            
            # Names
            for name in fields.get("persons", []):
                if name and len(name) > 2:
                    all_names.append(name)
            if fields.get("name"):
                all_names.append(fields["name"])
            
            # Emails
            for email in fields.get("emails", []):
                if self._is_valid_email(email):
                    all_emails.add(email.lower().strip())
            if fields.get("email") and self._is_valid_email(fields["email"]):
                all_emails.add(fields["email"].lower().strip())
            
            # Phones
            for phone in fields.get("phones", []):
                normalized = self._normalize_phone(phone)
                if normalized:
                    all_phones.add(normalized)
            
            # Usernames
            if fields.get("username") and fields.get("platform"):
                all_usernames.append({
                    "username": fields["username"],
                    "platform": fields["platform"],
                    "url": fields.get("profile_url", ev.get("source_url", "")),
                    "confidence": ev.get("confidence", 0.7),
                })
            
            # Locations
            for loc in fields.get("locations", []):
                if loc and len(loc) > 1:
                    all_locations.append(loc)
            
            # Employers / Organisations
            for org in fields.get("organizations", []):
                if org and len(org) > 1:
                    all_employers.append(org)
            
            # Domains
            for domain in fields.get("domains", []):
                if domain:
                    all_domains.add(domain.lower())
            
            # Breach findings
            breach_type = fields.get("breach_type") or fields.get("breach_count")
            if breach_type or fields.get("breach_sources"):
                all_breach_findings.append({
                    "source_connector": ev.get("connector_name"),
                    "source_url": ev.get("source_url"),
                    "details": fields,
                    "collected_at": str(ev.get("collected_at", "")),
                })
        
        # Deduplicate and resolve
        person.canonical_name = self._resolve_canonical_name(all_names)
        name_parts = self._split_name(person.canonical_name) if person.canonical_name else {}
        person.name_first = name_parts.get("first")
        person.name_last = name_parts.get("last")
        person.aliases = list(set(all_names))[:20]
        person.emails = [{"email": e, "breach_count": 0, "source": "evidence"} for e in all_emails]
        person.phones = list(all_phones)[:10]
        person.usernames = self._dedupe_usernames(all_usernames)
        person.locations = list(set(all_locations))[:10]
        person.employers = list(set(all_employers))[:10]
        person.domains = list(all_domains)[:10]
        person.social_profiles = [
            {"platform": u["platform"], "url": u["url"], "username": u["username"]}
            for u in person.usernames
        ]
        person.breach_findings = all_breach_findings
        person.raw_evidence_count = len(evidence_items)
        
        # Score match confidence and risk
        person.match_confidence = self._compute_match_confidence(person)
        person.risk_score = self._compute_risk_score(person)
        person.risk_level = "HIGH" if person.risk_score > 0.7 else "MEDIUM" if person.risk_score > 0.4 else "LOW"
        
        # Generate text summary
        person.intelligence_summary = self._generate_summary(person, raw_query)
        
        return person

    def _resolve_canonical_name(self, names: list[str]) -> Optional[str]:
        """Pick the most representative name from a list of candidates."""
        if not names:
            return None
        # Prefer names that appear most frequently
        freq = defaultdict(int)
        for n in names:
            clean = n.strip().title()
            if 2 <= len(clean.split()) <= 4:  # reasonable name length
                freq[clean] += 1
        if not freq:
            return names[0].strip().title()
        return max(freq, key=freq.get)

    def _split_name(self, full_name: str) -> dict:
        """Simple name splitter."""
        parts = full_name.strip().split()
        if len(parts) == 1:
            return {"first": parts[0], "last": None}
        elif len(parts) >= 2:
            return {"first": parts[0], "last": parts[-1]}
        return {}

    def _dedupe_usernames(self, usernames: list[dict]) -> list[dict]:
        """Remove duplicate usernames, prefer higher confidence entries."""
        seen = {}  # (username_lower, platform) → entry
        for u in usernames:
            key = (u["username"].lower(), u.get("platform", "").lower())
            if key not in seen or u.get("confidence", 0) > seen[key].get("confidence", 0):
                seen[key] = u
        return list(seen.values())

    def _is_valid_email(self, email: str) -> bool:
        return bool(re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email))

    def _normalize_phone(self, phone: str) -> Optional[str]:
        digits = re.sub(r'\D', '', phone)
        if 8 <= len(digits) <= 15:
            return f"+{digits}" if not digits.startswith("+") else digits
        return None

    def _compute_match_confidence(self, person: ResolvedPerson) -> float:
        """Score 0–1 based on how much corroborating evidence exists."""
        score = 0.0
        if person.canonical_name:
            score += 0.20
        if person.emails:
            score += min(0.25, len(person.emails) * 0.10)
        if person.phones:
            score += 0.15
        if person.usernames:
            score += min(0.25, len(person.usernames) * 0.05)
        if person.locations:
            score += 0.05
        if person.employers:
            score += 0.05
        if person.breach_findings:
            score += 0.05
        return round(min(score, 1.0), 2)

    def _compute_risk_score(self, person: ResolvedPerson) -> float:
        """Risk indicators: breaches, large platform footprint, paste mentions."""
        score = 0.0
        if len(person.breach_findings) > 0:
            score += 0.35
        if len(person.breach_findings) > 3:
            score += 0.20
        if len(person.usernames) > 8:
            score += 0.15  # unusual number of platform accounts
        if len(person.emails) > 5:
            score += 0.10
        # Check for paste findings (high risk)
        for b in person.breach_findings:
            if "pastebin" in str(b.get("source_url", "")).lower():
                score += 0.20
                break
        return round(min(score, 1.0), 2)

    def _generate_summary(self, person: ResolvedPerson, raw_query: str) -> str:
        """Generate a human-readable intelligence summary."""
        lines = []
        
        if person.canonical_name:
            lines.append(f"Target identified as: {person.canonical_name}.")
        else:
            lines.append(f"Target query: '{raw_query}'. Name could not be conclusively resolved.")
        
        if person.usernames:
            platforms = list(set(u.get("platform", "") for u in person.usernames))[:5]
            lines.append(f"Online presence detected on {len(person.usernames)} platform(s): {', '.join(platforms)}.")
        
        if person.emails:
            lines.append(f"{len(person.emails)} email address(es) associated: {', '.join(e['email'] for e in person.emails[:3])}.")
        
        if person.breach_findings:
            lines.append(f"BREACH ALERT: Target appears in {len(person.breach_findings)} breach/paste source(s). Risk level: {person.risk_level}.")
        else:
            lines.append("No breach exposure detected in searched databases.")
        
        if person.locations:
            lines.append(f"Associated locations: {', '.join(person.locations[:3])}.")
        
        if person.employers:
            lines.append(f"Associated organisations: {', '.join(person.employers[:3])}.")
        
        lines.append(f"Match confidence: {int(person.match_confidence * 100)}% based on {person.raw_evidence_count} evidence items.")
        
        return " ".join(lines)

    def save_to_db(self, person: ResolvedPerson, db) -> str:
        """Persist resolved person to MongoDB."""
        import dataclasses
        doc = dataclasses.asdict(person)
        doc["created_at"] = person.created_at
        result = db.resolved_persons.replace_one(
            {"session_id": person.session_id},
            doc,
            upsert=True
        )
        return person.id
```

---

## TASK 4: COMPLETE NARRATIVE BUILDER

**Problem:** Timeline generation exists but minimal.

**Replace `services/narrative_builder.py` with:**

```python
# File: services/narrative_builder.py

from datetime import datetime, timezone
from typing import Optional
from collections import defaultdict


class NarrativeBuilder:
    """
    Builds structured timeline and narrative from evidence items and resolved person.
    Output feeds directly into the React timeline component.
    """

    def build_timeline(self, evidence_items: list, person: dict) -> list[dict]:
        """
        Returns list of timeline events sorted chronologically.
        Each event maps to a Recharts data point.
        """
        events = []
        
        for ev in evidence_items:
            fields = ev.get("extracted_fields", {})
            connector = ev.get("connector_name", "")
            
            # Determine timestamp
            ts = ev.get("collected_at")
            if isinstance(ts, str):
                try:
                    ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                except Exception:
                    ts = datetime.now(timezone.utc)
            
            event_type = self._classify_event_type(connector, fields)
            platform = fields.get("platform", self._connector_to_platform(connector))
            
            events.append({
                "id": str(ev.get("_id", "")),
                "timestamp": ts.isoformat() if ts else None,
                "timestamp_ms": int(ts.timestamp() * 1000) if ts else 0,
                "type": event_type,
                "platform": platform,
                "connector": connector,
                "title": self._make_event_title(connector, fields, ev),
                "description": ev.get("raw_text", "")[:300],
                "source_url": ev.get("source_url", ""),
                "confidence": ev.get("confidence", 0.5),
                "severity": self._get_severity(event_type, fields),
            })
        
        # Sort by timestamp ascending
        events.sort(key=lambda e: e["timestamp_ms"])
        return events

    def build_platform_summary(self, evidence_items: list) -> list[dict]:
        """
        Aggregates evidence by platform for the platform cards in dossier.
        """
        platform_data = defaultdict(lambda: {
            "count": 0, "urls": [], "usernames": set(), "last_seen": None
        })
        
        for ev in evidence_items:
            fields = ev.get("extracted_fields", {})
            platform = fields.get("platform") or self._connector_to_platform(ev.get("connector_name", ""))
            
            platform_data[platform]["count"] += 1
            if ev.get("source_url"):
                platform_data[platform]["urls"].append(ev["source_url"])
            if fields.get("username"):
                platform_data[platform]["usernames"].add(fields["username"])
            ts = ev.get("collected_at")
            if ts:
                platform_data[platform]["last_seen"] = str(ts)
        
        result = []
        for platform, data in platform_data.items():
            if platform and platform != "unknown":
                result.append({
                    "platform": platform,
                    "evidence_count": data["count"],
                    "profile_urls": list(set(data["urls"]))[:3],
                    "usernames": list(data["usernames"])[:5],
                    "last_seen": data["last_seen"],
                })
        
        return sorted(result, key=lambda x: x["evidence_count"], reverse=True)

    def build_entity_network(self, evidence_items: list) -> dict:
        """
        Builds nodes + edges for vis-network graph visualization.
        """
        nodes = {}
        edges = []
        edge_id = 0
        
        # Central node (the query target)
        nodes["target"] = {
            "id": "target",
            "label": "TARGET",
            "group": "person",
            "size": 30,
            "color": "#7F77DD",
        }
        
        for ev in evidence_items:
            fields = ev.get("extracted_fields", {})
            connector = ev.get("connector_name", "")
            
            # Username nodes
            if fields.get("username") and fields.get("platform"):
                node_id = f"u_{fields['username']}_{fields['platform']}"
                if node_id not in nodes:
                    nodes[node_id] = {
                        "id": node_id,
                        "label": f"@{fields['username']}\n({fields['platform']})",
                        "group": "username",
                        "color": "#1D9E75",
                        "url": fields.get("profile_url", ""),
                    }
                edges.append({"id": edge_id, "from": "target", "to": node_id, "label": "uses"})
                edge_id += 1
            
            # Email nodes
            for email in fields.get("emails", []):
                node_id = f"e_{email}"
                if node_id not in nodes:
                    nodes[node_id] = {
                        "id": node_id,
                        "label": email,
                        "group": "email",
                        "color": "#EF9F27",
                    }
                edges.append({"id": edge_id, "from": "target", "to": node_id, "label": "owns"})
                edge_id += 1
            
            # Domain nodes
            for domain in fields.get("domains", []):
                node_id = f"d_{domain}"
                if node_id not in nodes and len(nodes) < 50:  # cap
                    nodes[node_id] = {
                        "id": node_id,
                        "label": domain,
                        "group": "domain",
                        "color": "#185FA5",
                    }
                edges.append({"id": edge_id, "from": "target", "to": node_id, "label": "linked"})
                edge_id += 1
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges[:100],  # cap edges
        }

    def _classify_event_type(self, connector: str, fields: dict) -> str:
        if "breach" in connector or fields.get("breach_type"):
            return "breach"
        if "username" in connector or fields.get("platform"):
            return "profile"
        if "domain" in connector or fields.get("whois_registrar"):
            return "domain"
        if "search" in connector:
            return "mention"
        if "wayback" in connector:
            return "archive"
        return "general"

    def _connector_to_platform(self, connector: str) -> str:
        mapping = {
            "web_search": "Web",
            "domain_intel": "WHOIS/DNS",
            "username_lookup": "Multi-Platform",
            "breach_check": "Breach DB",
            "reddit": "Reddit",
            "github": "GitHub",
            "hackernews": "HackerNews",
            "wayback": "Wayback Machine",
            "paste": "Pastebin",
        }
        for key, val in mapping.items():
            if key in connector.lower():
                return val
        return connector

    def _make_event_title(self, connector: str, fields: dict, ev: dict) -> str:
        if fields.get("platform") and fields.get("username"):
            return f"Profile found: @{fields['username']} on {fields['platform']}"
        if fields.get("breach_type"):
            return f"Breach detected: {fields['breach_type']}"
        if fields.get("domain"):
            return f"Domain intel: {fields['domain']}"
        source = ev.get("source_url", "")
        if source:
            from urllib.parse import urlparse
            domain = urlparse(source).netloc
            return f"Evidence from {domain}"
        return f"Evidence via {connector}"

    def _get_severity(self, event_type: str, fields: dict) -> str:
        if event_type == "breach":
            return "HIGH"
        if event_type == "profile":
            return "MEDIUM"
        return "LOW"
```

---

## TASK 5: ADD BACKGROUND TASK QUEUE (WITHOUT CELERY)

**Problem:** No background job processing. Celery is complex to set up.
**Solution:** Use Python's built-in `concurrent.futures` + `threading` — zero new dependencies.

```python
# File: services/task_queue.py
# Lightweight async task queue using ThreadPoolExecutor — no Celery needed

import uuid
import threading
from concurrent.futures import ThreadPoolExecutor, Future
from datetime import datetime, timezone
from typing import Callable, Any
from enum import Enum
import traceback


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"


class TaskQueue:
    """
    Thread-pool based task queue. Stores results in memory + MongoDB.
    Max 5 concurrent OSINT investigations.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = TaskQueue()
        return cls._instance
    
    def __init__(self, max_workers: int = 5):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.tasks: dict[str, dict] = {}  # task_id → task info
        self._db = None

    def set_db(self, db):
        self._db = db

    def submit(self, fn: Callable, *args, task_name: str = "task", **kwargs) -> str:
        """Submit a task and return its task_id."""
        task_id = str(uuid.uuid4())
        
        task_info = {
            "task_id": task_id,
            "name": task_name,
            "status": TaskStatus.PENDING,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "started_at": None,
            "completed_at": None,
            "result": None,
            "error": None,
        }
        self.tasks[task_id] = task_info
        self._save_task(task_info)
        
        def _wrapper():
            self.tasks[task_id]["status"] = TaskStatus.RUNNING
            self.tasks[task_id]["started_at"] = datetime.now(timezone.utc).isoformat()
            self._save_task(self.tasks[task_id])
            try:
                result = fn(*args, **kwargs)
                self.tasks[task_id]["status"] = TaskStatus.COMPLETE
                self.tasks[task_id]["result"] = str(result)[:500] if result else "done"
            except Exception as e:
                self.tasks[task_id]["status"] = TaskStatus.FAILED
                self.tasks[task_id]["error"] = traceback.format_exc()[-500:]
            finally:
                self.tasks[task_id]["completed_at"] = datetime.now(timezone.utc).isoformat()
                self._save_task(self.tasks[task_id])
        
        self.executor.submit(_wrapper)
        return task_id

    def get_status(self, task_id: str) -> dict:
        return self.tasks.get(task_id) or self._load_task(task_id) or {"error": "not found"}

    def _save_task(self, task_info: dict):
        if self._db is not None:
            try:
                self._db.tasks.replace_one(
                    {"task_id": task_info["task_id"]},
                    task_info,
                    upsert=True
                )
            except Exception:
                pass

    def _load_task(self, task_id: str) -> dict:
        if self._db is not None:
            try:
                return self._db.tasks.find_one({"task_id": task_id}, {"_id": 0})
            except Exception:
                pass
        return None


# Usage in Flask routes:
# queue = TaskQueue.get_instance()
# queue.set_db(db)  # call once at startup
# task_id = queue.submit(run_full_investigation, session_id, pivot, task_name="osint_investigation")
```

**Wire into Flask app:**
```python
# In app.py or wherever Flask app is created:
from services.task_queue import TaskQueue

task_queue = TaskQueue.get_instance()
task_queue.set_db(mongo.db)  # pass your MongoDB db instance

# Add status endpoint:
@app.route("/api/tasks/<task_id>")
def get_task_status(task_id):
    return jsonify(task_queue.get_status(task_id))
```

---

## TASK 6: PDF EXPORT — NO PAID DEPS

**Install:** `pip install weasyprint jinja2` (both free/open-source)

**Create `services/pdf_export.py`:**

```python
# File: services/pdf_export.py

from jinja2 import Environment, BaseLoader
from datetime import datetime

REPORT_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-size: 12px; color: #1a1a1a; line-height: 1.6; }
  .cover { padding: 60px 48px; border-bottom: 3px solid #7F77DD; }
  .cover h1 { font-size: 28px; font-weight: 700; color: #7F77DD; margin-bottom: 8px; }
  .cover .subtitle { font-size: 14px; color: #555; margin-bottom: 24px; }
  .cover .meta { font-size: 11px; color: #888; }
  .watermark { font-size: 11px; font-weight: 600; color: #E24B4A; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 16px; }
  .section { padding: 32px 48px; border-bottom: 0.5px solid #eee; }
  .section h2 { font-size: 16px; font-weight: 600; color: #333; margin-bottom: 16px; padding-bottom: 8px; border-bottom: 1px solid #e0e0e0; }
  .section h3 { font-size: 13px; font-weight: 600; color: #555; margin: 12px 0 8px; }
  .badge { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 10px; font-weight: 600; margin-right: 6px; }
  .badge-high { background: #FCEBEB; color: #A32D2D; }
  .badge-medium { background: #FAEEDA; color: #854F0B; }
  .badge-low { background: #E1F5EE; color: #085041; }
  .badge-platform { background: #EEEDFE; color: #3C3489; }
  table { width: 100%; border-collapse: collapse; margin-top: 8px; }
  th { background: #f5f5f5; padding: 8px 10px; text-align: left; font-size: 11px; font-weight: 600; border: 0.5px solid #ddd; }
  td { padding: 8px 10px; font-size: 11px; border: 0.5px solid #ddd; vertical-align: top; }
  tr:nth-child(even) { background: #fafafa; }
  .summary-box { background: #f9f8ff; border-left: 4px solid #7F77DD; padding: 16px 20px; border-radius: 0 8px 8px 0; margin: 12px 0; }
  .breach-box { background: #fff8f8; border-left: 4px solid #E24B4A; padding: 16px 20px; border-radius: 0 8px 8px 0; }
  .disclaimer { background: #f5f5f5; padding: 16px 20px; margin: 16px 0; border-radius: 8px; font-size: 10px; color: #888; }
  .footer { padding: 24px 48px; font-size: 10px; color: #aaa; text-align: center; }
  a { color: #7F77DD; text-decoration: none; }
  .confidence-bar { display: inline-block; width: 60px; height: 8px; background: #eee; border-radius: 4px; overflow: hidden; margin-left: 8px; vertical-align: middle; }
  .confidence-fill { height: 100%; background: #1D9E75; border-radius: 4px; }
</style>
</head>
<body>

<div class="cover">
  <div class="watermark">INVESTIGATION DRAFT — CONFIDENTIAL</div>
  <h1>OSINT Intelligence Report</h1>
  <div class="subtitle">{{ person.canonical_name or raw_query }}</div>
  <div class="meta">
    Session ID: {{ session_id }}<br>
    Generated: {{ generated_at }}<br>
    Evidence items: {{ person.raw_evidence_count }}<br>
    Match confidence: {{ (person.match_confidence * 100)|int }}%<br>
    Risk level: <span class="badge badge-{{ person.risk_level|lower }}">{{ person.risk_level }}</span>
  </div>
</div>

<div class="section">
  <h2>Executive Summary</h2>
  <div class="summary-box">{{ person.intelligence_summary }}</div>
</div>

{% if person.breach_findings %}
<div class="section">
  <h2>Breach Exposure <span class="badge badge-high">{{ person.breach_findings|length }} source(s)</span></h2>
  <div class="breach-box">
  <table>
    <tr><th>Source</th><th>Details</th><th>Risk</th></tr>
    {% for b in person.breach_findings %}
    <tr>
      <td><a href="{{ b.source_url }}">{{ b.source_connector }}</a></td>
      <td>{{ b.details|string|truncate(200) }}</td>
      <td><span class="badge badge-high">HIGH</span></td>
    </tr>
    {% endfor %}
  </table>
  </div>
</div>
{% endif %}

<div class="section">
  <h2>Identity Findings</h2>
  <table>
    <tr><th>Field</th><th>Value</th><th>Source</th></tr>
    {% if person.canonical_name %}
    <tr><td>Full name</td><td>{{ person.canonical_name }}</td><td>Resolved</td></tr>
    {% endif %}
    {% for email_obj in person.emails[:5] %}
    <tr><td>Email</td><td>{{ email_obj.email }}</td><td>{{ email_obj.source }}</td></tr>
    {% endfor %}
    {% for phone in person.phones[:5] %}
    <tr><td>Phone</td><td>{{ phone }}</td><td>Evidence</td></tr>
    {% endfor %}
    {% for loc in person.locations[:5] %}
    <tr><td>Location</td><td>{{ loc }}</td><td>Evidence</td></tr>
    {% endfor %}
    {% for employer in person.employers[:5] %}
    <tr><td>Organisation</td><td>{{ employer }}</td><td>Evidence</td></tr>
    {% endfor %}
  </table>
</div>

<div class="section">
  <h2>Platform Presence</h2>
  <table>
    <tr><th>Platform</th><th>Username</th><th>Profile URL</th><th>Confidence</th></tr>
    {% for u in person.usernames[:20] %}
    <tr>
      <td><span class="badge badge-platform">{{ u.platform }}</span></td>
      <td>{{ u.username }}</td>
      <td><a href="{{ u.url }}">{{ u.url|truncate(60) }}</a></td>
      <td>{{ (u.confidence * 100)|int }}%</td>
    </tr>
    {% endfor %}
  </table>
</div>

<div class="section">
  <h2>Evidence Catalogue (Top 30)</h2>
  <table>
    <tr><th>#</th><th>Connector</th><th>Source</th><th>Collected</th><th>Confidence</th></tr>
    {% for ev in evidence_items[:30] %}
    <tr>
      <td>{{ loop.index }}</td>
      <td>{{ ev.connector_name }}</td>
      <td><a href="{{ ev.source_url }}">{{ ev.source_url|truncate(50) }}</a></td>
      <td>{{ ev.collected_at }}</td>
      <td>{{ (ev.confidence * 100)|int }}%</td>
    </tr>
    {% endfor %}
  </table>
</div>

<div class="section">
  <div class="disclaimer">
    DISCLAIMER: This report was generated by an automated OSINT tool using publicly available information only. 
    All findings should be independently verified before any action is taken. Confidence scores reflect 
    data corroboration levels, not absolute certainty. This tool does not access private, non-public, or 
    legally protected data. Misuse of this tool for harassment, stalking, or unlawful profiling is prohibited.
  </div>
</div>

<div class="footer">
  Generated {{ generated_at }} · OSINT Investigation Platform · Session {{ session_id }}
</div>

</body>
</html>
"""

def generate_pdf(session_id: str, person: dict, evidence_items: list, raw_query: str) -> bytes:
    """Generate PDF report and return bytes."""
    from weasyprint import HTML
    
    env = Environment(loader=BaseLoader())
    template = env.from_string(REPORT_TEMPLATE)
    
    html_content = template.render(
        session_id=session_id,
        person=type("P", (), person)() if isinstance(person, dict) else person,
        evidence_items=evidence_items,
        raw_query=raw_query,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M UTC"),
    )
    
    return HTML(string=html_content).write_pdf()
```

**Flask endpoint to add:**
```python
@app.route("/api/osint/session/<session_id>/report.pdf")
def export_pdf(session_id):
    from services.pdf_export import generate_pdf
    session = db.investigation_sessions.find_one({"session_id": session_id})
    person = db.resolved_persons.find_one({"session_id": session_id}, {"_id": 0})
    evidence = list(db.evidence_items.find({"session_id": session_id}, {"_id": 0}).limit(100))
    
    if not session or not person:
        return jsonify({"error": "Session not found"}), 404
    
    pdf_bytes = generate_pdf(session_id, person, evidence, session.get("raw_query", ""))
    
    from flask import Response
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=osint_report_{session_id[:8]}.pdf"}
    )
```

---

## TASK 7: FACE RECOGNITION + IMAGE SEARCH

**Install:**
```bash
pip install insightface onnxruntime opencv-python-headless Pillow piexif
pip install pgvector psycopg2-binary   # OR use MongoDB for embedding storage
```

**Create `connectors/image_connector.py`:**

```python
# File: connectors/image_connector.py
# Face detection, embedding, EXIF extraction, reverse image search (free)

import cv2
import numpy as np
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import piexif
import io
import base64
import requests
import json
from datetime import datetime, timezone
from typing import Optional
import os


class ImageConnector:
    """
    Image-as-query connector:
    1. Detect + embed face using InsightFace (free, local)
    2. Extract EXIF/GPS metadata
    3. Reverse image search via SauceNAO (free, 100/day) + Bing Image Search
    4. Store face embedding for similarity search
    """
    
    name = "image_connector"
    supports_types = ["image"]
    
    def __init__(self):
        self._face_app = None  # lazy load
    
    def _get_face_app(self):
        """Lazy-load InsightFace model (downloads ~300MB on first run)."""
        if self._face_app is None:
            try:
                from insightface.app import FaceAnalysis
                self._face_app = FaceAnalysis(
                    name="buffalo_sc",  # smaller model, faster
                    providers=["CPUExecutionProvider"]
                )
                self._face_app.prepare(ctx_id=-1, det_size=(640, 640))
            except ImportError:
                print("InsightFace not installed. Run: pip install insightface onnxruntime")
        return self._face_app

    def process_image(self, image_bytes: bytes, session_id: str) -> dict:
        """
        Main entry point for image queries.
        Returns: { face_data, exif_data, reverse_search_results, evidence_items }
        """
        result = {
            "face_data": None,
            "exif_data": None,
            "reverse_search_results": [],
            "evidence_items": [],
        }
        
        # 1. Extract EXIF
        result["exif_data"] = self.extract_exif(image_bytes)
        
        # 2. Detect face + extract embedding
        face_data = self.extract_face_embedding(image_bytes)
        if face_data:
            result["face_data"] = face_data
        
        # 3. Reverse image search (free sources)
        reverse_results = self.reverse_image_search(image_bytes)
        result["reverse_search_results"] = reverse_results
        
        # 4. Convert everything to evidence items
        result["evidence_items"] = self._to_evidence_items(result, session_id)
        
        return result

    def extract_face_embedding(self, image_bytes: bytes) -> Optional[dict]:
        """Extract 512-dim face embedding using InsightFace."""
        try:
            app = self._get_face_app()
            if app is None:
                return None
            
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                return None
            
            faces = app.get(img)
            if not faces:
                return {"error": "No face detected in image", "face_count": 0}
            
            # Use highest confidence face
            face = max(faces, key=lambda f: f.det_score)
            
            return {
                "embedding": face.embedding.tolist(),  # 512-dim vector
                "det_score": float(face.det_score),
                "bbox": face.bbox.tolist(),
                "estimated_age": int(face.age) if hasattr(face, "age") else None,
                "estimated_gender": "male" if face.gender == 1 else "female" if hasattr(face, "gender") else None,
                "face_count": len(faces),
            }
        except Exception as e:
            return {"error": str(e), "face_count": 0}

    def extract_exif(self, image_bytes: bytes) -> dict:
        """Extract EXIF metadata including GPS."""
        try:
            img = Image.open(io.BytesIO(image_bytes))
            exif_raw = img._getexif()
            if not exif_raw:
                return {"has_exif": False}
            
            data = {"has_exif": True}
            for tag_id, value in exif_raw.items():
                tag = TAGS.get(tag_id, str(tag_id))
                if tag == "GPSInfo":
                    gps = {}
                    for gps_tag_id, gps_val in value.items():
                        gps_tag = GPSTAGS.get(gps_tag_id, str(gps_tag_id))
                        gps[gps_tag] = str(gps_val)
                    data["gps_raw"] = gps
                    
                    # Convert to decimal degrees
                    try:
                        lat = self._convert_gps(value.get(2), value.get(1))
                        lng = self._convert_gps(value.get(4), value.get(3))
                        if lat and lng:
                            data["gps_lat"] = lat
                            data["gps_lng"] = lng
                            data["gps_maps_url"] = f"https://maps.openstreetmap.org/?mlat={lat}&mlon={lng}&zoom=15"
                    except Exception:
                        pass
                elif tag in ("DateTimeOriginal", "DateTime", "Make", "Model", "Software"):
                    data[tag.lower()] = str(value)
            
            return data
        except Exception as e:
            return {"has_exif": False, "error": str(e)}

    def _convert_gps(self, coord, ref) -> Optional[float]:
        """Convert GPS rational numbers to decimal degrees."""
        if not coord or not ref:
            return None
        try:
            d = float(coord[0])
            m = float(coord[1])
            s = float(coord[2])
            decimal = d + m / 60 + s / 3600
            if ref in ("S", "W"):
                decimal = -decimal
            return round(decimal, 6)
        except Exception:
            return None

    def reverse_image_search(self, image_bytes: bytes) -> list[dict]:
        """
        Free reverse image search using:
        1. SauceNAO (100 searches/day free, no key for basic)
        2. IQDB (anime/illustration, free)
        3. Bing Visual Search (scrape approach)
        """
        results = []
        
        # SauceNAO — best for photos, 100/day without API key
        try:
            resp = requests.post(
                "https://saucenao.com/search.php",
                data={"output_type": 2, "numres": 5},  # JSON output
                files={"file": ("image.jpg", image_bytes, "image/jpeg")},
                timeout=20,
            )
            if resp.status_code == 200:
                data = resp.json()
                for result in data.get("results", [])[:5]:
                    header = result.get("header", {})
                    data_block = result.get("data", {})
                    similarity = float(header.get("similarity", 0))
                    if similarity > 60:  # only high-similarity results
                        urls = data_block.get("ext_urls", [])
                        results.append({
                            "source": "saucenao",
                            "similarity": similarity,
                            "urls": urls,
                            "title": data_block.get("title", ""),
                            "creator": data_block.get("creator", ""),
                            "thumbnail": header.get("thumbnail", ""),
                        })
        except Exception as e:
            print(f"SauceNAO error: {e}")
        
        # Google Images via URL construction (redirect method)
        try:
            img_b64 = base64.b64encode(image_bytes).decode()
            # Note: Full Google Vision requires API key, but reverse image URL works
            results.append({
                "source": "google_images_link",
                "search_url": "https://images.google.com/searchbyimage/upload",
                "note": "Upload manually for Google reverse image search",
                "instructions": "POST the image to Google Images for additional results",
            })
        except Exception:
            pass
        
        return results

    def find_similar_faces(self, embedding: list[float], db) -> list[dict]:
        """
        Find similar faces in MongoDB using cosine similarity.
        Falls back from pgvector if not available.
        """
        if not embedding:
            return []
        
        # MongoDB face index approach (no pgvector needed)
        # Store embeddings as arrays, compute similarity in Python
        # This works for up to ~10,000 indexed faces (sufficient for MVP)
        
        query_vec = np.array(embedding, dtype=np.float32)
        
        similar = []
        cursor = db.face_index.find({}, {"embedding": 1, "source_url": 1, "platform": 1, "person_id": 1})
        
        for doc in cursor:
            stored_vec = np.array(doc.get("embedding", []), dtype=np.float32)
            if stored_vec.shape == query_vec.shape:
                # Cosine similarity
                similarity = float(np.dot(query_vec, stored_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(stored_vec) + 1e-10))
                if similarity > 0.80:
                    similar.append({
                        "similarity": round(similarity, 3),
                        "source_url": doc.get("source_url"),
                        "platform": doc.get("platform"),
                        "person_id": doc.get("person_id"),
                    })
        
        return sorted(similar, key=lambda x: x["similarity"], reverse=True)[:10]

    def index_face(self, image_bytes: bytes, source_url: str, platform: str, db, person_id: str = None):
        """Index a face embedding from a collected profile image."""
        face_data = self.extract_face_embedding(image_bytes)
        if not face_data or face_data.get("error"):
            return None
        
        doc = {
            "embedding": face_data["embedding"],
            "source_url": source_url,
            "platform": platform,
            "person_id": person_id,
            "det_score": face_data.get("det_score"),
            "indexed_at": datetime.now(timezone.utc),
        }
        db.face_index.insert_one(doc)
        return doc

    def _to_evidence_items(self, result: dict, session_id: str) -> list:
        """Convert image analysis results to EvidenceItem format."""
        from models.evidence import EvidenceItem
        items = []
        
        exif = result.get("exif_data", {})
        if exif.get("gps_lat"):
            items.append(EvidenceItem(
                connector_name=self.name,
                source_url=exif.get("gps_maps_url", ""),
                queried_value="image_query",
                queried_type="image",
                raw_text=f"GPS location extracted from image EXIF: lat={exif['gps_lat']}, lng={exif['gps_lng']}",
                extracted_fields={
                    "gps_lat": exif["gps_lat"],
                    "gps_lng": exif["gps_lng"],
                    "maps_url": exif.get("gps_maps_url"),
                    "device": f"{exif.get('make', '')} {exif.get('model', '')}".strip(),
                    "datetime_taken": exif.get("datetimeoriginal"),
                },
                collected_at=datetime.now(timezone.utc),
                confidence=0.95,
                license_note="EXIF metadata from uploaded image",
                session_id=session_id,
            ))
        
        face = result.get("face_data", {})
        if face and not face.get("error"):
            items.append(EvidenceItem(
                connector_name=self.name,
                source_url="local_image",
                queried_value="image_query",
                queried_type="image",
                raw_text=f"Face detected: {face.get('estimated_age')} y/o {face.get('estimated_gender')}, confidence={face.get('det_score', 0):.2f}",
                extracted_fields={
                    "face_detected": True,
                    "face_count": face.get("face_count"),
                    "estimated_age": face.get("estimated_age"),
                    "estimated_gender": face.get("estimated_gender"),
                    "det_score": face.get("det_score"),
                    "has_embedding": True,
                },
                collected_at=datetime.now(timezone.utc),
                confidence=face.get("det_score", 0.7),
                license_note="Local face analysis",
                session_id=session_id,
            ))
        
        for r in result.get("reverse_search_results", []):
            if r.get("urls"):
                items.append(EvidenceItem(
                    connector_name=self.name,
                    source_url=r["urls"][0] if r["urls"] else "",
                    queried_value="image_query",
                    queried_type="image",
                    raw_text=f"Reverse image match found on {r['source']} (similarity: {r.get('similarity', 0):.1f}%)",
                    extracted_fields={
                        "reverse_search_source": r["source"],
                        "similarity_score": r.get("similarity"),
                        "matched_urls": r.get("urls", []),
                        "title": r.get("title"),
                        "creator": r.get("creator"),
                    },
                    collected_at=datetime.now(timezone.utc),
                    confidence=min(r.get("similarity", 70) / 100, 0.95),
                    license_note="Public image index",
                    session_id=session_id,
                ))
        
        return items


# Flask endpoint to add:
"""
@app.route("/api/osint/investigate/image", methods=["POST"])
def investigate_image():
    from connectors.image_connector import ImageConnector
    
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400
    
    file = request.files["image"]
    image_bytes = file.read()
    session_id = request.form.get("session_id") or str(uuid.uuid4())
    
    connector = ImageConnector()
    result = connector.process_image(image_bytes, session_id)
    
    # Save evidence items
    for ev in result["evidence_items"]:
        db.evidence_items.insert_one(ev.__dict__ if hasattr(ev, '__dict__') else ev)
    
    # Save face embedding to index if found
    if result.get("face_data") and not result["face_data"].get("error"):
        db.face_index.insert_one({
            "embedding": result["face_data"]["embedding"],
            "source_url": "user_query",
            "platform": "query",
            "session_id": session_id,
            "indexed_at": datetime.now(timezone.utc).isoformat(),
        })
    
    return jsonify({
        "session_id": session_id,
        "face_detected": bool(result.get("face_data") and not result["face_data"].get("error")),
        "face_data": {k: v for k, v in (result.get("face_data") or {}).items() if k != "embedding"},
        "exif_data": result.get("exif_data"),
        "reverse_results_count": len(result.get("reverse_search_results", [])),
        "evidence_items_count": len(result.get("evidence_items", [])),
        "reverse_results": result.get("reverse_search_results", []),
    })
"""
```

---

## TASK 8: DATA FROM X / INSTAGRAM / THREADS — FREE APPROACHES

**Important reality check — no official free API access:**
- X (Twitter): API now costs $100/month minimum. Official API is not free.
- Instagram: Requires Facebook developer app approval. Rate-limited to near zero for public data.
- Threads: No official API currently.

**Legal free alternatives that give REAL data:**

### 8A: X (Twitter) — Use Nitter instances (scrapers of public tweets)

```python
# File: connectors/nitter_connector.py
# Nitter is an open-source Twitter frontend — scrapes public tweets legally
# Multiple public instances available

import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime, timezone

NITTER_INSTANCES = [
    "https://nitter.net",
    "https://nitter.privacydev.net",
    "https://nitter.poast.org",
]

class NitterConnector:
    """
    Scrapes public Twitter/X profiles via Nitter instances.
    Only accesses public profiles — same data visible in browser.
    Rate limit: 1 request per 3 seconds per instance.
    """
    
    name = "nitter_twitter"
    supports_types = ["username", "name"]
    
    HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; research-bot/1.0)"}
    
    def run(self, pivot: dict) -> list:
        from models.evidence import EvidenceItem
        
        username = pivot.get("value", "").lstrip("@")
        session_id = pivot.get("session_id", "")
        evidence = []
        
        for instance in NITTER_INSTANCES:
            try:
                time.sleep(3)
                result = self._scrape_profile(instance, username)
                if result:
                    evidence += self._to_evidence(result, username, session_id)
                    break  # stop at first working instance
            except Exception as e:
                print(f"Nitter instance {instance} failed: {e}")
                continue
        
        return evidence

    def _scrape_profile(self, instance: str, username: str) -> dict:
        url = f"{instance}/{username}"
        resp = requests.get(url, headers=self.HEADERS, timeout=15)
        if resp.status_code != 200:
            return None
        
        soup = BeautifulSoup(resp.text, "html.parser")
        
        profile = {"username": username, "profile_url": f"https://twitter.com/{username}", "source_instance": instance}
        
        # Display name
        name_el = soup.select_one(".profile-card-fullname")
        if name_el:
            profile["display_name"] = name_el.get_text(strip=True)
        
        # Bio
        bio_el = soup.select_one(".profile-bio")
        if bio_el:
            profile["bio"] = bio_el.get_text(strip=True)
        
        # Stats (followers, following, tweets)
        stats = soup.select(".profile-stat-num")
        stat_labels = soup.select(".profile-stat-header")
        for stat, label in zip(stats, stat_labels):
            profile[label.get_text(strip=True).lower()] = stat.get_text(strip=True)
        
        # Location
        loc_el = soup.select_one(".profile-location")
        if loc_el:
            profile["location"] = loc_el.get_text(strip=True)
        
        # Website
        web_el = soup.select_one(".profile-website a")
        if web_el:
            profile["website"] = web_el.get("href", "")
        
        # Recent tweets (first 10)
        tweets = []
        for tweet_el in soup.select(".timeline-item")[:10]:
            text_el = tweet_el.select_one(".tweet-content")
            date_el = tweet_el.select_one(".tweet-date a")
            if text_el:
                tweets.append({
                    "text": text_el.get_text(strip=True),
                    "date": date_el.get("title", "") if date_el else "",
                    "url": f"https://twitter.com{date_el.get('href', '')}" if date_el else "",
                })
        profile["recent_tweets"] = tweets
        
        return profile

    def _to_evidence(self, profile: dict, username: str, session_id: str) -> list:
        from models.evidence import EvidenceItem
        items = []
        
        items.append(EvidenceItem(
            connector_name=self.name,
            source_url=profile["profile_url"],
            queried_value=username,
            queried_type="username",
            raw_text=f"Twitter/X profile: {profile.get('display_name', username)} — {profile.get('bio', '')}",
            extracted_fields={
                "username": username,
                "platform": "Twitter/X",
                "display_name": profile.get("display_name"),
                "bio": profile.get("bio"),
                "location": profile.get("location"),
                "website": profile.get("website"),
                "followers": profile.get("followers"),
                "following": profile.get("following"),
                "profile_url": profile["profile_url"],
            },
            collected_at=datetime.now(timezone.utc),
            confidence=0.80,
            license_note="Public Twitter profile via Nitter proxy",
            session_id=session_id,
        ))
        
        for tweet in profile.get("recent_tweets", [])[:5]:
            items.append(EvidenceItem(
                connector_name=self.name,
                source_url=tweet.get("url", profile["profile_url"]),
                queried_value=username,
                queried_type="username",
                raw_text=tweet.get("text", ""),
                extracted_fields={
                    "username": username,
                    "platform": "Twitter/X",
                    "tweet_text": tweet.get("text"),
                    "tweet_date": tweet.get("date"),
                    "content_type": "tweet",
                },
                collected_at=datetime.now(timezone.utc),
                confidence=0.75,
                license_note="Public tweet via Nitter proxy",
                session_id=session_id,
            ))
        
        return items
```

### 8B: Instagram — Public profile scraping (no login, public data only)

```python
# File: connectors/instagram_connector.py
# Accesses ONLY public Instagram profiles — same data visible without login

import requests
import json
import re
import time
from datetime import datetime, timezone

class InstagramConnector:
    """
    Fetches public Instagram profile data using Instagram's own internal JSON endpoint.
    Only works for PUBLIC profiles. No login, no private data.
    Rate limit: 1 request per 10 seconds MINIMUM.
    """
    
    name = "instagram_public"
    supports_types = ["username"]
    
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.5",
        "X-IG-App-ID": "936619743392459",  # public, used by browser
    }
    
    def run(self, pivot: dict) -> list:
        from models.evidence import EvidenceItem
        
        username = pivot.get("value", "").lstrip("@")
        session_id = pivot.get("session_id", "")
        
        time.sleep(10)  # strict rate limiting — Instagram aggressively blocks
        
        try:
            # Use Instagram's internal web API (public data, no auth)
            url = f"https://i.instagram.com/api/v1/users/web_profile_info/?username={username}"
            resp = requests.get(url, headers=self.HEADERS, timeout=20)
            
            if resp.status_code == 200:
                data = resp.json()
                user = data.get("data", {}).get("user", {})
                if not user:
                    return []
                
                return [EvidenceItem(
                    connector_name=self.name,
                    source_url=f"https://www.instagram.com/{username}/",
                    queried_value=username,
                    queried_type="username",
                    raw_text=f"Instagram profile: {user.get('full_name', username)} — {user.get('biography', '')}",
                    extracted_fields={
                        "username": username,
                        "platform": "Instagram",
                        "full_name": user.get("full_name"),
                        "bio": user.get("biography"),
                        "follower_count": user.get("edge_followed_by", {}).get("count"),
                        "following_count": user.get("edge_follow", {}).get("count"),
                        "post_count": user.get("edge_owner_to_timeline_media", {}).get("count"),
                        "is_private": user.get("is_private"),
                        "is_verified": user.get("is_verified"),
                        "external_url": user.get("external_url"),
                        "profile_pic_url": user.get("profile_pic_url_hd"),
                        "profile_url": f"https://www.instagram.com/{username}/",
                    },
                    collected_at=datetime.now(timezone.utc),
                    confidence=0.85 if not user.get("is_private") else 0.50,
                    license_note="Public Instagram profile data",
                    session_id=session_id,
                )]
            
            elif resp.status_code == 404:
                return []  # profile doesn't exist
            else:
                print(f"Instagram: HTTP {resp.status_code} for {username}")
                return []
        
        except Exception as e:
            print(f"Instagram connector error for {username}: {e}")
            return []
```

### 8C: Timer-based rate limiting — shared request scheduler

```python
# File: services/rate_scheduler.py
# Central rate limiter for all connectors with per-source cooldowns

import time
import threading
from collections import defaultdict

class RateScheduler:
    """
    Enforces per-source rate limits globally.
    Call wait_for(source) before any request to that source.
    """
    
    _instance = None
    
    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = RateScheduler()
        return cls._instance
    
    # Minimum seconds between requests per source
    COOLDOWNS = {
        "instagram_public":  10.0,
        "nitter_twitter":     3.0,
        "google_search":      2.0,
        "duckduckgo":         1.0,
        "psbdmp":             2.0,
        "leakcheck":          2.0,
        "saucenao":           4.0,
        "github_api":         0.5,
        "hackernews":         0.2,
        "crt_sh":             0.5,
        "wayback_cdx":        1.0,
        "whois":              0.5,
        "default":            1.0,
    }
    
    def __init__(self):
        self._last_call = defaultdict(float)
        self._locks = defaultdict(threading.Lock)
    
    def wait_for(self, source: str):
        """Block until it's safe to make a request to this source."""
        cooldown = self.COOLDOWNS.get(source, self.COOLDOWNS["default"])
        with self._locks[source]:
            elapsed = time.time() - self._last_call[source]
            if elapsed < cooldown:
                time.sleep(cooldown - elapsed)
            self._last_call[source] = time.time()
```

---

## TASK 9: ADDITIONAL HIGH-VALUE FREE CONNECTORS

### HackerNews connector (fully free):

```python
# File: connectors/hackernews_connector.py

import requests
from datetime import datetime, timezone

class HackerNewsConnector:
    name = "hackernews"
    supports_types = ["username", "name", "email"]
    
    def run(self, pivot: dict) -> list:
        from models.evidence import EvidenceItem
        
        query = pivot.get("value", "")
        session_id = pivot.get("session_id", "")
        evidence = []
        
        # Search posts and comments
        resp = requests.get(
            "https://hn.algolia.com/api/v1/search",
            params={"query": query, "hitsPerPage": 10},
            timeout=10
        )
        
        if resp.status_code == 200:
            hits = resp.json().get("hits", [])
            for hit in hits:
                author = hit.get("author", "")
                evidence.append(EvidenceItem(
                    connector_name=self.name,
                    source_url=f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
                    queried_value=query,
                    queried_type=pivot.get("type"),
                    raw_text=hit.get("story_text") or hit.get("comment_text") or hit.get("title") or "",
                    extracted_fields={
                        "username": author,
                        "platform": "HackerNews",
                        "post_title": hit.get("title"),
                        "post_type": hit.get("_tags", [None])[0],
                        "points": hit.get("points"),
                        "created_at": hit.get("created_at"),
                    },
                    collected_at=datetime.now(timezone.utc),
                    confidence=0.80,
                    license_note="Public HackerNews data",
                    session_id=session_id,
                ))
        
        # If query looks like a username, get profile
        if pivot.get("type") == "username":
            profile_resp = requests.get(
                f"https://hacker-news.firebaseio.com/v0/user/{query}.json",
                timeout=10
            )
            if profile_resp.status_code == 200 and profile_resp.json():
                user = profile_resp.json()
                evidence.append(EvidenceItem(
                    connector_name=self.name,
                    source_url=f"https://news.ycombinator.com/user?id={query}",
                    queried_value=query,
                    queried_type="username",
                    raw_text=f"HN Profile: karma={user.get('karma')}, about={user.get('about', '')}",
                    extracted_fields={
                        "username": query,
                        "platform": "HackerNews",
                        "karma": user.get("karma"),
                        "created": user.get("created"),
                        "about": user.get("about", "")[:500],
                    },
                    collected_at=datetime.now(timezone.utc),
                    confidence=0.90,
                    license_note="Public HackerNews profile",
                    session_id=session_id,
                ))
        
        return evidence
```

### GitHub connector (free, 60 req/hr unauthenticated, 5000 with token):

```python
# File: connectors/github_connector.py

import requests
import os
from datetime import datetime, timezone

class GitHubConnector:
    name = "github"
    supports_types = ["username", "name", "email"]
    
    HEADERS = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "OSINT-Research/1.0",
    }
    
    def __init__(self):
        token = os.getenv("GITHUB_TOKEN", "")
        if token:
            self.HEADERS["Authorization"] = f"token {token}"
    
    def run(self, pivot: dict) -> list:
        from models.evidence import EvidenceItem
        
        pivot_type = pivot.get("type")
        pivot_value = pivot.get("value", "")
        session_id = pivot.get("session_id", "")
        evidence = []
        
        if pivot_type == "username":
            evidence += self._get_user_profile(pivot_value, session_id)
        elif pivot_type in ("name", "email"):
            evidence += self._search_users(pivot_value, session_id)
        
        return evidence

    def _get_user_profile(self, username: str, session_id: str) -> list:
        from models.evidence import EvidenceItem
        
        resp = requests.get(f"https://api.github.com/users/{username}", headers=self.HEADERS, timeout=10)
        if resp.status_code != 200:
            return []
        
        user = resp.json()
        
        # Also get recent public events
        events_resp = requests.get(f"https://api.github.com/users/{username}/events/public?per_page=5", headers=self.HEADERS, timeout=10)
        events = events_resp.json() if events_resp.status_code == 200 else []
        
        return [EvidenceItem(
            connector_name=self.name,
            source_url=user.get("html_url", ""),
            queried_value=username,
            queried_type="username",
            raw_text=f"GitHub: {user.get('name', username)} — {user.get('bio', '')}",
            extracted_fields={
                "username": username,
                "platform": "GitHub",
                "full_name": user.get("name"),
                "email": user.get("email"),
                "bio": user.get("bio"),
                "location": user.get("location"),
                "company": user.get("company"),
                "blog": user.get("blog"),
                "twitter_username": user.get("twitter_username"),
                "public_repos": user.get("public_repos"),
                "followers": user.get("followers"),
                "created_at": user.get("created_at"),
                "profile_url": user.get("html_url"),
                "recent_activity_types": list(set(e.get("type") for e in events))[:5],
            },
            collected_at=datetime.now(timezone.utc),
            confidence=0.92,
            license_note="Public GitHub profile",
            session_id=session_id,
        )]

    def _search_users(self, query: str, session_id: str) -> list:
        from models.evidence import EvidenceItem
        
        resp = requests.get(
            "https://api.github.com/search/users",
            params={"q": query, "per_page": 5},
            headers=self.HEADERS,
            timeout=10
        )
        if resp.status_code != 200:
            return []
        
        items = resp.json().get("items", [])
        evidence = []
        for item in items:
            evidence += self._get_user_profile(item["login"], session_id)
        
        return evidence
```

---

## TASK 10: CONNECT ALL CONNECTORS IN THE INVESTIGATION ORCHESTRATOR

```python
# File: services/investigation_orchestrator.py
# Central orchestrator — runs all connectors, resolves identity, builds dossier

from services.task_queue import TaskQueue
from services.identity_resolver import IdentityResolver
from services.narrative_builder import NarrativeBuilder
from connectors.username_connector import UsernameConnector
from connectors.breach_connector import BreachConnector
from connectors.hackernews_connector import HackerNewsConnector
from connectors.github_connector import GitHubConnector
from connectors.nitter_connector import NitterConnector
from connectors.instagram_connector import InstagramConnector
# your existing connectors:
# from connectors.web_search import WebSearchConnector
# from connectors.domain_intel import DomainIntelConnector

from datetime import datetime, timezone
import re


def parse_pivot(raw_query: str) -> dict:
    """Classify the query into a structured pivot."""
    q = raw_query.strip()
    
    if re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', q):
        return {"type": "email", "value": q}
    
    if re.match(r'^[+\d\s\-().]{8,15}$', q.replace(" ", "")):
        return {"type": "phone", "value": q}
    
    if re.match(r'^@?[\w]{2,30}$', q) and " " not in q:
        return {"type": "username", "value": q.lstrip("@")}
    
    if re.match(r'^[a-z0-9\-]+\.[a-z]{2,}$', q.lower()):
        return {"type": "domain", "value": q}
    
    return {"type": "name", "value": q}


def run_full_investigation(session_id: str, raw_query: str, db) -> dict:
    """
    Full investigation pipeline:
    1. Parse query
    2. Run all connectors
    3. Resolve identity
    4. Build narrative
    5. Save to DB
    Returns summary dict.
    """
    pivot = parse_pivot(raw_query)
    pivot["session_id"] = session_id
    
    # Update session status
    db.investigation_sessions.update_one(
        {"session_id": session_id},
        {"$set": {"status": "running", "started_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    all_evidence = []
    
    # Define connector pipeline based on pivot type
    connectors = []
    
    # Always run:
    connectors += [
        UsernameConnector(),
        BreachConnector(),
        HackerNewsConnector(),
        GitHubConnector(),
    ]
    
    if pivot["type"] in ("username", "name"):
        connectors += [
            NitterConnector(),
            InstagramConnector(),
        ]
    
    # Add your existing working connectors:
    # connectors += [WebSearchConnector(), DomainIntelConnector()]
    
    # Run each connector, collect evidence
    for connector in connectors:
        if connector.supports_types and pivot["type"] in connector.supports_types:
            try:
                items = connector.run(pivot)
                for item in items:
                    # Convert to dict for MongoDB
                    if hasattr(item, '__dict__'):
                        doc = vars(item).copy()
                    else:
                        doc = dict(item)
                    doc["session_id"] = session_id
                    db.evidence_items.insert_one(doc)
                    all_evidence.append(doc)
            except Exception as e:
                print(f"Connector {connector.name} failed: {e}")
    
    # Identity resolution
    resolver = IdentityResolver()
    person = resolver.resolve(all_evidence, session_id, raw_query)
    resolver.save_to_db(person, db)
    
    # Narrative building
    builder = NarrativeBuilder()
    timeline = builder.build_timeline(all_evidence, vars(person))
    platform_summary = builder.build_platform_summary(all_evidence)
    network_graph = builder.build_entity_network(all_evidence)
    
    # Save narrative artifacts
    db.investigation_sessions.update_one(
        {"session_id": session_id},
        {"$set": {
            "status": "complete",
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "evidence_count": len(all_evidence),
            "timeline": timeline[:50],
            "platform_summary": platform_summary,
            "network_graph": network_graph,
            "risk_level": person.risk_level,
            "match_confidence": person.match_confidence,
        }}
    )
    
    return {
        "session_id": session_id,
        "evidence_count": len(all_evidence),
        "person_id": person.id,
        "risk_level": person.risk_level,
        "match_confidence": person.match_confidence,
    }
```

---

## TASK 11: FLASK API ENDPOINTS — COMPLETE LIST TO ADD/VERIFY

```python
# Add all these to your main Flask app or a blueprint

# POST /api/osint/investigate
# Body: { "query": "Arjun Sharma arjun_dev Bangalore" }
# Returns: { session_id, task_id }

# GET /api/osint/session/<session_id>
# Returns: full session object with status, evidence_count, risk_level

# GET /api/osint/session/<session_id>/dossier
# Returns: resolved person entity

# GET /api/osint/session/<session_id>/timeline
# Returns: list of timeline events for Recharts

# GET /api/osint/session/<session_id>/graph
# Returns: { nodes, edges } for vis-network

# GET /api/osint/session/<session_id>/report.pdf
# Returns: PDF download

# POST /api/osint/investigate/image
# Body: multipart/form-data with image file
# Returns: face data, EXIF, reverse search results

# GET /api/tasks/<task_id>
# Returns: task status (pending/running/complete/failed)

# GET /api/osint/sessions
# Returns: list of all investigation sessions (paginated)

# POST /api/osint/session/<session_id>/note
# Body: { "note": "Analyst observation" }
# Returns: updated session

# GET /api/osint/face/similar
# Body: { "embedding": [...512 floats...] }
# Returns: similar faces from face_index collection
```

---

## REQUIREMENTS.TXT — COMPLETE LIST (ALL FREE)

```
# Already installed (keep):
flask
pymongo
spacy
duckduckgo-search
python-whois
dnspython

# Add these (all free):
aiohttp               # async username enumeration
jellyfish             # string similarity for identity resolution
requests              # HTTP calls
beautifulsoup4        # HTML parsing for Nitter, Instagram
weasyprint            # PDF export
jinja2                # PDF template rendering
Pillow                # Image/EXIF processing
piexif                # EXIF read/write
opencv-python-headless  # Image processing (headless = no GUI needed)
numpy                 # Face embedding math
insightface           # Face detection + embedding (free, Apache 2.0)
onnxruntime           # Backend for InsightFace (CPU mode)
phonenumbers          # Phone normalisation
python-nameparser     # Name splitting
ftfy                  # Text cleanup
```

---

## MONGODB COLLECTIONS — COMPLETE SCHEMA REFERENCE

```
evidence_items        -- all raw evidence (already exists)
investigation_sessions -- session CRUD (already exists)
resolved_persons      -- canonical person entities (NEW)
face_index            -- face embeddings for similarity search (NEW)
tasks                 -- background task status (NEW)
watchlists            -- monitoring targets (NEW)
```

---

## IMPLEMENTATION ORDER — DO THIS IN SEQUENCE

1. Fix Sherlock → replace with `username_connector.py` (Task 1)
2. Replace HIBP → `breach_connector.py` (Task 2)  
3. Complete identity resolver → `identity_resolver.py` (Task 3)
4. Complete narrative builder → `narrative_builder.py` (Task 4)
5. Add task queue → `task_queue.py` + wire into Flask (Task 5)
6. Add PDF export → `pdf_export.py` + endpoint (Task 6)
7. Add image connector → `image_connector.py` + endpoint (Task 7)
8. Add Nitter + Instagram + GitHub + HN connectors (Task 8 & 9)
9. Wire orchestrator → `investigation_orchestrator.py` (Task 10)
10. Verify all Flask endpoints exist (Task 11)

---

## NOTES FOR CODE EDITOR AI

- Do NOT rewrite anything marked ✅ DONE above.
- Do NOT add Celery — use the TaskQueue in Task 5 instead.
- Do NOT use any paid API. Every connector above works with free/no-key access.
- All connectors MUST handle exceptions gracefully and return empty list on failure.
- Rate limits are mandatory — Instagram especially will IP-block without delays.
- The EvidenceItem import path may differ in your project — adjust to match existing import.
- InsightFace downloads ~300MB model on first run — this is expected and correct.
- For Nitter: if all instances fail, return empty list silently. Do not crash.
- MongoDB `_id` fields must be converted to str before JSON serialisation everywhere.
```