"""
crt.sh certificate transparency connector.

Free, no-key domain pivot source for subdomains, organizations, and certificate
identity fields exposed through public CT logs.
"""

import re
import time
from datetime import datetime, timezone
from urllib.parse import quote

import requests


class CrtShConnector:
    name = "crtsh"
    supports_types = ["domain", "email", "name"]

    HEADERS = {"User-Agent": "SDINT-OSINT/1.0"}

    def run(self, pivot: dict) -> list:
        from osint.models.evidence import EvidenceItem

        pivot_type = pivot.get("type", "")
        value = (pivot.get("value", "") or "").strip()
        session_id = pivot.get("session_id", "")
        context = pivot.get("context", {}) or {}
        if not value:
            return []

        domain = self._domain_from_value(pivot_type, value)
        if not domain and context.get("bio"):
            domain = self._first_domain(context.get("bio", ""))
        if not domain:
            return []

        rows = self._query(domain)
        if not rows:
            return []

        subdomains = set()
        organizations = set()
        issuers = set()
        for row in rows:
            name_value = row.get("name_value") or ""
            for host in re.split(r"\s+", name_value):
                clean = host.strip().lower().lstrip("*.").rstrip(".")
                if clean.endswith(domain.lower()) and clean != domain.lower():
                    subdomains.add(clean)
            if row.get("organization_name"):
                organizations.add(row["organization_name"].strip())
            if row.get("issuer_name"):
                issuers.add(row["issuer_name"].strip())

        if not subdomains and not organizations:
            return []

        preview = sorted(subdomains)[:25]
        return [EvidenceItem(
            connector_name=self.name,
            source_url=f"https://crt.sh/?q={quote(domain)}",
            queried_value=domain,
            queried_type="domain",
            raw_text=(
                f"crt.sh found {len(subdomains)} subdomain(s) for {domain}: "
                f"{', '.join(preview[:10])}"
            ),
            extracted_fields={
                "domain": domain,
                "domains": sorted(subdomains)[:100],
                "organizations": sorted(organizations)[:20],
                "issuers": sorted(issuers)[:20],
                "platform": "crt.sh",
                "profile_url": f"https://crt.sh/?q={quote(domain)}",
            },
            collected_at=datetime.now(timezone.utc),
            confidence=0.88,
            license_note="Public certificate transparency logs via crt.sh",
            session_id=session_id,
        )]

    def _query(self, domain: str) -> list:
        try:
            time.sleep(1.0)
            resp = requests.get(
                "https://crt.sh/",
                params={"q": f"%.{domain}", "output": "json"},
                headers=self.HEADERS,
                timeout=20,
            )
            if resp.status_code != 200:
                return []
            data = resp.json()
            return data if isinstance(data, list) else []
        except Exception as exc:
            print(f"crt.sh error: {exc}")
            return []

    def _domain_from_value(self, pivot_type: str, value: str) -> str:
        if pivot_type == "domain":
            return value.lower().strip()
        if pivot_type == "email" and "@" in value:
            return value.split("@", 1)[1].lower().strip()
        return self._first_domain(value)

    def _first_domain(self, text: str) -> str:
        match = re.search(r"\b(?:[a-z0-9-]+\.)+[a-z]{2,}\b", text.lower())
        return match.group(0) if match else ""
