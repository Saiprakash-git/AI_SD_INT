"""
News connector using GDELT 2 Doc API.

Finds public news articles for name/domain/email pivots, optionally narrowed
with provided location/bio context and DOB-derived start date.
"""

from datetime import datetime, timezone

import requests


class NewsConnector:
    name = "gdelt_news"
    supports_types = ["name", "domain", "email", "username"]

    HEADERS = {"User-Agent": "SDINT-OSINT/1.0"}

    def run(self, pivot: dict) -> list:
        from osint.models.evidence import EvidenceItem

        value = (pivot.get("value", "") or "").strip()
        pivot_type = pivot.get("type", "")
        context = pivot.get("context", {}) or {}
        session_id = pivot.get("session_id", "")
        if not value:
            return []

        articles = self._search(value, context)
        evidence = []
        for article in articles[:10]:
            evidence.append(EvidenceItem(
                connector_name=self.name,
                source_url=article.get("url", ""),
                queried_value=value,
                queried_type=pivot_type,
                raw_text=f"{article.get('title', '')} {article.get('seendate', '')} {article.get('sourcecountry', '')}",
                extracted_fields={
                    "platform": "News",
                    "title": article.get("title", ""),
                    "domain": article.get("domain", ""),
                    "source_country": article.get("sourcecountry", ""),
                    "language": article.get("language", ""),
                    "published_at": article.get("seendate", ""),
                    "profile_url": article.get("url", ""),
                },
                collected_at=datetime.now(timezone.utc),
                confidence=0.64,
                license_note="Public GDELT news search",
                session_id=session_id,
            ))
        return evidence

    def _search(self, value: str, context: dict) -> list:
        query_parts = [f'"{value}"']
        if context.get("location"):
            query_parts.append(f'"{context["location"]}"')
        if context.get("bio"):
            words = " ".join(context["bio"].split()[:6])
            if words:
                query_parts.append(f'"{words}"')
        params = {
            "query": " ".join(query_parts),
            "mode": "ArtList",
            "format": "json",
            "maxrecords": 20,
            "sort": "HybridRel",
        }
        if context.get("dob"):
            start = context["dob"].replace("-", "")
            if len(start) == 8:
                params["startdatetime"] = f"{start}000000"
                params["enddatetime"] = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        try:
            resp = requests.get(
                "https://api.gdeltproject.org/api/v2/doc/doc",
                params=params,
                headers=self.HEADERS,
                timeout=20,
            )
            if resp.status_code != 200:
                return []
            return resp.json().get("articles", [])
        except Exception as exc:
            print(f"GDELT news error: {exc}")
            return []
