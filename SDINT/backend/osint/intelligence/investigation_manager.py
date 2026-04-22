"""
Investigation Manager — Unified interface for managing investigations.

Core functionality:
  - Investigation lifecycle management (create, update, close)
  - Evidence linking to investigations
  - Identity resolution per investigation
  - Narrative building
  - Threat assessment
"""

import logging
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone

from osint.db.evidence_store import EvidenceStore
from osint.intelligence.identity_resolver import IdentityResolver, IdentityProfile
from osint.intelligence.entity_pivot import EntityPivot
from osint.intelligence.narrative_builder import NarrativeBuilder, Narrative


logger = logging.getLogger(__name__)


@dataclass
class Investigation:
    """Investigation case."""
    investigation_id: str
    title: str
    description: str
    status: str = "active"  # active, paused, closed, archived
    priority: str = "medium"  # low, medium, high, critical
    threat_level: str = "unknown"  # info, low, medium, high, critical
    
    investigator: str = ""
    tags: List[str] = field(default_factory=list)
    
    evidence_count: int = 0
    identity_count: int = 0
    narrative_count: int = 0
    
    evidence_ids: List[str] = field(default_factory=list)
    identity_ids: List[str] = field(default_factory=list)
    narrative_ids: List[str] = field(default_factory=list)
    
    findings: Dict = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)
    
    created_at: str = ""
    updated_at: str = ""
    closed_at: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "investigation_id": self.investigation_id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "threat_level": self.threat_level,
            "investigator": self.investigator,
            "tags": self.tags,
            "evidence_count": self.evidence_count,
            "identity_count": self.identity_count,
            "narrative_count": self.narrative_count,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


class InvestigationManager:
    """
    Manage investigations end-to-end.
    """

    def __init__(self, store: Optional[EvidenceStore] = None):
        self.store = store or EvidenceStore()
        self.logger = logging.getLogger("InvestigationManager")
        
        # Initialize sub-components
        self.identity_resolver = IdentityResolver(store)
        self.entity_pivot = EntityPivot(store)
        self.narrative_builder = NarrativeBuilder(store)
        
        # Investigation cache
        self._investigations: Dict[str, Investigation] = {}

    def create_investigation(
        self,
        title: str,
        description: str,
        investigator: str = "",
        priority: str = "medium",
        tags: Optional[List[str]] = None
    ) -> Investigation:
        """Create new investigation."""
        investigation_id = f"inv_{hash((title, datetime.now())) % 10000000}"
        
        investigation = Investigation(
            investigation_id=investigation_id,
            title=title,
            description=description,
            investigator=investigator,
            priority=priority,
            tags=tags or [],
            created_at=datetime.now(timezone.utc).isoformat(),
            updated_at=datetime.now(timezone.utc).isoformat()
        )
        
        self._investigations[investigation_id] = investigation
        self.logger.info(f"Created investigation: {investigation_id}")
        
        return investigation

    def add_evidence_to_investigation(
        self,
        investigation_id: str,
        evidence_ids: List[str]
    ) -> int:
        """Add evidence items to investigation."""
        if investigation_id not in self._investigations:
            raise ValueError(f"Investigation {investigation_id} not found")
        
        inv = self._investigations[investigation_id]
        added = 0
        
        for evidence_id in evidence_ids:
            if evidence_id not in inv.evidence_ids:
                inv.evidence_ids.append(evidence_id)
                added += 1
        
        inv.evidence_count = len(inv.evidence_ids)
        inv.updated_at = datetime.now(timezone.utc).isoformat()
        
        self.logger.info(f"Added {added} evidence items to {investigation_id}")
        
        return added

    def get_investigation_entities(
        self,
        investigation_id: str
    ) -> Dict[str, List[Dict]]:
        """Get all entities in investigation grouped by type."""
        if investigation_id not in self._investigations:
            raise ValueError(f"Investigation {investigation_id} not found")
        
        inv = self._investigations[investigation_id]
        entities_by_type: Dict[str, List[Dict]] = {}
        
        for evidence_id in inv.evidence_ids:
            item = self.store.collection.find_one({"evidence_id": evidence_id})
            if not item:
                continue
            
            for entity in item.get("entities", []):
                entity_type = entity["type"]
                if entity_type not in entities_by_type:
                    entities_by_type[entity_type] = []
                
                entity_dict = {
                    "value": entity["value"],
                    "confidence": entity.get("confidence", 0.5),
                    "source": entity.get("source", "unknown")
                }
                
                if entity_dict not in entities_by_type[entity_type]:
                    entities_by_type[entity_type].append(entity_dict)
        
        return entities_by_type

    def resolve_investigation_identities(
        self,
        investigation_id: str
    ) -> List[IdentityProfile]:
        """Resolve identities for all entities in investigation."""
        if investigation_id not in self._investigations:
            raise ValueError(f"Investigation {investigation_id} not found")
        
        inv = self._investigations[investigation_id]
        entities_by_type = self.get_investigation_entities(investigation_id)
        
        identities = []
        seen_profiles: set = set()
        
        # Resolve by email
        for email_entity in entities_by_type.get("email", []):
            profile = self.identity_resolver.resolve_by_email(email_entity["value"])
            profile_key = (profile.primary_entity["type"], profile.primary_entity["value"])
            
            if profile_key not in seen_profiles:
                identities.append(profile)
                seen_profiles.add(profile_key)
        
        # Resolve by username
        for user_entity in entities_by_type.get("username", []):
            profile = self.identity_resolver.resolve_by_username(user_entity["value"])
            profile_key = (profile.primary_entity["type"], profile.primary_entity["value"])
            
            if profile_key not in seen_profiles:
                identities.append(profile)
                seen_profiles.add(profile_key)
        
        # Resolve by domain
        for domain_entity in entities_by_type.get("domain", []):
            profile = self.identity_resolver.resolve_by_domain(domain_entity["value"])
            profile_key = (profile.primary_entity["type"], profile.primary_entity["value"])
            
            if profile_key not in seen_profiles:
                identities.append(profile)
                seen_profiles.add(profile_key)
        
        # Resolve by person
        for person_entity in entities_by_type.get("person", []):
            profile = self.identity_resolver.resolve_by_person(person_entity["value"])
            profile_key = (profile.primary_entity["type"], profile.primary_entity["value"])
            
            if profile_key not in seen_profiles:
                identities.append(profile)
                seen_profiles.add(profile_key)
        
        inv.identity_count = len(identities)
        inv.updated_at = datetime.now(timezone.utc).isoformat()
        
        self.logger.info(
            f"Resolved {len(identities)} identities for {investigation_id}"
        )
        
        return identities

    def build_investigation_timeline(
        self,
        investigation_id: str
    ) -> Narrative:
        """Build timeline from all evidence in investigation."""
        if investigation_id not in self._investigations:
            raise ValueError(f"Investigation {investigation_id} not found")
        
        inv = self._investigations[investigation_id]
        
        narrative = self.narrative_builder.build_timeline(
            inv.evidence_ids,
            title=f"Timeline: {inv.title}"
        )
        
        # Assess threat
        patterns = self.narrative_builder.detect_patterns(narrative)
        inv.threat_level = self.narrative_builder.assess_threat(narrative)
        
        inv.narrative_count += 1
        inv.findings["patterns"] = patterns
        inv.findings["threat_assessment"] = inv.threat_level
        inv.updated_at = datetime.now(timezone.utc).isoformat()
        
        self.logger.info(f"Built timeline for {investigation_id}")
        
        return narrative

    def find_investigation_pivots(
        self,
        investigation_id: str,
        entity_type: str,
        entity_value: str
    ) -> List[Dict]:
        """Find pivot suggestions for entity in investigation."""
        suggestions = self.entity_pivot.suggest_pivots(
            {"type": entity_type, "value": entity_value}
        )
        
        return [s.__dict__ for s in suggestions]

    def add_investigation_note(
        self,
        investigation_id: str,
        note: str
    ) -> None:
        """Add note to investigation."""
        if investigation_id not in self._investigations:
            raise ValueError(f"Investigation {investigation_id} not found")
        
        inv = self._investigations[investigation_id]
        timestamp = datetime.now(timezone.utc).isoformat()
        inv.notes.append(f"[{timestamp}] {note}")
        inv.updated_at = timestamp

    def close_investigation(
        self,
        investigation_id: str,
        final_assessment: Optional[str] = None
    ) -> Investigation:
        """Close investigation."""
        if investigation_id not in self._investigations:
            raise ValueError(f"Investigation {investigation_id} not found")
        
        inv = self._investigations[investigation_id]
        inv.status = "closed"
        inv.closed_at = datetime.now(timezone.utc).isoformat()
        
        if final_assessment:
            inv.findings["final_assessment"] = final_assessment
        
        self.logger.info(f"Closed investigation {investigation_id}")
        
        return inv

    def get_investigation_summary(
        self,
        investigation_id: str
    ) -> Dict:
        """Get complete investigation summary."""
        if investigation_id not in self._investigations:
            raise ValueError(f"Investigation {investigation_id} not found")
        
        inv = self._investigations[investigation_id]
        
        return {
            "investigation": inv.to_dict(),
            "entities": self.get_investigation_entities(investigation_id),
            "findings": inv.findings,
            "notes_count": len(inv.notes),
            "threat_level": inv.threat_level,
            "status": inv.status
        }
