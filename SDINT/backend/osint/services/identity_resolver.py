"""
Identity resolution - merges all evidence into canonical person entity.
Core to OSINT identity discovery mission.
"""

import re
import hashlib
from collections import defaultdict
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict


@dataclass
class ResolvedPerson:
    """Canonical person built from merged evidence."""
    id: str
    session_id: str
    canonical_name: str = None
    name_first: str = None
    name_last: str = None
    aliases: list = field(default_factory=list)
    usernames: list = field(default_factory=list)
    emails: list = field(default_factory=list)
    phones: list = field(default_factory=list)
    locations: list = field(default_factory=list)
    employers: list = field(default_factory=list)
    domains: list = field(default_factory=list)
    social_profiles: list = field(default_factory=list)
    breach_findings: list = field(default_factory=list)
    evidence_ids: list = field(default_factory=list)
    corroborations: list = field(default_factory=list)
    match_confidence: float = 0.0
    risk_score: float = 0.0
    risk_level: str = "LOW"
    intelligence_summary: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    raw_evidence_count: int = 0


class IdentityResolver:
    """Merge evidence into canonical identity."""
    
    USERNAME_SIMILARITY_THRESHOLD = 0.88
    NAME_SIMILARITY_THRESHOLD = 0.85

    def resolve(self, evidence_items: list, session_id: str, raw_query: str) -> ResolvedPerson:
        """Main entry point - takes evidence, returns resolved person."""
        person_id = hashlib.md5(f"{session_id}{raw_query}".encode()).hexdigest()
        
        person = ResolvedPerson(id=person_id, session_id=session_id)
        
        # Extract from all evidence
        all_names = []
        all_emails = set()
        all_phones = set()
        all_usernames = []
        all_locations = []
        all_employers = []
        all_domains = set()
        all_profiles = []
        all_breach_findings = []
        
        for ev in evidence_items:
            # Handle both dict and object
            ev_dict = ev.__dict__ if hasattr(ev, '__dict__') else ev
            person.evidence_ids.append(str(ev_dict.get("_id", "")))
            fields = ev_dict.get("extracted_fields", {})
            
            # Extract names
            for name in fields.get("persons", []):
                if name and len(name) > 2:
                    all_names.append(name)
            if fields.get("name"):
                all_names.append(fields["name"])
            
            # Extract emails
            for email in fields.get("emails", []):
                if self._is_valid_email(email):
                    all_emails.add(email.lower().strip())
            if fields.get("email") and self._is_valid_email(fields["email"]):
                all_emails.add(fields["email"].lower().strip())
            
            # Extract phones
            for phone in fields.get("phones", []):
                normalized = self._normalize_phone(phone)
                if normalized:
                    all_phones.add(normalized)
            
            # Extract usernames
            if fields.get("username") and fields.get("platform"):
                all_usernames.append({
                    "username": fields["username"],
                    "platform": fields["platform"],
                    "url": fields.get("profile_url", ev_dict.get("source_url", "")),
                    "confidence": ev_dict.get("confidence", 0.7),
                })
            
            # Extract locations
            for loc in fields.get("locations", []):
                if loc and len(loc) > 1:
                    all_locations.append(loc)
            
            # Extract organizations
            for org in fields.get("organizations", []):
                if org and len(org) > 1:
                    all_employers.append(org)
            
            # Extract domains
            for domain in fields.get("domains", []):
                if domain:
                    all_domains.add(domain.lower())
            
            # Breach findings
            if fields.get("breach_count") or fields.get("breach_sources") or fields.get("breach_type"):
                all_breach_findings.append({
                    "source": ev_dict.get("connector_name"),
                    "url": ev_dict.get("source_url"),
                    "details": fields,
                    "timestamp": str(ev_dict.get("collected_at", "")),
                })
        
        # Resolve canonical identity
        person.canonical_name = self._resolve_canonical_name(all_names)
        name_parts = self._split_name(person.canonical_name) if person.canonical_name else {}
        person.name_first = name_parts.get("first")
        person.name_last = name_parts.get("last")
        person.aliases = list(set(all_names))[:20]
        person.emails = [{"email": e, "source": "evidence"} for e in all_emails]
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
        
        # Scoring
        person.match_confidence = self._compute_match_confidence(person)
        person.risk_score = self._compute_risk_score(person)
        person.risk_level = "HIGH" if person.risk_score > 0.7 else "MEDIUM" if person.risk_score > 0.4 else "LOW"
        person.intelligence_summary = self._generate_summary(person, raw_query)
        
        return person

    def _resolve_canonical_name(self, names: list) -> str:
        """Pick most representative name."""
        if not names:
            return None
        freq = defaultdict(int)
        for n in names:
            clean = n.strip().title()
            if 2 <= len(clean.split()) <= 4:
                freq[clean] += 1
        if not freq:
            return names[0].strip().title() if names else None
        return max(freq, key=freq.get)

    def _split_name(self, full_name: str) -> dict:
        """Split name into first/last."""
        parts = full_name.strip().split()
        if len(parts) == 1:
            return {"first": parts[0], "last": None}
        elif len(parts) >= 2:
            return {"first": parts[0], "last": parts[-1]}
        return {}

    def _dedupe_usernames(self, usernames: list) -> list:
        """Remove duplicates, prefer higher confidence."""
        seen = {}
        for u in usernames:
            key = (u["username"].lower(), u.get("platform", "").lower())
            if key not in seen or u.get("confidence", 0) > seen[key].get("confidence", 0):
                seen[key] = u
        return list(seen.values())

    def _is_valid_email(self, email: str) -> bool:
        return bool(re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email))

    def _normalize_phone(self, phone: str) -> str:
        digits = re.sub(r'\D', '', phone)
        if 8 <= len(digits) <= 15:
            return f"+{digits}" if not digits.startswith("+") else digits
        return None

    def _compute_match_confidence(self, person: ResolvedPerson) -> float:
        """Score 0-1 based on corroborating evidence and generate reasons."""
        score = 0.0
        corroborations = []
        
        # Email match
        if person.emails and len(person.emails) > 1:
            score += 0.35
            corroborations.append(f"✓ Email {person.emails[0]['email']} found in {len(person.emails)} distinct sources")
        elif person.emails:
            score += 0.25
            corroborations.append(f"✓ Email {person.emails[0]['email']} verified in evidence")
            
        # Username match across platforms
        if person.usernames:
            platforms = set([u.get('platform') for u in person.usernames if u.get('platform') and u.get('platform') != 'Unknown'])
            if len(platforms) >= 3:
                score += 0.45
                corroborations.append(f"✓ Consistent username pattern matched across {len(platforms)} platforms")
            elif len(platforms) > 1:
                score += 0.25
                corroborations.append(f"✓ Username matched across {len(platforms)} platforms")
            else:
                score += 0.1
                corroborations.append(f"⚠ Username found on a single platform — low confidence link")
                
        # Location match
        if person.locations and len(person.locations) > 0:
            score += 0.15
            corroborations.append(f"✓ Location '{person.locations[0]}' consistent in profile data")
            
        # Breach data
        if person.breach_findings:
            score += 0.15
            corroborations.append(f"✓ Identifiers found in {len(person.breach_findings)} breach databases")
            
        if person.canonical_name and score < 0.6:
            score += 0.2
            if score <= 0.3:
                corroborations.append(f"⚠ Name match only — high chance of false positive")
            
        person.corroborations = corroborations
        return round(min(score, 1.0), 2)

    def _compute_risk_score(self, person: ResolvedPerson) -> float:
        """Risk based on breaches, platform footprint, etc."""
        score = 0.0
        if len(person.breach_findings) > 0:
            score += 0.35
        if len(person.breach_findings) > 3:
            score += 0.20
        if len(person.usernames) > 8:
            score += 0.15
        if len(person.emails) > 5:
            score += 0.10
        return round(min(score, 1.0), 2)

    def _generate_summary(self, person: ResolvedPerson, raw_query: str) -> str:
        """Generate human-readable intelligence summary."""
        lines = []
        
        if person.canonical_name:
            lines.append(f"Identity: {person.canonical_name}")
        else:
            lines.append(f"Query: {raw_query}")
        
        if person.usernames:
            platforms = list(set(u.get("platform", "") for u in person.usernames))[:5]
            lines.append(f"Online presence: {len(person.usernames)} platform(s) - {', '.join(platforms)}")
        
        if person.emails:
            lines.append(f"Emails: {len(person.emails)} address(es)")
        
        if person.breach_findings:
            lines.append(f"⚠️ BREACHES: Found in {len(person.breach_findings)} source(s) - RISK: {person.risk_level}")
        
        if person.locations:
            lines.append(f"Locations: {', '.join(person.locations[:3])}")
        
        lines.append(f"Confidence: {int(person.match_confidence * 100)}% | Evidence: {person.raw_evidence_count} items")
        
        return " | ".join(lines)

    def save_to_db(self, person: ResolvedPerson, db) -> str:
        """Persist to MongoDB."""
        doc = asdict(person)
        try:
            db.resolved_persons.replace_one(
                {"session_id": person.session_id},
                doc,
                upsert=True
            )
        except Exception as e:
            print(f"Error saving resolved person: {e}")
        return person.id
