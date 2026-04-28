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

        usernames = []
        if pivot_type == "username":
            usernames = [value.lstrip("@")]
            from osint.connectors.username_connector import generate_username_variants
            usernames.extend(generate_username_variants(hint=value))
        elif pivot_type in ("name", "email"):
            from osint.connectors.username_connector import generate_username_variants
            if pivot_type == "name":
                usernames = generate_username_variants(name=value)
            else:
                usernames = generate_username_variants(email=value)
        else:
            usernames = [value]
            
        usernames = list(set(usernames))
        query = self._mongo_query(pivot_type, value, usernames)
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

    def _mongo_query(self, pivot_type: str, value: str, usernames: list) -> dict:
        escaped_value = re.escape(value)
        rx_val = {"$regex": escaped_value, "$options": "i"}
        
        author_conditions = []
        for u in usernames:
            author_conditions.append({"author": {"$regex": f"^{re.escape(u)}$", "$options": "i"}})
            
        if not author_conditions:
            author_conditions = [{"author": rx_val}]
            
        if pivot_type == "username":
            return {"$or": author_conditions + [{"text": rx_val}, {"content": rx_val}, {"title": rx_val}]}
            
        return {"$or": author_conditions + [{"text": rx_val}, {"body": rx_val}, {"content": rx_val}, {"title": rx_val}, {"url": rx_val}]}
