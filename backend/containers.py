"""
Stage 4 — Container priority via Container_prioritization/
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CP = ROOT / "Container_prioritization"
if str(CP) not in sys.path:
    sys.path.insert(0, str(CP))

from prioritize import prioritize_containers as _prioritize  # noqa: E402


def prioritize_containers(
    opportunities: list[dict[str, Any]],
    available_containers: int = 6,
    container_type: str = "20FT",
) -> dict[str, Any]:
    return _prioritize(
        opportunities,
        available_containers=available_containers,
        container_type=container_type,
    )
