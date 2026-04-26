"""
Google-dork style query generator using DuckDuckGo as the no-key search backend.

This multiplies a pivot into targeted site/filetype/intext/inurl searches while
still keeping collection on free public search results.
"""

from datetime import datetime, timezone
from urllib.parse import quote_plus


class GoogleDorkConnector:
    name = "google_dork"
    supports_types = ["email", "username", "name", "domain", "phone"]

    def run(self, pivot: dict) -> list:
        from osint.models.evidence import EvidenceItem

        value = (pivot.get("value", "") or "").strip()
        pivot_type = pivot.get("type", "")
        session_id = pivot.get("session_id", "")
        context = pivot.get("context", {}) or {}
        if not value:
            return []

        queries = self._queries(pivot_type, value, context)
        results = self._search(queries[:8])
        evidence = []

        for item in results[:20]:
            evidence.append(EvidenceItem(
                connector_name=self.name,
                source_url=item.get("href") or item.get("link") or "",
                queried_value=value,
                queried_type=pivot_type,
                raw_text=f"{item.get('title', '')} {item.get('body', '')}".strip(),
                extracted_fields={
                    "platform": "Web Search Dork",
                    "title": item.get("title", ""),
                    "query": item.get("_query", ""),
                    "profile_url": item.get("href") or item.get("link") or "",
                },
                collected_at=datetime.now(timezone.utc),
                confidence=0.62,
                license_note="Public web search result generated from dork query",
                session_id=session_id,
            ))
        return evidence

    def _queries(self, pivot_type: str, value: str, context: dict) -> list:
        quoted = f'"{value}"'
        location = (context.get("location") or "").strip()
        bio = (context.get("bio") or "").strip()
        base = [
            quoted,
            f'{quoted} site:linkedin.com/in',
            f'{quoted} site:github.com',
            f'{quoted} site:reddit.com',
            f'{quoted} site:x.com OR site:twitter.com',
            f'{quoted} site:instagram.com',
            f'{quoted} filetype:pdf',
            f'{quoted} filetype:doc OR filetype:docx',
            f'{quoted} inurl:profile',
            f'{quoted} intext:email',
            f'{quoted} intext:contact',
            f'{quoted} "telegram"',
        ]
        if pivot_type == "domain":
            base.extend([
                f"site:{value}",
                f"site:*.{value}",
                f'"@{value}"',
                f'site:{value} filetype:pdf',
            ])
        if pivot_type == "email":
            local, _, domain = value.partition("@")
            base.extend([f'"{local}" "{domain}"', f'"@{domain}" "{local}"'])
        if location:
            base.extend([f'{quoted} "{location}"', f'{quoted} site:linkedin.com/in "{location}"'])
        if bio:
            base.append(f'{quoted} "{bio[:80]}"')
        return list(dict.fromkeys(base))

    def _search(self, queries: list) -> list:
        output = []
        try:
            from duckduckgo_search import DDGS
        except Exception:
            try:
                from ddgs import DDGS
            except Exception:
                DDGS = None

        if not DDGS:
            return [
                {
                    "title": f"Dork query: {q}",
                    "body": "Install duckduckgo_search/ddgs for live dork results.",
                    "href": f"https://duckduckgo.com/?q={quote_plus(q)}",
                    "_query": q,
                }
                for q in queries
            ]

        try:
            ddg = DDGS()
            seen = set()
            for query in queries:
                for result in ddg.text(query, max_results=3):
                    url = result.get("href") or result.get("link") or ""
                    if not url or url in seen:
                        continue
                    seen.add(url)
                    result["_query"] = query
                    output.append(result)
        except Exception as exc:
            print(f"Google dork search error: {exc}")
        return output
