"""
Nitter connector for public X/Twitter profile discovery.
Falls back silently if instances are unavailable.
"""

import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone


NITTER_INSTANCES = [
    "https://nitter.net",
    "https://nitter.privacydev.net",
    "https://nitter.poast.org",
]


class NitterConnector:
    name = "nitter_twitter"
    supports_types = ["username", "name", "email"]

    HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; SDINT/1.0)"}

    def run(self, pivot: dict) -> list:
        from osint.models.evidence import EvidenceItem

        value = (pivot.get("value", "") or "").strip()
        pivot_type = pivot.get("type", "")
        session_id = pivot.get("session_id", "")
        if not value:
            return []

        candidates = []
        if pivot_type == "username":
            candidates = [value.lstrip("@")]
        elif pivot_type == "email":
            candidates = [value.split("@")[0].strip().lstrip("@")]
        elif pivot_type == "name":
            parts = [p for p in value.lower().split() if p]
            if parts:
                candidates = ["".join(parts), parts[0]]

        evidence = []
        for username in candidates[:3]:
            if not username:
                continue
            profile = self._fetch_profile(username)
            if not profile:
                continue
            evidence.append(EvidenceItem(
                connector_name=self.name,
                source_url=profile["profile_url"],
                queried_value=username,
                queried_type="username",
                raw_text=f"X profile {profile.get('display_name', username)} {profile.get('bio', '')}",
                extracted_fields={
                    "username": username,
                    "platform": "Twitter/X",
                    "display_name": profile.get("display_name"),
                    "bio": profile.get("bio"),
                    "location": profile.get("location"),
                    "profile_url": profile["profile_url"],
                },
                collected_at=datetime.now(timezone.utc),
                confidence=0.72,
                license_note="Public profile via Nitter mirror",
                session_id=session_id,
            ))
        return evidence

    def _fetch_profile(self, username: str):
        for instance in NITTER_INSTANCES:
            try:
                time.sleep(1.0)
                url = f"{instance}/{username}"
                resp = requests.get(url, headers=self.HEADERS, timeout=12)
                if resp.status_code != 200:
                    continue
                soup = BeautifulSoup(resp.text, "html.parser")
                name_el = soup.select_one(".profile-card-fullname")
                bio_el = soup.select_one(".profile-bio")
                loc_el = soup.select_one(".profile-location")
                return {
                    "profile_url": f"https://twitter.com/{username}",
                    "display_name": name_el.get_text(strip=True) if name_el else username,
                    "bio": bio_el.get_text(strip=True) if bio_el else "",
                    "location": loc_el.get_text(strip=True) if loc_el else "",
                }
            except Exception:
                continue
        return None

