"""
MODULE 3 — Intelligence & Analysis

Public API for investigation analysis and intelligence generation.

Exports:
  - IdentityResolver: Link entities into identities
  - EntityPivot: Build relationship networks
  - NarrativeBuilder: Connect evidence into stories
  - InvestigationManager: Unified investigation management
"""

from osint.intelligence.identity_resolver import (
    IdentityResolver,
    IdentityProfile,
    EntityEquivalence,
)

from osint.intelligence.entity_pivot import (
    EntityPivot,
    EntityRelationship,
    PivotSuggestion,
)

from osint.intelligence.narrative_builder import (
    NarrativeBuilder,
    Narrative,
    TimelineEvent,
)

from osint.intelligence.investigation_manager import (
    InvestigationManager,
    Investigation,
)

__all__ = [
    # Identity
    "IdentityResolver",
    "IdentityProfile",
    "EntityEquivalence",
    # Pivoting
    "EntityPivot",
    "EntityRelationship",
    "PivotSuggestion",
    # Narratives
    "NarrativeBuilder",
    "Narrative",
    "TimelineEvent",
    # Investigation
    "InvestigationManager",
    "Investigation",
]
