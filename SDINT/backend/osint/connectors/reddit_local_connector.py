"""
Local Reddit OSINT connector.

Searches SDINT's existing MongoDB posts/comments collections as an OSINT pivot
source, so social-analysis data becomes reusable investigation evidence.
"""

import re
from datetime import datetime, timezone


class RedditLocalConnector:
    name = "reddit_local"
    supports_types = ["username", "name", "email", "domain", "phone"]

    def run(self, pivot: dict) -> list:
        from osint.models.evidence import EvidenceItem

        db = pivot.get("db")
        value = (pivot.get("value", "") or "").strip()
        pivot_type = pivot.get("type", "")
        session_id = pivot.get("session_id", "")
        if db is None or not value:
            return []

        query = self._mongo_query(pivot_type, value)
        evidence = []

        try:
            comments = list(db["comments"].find(query, {"_id": 0}).sort("score", -1).limit(10))
            posts = list(db["posts"].find(query, {"_id": 0}).sort("score", -1).limit(10))
        except Exception as exc:
            print(f"Reddit local query error: {exc}")
            return []

        for comment in comments:
            author = comment.get("author", "")
            text = comment.get("text") or comment.get("body") or ""
            post_id = comment.get("post_id", "")
            evidence.append(EvidenceItem(
                connector_name=self.name,
                source_url=f"https://www.reddit.com/comments/{post_id}" if post_id else "",
                queried_value=value,
                queried_type=pivot_type,
                raw_text=text[:1000],
                extracted_fields={
                    "username": author,
                    "platform": "Reddit",
                    "post_id": post_id,
                    "comment_id": comment.get("comment_id"),
                    "subreddit": comment.get("subreddit"),
                    "score": comment.get("score"),
                    "sentiment_label": comment.get("sentiment_label"),
                    "is_toxic": comment.get("is_toxic"),
                    "profile_url": f"https://www.reddit.com/user/{author}" if author else "",
                },
                collected_at=datetime.now(timezone.utc),
                confidence=0.82,
                license_note="Existing SDINT Reddit comment data",
                session_id=session_id,
            ))

        for post in posts:
            title = post.get("title", "")
            body = post.get("content") or post.get("selftext") or ""
            post_id = post.get("post_id", "")
            author = post.get("author", "")
            evidence.append(EvidenceItem(
                connector_name=self.name,
                source_url=post.get("url") or (f"https://www.reddit.com/comments/{post_id}" if post_id else ""),
                queried_value=value,
                queried_type=pivot_type,
                raw_text=f"{title}\n{body}"[:1000],
                extracted_fields={
                    "username": author,
                    "platform": "Reddit",
                    "post_id": post_id,
                    "subreddit": post.get("subreddit"),
                    "score": post.get("score"),
                    "title": title,
                    "profile_url": f"https://www.reddit.com/user/{author}" if author else "",
                },
                collected_at=datetime.now(timezone.utc),
                confidence=0.84,
                license_note="Existing SDINT Reddit post data",
                session_id=session_id,
            ))

        return evidence

    def _mongo_query(self, pivot_type: str, value: str) -> dict:
        escaped = re.escape(value)
        rx = {"$regex": escaped, "$options": "i"}
        if pivot_type == "username":
            clean = value.lstrip("@")
            return {"$or": [{"author": {"$regex": f"^{re.escape(clean)}$", "$options": "i"}}, {"text": rx}, {"content": rx}, {"title": rx}]}
        return {"$or": [{"author": rx}, {"text": rx}, {"body": rx}, {"content": rx}, {"title": rx}, {"url": rx}]}
