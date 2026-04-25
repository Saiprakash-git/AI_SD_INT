"""
Compatibility evidence model used by connector pipeline.

This lightweight class matches the connector constructor shape used across
the session-based OSINT investigation flow.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict


@dataclass
class EvidenceItem:
    connector_name: str
    source_url: str
    queried_value: str
    queried_type: str
    raw_text: str
    extracted_fields: Dict[str, Any] = field(default_factory=dict)
    collected_at: Any = field(default_factory=lambda: datetime.now(timezone.utc))
    confidence: float = 0.5
    license_note: str = ""
    session_id: str = ""

