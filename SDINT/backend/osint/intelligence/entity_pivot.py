"""
Entity Pivoting — Discover relationships through co-occurrence analysis.

Core functionality:
  - Find entities that appear together in evidence
  - Build relationship networks
  - Rank by frequency and confidence
  - Provide pivot suggestions for investigation
"""

import logging
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass, field
from collections import Counter, defaultdict

from osint.db.evidence_store import EvidenceStore
from osint.schemas.evidence_schema import EntityType


logger = logging.getLogger(__name__)


@dataclass
class EntityRelationship:
    """Relationship between two entities."""
    entity_a: Dict  # {type, value}
    entity_b: Dict  # {type, value}
    co_occurrence_count: int  # How many times they appear together
    confidence: float  # 0.0-1.0 (based on source reliability)
    evidence_ids: List[str] = field(default_factory=list)  # Supporting evidence
    relationship_types: List[str] = field(default_factory=list)  # "same_person", "same_org", etc.
    
    def to_dict(self) -> Dict:
        return {
            "entity_a": self.entity_a,
            "entity_b": self.entity_b,
            "co_occurrence_count": self.co_occurrence_count,
            "confidence": round(self.confidence, 3),
            "evidence_count": len(self.evidence_ids),
            "relationship_types": self.relationship_types
        }


@dataclass
class PivotSuggestion:
    """Suggested direction for investigation pivot."""
    from_entity: Dict  # Starting point
    to_entity: Dict  # Next entity to explore
    strength: float  # How strong the connection (0.0-1.0)
    justification: str  # Why this pivot is suggested
    next_steps: List[str] = field(default_factory=list)  # Recommendations


class EntityPivot:
    """
    Build pivot networks from entities.
    
    Starting with one entity, discover connected entities and build
    relationship network for investigative leads.
    """

    def __init__(self, store: Optional[EvidenceStore] = None):
        self.store = store or EvidenceStore()
        self.logger = logging.getLogger("EntityPivot")
        
        self._pivot_cache: Dict[Tuple, List[EntityRelationship]] = {}

    def find_related_entities(
        self,
        entity: Dict,
        max_depth: int = 2,
        min_confidence: float = 0.6
    ) -> List[EntityRelationship]:
        """
        Find entities related to given entity via co-occurrence.
        
        Args:
            entity: {type, value}
            max_depth: How many hops to traverse
            min_confidence: Minimum confidence threshold
            
        Returns:
            List of relationships sorted by strength
        """
        entity_type = entity.get("type")
        entity_value = entity.get("value", "").lower()

        # Cache key
        cache_key = (entity_type, entity_value, max_depth)
        if cache_key in self._pivot_cache:
            return self._pivot_cache[cache_key]

        # Find evidence mentioning this entity
        evidence_list = self.store.get_by_entity(entity_type, entity_value)

        if not evidence_list:
            self.logger.warning(f"No evidence found for {entity_type}:{entity_value}")
            return []

        # Count co-occurrences
        entity_cooccurrences: Dict[Tuple, Tuple[int, List[str], float]] = defaultdict(
            lambda: (0, [], 0.0)
        )

        for item in evidence_list:
            # Get all entities in this evidence item
            for other_entity in item.entities:
                if other_entity.type == entity_type and other_entity.value.lower() == entity_value:
                    continue  # Skip self

                key = (other_entity.type, other_entity.value.lower())
                count, evidence_ids, total_conf = entity_cooccurrences[key]

                entity_cooccurrences[key] = (
                    count + 1,
                    evidence_ids + [item.evidence_id],
                    total_conf + other_entity.confidence
                )

        # Convert to relationships
        relationships = []

        for (other_type, other_value), (count, evidence_ids, total_conf) in entity_cooccurrences.items():
            avg_confidence = total_conf / count if count > 0 else 0

            if avg_confidence >= min_confidence:
                rel = EntityRelationship(
                    entity_a=entity,
                    entity_b={"type": other_type, "value": other_value},
                    co_occurrence_count=count,
                    confidence=avg_confidence,
                    evidence_ids=evidence_ids[:10],  # Keep first 10
                    relationship_types=self._infer_relationship_types(
                        entity_type, other_type
                    )
                )
                relationships.append(rel)

        # Sort by strength
        relationships.sort(
            key=lambda r: (r.co_occurrence_count, r.confidence),
            reverse=True
        )

        self._pivot_cache[cache_key] = relationships

        self.logger.info(
            f"Found {len(relationships)} related entities for {entity_type}:{entity_value}"
        )

        return relationships

    def build_pivot_network(
        self,
        start_entity: Dict,
        depth: int = 2,
        min_confidence: float = 0.6
    ) -> Dict[str, List[EntityRelationship]]:
        """
        Build a network of related entities starting from one entity.
        
        Returns nested dict: level 0 -> level 1 -> level 2 relationships
        """
        network = {}
        visited: Set[Tuple] = set()
        to_process = [(start_entity, 0)]

        while to_process:
            current_entity, current_depth = to_process.pop(0)

            # Skip if already processed
            entity_key = (
                current_entity.get("type"),
                current_entity.get("value", "").lower()
            )
            if entity_key in visited or current_depth > depth:
                continue

            visited.add(entity_key)

            # Find related entities
            related = self.find_related_entities(
                current_entity,
                max_depth=1,
                min_confidence=min_confidence
            )

            depth_key = f"depth_{current_depth}"
            if depth_key not in network:
                network[depth_key] = []

            network[depth_key].extend(related)

            # Queue next level
            if current_depth < depth:
                for rel in related[:5]:  # Limit branching factor
                    to_process.append((rel.entity_b, current_depth + 1))

        return network

    def suggest_pivots(
        self,
        entity: Dict,
        investigation_context: Optional[str] = None
    ) -> List[PivotSuggestion]:
        """
        Suggest next entities to investigate based on current entity.
        
        Considers:
        - Frequency of co-occurrence
        - Confidence of relationship
        - Entity type patterns
        - Investigation type (person, org, infrastructure, etc.)
        """
        related = self.find_related_entities(entity, max_depth=1)
        suggestions = []

        for rel in related[:5]:  # Top 5 suggestions
            strength = min(1.0, rel.confidence * (rel.co_occurrence_count / 10))

            # Build justification
            justification = (
                f"Co-occurs {rel.co_occurrence_count} times "
                f"with {entity['type']}:{entity['value']} "
                f"(confidence: {rel.confidence:.2f})"
            )

            # Build next steps
            next_steps = []
            if rel.entity_b.get("type") == "email":
                next_steps = [
                    f"Search breach databases for {rel.entity_b['value']}",
                    f"Look for usernames associated with this email",
                    f"Check domain history"
                ]
            elif rel.entity_b.get("type") == "username":
                next_steps = [
                    f"Search {rel.entity_b['value']} on social platforms",
                    f"Check associated email addresses",
                    f"Look for linked accounts"
                ]
            elif rel.entity_b.get("type") == "domain":
                next_steps = [
                    f"Gather WHOIS information",
                    f"Check SSL certificates",
                    f"Look for subdomains",
                    f"Search DNS history"
                ]

            suggestion = PivotSuggestion(
                from_entity=entity,
                to_entity=rel.entity_b,
                strength=strength,
                justification=justification,
                next_steps=next_steps
            )
            suggestions.append(suggestion)

        return suggestions

    def find_clusters(
        self,
        entities: List[Dict],
        min_confidence: float = 0.6
    ) -> List[List[EntityRelationship]]:
        """
        Find clusters of related entities.
        
        Groups entities that are all connected to each other.
        """
        clusters = []
        processed: Set[Tuple] = set()

        for start_entity in entities:
            entity_key = (
                start_entity.get("type"),
                start_entity.get("value", "").lower()
            )

            if entity_key in processed:
                continue

            # Find all connected entities
            cluster = []
            to_process = [start_entity]
            cluster_keys: Set[Tuple] = set()

            while to_process:
                current = to_process.pop(0)
                current_key = (
                    current.get("type"),
                    current.get("value", "").lower()
                )

                if current_key in cluster_keys:
                    continue

                cluster_keys.add(current_key)
                related = self.find_related_entities(
                    current,
                    max_depth=1,
                    min_confidence=min_confidence
                )

                cluster.extend(related)

                for rel in related:
                    if rel.entity_b not in to_process:
                        to_process.append(rel.entity_b)

            if cluster:
                clusters.append(cluster)
                processed.update(cluster_keys)

        self.logger.info(f"Found {len(clusters)} entity clusters")

        return clusters

    def _infer_relationship_types(self, type_a: str, type_b: str) -> List[str]:
        """Infer relationship types based on entity types."""
        types = []

        # Person relationships
        if type_a == "person" and type_b == "email":
            types.append("person_contact")
        elif type_a == "person" and type_b == "username":
            types.append("person_online")
        elif type_a == "person" and type_b == "organization":
            types.append("person_affiliation")

        # Organization relationships
        elif type_a == "organization" and type_b == "domain":
            types.append("org_domain")
        elif type_a == "organization" and type_b == "email":
            types.append("org_email")

        # Infrastructure relationships
        elif type_a == "domain" and type_b == "ip_address":
            types.append("domain_resolves_to")
        elif type_a == "domain" and type_b == "email":
            types.append("domain_email")

        # Account relationships
        elif type_a == "username" and type_b == "email":
            types.append("account_contact")
        elif type_a == "username" and type_b == "person":
            types.append("account_person")

        return types if types else ["related"]

    def get_graph_data(
        self,
        start_entity: Dict,
        depth: int = 2
    ) -> Dict:
        """
        Get relationship data in format suitable for visualization.
        
        Returns:
            {
                "nodes": [{"id": "type:value", "label": "...", "type": "..."}],
                "edges": [{"source": "...", "target": "...", "weight": 0.5}]
            }
        """
        nodes = []
        edges = []
        visited: Set[str] = set()

        network = self.build_pivot_network(start_entity, depth=depth)

        # Add start node
        start_id = f"{start_entity['type']}:{start_entity['value']}"
        nodes.append({
            "id": start_id,
            "label": start_entity["value"],
            "type": start_entity["type"],
            "root": True
        })
        visited.add(start_id)

        # Add relationships as nodes and edges
        for depth_key, relationships in network.items():
            for rel in relationships:
                node_a_id = f"{rel.entity_a['type']}:{rel.entity_a['value']}"
                node_b_id = f"{rel.entity_b['type']}:{rel.entity_b['value']}"

                # Add nodes
                if node_a_id not in visited:
                    nodes.append({
                        "id": node_a_id,
                        "label": rel.entity_a["value"],
                        "type": rel.entity_a["type"]
                    })
                    visited.add(node_a_id)

                if node_b_id not in visited:
                    nodes.append({
                        "id": node_b_id,
                        "label": rel.entity_b["value"],
                        "type": rel.entity_b["type"]
                    })
                    visited.add(node_b_id)

                # Add edge
                edges.append({
                    "source": node_a_id,
                    "target": node_b_id,
                    "weight": rel.confidence,
                    "count": rel.co_occurrence_count
                })

        return {
            "nodes": nodes,
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges)
        }
