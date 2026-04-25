"""
Rate limiter for all connectors with per-source cooldowns.
Prevents IP bans and respects API rate limits.
"""

import time
import threading
from collections import defaultdict


class RateScheduler:
    """Thread-safe rate limiter for concurrent OSINT requests."""
    
    _instance = None
    _lock = threading.Lock()
    
    @classmethod
    def get(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = RateScheduler()
        return cls._instance
    
    # Minimum seconds between requests per source
    COOLDOWNS = {
        "instagram_public": 10.0,
        "nitter_twitter": 3.0,
        "google_search": 2.0,
        "duckduckgo": 1.0,
        "psbdmp": 2.0,
        "leakcheck": 2.0,
        "saucenao": 4.0,
        "github_api": 0.5,
        "github": 0.5,
        "hackernews": 0.2,
        "crt_sh": 0.5,
        "wayback_cdx": 1.0,
        "whois": 0.5,
        "default": 1.0,
    }
    
    def __init__(self):
        self._last_call = defaultdict(float)
        self._locks = defaultdict(threading.Lock)
    
    def wait_for(self, source: str):
        """Block until it's safe to make a request to this source."""
        cooldown = self.COOLDOWNS.get(source, self.COOLDOWNS["default"])
        with self._locks[source]:
            elapsed = time.time() - self._last_call[source]
            if elapsed < cooldown:
                time.sleep(cooldown - elapsed)
            self._last_call[source] = time.time()
