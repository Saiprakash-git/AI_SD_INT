"""
OSINT Evidence Engine — MODULE 1

Public API for the unified evidence system.

Exports:
  - Core Schema: EvidenceItem, EntityRecord, SourceType, EntityType
  - Builders: EvidenceBuilder, EvidenceFactory
  - Storage: EvidenceStore, EvidenceBatch
  - Utils: EvidenceNormalizer, EvidenceQuery, EntityExtractor
"""

from osint.schemas.evidence_schema import (
    EvidenceItem,
    EntityRecord,
    EvidenceContent,
    EvidenceTimestamps,
    SourceType,
    EntityType,
    EvidenceStatus,
    generate_evidence_id,
    validate_evidence_item,
)

from osint.extractors.entity_extractor import EntityExtractor

from osint.services.evidence_builder import EvidenceBuilder

from osint.db.evidence_store import EvidenceStore

from osint.evidence_utils import (
    EvidenceNormalizer,
    EvidenceFactory,
    EvidenceQuery,
    EvidenceBatch,
)

# Re-exports for convenience
__all__ = [
    # Schema
    "EvidenceItem",
    "EntityRecord",
    "EvidenceContent",
    "EvidenceTimestamps",
    "SourceType",
    "EntityType",
    "EvidenceStatus",
    "generate_evidence_id",
    "validate_evidence_item",
    # Extraction
    "EntityExtractor",
    # Building
    "EvidenceBuilder",
    "EvidenceFactory",
    # Storage
    "EvidenceStore",
    "EvidenceBatch",
    # Utils
    "EvidenceNormalizer",
    "EvidenceQuery",
]
