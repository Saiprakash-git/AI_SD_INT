"""
Base Connector — Abstract parent for all data source connectors.

Features:
  - Automatic retry logic with exponential backoff
  - Rate limiting (configurable)
  - Timeout protection
  - Error handling and logging
  - Results normalization to EvidenceItem
"""

import time
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime

from osint.schemas.evidence_schema import EvidenceItem


class ConnectorError(Exception):
    """Base exception for connector errors."""
    pass


class ConnectorRetryError(ConnectorError):
    """Max retries exceeded."""
    pass


class ConnectorTimeoutError(ConnectorError):
    """Operation timeout."""
    pass


class BaseConnector(ABC):
    """
    Abstract base class for all connectors.
    
    Inheritors must implement:
      - _validate_query(): Check query is valid format
      - _execute_query(): Perform actual search/lookup
      - _normalize_results(): Convert raw results to EvidenceItem list
    """

    def __init__(
        self,
        source_type: str,
        source_platform: str,
        rate_limit_delay: float = 0.5,
        max_retries: int = 3,
        timeout: int = 30,
        batch_mode: bool = False
    ):
        """
        Args:
            source_type: Type of source (e.g., 'web_search', 'username_search')
            source_platform: Platform name (e.g., 'duckduckgo', 'sherlock')
            rate_limit_delay: Seconds between requests (avoid rate limiting)
            max_retries: Number of retries on failure
            timeout: Request timeout in seconds
            batch_mode: Whether to batch results before normalization
        """
        self.source_type = source_type
        self.source_platform = source_platform
        self.rate_limit_delay = rate_limit_delay
        self.max_retries = max_retries
        self.timeout = timeout
        self.batch_mode = batch_mode
        
        self.logger = logging.getLogger(self.__class__.__name__)
        self._last_request_time = 0

    def search(
        self,
        query: str,
        limit: int = 50,
        investigation_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        **kwargs
    ) -> List[EvidenceItem]:
        """
        Perform search with retry logic and normalization.
        
        Args:
            query: Search query
            limit: Max results to return
            investigation_id: Link results to investigation
            tags: Additional tags for evidence items
            **kwargs: Connector-specific options
            
        Returns:
            List[EvidenceItem] normalized from raw results
        """
        # Validate query
        try:
            self._validate_query(query)
        except Exception as e:
            self.logger.error(f"Invalid query: {e}")
            raise

        # Prepare tags
        if tags is None:
            tags = []
        tags.extend([self.source_type, self.source_platform])

        # Retry loop with exponential backoff
        last_error = None
        for attempt in range(self.max_retries):
            try:
                # Rate limiting
                self._apply_rate_limit()

                # Execute query
                start_time = time.time()
                raw_results = self._execute_query(query, limit, **kwargs)
                elapsed = time.time() - start_time

                if elapsed > self.timeout:
                    raise ConnectorTimeoutError(
                        f"Query took {elapsed:.1f}s (timeout: {self.timeout}s)"
                    )

                # Normalize to EvidenceItem
                evidence_items = self._normalize_results(
                    raw_results,
                    query=query,
                    investigation_id=investigation_id,
                    tags=tags
                )

                self.logger.info(
                    f"Query '{query}' returned {len(evidence_items)} "
                    f"evidence items (attempt {attempt + 1}/{self.max_retries})"
                )
                return evidence_items

            except ConnectorTimeoutError as e:
                last_error = e
                self.logger.warning(f"Timeout on attempt {attempt + 1}: {e}")
                if attempt < self.max_retries - 1:
                    backoff = 2 ** attempt  # 1, 2, 4, 8...
                    self.logger.info(f"Retrying in {backoff}s...")
                    time.sleep(backoff)
            except Exception as e:
                last_error = e
                self.logger.warning(f"Error on attempt {attempt + 1}: {e}")
                if attempt < self.max_retries - 1:
                    backoff = 2 ** attempt
                    self.logger.info(f"Retrying in {backoff}s...")
                    time.sleep(backoff)

        # All retries exhausted
        raise ConnectorRetryError(
            f"Query '{query}' failed after {self.max_retries} attempts. "
            f"Last error: {last_error}"
        )

    def _apply_rate_limit(self) -> None:
        """Apply rate limiting between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self._last_request_time = time.time()

    @abstractmethod
    def _validate_query(self, query: str) -> None:
        """
        Validate query format.
        
        Raises:
            ValueError: If query invalid
        """
        pass

    @abstractmethod
    def _execute_query(self, query: str, limit: int, **kwargs) -> Any:
        """
        Execute the actual search/lookup.
        
        Returns:
            Raw results from connector (format varies)
        """
        pass

    @abstractmethod
    def _normalize_results(
        self,
        raw_results: Any,
        query: str,
        investigation_id: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[EvidenceItem]:
        """
        Convert raw results to EvidenceItem list.
        
        Must use EvidenceBuilder.from_raw() for consistency.
        """
        pass

    def health_check(self) -> Dict[str, Any]:
        """
        Check connector health/availability.
        
        Returns:
            {
                'status': 'healthy'|'degraded'|'offline',
                'message': str,
                'last_request': timestamp,
                'error': Optional[str]
            }
        """
        try:
            # Try a simple test query (connector-specific)
            test_result = self._health_check_query()
            return {
                'status': 'healthy' if test_result else 'degraded',
                'message': 'Connector is operational',
                'last_request': datetime.utcnow().isoformat(),
                'error': None
            }
        except Exception as e:
            return {
                'status': 'offline',
                'message': f'Connector health check failed',
                'last_request': datetime.utcnow().isoformat(),
                'error': str(e)
            }

    def _health_check_query(self) -> bool:
        """
        Connector-specific health check.
        
        Default: return True. Override to implement specific checks.
        """
        return True
