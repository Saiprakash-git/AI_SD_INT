"""
Watchlist and alert service for continuous OSINT monitoring.
"""

from datetime import datetime, timezone


class WatchlistService:
    @staticmethod
    def create(db, query: str, label: str = "", pivot_type: str = "", metadata: dict = None) -> dict:
        item = {
            "watch_id": __import__("uuid").uuid4().hex,
            "query": query,
            "label": label or query,
            "pivot_type": pivot_type or "",
            "active": True,
            "metadata": metadata or {},
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "last_checked_at": None,
            "last_session_id": None,
        }
        db.watchlists.insert_one(item)
        item.pop("_id", None)
        return item

    @staticmethod
    def list(db, active_only: bool = False, limit: int = 100) -> list:
        query = {"active": True} if active_only else {}
        return list(db.watchlists.find(query, {"_id": 0}).sort("updated_at", -1).limit(limit))

    @staticmethod
    def set_active(db, watch_id: str, active: bool) -> bool:
        res = db.watchlists.update_one(
            {"watch_id": watch_id},
            {"$set": {"active": bool(active), "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        return res.modified_count > 0

    @staticmethod
    def evaluate_session_alerts(db, session: dict, person: dict, artifacts: dict) -> list:
        alerts = []
        if not session:
            return alerts

        risk = (session.get("risk_level") or "").upper()
        if risk in {"HIGH", "CRITICAL"}:
            alerts.append({
                "type": "risk_level",
                "severity": risk,
                "message": f"Investigation risk level is {risk}"
            })

        breach_count = len((person or {}).get("breach_findings", []) or [])
        if breach_count > 0:
            alerts.append({
                "type": "breach_exposure",
                "severity": "HIGH" if breach_count >= 2 else "MEDIUM",
                "message": f"{breach_count} breach findings detected"
            })

        analysis = (artifacts or {}).get("open_source_analysis", {}) or {}
        misinfo = float(analysis.get("misinformation_risk", 0.0) or 0.0)
        if misinfo >= 0.5:
            alerts.append({
                "type": "misinformation_risk",
                "severity": "MEDIUM" if misinfo < 0.75 else "HIGH",
                "message": f"Misinformation risk score is {misinfo}"
            })

        return alerts

