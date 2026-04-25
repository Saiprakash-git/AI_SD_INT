"""
Identity Resolution — Link entities across evidence sources into unified identities.

Core functionality:
  - Entity equivalence detection (email ≈ username ≈ person)
  - Identity profile creation (unified view of one person/entity)
  - Relationship mapping (who connected to whom)
  - Confidence scoring for identity links
  - Full person dossier generation from evidence
"""

import re
import logging
import hashlib
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from collections import defaultdict

try:
    import jellyfish
    JELLYFISH_AVAILABLE = True
except ImportError:
    JELLYFISH_AVAILABLE = False

from osint.db.evidence_store import EvidenceStore
from osint.schemas.evidence_schema import EntityType


logger = logging.getLogger(__name__)


# ─── Resolved Person Entity ─────────────────────────────────────────────────

@dataclass
class ResolvedPerson:
    """Canonical person entity built from merged evidence."""
    person_id: str
    investigation_id: Optional[str] = None
    canonical_name: Optional[str] = None
    name_first: Optional[str] = None
    name_last: Optional[str] = None
    aliases: List[str] = field(default_factory=list)
    usernames: List[Dict] = field(default_factory=list)
    emails: List[Dict] = field(default_factory=list)
    phones: List[str] = field(default_factory=list)
    locations: List[str] = field(default_factory=list)
    employers: List[str] = field(default_factory=list)
    domains: List[str] = field(default_factory=list)
    social_profiles: List[Dict] = field(default_factory=list)
    breach_findings: List[Dict] = field(default_factory=list)
    evidence_ids: List[str] = field(default_factory=list)
    match_confidence: float = 0.0
    risk_score: float = 0.0
    risk_level: str = "LOW"
    intelligence_summary: str = ""
    raw_evidence_count: int = 0
    created_at: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class EntityEquivalence:
    """Link between two entities that likely refer to same person/thing."""
    entity_a: Dict  # {type, value}
    entity_b: Dict  # {type, value}
    confidence: float  # 0.0-1.0, how sure we are they're the same
    reason: str  # Why we think they're linked
    evidence_ids: List[str] = field(default_factory=list)  # Supporting evidence


@dataclass
class IdentityProfile:
    """Unified identity combining multiple entity mentions."""
    identity_id: str  # Unique ID for this identity
    primary_entity: Dict  # {type, value} - most reliable identifier
    equivalent_entities: List[Dict] = field(default_factory=list)  # All known mentions
    entity_types: Set[str] = field(default_factory=set)  # {email, username, person, ...}
    confidence: float = 0.8  # Overall confidence 0.0-1.0
    evidence_ids: List[str] = field(default_factory=list)  # All related evidence
    relationships: Dict[str, List[str]] = field(default_factory=dict)  # {identity_id: confidence}
    metadata: Dict = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "identity_id": self.identity_id,
            "primary_entity": self.primary_entity,
            "equivalent_entities": self.equivalent_entities,
            "entity_types": list(self.entity_types),
            "confidence": round(self.confidence, 3),
            "evidence_count": len(self.evidence_ids),
            "relationships": self.relationships,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


class IdentityResolver:
    """
    Resolve entities into unified identities.
    
    Uses multiple strategies:
    1. Exact matching (same email/username)
    2. Fuzzy matching (similar names)
    3. Co-occurrence (entities appearing together)
    4. Structural linking (metadata relationships)
    """

    def __init__(self, store: Optional[EvidenceStore] = None):
        self.store = store or EvidenceStore()
        self.logger = logging.getLogger("IdentityResolver")
        
        # Caches for performance
        self._entity_cache: Dict[str, List[Dict]] = {}
        self._equivalence_cache: Dict[Tuple, EntityEquivalence] = {}

    # ─── Full Evidence Resolution ────────────────────────────────────────

    def resolve_from_evidence(
        self,
        evidence_items: List,
        investigation_id: Optional[str] = None,
        raw_query: str = ""
    ) -> ResolvedPerson:
        """
        Build a ResolvedPerson from all evidence items.
        This is the main entry point for full identity resolution.

        Args:
            evidence_items: List of EvidenceItem objects or dicts
            investigation_id: Optional investigation ID
            raw_query: The original query string

        Returns:
            ResolvedPerson with all merged intelligence
        """
        person_id = hashlib.md5(
            f"{investigation_id or ''}{raw_query}{datetime.now(timezone.utc).isoformat()}".encode()
        ).hexdigest()[:16]

        person = ResolvedPerson(
            person_id=f"person_{person_id}",
            investigation_id=investigation_id,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        # Collect structured data from all evidence
        all_names = []
        all_emails = set()
        all_phones = set()
        all_usernames = []
        all_locations = []
        all_employers = []
        all_domains = set()
        all_breach_findings = []

        for item in evidence_items:
            # Handle both EvidenceItem objects and dicts
            if hasattr(item, 'to_dict'):
                d = item.to_dict()
            elif isinstance(item, dict):
                d = item
            else:
                continue

            person.evidence_ids.append(d.get("evidence_id", ""))

            # Extract entities
            for entity in d.get("entities", []):
                etype = entity.get("type", "")
                evalue = entity.get("value", "").strip()
                if not evalue:
                    continue

                if etype == "person" and len(evalue) > 2:
                    all_names.append(evalue)
                elif etype == "email" and re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', evalue):
                    all_emails.add(evalue.lower())
                elif etype == "username":
                    all_usernames.append({"username": evalue, "platform": "unknown", "url": "", "confidence": entity.get("confidence", 0.7)})
                elif etype == "phone":
                    digits = re.sub(r'\D', '', evalue)
                    if 8 <= len(digits) <= 15:
                        all_phones.add(f"+{digits}")
                elif etype == "location" and len(evalue) > 1:
                    all_locations.append(evalue)
                elif etype == "organization" and len(evalue) > 1:
                    all_employers.append(evalue)
                elif etype == "domain":
                    all_domains.add(evalue.lower())

            # Extract from metadata
            metadata = d.get("metadata", {})
            if metadata.get("username") and metadata.get("platform"):
                all_usernames.append({
                    "username": metadata["username"],
                    "platform": metadata["platform"],
                    "url": metadata.get("profile_url", d.get("content", {}).get("url", "")),
                    "confidence": d.get("confidence", 0.7),
                })

            # Breach findings
            source_type = d.get("source_type", "")
            if source_type == "breach_data" or metadata.get("severity"):
                all_breach_findings.append({
                    "source": source_type,
                    "source_url": d.get("content", {}).get("url", ""),
                    "severity": metadata.get("severity", "MEDIUM"),
                    "details": d.get("content", {}).get("body", "")[:300],
                })

        # Resolve canonical name
        person.canonical_name = self._resolve_canonical_name(all_names)
        if person.canonical_name:
            parts = person.canonical_name.strip().split()
            person.name_first = parts[0] if parts else None
            person.name_last = parts[-1] if len(parts) > 1 else None

        person.aliases = list(set(all_names))[:20]
        person.emails = [{"email": e, "source": "evidence"} for e in all_emails]
        person.phones = list(all_phones)[:10]
        person.usernames = self._dedupe_usernames(all_usernames)
        person.locations = list(set(all_locations))[:10]
        person.employers = list(set(all_employers))[:10]
        person.domains = list(all_domains)[:10]
        person.social_profiles = [
            {"platform": u["platform"], "url": u["url"], "username": u["username"]}
            for u in person.usernames if u.get("url")
        ]
        person.breach_findings = all_breach_findings
        person.raw_evidence_count = len(evidence_items)

        # Score
        person.match_confidence = self._compute_match_confidence(person)
        person.risk_score = self._compute_risk_score(person)
        person.risk_level = "HIGH" if person.risk_score > 0.7 else "MEDIUM" if person.risk_score > 0.4 else "LOW"

        # Generate summary
        person.intelligence_summary = self._generate_summary(person, raw_query)

        self.logger.info(
            f"Resolved person '{person.canonical_name or raw_query}': "
            f"{len(person.emails)} emails, {len(person.usernames)} usernames, "
            f"risk={person.risk_level}, confidence={person.match_confidence:.0%}"
        )

        return person

    def _resolve_canonical_name(self, names: List[str]) -> Optional[str]:
        """Pick the most representative name from candidates."""
        if not names:
            return None
        freq = defaultdict(int)
        for n in names:
            clean = n.strip().title()
            if 2 <= len(clean.split()) <= 4:
                freq[clean] += 1
        if not freq:
            return names[0].strip().title()
        return max(freq, key=freq.get)

    def _dedupe_usernames(self, usernames: List[Dict]) -> List[Dict]:
        """Remove duplicate usernames, prefer higher confidence."""
        seen = {}
        for u in usernames:
            key = (u["username"].lower(), u.get("platform", "").lower())
            if key not in seen or u.get("confidence", 0) > seen[key].get("confidence", 0):
                seen[key] = u
        return list(seen.values())

    def _compute_match_confidence(self, person: ResolvedPerson) -> float:
        """Score 0–1 based on corroborating evidence."""
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
        """Compute risk indicators from breach exposure and footprint."""
        score = 0.0
        if len(person.breach_findings) > 0:
            score += 0.35
        if len(person.breach_findings) > 3:
            score += 0.20
        if len(person.usernames) > 8:
            score += 0.15
        if len(person.emails) > 5:
            score += 0.10
        for b in person.breach_findings:
            if b.get("severity") == "HIGH":
                score += 0.10
                break
        return round(min(score, 1.0), 2)

    def _generate_summary(self, person: ResolvedPerson, raw_query: str) -> str:
        """Generate human-readable intelligence summary."""
        lines = []

        if person.canonical_name:
            lines.append(f"Target identified as: {person.canonical_name}.")
        else:
            lines.append(f"Target query: '{raw_query}'. Name could not be conclusively resolved.")

        if person.usernames:
            platforms = list(set(u.get("platform", "") for u in person.usernames))[:5]
            lines.append(f"Online presence detected on {len(person.usernames)} platform(s): {', '.join(p for p in platforms if p)}.")

        if person.emails:
            lines.append(f"{len(person.emails)} email(s) associated: {', '.join(e['email'] for e in person.emails[:3])}.")

        if person.breach_findings:
            lines.append(f"BREACH ALERT: Target appears in {len(person.breach_findings)} breach/paste source(s). Risk level: {person.risk_level}.")
        else:
            lines.append("No breach exposure detected.")

        if person.locations:
            lines.append(f"Associated locations: {', '.join(person.locations[:3])}.")

        if person.employers:
            lines.append(f"Associated organisations: {', '.join(person.employers[:3])}.")

        lines.append(f"Match confidence: {int(person.match_confidence * 100)}% based on {person.raw_evidence_count} evidence items.")

        return " ".join(lines)

    def save_resolved_person(self, person: ResolvedPerson, db) -> str:
        """Persist resolved person to MongoDB."""
        doc = person.to_dict()
        db.resolved_persons.replace_one(
            {"person_id": person.person_id},
            doc,
            upsert=True
        )
        self.logger.info(f"Saved resolved person {person.person_id}")
        return person.person_id

    # ─── Entity-based Resolution Methods ─────────────────────────────────

    def resolve_by_email(self, email: str, investigation_id: Optional[str] = None) -> IdentityProfile:
        """
        Resolve an email to identity profile.
        
        Creates identity from all related entities (usernames, persons, domains, etc.)
        """
        email = email.lower().strip()
        profile = IdentityProfile(
            identity_id=f"id_email_{hash(email) % 10000000}",
            primary_entity={"type": "email", "value": email},
            created_at=datetime.now(timezone.utc).isoformat()
        )

        # Find all evidence mentioning this email
        email_evidence = self.store.get_by_entity("email", email)
        profile.evidence_ids.extend([e.evidence_id for e in email_evidence])

        # Extract related entities
        related_entities = set()
        for item in email_evidence:
            profile.entity_types.add("email")
            
            # Look for co-occurring entities
            for entity in item.entities:
                if entity.type != "email":
                    related_entities.add((entity.type, entity.value))

        # Convert to equivalences
        for entity_type, entity_value in related_entities:
            profile.equivalent_entities.append({
                "type": entity_type,
                "value": entity_value
            })
            profile.entity_types.add(entity_type)

        profile.updated_at = datetime.now(timezone.utc).isoformat()
        return profile

    def resolve_by_username(self, username: str, investigation_id: Optional[str] = None) -> IdentityProfile:
        """
        Resolve a username to identity profile.
        """
        username = username.lower().strip()
        profile = IdentityProfile(
            identity_id=f"id_user_{hash(username) % 10000000}",
            primary_entity={"type": "username", "value": username},
            created_at=datetime.now(timezone.utc).isoformat()
        )

        # Find all evidence mentioning this username
        user_evidence = self.store.get_by_entity("username", username)
        profile.evidence_ids.extend([e.evidence_id for e in user_evidence])

        # Extract related entities
        related_entities = set()
        for item in user_evidence:
            profile.entity_types.add("username")
            for entity in item.entities:
                if entity.type != "username":
                    related_entities.add((entity.type, entity.value))

        for entity_type, entity_value in related_entities:
            profile.equivalent_entities.append({
                "type": entity_type,
                "value": entity_value
            })
            profile.entity_types.add(entity_type)

        profile.updated_at = datetime.now(timezone.utc).isoformat()
        return profile

    def resolve_by_domain(self, domain: str, investigation_id: Optional[str] = None) -> IdentityProfile:
        """
        Resolve a domain to identity profile (organization).
        """
        domain = domain.lower().strip()
        profile = IdentityProfile(
            identity_id=f"id_domain_{hash(domain) % 10000000}",
            primary_entity={"type": "domain", "value": domain},
            created_at=datetime.now(timezone.utc).isoformat()
        )

        # Find all evidence mentioning this domain
        domain_evidence = self.store.get_by_entity("domain", domain)
        profile.evidence_ids.extend([e.evidence_id for e in domain_evidence])

        # Extract related entities
        related_entities = set()
        for item in domain_evidence:
            profile.entity_types.add("domain")
            for entity in item.entities:
                if entity.type != "domain":
                    related_entities.add((entity.type, entity.value))

        for entity_type, entity_value in related_entities:
            profile.equivalent_entities.append({
                "type": entity_type,
                "value": entity_value
            })
            profile.entity_types.add(entity_type)

        profile.updated_at = datetime.now(timezone.utc).isoformat()
        return profile

    def resolve_by_person(self, person_name: str, investigation_id: Optional[str] = None) -> IdentityProfile:
        """
        Resolve a person name to identity profile.
        """
        person_name = person_name.lower().strip()
        profile = IdentityProfile(
            identity_id=f"id_person_{hash(person_name) % 10000000}",
            primary_entity={"type": "person", "value": person_name},
            created_at=datetime.now(timezone.utc).isoformat()
        )

        # Find all evidence mentioning this person
        person_evidence = self.store.get_by_entity("person", person_name)
        profile.evidence_ids.extend([e.evidence_id for e in person_evidence])

        # Extract related entities
        related_entities = set()
        for item in person_evidence:
            profile.entity_types.add("person")
            for entity in item.entities:
                if entity.type != "person":
                    related_entities.add((entity.type, entity.value))

        for entity_type, entity_value in related_entities:
            profile.equivalent_entities.append({
                "type": entity_type,
                "value": entity_value
            })
            profile.entity_types.add(entity_type)

        profile.updated_at = datetime.now(timezone.utc).isoformat()
        return profile

    def merge_profiles(
        self,
        profiles: List[IdentityProfile],
        merge_reason: str = "manual_merge"
    ) -> IdentityProfile:
        """
        Merge multiple identity profiles into one.
        
        Used when identity resolver determines entities refer to same person.
        """
        if not profiles:
            raise ValueError("Need at least one profile to merge")

        # Use first profile as base
        merged = profiles[0]
        merged.updated_at = datetime.now(timezone.utc).isoformat()

        # Add all entities from other profiles
        for profile in profiles[1:]:
            merged.equivalent_entities.extend(profile.equivalent_entities)
            merged.entity_types.update(profile.entity_types)
            merged.evidence_ids.extend(profile.evidence_ids)
            
            # Average confidence (weighted by evidence count)
            total_evidence = len(merged.evidence_ids) + len(profile.evidence_ids)
            if total_evidence > 0:
                merged.confidence = (
                    (merged.confidence * len(merged.evidence_ids) +
                     profile.confidence * len(profile.evidence_ids)) / total_evidence
                )
            
            # Add metadata about merge
            merged.metadata[f"merged_{profile.identity_id}"] = merge_reason

        # Deduplicate entities
        unique_entities = {}
        for entity in merged.equivalent_entities:
            key = (entity["type"], entity["value"].lower())
            if key not in unique_entities:
                unique_entities[key] = entity

        merged.equivalent_entities = list(unique_entities.values())

        self.logger.info(
            f"Merged {len(profiles)} profiles into {merged.identity_id} "
            f"with {len(merged.equivalent_entities)} entities"
        )

        return merged

    def get_related_identities(
        self,
        identity_id: str,
        depth: int = 1
    ) -> Dict[str, IdentityProfile]:
        """
        Get all related identity profiles (people who know each other, etc.).
        
        Uses co-occurrence: if two identities share evidence items, they're related.
        """
        related = {}

        # Get evidence for this identity
        # (would need to implement identity storage in MongoDB first)
        # For now, return empty dict
        self.logger.info(f"Found {len(related)} related identities for {identity_id}")

        return related

    def calculate_entity_similarity(
        self,
        entity_a: Dict,
        entity_b: Dict
    ) -> float:
        """
        Calculate similarity between two entities (0.0-1.0).
        
        Same type and value: 1.0
        Same type, similar value: 0.7-0.9 (fuzzy match)
        Different type: 0.3-0.7 (if commonly linked)
        Unrelated: 0.0
        """
        type_a, value_a = entity_a.get("type"), entity_a.get("value", "").lower()
        type_b, value_b = entity_b.get("type"), entity_b.get("value", "").lower()

        # Same entity
        if type_a == type_b and value_a == value_b:
            return 1.0

        # Different type but commonly linked
        type_links = {
            ("email", "username"): 0.8,
            ("email", "person"): 0.75,
            ("username", "person"): 0.7,
            ("email", "domain"): 0.6,
            ("person", "organization"): 0.5,
        }

        key1 = (type_a, type_b)
        key2 = (type_b, type_a)

        if key1 in type_links:
            return type_links[key1]
        elif key2 in type_links:
            return type_links[key2]

        return 0.0

    def find_equivalences(
        self,
        entity: Dict,
        min_confidence: float = 0.7
    ) -> List[EntityEquivalence]:
        """
        Find all entities likely equivalent to given entity.
        """
        equivalences = []
        entity_type = entity.get("type")
        entity_value = entity.get("value", "").lower()

        # Find evidence containing this entity
        evidence_list = self.store.get_by_entity(entity_type, entity_value)

        # Extract all other entities from this evidence
        related_entities: Dict[Tuple, Tuple[int, float]] = {}

        for item in evidence_list:
            for other_entity in item.entities:
                if other_entity.type == entity_type and other_entity.value.lower() == entity_value:
                    continue  # Skip same entity

                key = (other_entity.type, other_entity.value.lower())

                if key not in related_entities:
                    related_entities[key] = (0, 0.0)

                count, total_conf = related_entities[key]
                related_entities[key] = (count + 1, total_conf + other_entity.confidence)

        # Convert to equivalences
        for (entity_type_other, entity_value_other), (count, total_conf) in related_entities.items():
            avg_conf = total_conf / count if count > 0 else 0
            similarity = self.calculate_entity_similarity(
                entity,
                {"type": entity_type_other, "value": entity_value_other}
            )

            confidence = min(1.0, avg_conf * similarity)

            if confidence >= min_confidence:
                eq = EntityEquivalence(
                    entity_a=entity,
                    entity_b={"type": entity_type_other, "value": entity_value_other},
                    confidence=confidence,
                    reason=f"Co-occurred {count} times, similarity={similarity:.2f}",
                    evidence_ids=[e.evidence_id for e in evidence_list[:5]]
                )
                equivalences.append(eq)

        return sorted(equivalences, key=lambda x: x.confidence, reverse=True)
