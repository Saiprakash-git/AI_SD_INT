"""
Evidence Engine Utilities — Helper functions for common operations.

Provides convenience functions for:
- Evidence creation shortcuts
- Batch operations
- Entity normalization
- Common queries
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urlparse

from osint.schemas.evidence_schema import (
    EvidenceItem, EntityRecord, EntityType, SourceType
)
from osint.services.evidence_builder import EvidenceBuilder
from osint.db.evidence_store import EvidenceStore

logger = logging.getLogger(__name__)


class EvidenceNormalizer:
    """
    Normalizes and cleans entity values for consistent identification.
    
    Examples:
        - john@example.com → john@example.com (email normalized)
        - John Smith → john smith (person normalized)
        - example.com → example.com (domain normalized)
        - @johndoe → johndoe (platform prefix removed)
    """
    
    @staticmethod
    def normalize_email(email: str) -> str:
        """Normalize email to lowercase."""
        return email.lower().strip() if email else ""
    
    @staticmethod
    def normalize_username(username: str) -> str:
        """Normalize username: remove prefixes, lowercase."""
        username = username.strip()
        # Remove common prefixes
        for prefix in ["@", "u/", "r/", "#"]:
            if username.startswith(prefix):
                username = username[len(prefix):]
        return username.lower()
    
    @staticmethod
    def normalize_domain(domain: str) -> str:
        """Normalize domain: extract from URLs, lowercase."""
        domain = domain.lower().strip()
        # Extract domain from URL if needed
        if domain.startswith("http"):
            parsed = urlparse(domain)
            domain = parsed.netloc
        # Remove common prefixes
        for prefix in ["www.", "www-", "m."]:
            if domain.startswith(prefix):
                domain = domain[len(prefix):]
        return domain
    
    @staticmethod
    def normalize_person(name: str) -> str:
        """Normalize person name: lowercase, trim whitespace."""
        return " ".join(name.lower().split()) if name else ""
    
    @staticmethod
    def normalize_entity(entity_type: str, value: str) -> str:
        """Dispatch to appropriate normalizer."""
        if entity_type == EntityType.EMAIL.value:
            return EvidenceNormalizer.normalize_email(value)
        elif entity_type == EntityType.USERNAME.value:
            return EvidenceNormalizer.normalize_username(value)
        elif entity_type == EntityType.DOMAIN.value:
            return EvidenceNormalizer.normalize_domain(value)
        elif entity_type == EntityType.PERSON.value:
            return EvidenceNormalizer.normalize_person(value)
        else:
            return value.lower().strip() if value else ""


class EvidenceFactory:
    """Convenience factory for common evidence creation patterns."""
    
    @staticmethod
    def from_web_search(
        query: str,
        result_title: str,
        result_body: str,
        result_url: str,
        source: str = "duckduckgo",
        metadata: Optional[Dict[str, Any]] = None
    ) -> EvidenceItem:
        """Create evidence item from web search result."""
        if metadata is None:
            metadata = {}
        metadata["search_query"] = query
        
        return EvidenceBuilder.from_raw(
            source_type=SourceType.WEB_SEARCH.value,
            source_id=f"{source}_{hash(result_url) & 0xffff:04x}",
            source_platform=source,
            title=result_title,
            body=result_body,
            url=result_url,
            metadata=metadata,
            confidence=0.70,
            tags=["web_search", source],
            extract_entities=True
        )
    
    @staticmethod
    def from_username_search(
        username: str,
        platform: str,
        profile_url: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> EvidenceItem:
        """Create evidence item from username search result."""
        if metadata is None:
            metadata = {}
        
        return EvidenceBuilder.from_raw(
            source_type=SourceType.USERNAME_DISCOVERY.value,
            source_id=f"{platform}_{username}",
            source_platform=platform,
            title=f"Username: {username}",
            body=f"User account found on {platform}",
            url=profile_url,
            metadata=metadata,
            confidence=0.95,
            tags=["username_discovery", platform],
            extract_entities=False
        )
    
    @staticmethod
    def from_breach_data(
        email: str,
        breach_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> EvidenceItem:
        """Create evidence item from breach data."""
        if metadata is None:
            metadata = {}
        metadata["breach_name"] = breach_name
        
        return EvidenceBuilder.from_raw(
            source_type=SourceType.BREACH_DATA.value,
            source_id=f"breach_{breach_name}_{email}",
            source_platform="hibp",
            title=f"Breach: {breach_name}",
            body=f"Email {email} found in {breach_name} breach",
            url="",
            metadata=metadata,
            confidence=0.90,
            tags=["breach_data", breach_name],
            extract_entities=False
        )


class EvidenceQuery:
    """Convenience query builder for common investigation patterns."""
    
    def __init__(self):
        self.store = EvidenceStore()
    
    def find_by_email(self, email: str) -> List[EvidenceItem]:
        """Find all evidence containing a specific email."""
        normalized = EvidenceNormalizer.normalize_email(email)
        return self.store.get_by_entity(EntityType.EMAIL.value, normalized)
    
    def find_by_username(self, username: str) -> List[EvidenceItem]:
        """Find all evidence containing a specific username."""
        normalized = EvidenceNormalizer.normalize_username(username)
        return self.store.get_by_entity(EntityType.USERNAME.value, normalized)
    
    def find_by_domain(self, domain: str) -> List[EvidenceItem]:
        """Find all evidence containing a specific domain."""
        normalized = EvidenceNormalizer.normalize_domain(domain)
        results = self.store.get_by_entity(EntityType.DOMAIN.value, normalized)
        # Also search URLs
        url_results = self.store.get_by_entity(EntityType.URL.value, domain)
        return list({r.evidence_id: r for r in results + url_results}.values())
    
    def find_by_person(self, name: str) -> List[EvidenceItem]:
        """Find all evidence mentioning a person."""
        return self.store.get_by_entity(EntityType.PERSON.value, name)
    
    def find_identity_bundle(self, identifier: str, identifier_type: str = "auto") -> Dict[str, List[EvidenceItem]]:
        """
        Find all evidence related to an identity using multiple identifier types.
        Useful for Module 3 (identity resolution).
        
        Args:
            identifier: Value to search for
            identifier_type: "auto", "email", "username", "domain", "person"
            
        Returns:
            Dict with results grouped by entity type
        """
        results = {}
        
        if identifier_type == "auto" or identifier_type == "email":
            if "@" in identifier:
                results["emails"] = self.find_by_email(identifier)
        
        if identifier_type == "auto" or identifier_type == "username":
            results["usernames"] = self.find_by_username(identifier)
        
        if identifier_type == "auto" or identifier_type == "domain":
            if "." in identifier and "@" not in identifier:
                results["domains"] = self.find_by_domain(identifier)
        
        if identifier_type == "auto" or identifier_type == "person":
            if " " in identifier or identifier_type == "person":
                results["persons"] = self.find_by_person(identifier)
        
        return {k: v for k, v in results.items() if v}  # Remove empty results
    
    def get_entity_pivots(self, entity_type: str, entity_value: str, depth: int = 1) -> Dict[str, Any]:
        """
        Find related entities for pivoting during investigation.
        Used for Module 3 (pivot generator).
        
        Args:
            entity_type: Type of entity to pivot from
            entity_value: Value of entity
            depth: How many levels to search (1 = direct, 2 = secondary, etc.)
            
        Returns:
            Structured pivot data with related entities
        """
        network = self.store.get_entity_network(entity_type, entity_value)
        
        pivots = {
            "target": network["target"],
            "evidence_count": network["evidence_count"],
            "related_entities": network["co_occurring_entities"],
            "investigation_tips": []
        }
        
        # Generate investigation tips based on findings
        if network["evidence_count"] > 10:
            pivots["investigation_tips"].append("High evidence density - common entity")
        if network["co_occurring_entities"]:
            top_cooccurrence = network["co_occurring_entities"][0]
            if top_cooccurrence["co_occurrence_count"] > 5:
                pivots["investigation_tips"].append(f"Strong link to {top_cooccurrence['type']}: {top_cooccurrence['value']}")
        
        return pivots


class EvidenceBatch:
    """Batch operations helper for efficient bulk processing."""
    
    def __init__(self):
        self.store = EvidenceStore()
        self.batch = []
    
    def add(self, item: EvidenceItem) -> "EvidenceBatch":
        """Add item to batch."""
        self.batch.append(item)
        return self
    
    def add_raw(self, **kwargs) -> "EvidenceBatch":
        """Add raw evidence creation to batch."""
        item = EvidenceBuilder.from_raw(**kwargs)
        self.batch.append(item)
        return self
    
    def commit(self) -> Dict[str, int]:
        """Insert batch and return statistics."""
        stats = self.store.insert_many(self.batch)
        logger.info(f"Batch commit: {stats['inserted']} inserted, {stats['skipped']} skipped, {stats['errors']} errors")
        self.batch = []
        return stats
    
    def __len__(self) -> int:
        """Return current batch size."""
        return len(self.batch)
    
    def __enter__(self):
        """Context manager support."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Auto-commit on context exit."""
        if exc_type is None and len(self.batch) > 0:
            self.commit()
        return False
