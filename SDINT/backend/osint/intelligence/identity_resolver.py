"""
Identity Resolution — Link entities across evidence sources into unified identities.

Core functionality:
  - Entity equivalence detection (email ≈ username ≈ person)
  - Identity profile creation (unified view of one person/entity)
  - Relationship mapping (who connected to whom)
  - Confidence scoring for identity links
"""

import logging
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone

from osint.db.evidence_store import EvidenceStore
from osint.schemas.evidence_schema import EntityType


logger = logging.getLogger(__name__)


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
