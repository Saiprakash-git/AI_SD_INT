import aiohttp
import asyncio
import os
from datetime import datetime, timezone
import json

class SauceNaoConnector:
    """Reverse image search using SauceNAO."""
    name = "saucenao_reverse_search"
    supports_types = ["image"]

    def run(self, pivot: dict) -> list:
        from osint.models.evidence import EvidenceItem
        context = pivot.get("context", {})
        image_path = context.get("image_path")
        
        if not image_path or not os.path.exists(image_path):
            return []

        # Run async search
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        results = loop.run_until_complete(self._search(image_path))
        loop.close()

        evidence_out = []
        for res in results:
            evidence = EvidenceItem(
                connector_name=self.name,
                source_url=res.get("url", ""),
                queried_value="Reverse Image Search",
                queried_type="image",
                raw_text=f"Image found on {res.get('site')} via SauceNAO",
                extracted_fields={
                    "platform": res.get("site"),
                    "title": res.get("title", ""),
                    "similarity": res.get("similarity", "")
                },
                collected_at=datetime.now(timezone.utc),
                confidence=float(res.get("similarity", 0)) / 100.0 if res.get("similarity") else 0.5,
                license_note="Public Reverse Search",
                session_id=pivot.get("session_id", ""),
            )
            evidence_out.append(evidence)
            
        return evidence_out

    async def _search(self, image_path: str) -> list:
        """Query SauceNAO API (works without API key with strict rate limits)"""
        url = 'https://saucenao.com/search.php'
        
        results = []
        try:
            with open(image_path, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('output_type', '2')
                data.add_field('file', f, filename=os.path.basename(image_path))
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, data=data, timeout=15) as resp:
                        if resp.status == 200:
                            json_resp = await resp.json()
                            for item in json_resp.get('results', []):
                                header = item.get('header', {})
                                data = item.get('data', {})
                                similarity = float(header.get('similarity', 0))
                                
                                if similarity > 60: # Only return high confidence matches
                                    urls = data.get('ext_urls', [])
                                    if urls:
                                        results.append({
                                            "url": urls[0],
                                            "site": header.get('index_name', 'Unknown'),
                                            "title": data.get('title', 'Matched Image'),
                                            "similarity": similarity
                                        })
        except Exception as e:
            print(f"SauceNAO search failed: {e}")
            
        return results
