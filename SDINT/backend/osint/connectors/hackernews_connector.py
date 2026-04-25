"""
HackerNews connector - free, no auth required
"""

import requests
from datetime import datetime, timezone


class HackerNewsConnector:
    """Search HackerNews for mentions and find user profiles."""
    
    name = "hackernews"
    supports_types = ["username", "name", "email"]
    
    def run(self, pivot: dict) -> list:
        from osint.models.evidence import EvidenceItem
        
        query = pivot.get("value", "")
        session_id = pivot.get("session_id", "")
        evidence = []
        
        # Search posts and comments
        try:
            resp = requests.get(
                "https://hn.algolia.com/api/v1/search",
                params={"query": query, "hitsPerPage": 5},
                timeout=10
            )
            
            if resp.status_code == 200:
                hits = resp.json().get("hits", [])
                for hit in hits:
                    author = hit.get("author", "")
                    evidence.append(EvidenceItem(
                        connector_name=self.name,
                        source_url=f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
                        queried_value=query,
                        queried_type=pivot.get("type"),
                        raw_text=hit.get("story_text") or hit.get("comment_text") or hit.get("title") or "",
                        extracted_fields={
                            "username": author,
                            "platform": "HackerNews",
                            "post_type": hit.get("_tags", [None])[0],
                            "points": hit.get("points"),
                        },
                        collected_at=datetime.now(timezone.utc),
                        confidence=0.75,
                        license_note="Public HackerNews data",
                        session_id=session_id,
                    ))
        except Exception as e:
            print(f"HN search error: {e}")
        
        # If username, get profile
        if pivot.get("type") == "username":
            try:
                profile_resp = requests.get(
                    f"https://hacker-news.firebaseio.com/v0/user/{query}.json",
                    timeout=10
                )
                if profile_resp.status_code == 200 and profile_resp.json():
                    user = profile_resp.json()
                    evidence.append(EvidenceItem(
                        connector_name=self.name,
                        source_url=f"https://news.ycombinator.com/user?id={query}",
                        queried_value=query,
                        queried_type="username",
                        raw_text=f"HN Profile: karma={user.get('karma')}, about={user.get('about', '')}",
                        extracted_fields={
                            "username": query,
                            "platform": "HackerNews",
                            "karma": user.get("karma"),
                            "about": user.get("about", "")[:300],
                        },
                        collected_at=datetime.now(timezone.utc),
                        confidence=0.90,
                        license_note="Public HackerNews profile",
                        session_id=session_id,
                    ))
            except Exception as e:
                print(f"HN profile error: {e}")
        
        return evidence
