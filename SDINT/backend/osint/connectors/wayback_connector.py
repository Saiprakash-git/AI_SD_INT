"""
Wayback Machine CDX connector.

Looks up historical snapshots for URL/domain/name pivots and summarizes older
known URLs that may reveal deleted profiles, old bios, or prior pages.
"""

import re
import time
from datetime import datetime, timezone
from urllib.parse import quote

import requests


class WaybackConnector:
    name = "wayback_cdx"
    supports_types = ["domain", "username", "name", "email"]

    HEADERS = {"User-Agent": "SDINT-OSINT/1.0"}

    def run(self, pivot: dict) -> list:
        from osint.models.evidence import EvidenceItem

        pivot_type = pivot.get("type", "")
        value = (pivot.get("value", "") or "").strip()
        session_id = pivot.get("session_id", "")
        context = pivot.get("context", {}) or {}
        targets = self._targets(pivot_type, value, context)
        evidence = []

        for target in targets[:5]:
            snapshots = self._cdx(target)
            if not snapshots:
                continue
            urls = []
            years = set()
            for row in snapshots:
                if len(row) < 3:
                    continue
                timestamp, original = row[1], row[2]
                urls.append(original)
                if timestamp:
                    years.add(timestamp[:4])
            evidence.append(EvidenceItem(
                connector_name=self.name,
                source_url=f"https://web.archive.org/cdx?url={quote(target)}",
                queried_value=value,
                queried_type=pivot_type,
                raw_text=f"Wayback has {len(snapshots)} snapshot(s) for {target}; years: {', '.join(sorted(years)[:10])}",
                extracted_fields={
                    "platform": "Wayback Machine",
                    "target": target,
                    "urls": urls[:25],
                    "snapshot_count": len(snapshots),
                    "years": sorted(years),
                    "profile_url": f"https://web.archive.org/web/*/{target}",
                },
                collected_at=datetime.now(timezone.utc),
                confidence=0.76,
                license_note="Public Internet Archive CDX API",
                session_id=session_id,
            ))
        return evidence

    def _cdx(self, target: str) -> list:
        try:
            time.sleep(0.8)
            resp = requests.get(
                "https://web.archive.org/cdx",
                params={
                    "url": target,
                    "output": "json",
                    "fl": "timestamp,original,statuscode,mimetype",
                    "filter": "statuscode:200",
                    "collapse": "urlkey",
                    "limit": 20,
                },
                headers=self.HEADERS,
                timeout=20,
            )
            if resp.status_code != 200:
                return []
            data = resp.json()
            return data[1:] if isinstance(data, list) and len(data) > 1 else []
        except Exception as exc:
            print(f"Wayback error for {target}: {exc}")
            return []

    def _targets(self, pivot_type: str, value: str, context: dict) -> list:
        targets = []
        if pivot_type == "domain":
            targets.extend([value, f"*.{value}"])
        elif pivot_type == "email" and "@" in value:
            domain = value.split("@", 1)[1]
            targets.extend([domain, f"*.{domain}"])
        elif pivot_type == "username":
            clean = value.lstrip("@")
            targets.extend([
                f"twitter.com/{clean}",
                f"x.com/{clean}",
                f"instagram.com/{clean}",
                f"github.com/{clean}",
                f"reddit.com/user/{clean}",
            ])
        elif pivot_type == "name":
            slug = re.sub(r"\s+", "", value.strip().lower())
            if slug:
                targets.extend([f"linkedin.com/in/{slug}", f"twitter.com/{slug}", f"instagram.com/{slug}"])
        bio = context.get("bio", "")
        targets.extend(re.findall(r"https?://[^\s)]+", bio))
        return list(dict.fromkeys(t for t in targets if t))
