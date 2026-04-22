"""
Entity Extractor — Extracts structured entities from raw text.

Uses a hybrid approach:
  1. spaCy NER for persons, organizations, locations, dates
  2. Regex patterns for emails, URLs, phones, IPs, usernames, domains, crypto wallets
  3. Platform-specific patterns (Reddit u/user, r/subreddit)

Each extracted entity gets a confidence score:
  - NER entities: use spaCy's label confidence (typically 0.7-0.95)
  - Regex entities: 1.0 (deterministic match)
  - Platform patterns: 0.95 (high confidence, format-specific)
"""

import re
import logging
from typing import List, Tuple, Set

logger = logging.getLogger(__name__)

# Lazy-load spaCy to avoid import-time model loading
_nlp = None

def _get_nlp():
    """Lazy-load the spaCy model on first use."""
    global _nlp
    if _nlp is None:
        try:
            import spacy
            _nlp = spacy.load("en_core_web_sm")
            logger.info("spaCy model 'en_core_web_sm' loaded successfully.")
        except OSError:
            logger.warning(
                "spaCy model 'en_core_web_sm' not found. "
                "Run: python -m spacy download en_core_web_sm"
            )
            _nlp = False  # Mark as unavailable
        except Exception as e:
            logger.error(f"Failed to load spaCy: {e}")
            _nlp = False
    return _nlp if _nlp is not False else None


# ─── Regex Patterns ──────────────────────────────────────────────────────────

PATTERNS = {
    "email": re.compile(
        r'\b[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}\b'
    ),
    "url": re.compile(
        r'https?://[^\s<>\"\'\)\]]+',
        re.IGNORECASE
    ),
    "phone": re.compile(
        r'(?:\+?1[-.\s]?)?'                        # Optional country code
        r'(?:\(?\d{3}\)?[-.\s]?)'                   # Area code
        r'\d{3}[-.\s]?\d{4}'                        # Number
        r'(?!\d)'                                    # Not followed by more digits
    ),
    "ip_address": re.compile(
        r'\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}'
        r'(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b'
    ),
    "domain": re.compile(
        r'\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)'
        r'+(?:com|org|net|edu|gov|io|co|us|uk|de|fr|jp|ru|info|biz|xyz|dev|app|ai)\b',
        re.IGNORECASE
    ),
    "reddit_username": re.compile(
        r'(?:u/|/u/)([a-zA-Z0-9_\-]{3,20})',
        re.IGNORECASE
    ),
    "reddit_subreddit": re.compile(
        r'(?:r/|/r/)([a-zA-Z0-9_]{2,21})',
        re.IGNORECASE
    ),
    "twitter_handle": re.compile(
        r'@([a-zA-Z0-9_]{1,15})\b'
    ),
    "hashtag": re.compile(
        r'#([a-zA-Z0-9_]{2,})\b'
    ),
    "crypto_btc": re.compile(
        r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b'
    ),
    "crypto_eth": re.compile(
        r'\b0x[a-fA-F0-9]{40}\b'
    ),
}

# Mapping from spaCy NER labels to our EntityType values
SPACY_LABEL_MAP = {
    "PERSON": "person",
    "ORG": "organization",
    "GPE": "location",        # Geopolitical entity (countries, cities)
    "LOC": "location",        # Non-GPE locations
    "DATE": "date",
    "FAC": "location",        # Facilities (buildings, airports)
}

# Entities to skip (too noisy from spaCy)
SPACY_SKIP_LABELS = {"CARDINAL", "ORDINAL", "QUANTITY", "MONEY", "PERCENT", "TIME"}


class EntityExtractor:
    """
    Hybrid entity extractor combining NER and regex pattern matching.
    
    Usage:
        extractor = EntityExtractor()
        entities = extractor.extract("Contact john@example.com or u/johndoe")
        # Returns: [
        #   {"type": "email", "value": "john@example.com", "confidence": 1.0, ...},
        #   {"type": "username", "value": "johndoe", "confidence": 0.95, ...}
        # ]
    """

    def __init__(self):
        self._seen: Set[Tuple[str, str]] = set()  # Dedup tracker: (type, normalized_value)

    def extract(self, text: str, include_context: bool = True) -> List[dict]:
        """
        Extract all entities from text using NER + regex.
        
        Args:
            text: Raw text to extract entities from
            include_context: If True, include surrounding text snippet
            
        Returns:
            List of entity dicts: [{type, value, confidence, source, context}]
        """
        if not text or not isinstance(text, str):
            return []

        self._seen.clear()
        entities = []

        # Phase 1: Regex extraction (high precision)
        entities.extend(self._extract_regex(text, include_context))

        # Phase 2: spaCy NER extraction (broader coverage)
        entities.extend(self._extract_ner(text, include_context))

        return entities

    def _extract_regex(self, text: str, include_context: bool) -> List[dict]:
        """Extract entities using regex patterns."""
        results = []

        # Email
        for m in PATTERNS["email"].finditer(text):
            entity = self._make_entity(
                "email", m.group().lower(), 1.0, "regex",
                self._get_context(text, m.start(), m.end()) if include_context else ""
            )
            if entity:
                results.append(entity)

        # URL
        for m in PATTERNS["url"].finditer(text):
            url = m.group().rstrip('.,;:)')  # Strip trailing punctuation
            entity = self._make_entity(
                "url", url, 1.0, "regex",
                self._get_context(text, m.start(), m.end()) if include_context else ""
            )
            if entity:
                results.append(entity)

        # Phone
        for m in PATTERNS["phone"].finditer(text):
            raw_phone = m.group().strip()
            # Filter out obvious false positives (too many digits in surrounding context)
            if len(re.sub(r'\D', '', raw_phone)) >= 10:
                entity = self._make_entity(
                    "phone", raw_phone, 0.85, "regex",
                    self._get_context(text, m.start(), m.end()) if include_context else ""
                )
                if entity:
                    results.append(entity)

        # IP Address
        for m in PATTERNS["ip_address"].finditer(text):
            entity = self._make_entity(
                "ip_address", m.group(), 1.0, "regex",
                self._get_context(text, m.start(), m.end()) if include_context else ""
            )
            if entity:
                results.append(entity)

        # Domain (skip if already captured as part of a URL or email)
        captured_urls = {m.group() for m in PATTERNS["url"].finditer(text)}
        captured_emails = {m.group() for m in PATTERNS["email"].finditer(text)}
        for m in PATTERNS["domain"].finditer(text):
            domain = m.group().lower()
            # Skip domains already captured inside URLs or emails
            is_in_url = any(domain in url for url in captured_urls)
            is_in_email = any(domain in email for email in captured_emails)
            if not is_in_url and not is_in_email:
                entity = self._make_entity(
                    "domain", domain, 0.9, "regex",
                    self._get_context(text, m.start(), m.end()) if include_context else ""
                )
                if entity:
                    results.append(entity)

        # Reddit usernames
        for m in PATTERNS["reddit_username"].finditer(text):
            username = m.group(1)  # Capture group without u/ prefix
            if username.lower() not in {"deleted", "automoderator", "removed"}:
                entity = self._make_entity(
                    "username", username, 0.95, "regex",
                    self._get_context(text, m.start(), m.end()) if include_context else ""
                )
                if entity:
                    results.append(entity)

        # Reddit subreddits
        for m in PATTERNS["reddit_subreddit"].finditer(text):
            subreddit = m.group(1)
            entity = self._make_entity(
                "subreddit", subreddit, 0.95, "regex",
                self._get_context(text, m.start(), m.end()) if include_context else ""
            )
            if entity:
                results.append(entity)

        # Twitter handles → treated as username
        for m in PATTERNS["twitter_handle"].finditer(text):
            handle = m.group(1)
            if len(handle) > 1:  # Skip single char handles
                entity = self._make_entity(
                    "username", handle, 0.9, "regex",
                    self._get_context(text, m.start(), m.end()) if include_context else ""
                )
                if entity:
                    results.append(entity)

        # Hashtags
        for m in PATTERNS["hashtag"].finditer(text):
            tag = m.group(1)
            entity = self._make_entity(
                "hashtag", tag, 1.0, "regex",
                self._get_context(text, m.start(), m.end()) if include_context else ""
            )
            if entity:
                results.append(entity)

        # Crypto wallets
        for pattern_name, entity_type in [("crypto_btc", "crypto_wallet"), ("crypto_eth", "crypto_wallet")]:
            for m in PATTERNS[pattern_name].finditer(text):
                entity = self._make_entity(
                    entity_type, m.group(), 0.8, "regex",
                    self._get_context(text, m.start(), m.end()) if include_context else ""
                )
                if entity:
                    results.append(entity)

        return results

    def _extract_ner(self, text: str, include_context: bool) -> List[dict]:
        """Extract entities using spaCy NER."""
        nlp = _get_nlp()
        if nlp is None:
            return []

        results = []

        try:
            # Truncate very long text for NER (spaCy perf degrades on huge docs)
            truncated = text[:10000] if len(text) > 10000 else text
            doc = nlp(truncated)

            for ent in doc.ents:
                if ent.label_ in SPACY_SKIP_LABELS:
                    continue

                entity_type = SPACY_LABEL_MAP.get(ent.label_)
                if not entity_type:
                    continue

                value = ent.text.strip()
                # Skip very short or very long entities (likely noise)
                if len(value) < 2 or len(value) > 100:
                    continue

                # Skip entities that are just numbers
                if value.replace(" ", "").isdigit():
                    continue

                # Approximate NER confidence based on entity length and type
                # spaCy doesn't expose per-entity confidence directly in all models
                confidence = 0.75
                if ent.label_ == "PERSON" and len(value.split()) >= 2:
                    confidence = 0.85  # Full names are higher confidence
                elif ent.label_ in ("ORG",) and len(value) > 3:
                    confidence = 0.80

                context = self._get_context(text, ent.start_char, ent.end_char) if include_context else ""

                entity = self._make_entity(entity_type, value, confidence, "ner", context)
                if entity:
                    results.append(entity)

        except Exception as e:
            logger.error(f"NER extraction failed: {e}")

        return results

    def _make_entity(self, entity_type: str, value: str, confidence: float,
                     source: str, context: str) -> dict:
        """
        Create an entity dict with deduplication.
        Returns None if duplicate.
        """
        normalized = value.lower().strip()
        dedup_key = (entity_type, normalized)

        if dedup_key in self._seen:
            return None

        self._seen.add(dedup_key)

        return {
            "type": entity_type,
            "value": value.strip(),
            "confidence": round(confidence, 3),
            "source": source,
            "context": context[:200] if context else ""  # Cap context length
        }

    @staticmethod
    def _get_context(text: str, start: int, end: int, window: int = 50) -> str:
        """Extract surrounding text context for an entity match."""
        ctx_start = max(0, start - window)
        ctx_end = min(len(text), end + window)
        return text[ctx_start:ctx_end].strip()
