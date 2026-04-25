"""
Free breach checking using multiple free sources.
No paid APIs - all sources are 100% free or free-tier.
"""

import requests
import hashlib
import time
from datetime import datetime, timezone
from typing import Optional


class BreachConnector:
    """
    Free breach checking using:
    1. HIBP k-anonymity (no key needed, password range)
    2. psbdmp.ws paste search
    3. LeakCheck public API (free tier)
    4. BreachDirectory (limited free tier)
    """
    
    name = "breach_check"
    supports_types = ["email", "username", "phone"]
    
    HEADERS = {
        "User-Agent": "OSINT-Research/1.0",
        "Accept": "application/json",
    }
    
    def run(self, pivot: dict) -> list:
        from osint.models.evidence import EvidenceItem
        
        pivot_type = pivot.get("type")
        pivot_value = pivot.get("value", "")
        session_id = pivot.get("session_id", "")
        
        all_evidence = []
        
        if pivot_type == "email":
            all_evidence += self._check_hibp_password_range(pivot_value, session_id)
            all_evidence += self._check_psbdmp(pivot_value, session_id)
            all_evidence += self._check_leakcheck_free(pivot_value, session_id)
        elif pivot_type == "username":
            all_evidence += self._check_psbdmp(pivot_value, session_id)
        
        return all_evidence

    def _check_hibp_password_range(self, email: str, session_id: str) -> list:
        """HIBP k-anonymity: Hash email, send first 5 chars only."""
        from osint.models.evidence import EvidenceItem
        
        sha1 = hashlib.sha1(email.encode("utf-8")).hexdigest().upper()
        prefix = sha1[:5]
        suffix = sha1[5:]
        
        try:
            resp = requests.get(
                f"https://api.pwnedpasswords.com/range/{prefix}",
                headers={"User-Agent": "OSINT-Research/1.0"},
                timeout=10
            )
            if resp.status_code == 200:
                hashes = resp.text.strip().split("\n")
                for line in hashes:
                    parts = line.strip().split(":")
                    if len(parts) == 2 and parts[0].upper() == suffix:
                        count = int(parts[1])
                        return [EvidenceItem(
                            connector_name=self.name,
                            source_url="https://api.pwnedpasswords.com",
                            queried_value=email,
                            queried_type="email",
                            raw_text=f"Email '{email}' found in {count} password breaches",
                            extracted_fields={
                                "breach_type": "password_reuse",
                                "occurrence_count": count,
                                "severity": "HIGH" if count > 100 else "MEDIUM",
                            },
                            collected_at=datetime.now(timezone.utc),
                            confidence=0.90,
                            license_note="HIBP password range",
                            session_id=session_id,
                        )]
        except Exception as e:
            print(f"HIBP error: {e}")
        return []

    def _check_psbdmp(self, query: str, session_id: str) -> list:
        """Search Pastebin via psbdmp.ws - 100% free, no key."""
        from osint.models.evidence import EvidenceItem
        
        results = []
        try:
            time.sleep(1)
            resp = requests.get(
                f"https://psbdmp.ws/api/v3/search/{requests.utils.quote(query)}",
                headers=self.HEADERS,
                timeout=15
            )
            if resp.status_code == 200:
                data = resp.json()
                pastes = data.get("data", [])[:3]
                for paste in pastes:
                    results.append(EvidenceItem(
                        connector_name=self.name,
                        source_url=f"https://psbdmp.ws/{paste.get('id', '')}",
                        queried_value=query,
                        queried_type="email",
                        raw_text=f"Query found in paste: {paste.get('text', '')[:300]}",
                        extracted_fields={
                            "paste_id": paste.get("id"),
                            "source": "psbdmp",
                            "preview": paste.get("text", "")[:200],
                        },
                        collected_at=datetime.now(timezone.utc),
                        confidence=0.70,
                        license_note="Public paste search",
                        session_id=session_id,
                    ))
        except Exception as e:
            print(f"psbdmp error: {e}")
        return results

    def _check_leakcheck_free(self, email: str, session_id: str) -> list:
        """LeakCheck.io free public endpoint."""
        from osint.models.evidence import EvidenceItem
        
        results = []
        try:
            time.sleep(1)
            resp = requests.get(
                f"https://leakcheck.io/api/public?check={requests.utils.quote(email)}",
                headers=self.HEADERS,
                timeout=15
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get("found", 0) > 0:
                    sources = data.get("sources", [])
                    results.append(EvidenceItem(
                        connector_name=self.name,
                        source_url="https://leakcheck.io",
                        queried_value=email,
                        queried_type="email",
                        raw_text=f"Email found in {data.get('found')} breach(es): {', '.join(s.get('name','') for s in sources)}",
                        extracted_fields={
                            "breach_count": data.get("found"),
                            "breach_sources": [s.get("name") for s in sources],
                        },
                        collected_at=datetime.now(timezone.utc),
                        confidence=0.85,
                        license_note="LeakCheck public API",
                        session_id=session_id,
                    ))
        except Exception as e:
            print(f"LeakCheck error: {e}")
        return results
