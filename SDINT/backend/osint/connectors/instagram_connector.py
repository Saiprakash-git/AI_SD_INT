"""
Instagram public profile connector (public profiles only).
"""

import requests
from datetime import datetime, timezone


class InstagramConnector:
    name = "instagram_public"
    supports_types = ["username", "name", "email"]

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15",
        "Accept": "*/*",
        "X-IG-App-ID": "936619743392459",
    }

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
                candidates = ["".join(parts), f"{parts[0]}_{parts[-1]}"]

        evidence = []
        for username in candidates[:3]:
            user = self._fetch_user(username)
            if not user:
                continue
            evidence.append(EvidenceItem(
                connector_name=self.name,
                source_url=f"https://www.instagram.com/{username}/",
                queried_value=username,
                queried_type="username",
                raw_text=f"Instagram profile {user.get('full_name', username)} {user.get('biography', '')}",
                extracted_fields={
                    "username": username,
                    "platform": "Instagram",
                    "full_name": user.get("full_name"),
                    "bio": user.get("biography"),
                    "followers": (user.get("edge_followed_by") or {}).get("count"),
                    "following": (user.get("edge_follow") or {}).get("count"),
                    "post_count": (user.get("edge_owner_to_timeline_media") or {}).get("count"),
                    "is_private": user.get("is_private"),
                    "is_verified": user.get("is_verified"),
                    "profile_url": f"https://www.instagram.com/{username}/",
                },
                collected_at=datetime.now(timezone.utc),
                confidence=0.78 if not user.get("is_private") else 0.55,
                license_note="Public Instagram profile data",
                session_id=session_id,
            ))
        return evidence

    def _fetch_user(self, username: str):
        try:
            url = f"https://i.instagram.com/api/v1/users/web_profile_info/?username={username}"
            resp = requests.get(url, headers=self.HEADERS, timeout=15)
            if resp.status_code != 200:
                return None
            return (resp.json().get("data") or {}).get("user")
        except Exception:
            return None

