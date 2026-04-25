"""
GitHub connector - free tier with unauthenticated access (60 req/hr)
"""

import requests
import os
from datetime import datetime, timezone


class GitHubConnector:
    """GitHub profile and activity search."""
    
    name = "github"
    supports_types = ["username", "name", "email"]
    
    HEADERS = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "OSINT-Research/1.0",
    }
    
    def __init__(self):
        token = os.getenv("GITHUB_TOKEN", "")
        if token:
            self.HEADERS["Authorization"] = f"token {token}"
    
    def run(self, pivot: dict) -> list:
        pivot_type = pivot.get("type")
        pivot_value = pivot.get("value", "")
        session_id = pivot.get("session_id", "")
        evidence = []
        
        if pivot_type == "username":
            evidence += self._get_user_profile(pivot_value, session_id)
        elif pivot_type in ("name", "email"):
            evidence += self._search_users(pivot_value, session_id)
        
        return evidence

    def _get_user_profile(self, username: str, session_id: str) -> list:
        from osint.models.evidence import EvidenceItem
        
        try:
            resp = requests.get(f"https://api.github.com/users/{username}", headers=self.HEADERS, timeout=10)
            if resp.status_code != 200:
                return []
            
            user = resp.json()
            
            # Get recent public events
            events_resp = requests.get(
                f"https://api.github.com/users/{username}/events/public?per_page=5",
                headers=self.HEADERS,
                timeout=10
            )
            events = events_resp.json() if events_resp.status_code == 200 else []
            
            return [EvidenceItem(
                connector_name=self.name,
                source_url=user.get("html_url", ""),
                queried_value=username,
                queried_type="username",
                raw_text=f"GitHub: {user.get('name', username)} — {user.get('bio', '')}",
                extracted_fields={
                    "username": username,
                    "platform": "GitHub",
                    "full_name": user.get("name"),
                    "email": user.get("email"),
                    "bio": user.get("bio"),
                    "location": user.get("location"),
                    "company": user.get("company"),
                    "blog": user.get("blog"),
                    "twitter_username": user.get("twitter_username"),
                    "public_repos": user.get("public_repos"),
                    "followers": user.get("followers"),
                    "profile_url": user.get("html_url"),
                },
                collected_at=datetime.now(timezone.utc),
                confidence=0.92,
                license_note="Public GitHub profile",
                session_id=session_id,
            )]
        except Exception as e:
            print(f"GitHub profile error: {e}")
            return []

    def _search_users(self, query: str, session_id: str) -> list:
        try:
            resp = requests.get(
                "https://api.github.com/search/users",
                params={"q": query, "per_page": 3},
                headers=self.HEADERS,
                timeout=10
            )
            if resp.status_code != 200:
                return []
            
            items = resp.json().get("items", [])
            evidence = []
            for item in items:
                evidence += self._get_user_profile(item["login"], session_id)
            
            return evidence
        except Exception as e:
            print(f"GitHub search error: {e}")
            return []
