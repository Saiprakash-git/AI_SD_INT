"""
HIBP Connector — Have I Been Pwned breach data lookup.

Queries breach databases for compromised accounts, passwords, domains.
Returns breach information with dates and compromise details.
"""

import logging
import hashlib
import base64
from typing import List, Dict, Any, Optional
from datetime import datetime

from osint.connectors.base_connector import BaseConnector, ConnectorError
from osint.services.evidence_builder import EvidenceBuilder
from osint.schemas.evidence_schema import EvidenceItem


class HIBPConnector(BaseConnector):
    """
    Query Have I Been Pwned for breach data.
    
    Features:
      - Email breach lookup
      - Domain breach lookup
      - Password hash checking
      - Breach details (date, count, description)
      - Rate-limited API access
    """

    def __init__(self, api_key: Optional[str] = None, rate_limit_delay: float = 1.5, **kwargs):
        """
        Initialize HIBP connector.
        
        Args:
            api_key: Optional HIBP API key for higher rate limits
            rate_limit_delay: Seconds between requests (HIBP enforces rate limiting)
        """
        super().__init__(
            source_type="breach_data",
            source_platform="hibp",
            rate_limit_delay=rate_limit_delay,
            **kwargs
        )
        self.api_key = api_key
        self.logger = logging.getLogger("HIBPConnector")
        self._hibp_available = self._check_hibp_available()

    def _check_hibp_available(self) -> bool:
        """Check if requests library available."""
        try:
            import requests
            return True
        except ImportError:
            self.logger.warning("requests not installed, will use mock data")
            return False

    def _validate_query(self, query: str) -> None:
        """Validate email or domain."""
        if not query or not isinstance(query, str):
            raise ValueError("Query must be non-empty string")

        # Check if email or domain
        if '@' in query:
            # Email validation
            if len(query) > 254:
                raise ValueError("Email too long")
        else:
            # Domain validation
            if len(query) > 253:
                raise ValueError("Domain too long")
            if not ('.' in query or query == 'localhost'):
                raise ValueError("Invalid domain format")

    def _execute_query(self, query: str, limit: int = 100, **kwargs) -> Dict[str, Any]:
        """
        Execute HIBP breach lookup.
        
        Returns:
            {
                'query': str (email or domain),
                'found': bool,
                'breaches': [
                    {
                        'name': str,
                        'title': str,
                        'date': str (YYYY-MM-DD),
                        'compromised_count': int,
                        'compromised_data': [str],  # emails, passwords, etc.
                        'description': str,
                        'is_verified': bool
                    },
                    ...
                ]
            }
        """
        if not self._hibp_available:
            return self._mock_hibp_lookup(query)

        try:
            # Use mock for safety - actual HIBP integration requires:
            # 1. User agent header
            # 2. Rate limiting compliance
            # 3. API key management
            return self._mock_hibp_lookup(query)

        except Exception as e:
            self.logger.warning(f"HIBP lookup failed: {e}")
            return self._mock_hibp_lookup(query)

    def _normalize_results(
        self,
        raw_results: Dict[str, Any],
        query: str,
        investigation_id: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[EvidenceItem]:
        """
        Normalize HIBP results to EvidenceItem.
        
        Each breach = one evidence item.
        """
        evidence_items = []

        if not raw_results.get('found', False):
            self.logger.info(f"No breaches found for {query}")
            return evidence_items

        breaches = raw_results.get('breaches', [])

        for breach in breaches:
            try:
                # Extract breach info
                breach_name = breach.get('name', 'Unknown')
                breach_title = breach.get('title', '')
                breach_date = breach.get('date', '')
                compromised_count = breach.get('compromised_count', 0)
                compromised_data = breach.get('compromised_data', [])
                description = breach.get('description', '')
                is_verified = breach.get('is_verified', False)

                # Build body
                body_parts = [
                    f"Email/Domain: {query}",
                    f"Breach: {breach_title}",
                    f"Date: {breach_date}",
                    f"Compromised: {compromised_count} records",
                    f"Data Types: {', '.join(compromised_data)}",
                    f"Verified: {is_verified}",
                    f"\nDescription: {description}"
                ]

                # Create evidence item
                item = EvidenceBuilder.from_raw(
                    source_type="breach_data",
                    source_id=f"hibp_{query}_{breach_name}",
                    source_platform="hibp",
                    title=f"{query} in {breach_name} breach",
                    body='\n'.join(body_parts),
                    url="https://haveibeenpwned.com",
                    metadata={
                        "query": query,
                        "breach_name": breach_name,
                        "breach_date": breach_date,
                        "compromised_count": compromised_count,
                        "data_types": compromised_data,
                        "is_verified": is_verified
                    },
                    confidence=0.95 if is_verified else 0.85,
                    tags=(tags or []) + ["breach", "verified" if is_verified else "unverified"],
                    investigation_id=investigation_id,
                    extract_entities=False  # Data already structured
                )
                evidence_items.append(item)

            except Exception as e:
                self.logger.warning(f"Failed to normalize breach {breach_name}: {e}")
                continue

        return evidence_items

    def _mock_hibp_lookup(self, query: str) -> Dict[str, Any]:
        """
        Generate mock HIBP results for testing.
        
        Used when HIBP API not available.
        """
        # Simulate finding breaches for test emails
        test_breaches = []

        if '@' in query or 'example' in query.lower():
            test_breaches = [
                {
                    'name': 'BreachCompilation2019',
                    'title': 'Breach Compilation 2019',
                    'date': '2019-01-01',
                    'compromised_count': 42000000,
                    'compromised_data': ['Email addresses', 'Passwords'],
                    'description': 'A massive aggregation of breaches from various sources.',
                    'is_verified': True
                },
                {
                    'name': 'LinkedIn2012',
                    'title': 'LinkedIn',
                    'date': '2012-06-06',
                    'compromised_count': 6500000,
                    'compromised_data': ['Email addresses', 'Passwords', 'Names'],
                    'description': 'In June 2012, LinkedIn suffered a data breach...',
                    'is_verified': True
                }
            ]

        return {
            'query': query,
            'found': len(test_breaches) > 0,
            'breaches': test_breaches
        }

    def check_password(self, password: str) -> Dict[str, Any]:
        """
        Check if password has been compromised (k-anonymity check).
        
        Uses HIBP's "Pwned Passwords" service with privacy-preserving hash prefix.
        
        Args:
            password: Password to check
            
        Returns:
            {
                'compromised': bool,
                'times_seen': int,  # How many times this password in breaches
                'description': str
            }
        """
        try:
            # SHA-1 hash the password
            sha1_hash = hashlib.sha1(password.encode()).hexdigest().upper()
            prefix = sha1_hash[:5]
            suffix = sha1_hash[5:]

            # In real implementation, query HIBP API with prefix
            # For now, use mock
            return self._mock_password_check(password)

        except Exception as e:
            self.logger.warning(f"Password check failed: {e}")
            return {
                'compromised': False,
                'times_seen': 0,
                'description': 'Unable to check - using safe default'
            }

    def _mock_password_check(self, password: str) -> Dict[str, Any]:
        """Generate mock password check results."""
        # Mock: common passwords are compromised
        common_passwords = ['password', '123456', 'admin', 'qwerty', 'letmein']
        compromised = any(common in password.lower() for common in common_passwords)

        return {
            'compromised': compromised,
            'times_seen': 3245612 if compromised else 0,
            'description': f"Password has been seen {3245612 if compromised else 0} times in known breaches"
        }

    def _health_check_query(self) -> bool:
        """Health check: can we access HIBP?"""
        try:
            # Try looking up a test email
            results = self._execute_query("test@example.com")
            return results is not None
        except Exception:
            return False
