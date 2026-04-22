"""
MODULE 2 — Connectors

Multi-source data collection connectors for the OSINT platform.

Exports:
  - BaseConnector: Abstract base class for all connectors
  - DuckDuckGoConnector: Web search
  - SherlockConnector: Cross-platform username search
  - HIBPConnector: Breach data lookup
  - DomainIntelligenceConnector: WHOIS, DNS, SSL info
"""

from osint.connectors.base_connector import (
    BaseConnector,
    ConnectorError,
    ConnectorRetryError,
    ConnectorTimeoutError,
)

from osint.connectors.duckduckgo_connector import DuckDuckGoConnector
from osint.connectors.sherlock_connector import SherlockConnector
from osint.connectors.hibp_connector import HIBPConnector
from osint.connectors.whois_connector import DomainIntelligenceConnector

__all__ = [
    # Base classes
    "BaseConnector",
    "ConnectorError",
    "ConnectorRetryError",
    "ConnectorTimeoutError",
    # Connectors
    "DuckDuckGoConnector",
    "SherlockConnector",
    "HIBPConnector",
    "DomainIntelligenceConnector",
]
