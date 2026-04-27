"""
Username enumeration across 20+ platforms using direct HTTP checks.
No sherlock dependency - uses custom platform definitions.
"""

import asyncio
import aiohttp
from datetime import datetime, timezone
from typing import Optional, List
import re


PLATFORMS = {
    "GitHub": "https://github.com/{username}",
    "Reddit": "https://www.reddit.com/user/{username}/about.json",
    "HackerNews": "https://hacker-news.firebaseio.com/v0/user/{username}.json",
    "GitLab": "https://gitlab.com/{username}",
    "PyPI": "https://pypi.org/user/{username}/",
    "npm": "https://www.npmjs.com/~{username}",
    "Keybase": "https://keybase.io/{username}/_/api/1.0/user/lookup.json?username={username}",
    "Telegram": "https://t.me/{username}",
    "Dev.to": "https://dev.to/api/users/by_username?url={username}",
    "Medium": "https://medium.com/@{username}",
    "Pastebin": "https://pastebin.com/u/{username}",
    "Replit": "https://replit.com/@{username}",
    "Codepen": "https://codepen.io/{username}",
    "Bitbucket": "https://bitbucket.org/{username}/",
    "Docker": "https://hub.docker.com/u/{username}/",
    "Gravatar": "https://en.gravatar.com/{username}",
}

JSON_PLATFORMS = {
    "Reddit": lambda r: r.get("data", {}).get("name") is not None,
    "HackerNews": lambda r: r is not None and "id" in r,
    "Dev.to": lambda r: r.get("id") is not None,
    "Keybase": lambda r: r.get("status", {}).get("code") == 0,
}


async def check_platform(session, platform: str, url: str, username: str) -> Optional[dict]:
    """Check if username exists on a platform."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }
    try:
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10), allow_redirects=True) as resp:
            if platform in JSON_PLATFORMS:
                if resp.status == 200:
                    try:
                        data = await resp.json(content_type=None)
                        if JSON_PLATFORMS[platform](data):
                            return {"platform": platform, "url": url, "found": True, "status": resp.status}
                    except Exception:
                        pass
            else:
                if resp.status == 200:
                    return {"platform": platform, "url": url, "found": True, "status": resp.status}
    except (asyncio.TimeoutError, Exception):
        pass
    return None


async def enumerate_username(username: str) -> list:
    """Check username across platforms concurrently."""
    results = []
    urls = {platform: template.format(username=username) for platform, template in PLATFORMS.items()}
    
    connector = aiohttp.TCPConnector(limit=20, limit_per_host=2)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [check_platform(session, platform, url, username) for platform, url in urls.items()]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
    
    for resp in responses:
        if isinstance(resp, dict) and resp.get("found"):
            results.append(resp)
    
    return results


def generate_username_variants(name: str = None, email: str = None, hint: str = None, context: dict = None) -> list:
    """Generate likely usernames from name, email, hint, and context."""
    variants = set()
    
    if hint:
        variants.add(hint.lower().strip().lstrip("@"))
    
    if email:
        local = email.split("@")[0].lower()
        variants.add(local)
        variants.add(local.replace(".", ""))
        variants.add(local.replace("_", ""))
        variants.add(local.replace("-", ""))
    
    if name:
        parts = name.lower().strip().split()
        if len(parts) >= 2:
            first, last = parts[0], parts[-1]
            base_variants = [
                f"{first}{last}",
                f"{first}.{last}",
                f"{first}_{last}",
                f"{first[0]}{last}",
                f"{first}{last[0]}",
                first,
                last,
            ]
            variants.update(base_variants)
            
            # Incorporate context
            if context:
                dob = context.get('dob', '')
                loc = context.get('location', '')
                
                years = []
                if dob:
                    # Extract year if possible
                    import re
                    year_match = re.search(r'\b(19|20)\d{2}\b', dob)
                    if year_match:
                        years.append(year_match.group(0))
                        years.append(year_match.group(0)[-2:]) # last 2 digits
                
                loc_short = loc[:2].lower() if loc else ""
                
                for bv in base_variants:
                    for y in years:
                        variants.add(f"{bv}{y}")
                        variants.add(f"{bv}_{y}")
                    if loc_short:
                        variants.add(f"{bv}{loc_short}")
                        variants.add(f"{bv}_{loc_short}")

    return list(variants)[:30]


class UsernameConnector:
    """Free username enumeration across 20+ platforms."""
    
    name = "username_lookup"
    supports_types = ["username", "name", "email"]
    
    def run(self, pivot: dict) -> list:
        """Synchronous wrapper for async enumeration."""
        from osint.models.evidence import EvidenceItem
        
        pivot_type = pivot.get("type")
        pivot_value = pivot.get("value", "")
        session_id = pivot.get("session_id", "")
        
        context = pivot.get("context", {})
        
        # Generate usernames to check
        if pivot_type == "username":
            usernames = [pivot_value.lstrip("@")]
            usernames.extend(generate_username_variants(hint=pivot_value, context=context))
        elif pivot_type == "name":
            usernames = generate_username_variants(name=pivot_value, context=context)
        elif pivot_type == "email":
            usernames = generate_username_variants(email=pivot_value, context=context)
        else:
            return []
            
        usernames = list(set(usernames)) # Deduplicate
        
        all_evidence = []
        
        for username in usernames:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                results = loop.run_until_complete(enumerate_username(username))
                loop.close()
                
                for result in results:
                    evidence = EvidenceItem(
                        connector_name=self.name,
                        source_url=result["url"],
                        queried_value=username,
                        queried_type="username",
                        raw_text=f"Username '{username}' found on {result['platform']}",
                        extracted_fields={
                            "username": username,
                            "platform": result["platform"],
                            "profile_url": result["url"],
                        },
                        collected_at=datetime.now(timezone.utc),
                        confidence=0.85,
                        license_note="Public web profile",
                        session_id=session_id,
                    )
                    all_evidence.append(evidence)
            except Exception as e:
                print(f"Username check error for '{username}': {e}")
        
        return all_evidence
