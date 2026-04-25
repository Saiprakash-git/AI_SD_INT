"""
Source credibility scoring for connector evidence.

The score is not a final truth score; it is a source-quality prior that
helps analysts interpret confidence and reduces over-trust in noisy feeds.
"""

from typing import Dict, Optional


class SourceCredibility:
    # Baseline prior per connector/source.
    BASE_SCORES: Dict[str, float] = {
        "github": 0.9,
        "hackernews": 0.75,
        "username_lookup": 0.7,
        "breach_check": 0.8,
        "nitter_twitter": 0.65,
        "instagram_public": 0.68,
        "web_search": 0.65,
    }

    @classmethod
    def score(
        cls,
        connector_name: str,
        item: dict,
        custom_weights: Optional[Dict[str, float]] = None
    ) -> float:
        weights = dict(cls.BASE_SCORES)
        if custom_weights:
            for key, value in custom_weights.items():
                try:
                    weights[key] = float(value)
                except (TypeError, ValueError):
                    continue

        score = weights.get(connector_name, 0.6)
        extracted = item.get("extracted_fields", {}) or {}

        # Lightweight heuristics for more robust ranking.
        if extracted.get("profile_url"):
            score += 0.03
        if extracted.get("breach_count"):
            score += 0.05
        if extracted.get("platform") and connector_name == "username_lookup":
            score += 0.02
        if not item.get("source_url"):
            score -= 0.04

        return max(0.0, min(1.0, round(score, 2)))

    @classmethod
    def validate_weights(cls, custom_weights: dict) -> Dict[str, float]:
        validated: Dict[str, float] = {}
        for key, value in (custom_weights or {}).items():
            try:
                v = float(value)
            except (TypeError, ValueError):
                continue
            validated[key] = max(0.0, min(1.0, round(v, 2)))
        return validated

