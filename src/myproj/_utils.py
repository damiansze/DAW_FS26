from __future__ import annotations


def fmt_ids(ids: list, max_show: int = 5) -> str:
    """Kürzt eine ID-Liste für lesbare Log-Ausgaben."""
    if len(ids) <= max_show:
        return str(ids)
    return f"{ids[:max_show]} ... (+{len(ids) - max_show} weitere)"
