"""
Narrative Builder — Connect evidence into stories and timelines.

Core functionality:
  - Timeline construction from evidence timestamps
  - Narrative chain building (connect related evidence)
  - Pattern detection
  - Threat assessment scoring
"""

import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone
from collections import defaultdict

from osint.db.evidence_store import EvidenceStore
from osint.schemas.evidence_schema import EvidenceItem


logger = logging.getLogger(__name__)


@dataclass
class TimelineEvent:
    """Single event in timeline."""
    evidence_id: str
    timestamp: str  # ISO format
    event_type: str  # post, comment, breach, search, etc.
    source_platform: str
    title: str
    description: str
    entities: List[Dict] = field(default_factory=list)
    confidence: float = 0.8
    threat_level: str = "info"  # info, low, medium, high, critical
    
    def to_dict(self) -> Dict:
        return {
            "evidence_id": self.evidence_id,
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "source_platform": self.source_platform,
            "title": self.title,
            "description": self.description,
            "entity_count": len(self.entities),
            "confidence": round(self.confidence, 3),
            "threat_level": self.threat_level
        }


@dataclass
class Narrative:
    """Connected story from multiple evidence items."""
    narrative_id: str
    title: str
    description: str
    timeline: List[TimelineEvent] = field(default_factory=list)
    evidence_ids: List[str] = field(default_factory=list)
    entities_involved: List[Dict] = field(default_factory=list)
    pattern_type: str = "unknown"  # phishing, social_engineering, harassment, etc.
    threat_assessment: str = "low"  # low, medium, high, critical
    confidence: float = 0.7
    created_at: str = ""
    updated_at: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "narrative_id": self.narrative_id,
            "title": self.title,
            "description": self.description,
            "timeline_events": len(self.timeline),
            "evidence_count": len(self.evidence_ids),
            "unique_entities": len(self.entities_involved),
            "pattern_type": self.pattern_type,
            "threat_assessment": self.threat_assessment,
            "confidence": round(self.confidence, 3),
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


class NarrativeBuilder:
    """
    Build narratives from connected evidence.
    
    Constructs timelines, identifies patterns, and assesses threats.
    """

    def __init__(self, store: Optional[EvidenceStore] = None):
        self.store = store or EvidenceStore()
        self.logger = logging.getLogger("NarrativeBuilder")

    def build_timeline(
        self,
        evidence_ids: List[str],
        title: str = "Investigation Timeline"
    ) -> Narrative:
        """
        Build a chronological timeline from evidence items.
        """
        narrative = Narrative(
            narrative_id=f"timeline_{hash(tuple(evidence_ids)) % 10000000}",
            title=title,
            description=f"Timeline of {len(evidence_ids)} events",
            created_at=datetime.now(timezone.utc).isoformat()
        )

        events = []
        entities_set = set()

        # Convert evidence to timeline events
        for evidence_id in evidence_ids:
            item = self.store.collection.find_one({"evidence_id": evidence_id})
            if not item:
                continue

            # Get timestamp - handle None values
            timestamp = item.get("timestamps", {}).get("source_created")
            if timestamp is None:
                timestamp = item.get("timestamps", {}).get("discovered", "")
            if timestamp is None:
                timestamp = ""

            event = TimelineEvent(
                evidence_id=evidence_id,
                timestamp=timestamp,
                event_type=item.get("source_type", "unknown"),
                source_platform=item.get("source_platform", "unknown"),
                title=item.get("content", {}).get("title", "Untitled"),
                description=item.get("content", {}).get("body", "")[:200],
                confidence=item.get("confidence", 0.5)
            )

            # Determine threat level
            event.threat_level = self._assess_event_threat(item)

            events.append(event)

            # Collect entities
            for entity in item.get("entities", []):
                entities_set.add((entity["type"], entity["value"]))

        # Sort by timestamp (handle None/empty strings)
        events.sort(key=lambda e: e.timestamp if e.timestamp else "")

        narrative.timeline = events
        narrative.evidence_ids = evidence_ids
        narrative.entities_involved = [
            {"type": e[0], "value": e[1]} for e in entities_set
        ]
        narrative.updated_at = datetime.now(timezone.utc).isoformat()

        self.logger.info(
            f"Built timeline with {len(events)} events "
            f"and {len(entities_set)} unique entities"
        )

        return narrative

    def build_narrative_chain(
        self,
        start_evidence_id: str,
        max_hops: int = 3
    ) -> Narrative:
        """
        Build a narrative chain starting from one evidence item,
        following entity connections.
        """
        visited_ids: set = {start_evidence_id}
        to_process = [start_evidence_id]
        chain_ids = []

        # BFS to find connected evidence
        for _ in range(max_hops):
            next_to_process = []

            for evidence_id in to_process:
                item = self.store.collection.find_one({"evidence_id": evidence_id})
                if not item:
                    continue

                chain_ids.append(evidence_id)

                # Find other evidence mentioning same entities
                for entity in item.get("entities", []):
                    related = self.store.get_by_entity(
                        entity["type"],
                        entity["value"]
                    )

                    for related_item in related:
                        if related_item.evidence_id not in visited_ids:
                            visited_ids.add(related_item.evidence_id)
                            next_to_process.append(related_item.evidence_id)

            to_process = next_to_process[:5]  # Limit branching

        # Build narrative from chain
        narrative = self.build_timeline(
            chain_ids,
            title="Connected Evidence Chain"
        )

        narrative.narrative_id = f"chain_{hash(tuple(chain_ids)) % 10000000}"

        self.logger.info(
            f"Built narrative chain with {len(chain_ids)} connected items"
        )

        return narrative

    def detect_patterns(
        self,
        narrative: Narrative
    ) -> Dict[str, float]:
        """
        Detect threat patterns in narrative.
        
        Returns confidence scores for various patterns.
        """
        patterns = {
            "phishing": 0.0,
            "social_engineering": 0.0,
            "harassment": 0.0,
            "fraud": 0.0,
            "data_exfiltration": 0.0,
            "account_takeover": 0.0,
            "credential_compromise": 0.0,
        }

        # Check for pattern indicators
        event_types = [e.event_type for e in narrative.timeline]
        descriptions = [e.description.lower() for e in narrative.timeline]
        entity_types = set(e["type"] for e in narrative.entities_involved)

        # Phishing patterns
        if "web_search" in event_types and ("email" in entity_types or "url" in entity_types):
            patterns["phishing"] += 0.3
        if any("phishing" in d for d in descriptions):
            patterns["phishing"] += 0.5

        # Social engineering
        if any(keyword in " ".join(descriptions) for keyword in ["pretend", "impersonate", "fake"]):
            patterns["social_engineering"] += 0.5

        # Harassment
        if any(keyword in " ".join(descriptions) for keyword in ["threat", "harass", "abuse"]):
            patterns["harassment"] += 0.6

        # Credential compromise
        if "breach_data" in event_types and "email" in entity_types:
            patterns["credential_compromise"] += 0.7

        # Data exfiltration
        if any(keyword in " ".join(descriptions) for keyword in ["data", "dump", "leak"]):
            patterns["data_exfiltration"] += 0.4

        # Normalize to 0.0-1.0
        for pattern in patterns:
            patterns[pattern] = min(1.0, patterns[pattern])

        top_pattern = max(patterns.items(), key=lambda x: x[1])
        if top_pattern[1] > 0:
            narrative.pattern_type = top_pattern[0]

        return patterns

    def assess_threat(self, narrative: Narrative) -> str:
        """
        Assess overall threat level of narrative.
        
        Returns: "info", "low", "medium", "high", "critical"
        """
        threat_score = 0.0

        # Factor 1: Number of events
        threat_score += min(0.2, len(narrative.timeline) * 0.02)

        # Factor 2: Pattern type
        pattern_scores = self.detect_patterns(narrative)
        max_pattern = max(pattern_scores.values())
        threat_score += max_pattern * 0.4

        # Factor 3: Evidence confidence
        avg_confidence = (
            sum(e.confidence for e in narrative.timeline) / len(narrative.timeline)
            if narrative.timeline else 0
        )
        threat_score += avg_confidence * 0.2

        # Factor 4: Unique entities (more entities = more complex = higher threat)
        threat_score += min(0.2, len(narrative.entities_involved) * 0.01)

        # Classify
        if threat_score < 0.2:
            return "info"
        elif threat_score < 0.4:
            return "low"
        elif threat_score < 0.6:
            return "medium"
        elif threat_score < 0.8:
            return "high"
        else:
            return "critical"

    def generate_narrative_summary(self, narrative: Narrative) -> str:
        """
        Generate human-readable summary of narrative.
        """
        lines = [
            f"=== {narrative.title} ===",
            f"Events: {len(narrative.timeline)}",
            f"Entities: {len(narrative.entities_involved)}",
            f"Pattern: {narrative.pattern_type}",
            f"Threat: {narrative.threat_assessment}",
            "",
            "Timeline:",
        ]

        for event in narrative.timeline:
            lines.append(
                f"  [{event.timestamp}] {event.event_type.upper()}: {event.title}"
            )

        lines.extend([
            "",
            "Entities Involved:",
        ])

        for entity in narrative.entities_involved[:10]:
            lines.append(f"  - {entity['type']}: {entity['value']}")

        return "\n".join(lines)

    def _assess_event_threat(self, item: Dict) -> str:
        """Assess threat level of single evidence item."""
        source_type = item.get("source_type", "")
        tags = item.get("tags", [])
        body = (item.get("content", {}).get("body", "") or "").lower()

        # Breach data is always high threat
        if source_type == "breach_data":
            return "high"

        # Look for threat keywords
        threat_keywords = ["malware", "ransomware", "trojan", "phishing", "exploit", "crack"]
        if any(keyword in body for keyword in threat_keywords):
            return "high"

        # Suspicious tags
        if any(tag in tags for tag in ["suspicious", "malicious", "compromised"]):
            return "medium"

        return "info"
