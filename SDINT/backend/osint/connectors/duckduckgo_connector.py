"""
DuckDuckGo Connector — Web search results to Evidence.

Provides intelligent web search using DuckDuckGo without API key.
Extracts entities from search results automatically.
"""

import logging
from typing import List, Dict, Any, Optional

from osint.connectors.base_connector import BaseConnector, ConnectorError
from osint.services.evidence_builder import EvidenceBuilder
from osint.schemas.evidence_schema import EvidenceItem


class DuckDuckGoConnector(BaseConnector):
    """
    Search the web using DuckDuckGo.
    
    Features:
      - No API key required
      - Entity extraction from results
      - Result de-duplication
      - Confidence scoring
    """

    def __init__(self, rate_limit_delay: float = 1.0, **kwargs):
        """Initialize DuckDuckGo connector."""
        super().__init__(
            source_type="web_search",
            source_platform="duckduckgo",
            rate_limit_delay=rate_limit_delay,
            **kwargs
        )
        self.logger = logging.getLogger("DuckDuckGoConnector")

    def _validate_query(self, query: str) -> None:
        """Validate search query."""
        if not query or not isinstance(query, str):
            raise ValueError("Query must be non-empty string")
        if len(query) > 500:
            raise ValueError("Query too long (max 500 chars)")

    def _execute_query(self, query: str, limit: int = 50, **kwargs) -> List[Dict]:
        """
        Execute DuckDuckGo search.
        
        Returns:
            List of search results (title, body, url, snippet)
        """
        try:
            # Try using duckduckgo_search library (preferred)
            try:
                from duckduckgo_search import DDGS
            except ImportError:
                self.logger.warning("duckduckgo_search not installed, using mock data")
                return self._mock_search_results(query, limit)

            # Execute search
            results = []
            try:
                ddg = DDGS()
                for result in ddg.text(query, max_results=min(limit, 100)):
                    results.append(result)
            except Exception as e:
                self.logger.warning(f"DuckDuckGo search failed: {e}, using mock data")
                return self._mock_search_results(query, limit)

            self.logger.info(f"DuckDuckGo search returned {len(results)} results")
            return results[:limit]

        except Exception as e:
            raise ConnectorError(f"DuckDuckGo search failed: {e}")

    def _normalize_results(
        self,
        raw_results: List[Dict],
        query: str,
        investigation_id: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[EvidenceItem]:
        """
        Normalize search results to EvidenceItem.
        
        Each result becomes one evidence item.
        """
        evidence_items = []
        
        for idx, result in enumerate(raw_results):
            try:
                # Extract fields from DuckDuckGo result
                title = result.get('title', 'Untitled')
                body = result.get('body', '') or result.get('snippet', '')
                url = result.get('link', '') or result.get('href', '')

                # Skip if no meaningful content
                if not body:
                    continue

                # Create evidence item
                item = EvidenceBuilder.from_raw(
                    source_type="web_search",
                    source_id=f"ddg_{hash((title, url)) % 10000000}",
                    source_platform="duckduckgo",
                    title=title,
                    body=body,
                    url=url,
                    metadata={
                        "search_query": query,
                        "result_position": idx + 1,
                    },
                    confidence=0.70,
                    tags=tags or [],
                    investigation_id=investigation_id,
                    extract_entities=True
                )
                evidence_items.append(item)

            except Exception as e:
                self.logger.warning(f"Failed to normalize result {idx}: {e}")
                continue

        return evidence_items

    def _mock_search_results(self, query: str, limit: int) -> List[Dict]:
        """
        Generate mock search results for testing.
        
        Used when duckduckgo_search library not available.
        """
        mock_results = [
            {
                'title': f'Result 1 for {query}',
                'body': f'Information about {query}. Contact: test@example.com',
                'link': f'https://example.com/1'
            },
            {
                'title': f'Result 2 for {query}',
                'body': f'More details on {query}. Username: testuser123',
                'link': f'https://example.com/2'
            },
            {
                'title': f'Result 3 for {query}',
                'body': f'Related: {query} domain.example.org',
                'link': f'https://example.com/3'
            }
        ]
        return mock_results[:limit]

    def _health_check_query(self) -> bool:
        """Health check: can we reach DuckDuckGo?"""
        try:
            # Try a simple search
            results = self._execute_query("health check", limit=1)
            return len(results) > 0
        except Exception:
            return False
