"""
Open-source content analysis artifact builder.

Produces:
- top keywords/topics
- platform footprint
- basic misinformation risk signals
"""

import re
from collections import Counter, defaultdict


STOPWORDS = {
    "the", "and", "for", "with", "that", "from", "this", "have", "into", "your",
    "about", "http", "https", "www", "com", "org", "net", "are", "was", "were",
    "has", "had", "will", "would", "could", "should", "found", "profile", "user",
    "platform", "query", "search", "data", "source", "public", "using", "check",
}

RISK_PATTERNS = {
    "credential_exposure": re.compile(r"\b(password|passwd|credential|login)\b", re.I),
    "impersonation_risk": re.compile(r"\b(fake|clone|impersonat|spoof)\b", re.I),
    "leak_reference": re.compile(r"\b(leak|breach|dump|paste)\b", re.I),
    "urgency_manipulation": re.compile(r"\b(urgent|breaking|must share|viral)\b", re.I),
}


class ContentAnalyzer:
    def analyze(self, evidence_items: list, raw_query: str) -> dict:
        texts = []
        platform_counts = defaultdict(int)
        connector_counts = defaultdict(int)
        all_tokens = []
        signals = defaultdict(int)
        entities = defaultdict(set)

        for ev in evidence_items:
            fields = ev.get("extracted_fields", {}) or {}
            connector = ev.get("connector_name", "unknown")
            connector_counts[connector] += 1

            platform = fields.get("platform") or ev.get("source_platform") or connector
            platform_counts[platform] += 1

            raw_text = (ev.get("raw_text") or "").strip()
            if raw_text:
                texts.append(raw_text)
                lowered = raw_text.lower()
                for key, pattern in RISK_PATTERNS.items():
                    if pattern.search(lowered):
                        signals[key] += 1

            for email in fields.get("emails", []):
                if isinstance(email, str) and email:
                    entities["emails"].add(email.lower())
            if fields.get("email"):
                entities["emails"].add(str(fields["email"]).lower())
            if fields.get("username"):
                entities["usernames"].add(str(fields["username"]).lower())
            for domain in fields.get("domains", []):
                if isinstance(domain, str) and domain:
                    entities["domains"].add(domain.lower())

            token_source = " ".join([raw_text, str(fields)])
            tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9_#@.-]{2,}", token_source.lower())
            all_tokens.extend([t for t in tokens if t not in STOPWORDS and not t.startswith("http")])

        top_keywords = Counter(all_tokens).most_common(25)
        total_items = len(evidence_items)
        risk_hits = sum(signals.values())
        misinformation_risk = 0.0 if total_items == 0 else min(1.0, round(risk_hits / max(3, total_items), 2))

        return {
            "query": raw_query,
            "total_evidence_items": total_items,
            "platform_footprint": sorted(
                [{"platform": k, "count": v} for k, v in platform_counts.items()],
                key=lambda x: x["count"],
                reverse=True,
            ),
            "connector_coverage": sorted(
                [{"connector": k, "count": v} for k, v in connector_counts.items()],
                key=lambda x: x["count"],
                reverse=True,
            ),
            "top_keywords": [{"keyword": k, "count": v} for k, v in top_keywords],
            "entity_summary": {
                "emails": sorted(list(entities["emails"]))[:20],
                "usernames": sorted(list(entities["usernames"]))[:30],
                "domains": sorted(list(entities["domains"]))[:20],
            },
            "misinformation_signals": dict(signals),
            "misinformation_risk": misinformation_risk,
        }

