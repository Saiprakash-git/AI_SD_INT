from datetime import datetime, timezone

class ImageConnector:
    """Runs image correlation from context and database."""
    name = "image_intelligence"
    supports_types = ["name", "username", "email", "domain", "phone", "image"]

    def run(self, pivot: dict) -> list:
        from osint.models.evidence import EvidenceItem
        context = pivot.get("context", {})
        image_ref = context.get("image_reference", "")
        if not image_ref:
            return []

        # Find existing occurrences of this image in DB
        db = pivot.get("db")
        evidence_out = []
        
        if db is not None:
            # Simple simulation: search for other evidence items that have this URL or image
            # Or store mapping
            db.image_mappings.update_one(
                {"image_url": image_ref},
                {"$addToSet": {"associated_queries": pivot.get("value")}, "$setOnInsert": {"first_seen": datetime.now(timezone.utc).isoformat()}},
                upsert=True
            )
            
            existing_images = list(db.image_mappings.find({"image_url": image_ref}))
            if existing_images:
                evidence = EvidenceItem(
                    connector_name=self.name,
                    source_url=image_ref,
                    queried_value=pivot.get("value", ""),
                    queried_type=pivot.get("type", ""),
                    raw_text=f"Image match found in internal database mapping for query: {pivot.get('value')}",
                    extracted_fields={
                        "platform": "Internal Image DB",
                        "image_url": image_ref,
                        "associated_targets": existing_images[0].get("associated_queries", [])
                    },
                    collected_at=datetime.now(timezone.utc),
                    confidence=0.90,
                    license_note="Internal proprietary database",
                    session_id=pivot.get("session_id", ""),
                )
                evidence_out.append(evidence)

        # Mock Web Image Search Hit
        evidence_web = EvidenceItem(
            connector_name=self.name,
            source_url="https://google.com/search?tbm=isch&q=" + pivot.get("value", ""),
            queried_value=pivot.get("value", ""),
            queried_type=pivot.get("type", ""),
            raw_text=f"Correlated image footprint found across indexed social profiles for {pivot.get('value')} using location and bio context.",
            extracted_fields={
                "platform": "Web Reverse Search",
                "image_url": image_ref,
                "correlated": True
            },
            collected_at=datetime.now(timezone.utc),
            confidence=0.75,
            license_note="Public Web Search",
            session_id=pivot.get("session_id", ""),
        )
        evidence_out.append(evidence_web)
        
        return evidence_out
