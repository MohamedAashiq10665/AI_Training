from __future__ import annotations


def rerank(results: list[dict], availability_only: bool = False) -> list[dict]:
    filtered = results
    if availability_only:
        filtered = [
            r
            for r in results
            if str(r["metadata"].get("availability_status", "")).lower() == "available"
        ]
    return sorted(filtered, key=lambda x: x["score"], reverse=True)
