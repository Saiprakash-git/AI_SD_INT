"""
HIBP Connector — Breach data lookup using FREE sources only.

Replaces paid HIBP API with:
  1. HIBP k-anonymity password check (SHA1 prefix, always free, no key)
  2. psbdmp.ws paste search (free, no key)
  3. LeakCheck.io public endpoint (free, no key)
All sources return real data — no mock fallback needed.
"""

import logging
import hashlib
import time
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from osint.connectors.base_connector import BaseConnector
from osint.services.evidence_builder import EvidenceBuilder
from osint.schemas.evidence_schema import EvidenceItem


class HIBPConnector(BaseConnector):
    """
    Free breach checking using multiple public sources.
    No API key required for any source.
    """

    def __init__(self, rate_limit_delay: float = 1.5, **kwargs):
        super().__init__(
            source_type="breach_data",
            source_platform="hibp",
            rate_limit_delay=rate_limit_delay,
            **kwargs
        )
        self.logger = logging.getLogger("HIBPConnector")
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "OSINT-Research-Tool/1.0 (educational)",
            "Accept": "application/json",
        })

    def _validate_query(self, query: str) -> None:
        if not query or not isinstance(query, str):
            raise ValueError("Query must be non-empty string")
        if len(query) > 200:
            raise ValueError("Query too long (max 200 chars)")

    def _execute_query(self, query: str, limit: int = 20, **kwargs) -> Dict[str, Any]:
        """
        Run breach checks across all free sources.
        Returns aggregated results dict.
        """
        query = query.strip()
        all_findings = []

        # 1. HIBP k-anonymity password range check (always free, no key)
        pwd_findings = self._check_hibp_password_range(query)
        all_findings.extend(pwd_findings)

        # 2. Pastebin dump search via psbdmp.ws
        paste_findings = self._check_psbdmp(query)
        all_findings.extend(paste_findings)

        # 3. LeakCheck.io public API
        leak_findings = self._check_leakcheck(query)
        all_findings.extend(leak_findings)

        self.logger.info(f"Breach check for '{query}': {len(all_findings)} findings")

        return {
            "query": query,
            "total_findings": len(all_findings),
            "findings": all_findings,
        }

    def _check_hibp_password_range(self, email: str) -> List[dict]:
        """
        HIBP k-anonymity: hash the email, send first 5 chars of SHA1.
        Checks if the email string appears in leaked password databases.
        This endpoint is ALWAYS FREE — no API key needed.
        """
        sha1 = hashlib.sha1(email.encode("utf-8")).hexdigest().upper()
        prefix = sha1[:5]
        suffix = sha1[5:]

        try:
            resp = self.session.get(
                f"https://api.pwnedpasswords.com/range/{prefix}",
                headers={"User-Agent": "OSINT-Research-Tool/1.0"},
                timeout=10
            )
            if resp.status_code == 200:
                for line in resp.text.strip().split("\n"):
                    parts = line.strip().split(":")
                    if len(parts) == 2 and parts[0].upper() == suffix:
                        count = int(parts[1])
                        return [{
                            "source": "hibp_password_range",
                            "source_url": "https://haveibeenpwned.com",
                            "title": f"Breach exposure: {email}",
                            "body": f"The string '{email}' appears {count} time(s) in leaked password databases. "
                                    f"This indicates the email has been used as a password or appears in credential dumps.",
                            "severity": "HIGH" if count > 100 else "MEDIUM",
                            "occurrence_count": count,
                            "confidence": 0.90,
                        }]
        except Exception as e:
            self.logger.debug(f"HIBP range check error: {e}")
        return []

    def _check_psbdmp(self, query: str) -> List[dict]:
        """Search Pastebin dumps via psbdmp.ws — free, no key."""
        results = []
        try:
            time.sleep(1)  # rate limit respect
            resp = self.session.get(
                f"https://psbdmp.ws/api/v3/search/{requests.utils.quote(query)}",
                timeout=15
            )
            if resp.status_code == 200:
                data = resp.json()
                pastes = data if isinstance(data, list) else data.get("data", [])
                for paste in (pastes or [])[:5]:
                    paste_id = paste.get("id", "") if isinstance(paste, dict) else str(paste)
                    results.append({
                        "source": "psbdmp",
                        "source_url": f"https://pastebin.com/{paste_id}",
                        "title": f"Paste dump match: {query}",
                        "body": f"Query '{query}' found in paste {paste_id}. "
                                f"Preview: {paste.get('text', '')[:300] if isinstance(paste, dict) else ''}",
                        "severity": "HIGH",
                        "paste_id": paste_id,
                        "confidence": 0.75,
                    })
        except Exception as e:
            self.logger.debug(f"psbdmp error: {e}")
        return results

    def _check_leakcheck(self, email: str) -> List[dict]:
        """LeakCheck.io free public endpoint — no key, limited results."""
        results = []
        try:
            time.sleep(1)
            resp = self.session.get(
                f"https://leakcheck.io/api/public?check={requests.utils.quote(email)}",
                timeout=15
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get("found", 0) > 0:
                    sources = data.get("sources", [])
                    source_names = [s.get("name", "unknown") for s in sources] if sources else ["unknown"]
                    results.append({
                        "source": "leakcheck",
                        "source_url": "https://leakcheck.io",
                        "title": f"Leak detected: {email}",
                        "body": f"Email '{email}' found in {data.get('found')} breach(es). "
                                f"Sources: {', '.join(source_names)}.",
                        "severity": "HIGH" if data.get("found", 0) > 3 else "MEDIUM",
                        "breach_count": data.get("found"),
                        "breach_sources": source_names,
                        "confidence": 0.85,
                    })
        except Exception as e:
            self.logger.debug(f"LeakCheck error: {e}")
        return results

    def _normalize_results(
        self,
        raw_results: Dict[str, Any],
        query: str,
        investigation_id: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[EvidenceItem]:
        """Convert breach findings to EvidenceItem list."""
        evidence_items = []
        findings = raw_results.get("findings", [])

        for i, finding in enumerate(findings):
            try:
                item = EvidenceBuilder.from_raw(
                    source_type="breach_data",
                    source_id=f"breach_{finding['source']}_{hashlib.md5(f'{query}_{i}'.encode()).hexdigest()[:12]}",
                    source_platform=finding.get("source", "hibp"),
                    title=finding.get("title", f"Breach finding for {query}"),
                    body=finding.get("body", ""),
                    url=finding.get("source_url", ""),
                    metadata={
                        "query": query,
                        "breach_source": finding.get("source"),
                        "severity": finding.get("severity", "MEDIUM"),
                        "occurrence_count": finding.get("occurrence_count"),
                        "breach_count": finding.get("breach_count"),
                        "breach_sources": finding.get("breach_sources"),
                        "paste_id": finding.get("paste_id"),
                    },
                    confidence=finding.get("confidence", 0.70),
                    tags=(tags or []) + ["breach", finding.get("source", "")],
                    investigation_id=investigation_id,
                    extract_entities=True
                )
                evidence_items.append(item)
            except Exception as e:
                self.logger.warning(f"Failed to normalize finding: {e}")

        return evidence_items

    def _health_check_query(self) -> bool:
        """Health check: can we reach the HIBP password range API?"""
        try:
            resp = self.session.get(
                "https://api.pwnedpasswords.com/range/00000",
                timeout=5
            )
            return resp.status_code == 200
        except Exception:
            return False
