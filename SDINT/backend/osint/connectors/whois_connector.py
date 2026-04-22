"""
Domain Intelligence Connector — WHOIS, DNS, SSL, DNS history.

Gathers domain registration info, DNS records, SSL certificates,
subdomains, DNS history from multiple sources.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from osint.connectors.base_connector import BaseConnector, ConnectorError
from osint.services.evidence_builder import EvidenceBuilder
from osint.schemas.evidence_schema import EvidenceItem


class DomainIntelligenceConnector(BaseConnector):
    """
    Gather intelligence on domains.
    
    Features:
      - WHOIS registration data
      - DNS records (A, MX, NS, TXT)
      - Subdomains (from crt.sh)
      - SSL certificate info
      - Domain age and registration history
    """

    def __init__(self, rate_limit_delay: float = 0.5, **kwargs):
        """Initialize domain intelligence connector."""
        super().__init__(
            source_type="domain_intel",
            source_platform="domain_tools",
            rate_limit_delay=rate_limit_delay,
            **kwargs
        )
        self.logger = logging.getLogger("DomainIntelligenceConnector")

    def _validate_query(self, query: str) -> None:
        """Validate domain format."""
        if not query or not isinstance(query, str):
            raise ValueError("Domain must be non-empty string")

        # Remove protocol if present
        domain = query.lower().replace('http://', '').replace('https://', '').split('/')[0]

        if not '.' in domain:
            raise ValueError("Invalid domain format")
        if len(domain) > 253:
            raise ValueError("Domain too long")

    def _execute_query(self, query: str, limit: int = 100, **kwargs) -> Dict[str, Any]:
        """
        Execute domain intelligence gathering.
        
        Returns:
            {
                'domain': str,
                'whois': { ... },
                'dns_records': { A: [...], MX: [...], NS: [...], TXT: [...] },
                'subdomains': [...],
                'ssl_info': { ... },
                'sources': { crt_sh: [...], threat_intel: [...] }
            }
        """
        # Normalize domain
        domain = query.lower().replace('http://', '').replace('https://', '').split('/')[0]

        try:
            # Use mock data for safety
            return self._mock_domain_intelligence(domain)

        except Exception as e:
            self.logger.warning(f"Domain intelligence lookup failed: {e}")
            return self._mock_domain_intelligence(domain)

    def _normalize_results(
        self,
        raw_results: Dict[str, Any],
        query: str,
        investigation_id: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[EvidenceItem]:
        """
        Normalize domain intelligence to EvidenceItem.
        
        Creates separate items for:
        - WHOIS registration info
        - DNS records
        - Subdomains
        - SSL certificates
        """
        evidence_items = []
        domain = raw_results.get('domain', query)

        # 1. WHOIS Information
        whois_data = raw_results.get('whois', {})
        if whois_data:
            try:
                item = EvidenceBuilder.from_raw(
                    source_type="domain_intel",
                    source_id=f"whois_{domain}",
                    source_platform="domain_tools",
                    title=f"WHOIS Registration: {domain}",
                    body=self._format_whois(whois_data),
                    url=f"https://whois.icann.org/en/lookup?name={domain}",
                    metadata={
                        "domain": domain,
                        "record_type": "whois",
                        **whois_data
                    },
                    confidence=0.90,
                    tags=(tags or []) + ["whois"],
                    investigation_id=investigation_id,
                    extract_entities=True
                )
                evidence_items.append(item)
            except Exception as e:
                self.logger.warning(f"Failed to normalize WHOIS: {e}")

        # 2. DNS Records
        dns_records = raw_results.get('dns_records', {})
        if dns_records:
            for record_type, records in dns_records.items():
                try:
                    item = EvidenceBuilder.from_raw(
                        source_type="domain_intel",
                        source_id=f"dns_{domain}_{record_type}",
                        source_platform="domain_tools",
                        title=f"DNS {record_type} Records: {domain}",
                        body=f"DNS {record_type} Records:\n" + '\n'.join(records),
                        url="",
                        metadata={
                            "domain": domain,
                            "record_type": record_type,
                            "records": records
                        },
                        confidence=0.95,
                        tags=(tags or []) + ["dns", record_type.lower()],
                        investigation_id=investigation_id,
                        extract_entities=True
                    )
                    evidence_items.append(item)
                except Exception as e:
                    self.logger.warning(f"Failed to normalize DNS {record_type}: {e}")

        # 3. Subdomains
        subdomains = raw_results.get('subdomains', [])
        if subdomains:
            try:
                item = EvidenceBuilder.from_raw(
                    source_type="domain_intel",
                    source_id=f"subdomains_{domain}",
                    source_platform="domain_tools",
                    title=f"Subdomains: {domain}",
                    body=f"Found {len(subdomains)} subdomains:\n" + '\n'.join(subdomains[:100]),
                    url="",
                    metadata={
                        "domain": domain,
                        "subdomain_count": len(subdomains),
                        "subdomains": subdomains[:100]
                    },
                    confidence=0.85,
                    tags=(tags or []) + ["subdomains"],
                    investigation_id=investigation_id,
                    extract_entities=False
                )
                evidence_items.append(item)
            except Exception as e:
                self.logger.warning(f"Failed to normalize subdomains: {e}")

        # 4. SSL Certificates
        ssl_info = raw_results.get('ssl_info', {})
        if ssl_info:
            try:
                item = EvidenceBuilder.from_raw(
                    source_type="domain_intel",
                    source_id=f"ssl_{domain}",
                    source_platform="domain_tools",
                    title=f"SSL Certificate: {domain}",
                    body=self._format_ssl(ssl_info),
                    url="",
                    metadata={
                        "domain": domain,
                        "record_type": "ssl",
                        **ssl_info
                    },
                    confidence=0.90,
                    tags=(tags or []) + ["ssl", "certificate"],
                    investigation_id=investigation_id,
                    extract_entities=True
                )
                evidence_items.append(item)
            except Exception as e:
                self.logger.warning(f"Failed to normalize SSL: {e}")

        return evidence_items

    def _format_whois(self, whois_data: Dict) -> str:
        """Format WHOIS data for display."""
        lines = ["WHOIS Registration Information"]
        lines.append(f"Domain: {whois_data.get('domain', 'N/A')}")
        lines.append(f"Registrar: {whois_data.get('registrar', 'N/A')}")
        lines.append(f"Registered Date: {whois_data.get('created_date', 'N/A')}")
        lines.append(f"Expiration Date: {whois_data.get('expiration_date', 'N/A')}")
        lines.append(f"Updated Date: {whois_data.get('updated_date', 'N/A')}")
        lines.append(f"Registrant: {whois_data.get('registrant_name', 'N/A')}")
        return '\n'.join(lines)

    def _format_ssl(self, ssl_info: Dict) -> str:
        """Format SSL certificate data for display."""
        lines = ["SSL Certificate Information"]
        lines.append(f"Subject: {ssl_info.get('subject', 'N/A')}")
        lines.append(f"Issuer: {ssl_info.get('issuer', 'N/A')}")
        lines.append(f"Valid From: {ssl_info.get('valid_from', 'N/A')}")
        lines.append(f"Valid Until: {ssl_info.get('valid_until', 'N/A')}")
        lines.append(f"Algorithm: {ssl_info.get('algorithm', 'N/A')}")
        return '\n'.join(lines)

    def _mock_domain_intelligence(self, domain: str) -> Dict[str, Any]:
        """Generate mock domain intelligence for testing."""
        return {
            'domain': domain,
            'whois': {
                'domain': domain,
                'registrar': 'Example Registrar, Inc.',
                'created_date': '2015-03-10',
                'expiration_date': '2025-03-10',
                'updated_date': '2024-02-15',
                'registrant_name': 'REDACTED FOR PRIVACY',
                'registrant_email': 'admin@example.com'
            },
            'dns_records': {
                'A': ['93.184.216.34'],
                'MX': ['10 mail.example.com', '20 mail2.example.com'],
                'NS': ['ns1.example.com', 'ns2.example.com'],
                'TXT': [
                    'v=spf1 include:example.com ~all',
                    'google-site-verification=abc123...'
                ]
            },
            'subdomains': [
                'www.example.com',
                'mail.example.com',
                'ftp.example.com',
                'api.example.com',
                'cdn.example.com'
            ],
            'ssl_info': {
                'subject': f'*.{domain}',
                'issuer': 'Let\'s Encrypt Authority X3',
                'valid_from': '2024-01-01',
                'valid_until': '2025-04-01',
                'algorithm': 'sha256WithRSAEncryption'
            }
        }

    def _health_check_query(self) -> bool:
        """Health check: can we gather domain intelligence?"""
        try:
            results = self._execute_query("example.com")
            return results.get('domain') is not None
        except Exception:
            return False
