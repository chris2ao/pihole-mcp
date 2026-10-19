from typing import Any
from urllib.parse import quote


def seg(value: str) -> str:
    """URL-encode a single path segment."""
    return quote(str(value), safe="")


def compact(params: dict[str, Any]) -> dict[str, Any]:
    """Drop None values so optional filters are not sent."""
    return {k: v for k, v in params.items() if v is not None}


def preview(action: str, **details: Any) -> dict:
    """Response for a guarded tool called without confirm=True. Nothing is changed."""
    return {
        "preview": True,
        "action": action,
        **details,
        "note": "No change made. Call again with confirm=true to apply.",
    }
