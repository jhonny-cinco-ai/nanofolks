"""Room-level memory policy overrides."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from nanofolks.utils.helpers import ensure_dir, get_memory_path
from nanofolks.utils.ids import normalize_room_id


def _load_policy_file(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _extract_budget_overrides(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    if "context_budget" in payload and isinstance(payload["context_budget"], dict):
        return payload["context_budget"]
    return payload


def get_context_budget_overrides(workspace: Path, room_id: str) -> dict[str, Any]:
    """Load per-room context budget overrides (if any)."""
    policies_dir = ensure_dir(get_memory_path(workspace) / "policies")
    overrides: dict[str, Any] = {}

    default_path = policies_dir / "default.json"
    if default_path.exists():
        overrides.update(_extract_budget_overrides(_load_policy_file(default_path)))

    normalized = normalize_room_id(room_id)
    if normalized:
        room_path = policies_dir / f"{normalized}.json"
        if room_path.exists():
            overrides.update(_extract_budget_overrides(_load_policy_file(room_path)))

    return overrides

