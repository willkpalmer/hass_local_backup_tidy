"""Helpers for parsing/validating the configured backup times."""
from __future__ import annotations

import re

from .const import TIME_RE

_TIME_RE = re.compile(TIME_RE)


def parse_times(times_str: str) -> list[str]:
    """Split a comma-separated time string into a list of trimmed entries."""
    return [t.strip() for t in times_str.split(",") if t.strip()]


def validate_times(times_str: str) -> str:
    """Validate a comma-separated HH:MM time list, returning it deduped/normalized."""
    times = parse_times(times_str)
    if not times:
        raise ValueError("At least one time is required")

    seen: set[str] = set()
    deduped: list[str] = []
    for time_str in times:
        if not _TIME_RE.match(time_str):
            raise ValueError(f"Invalid time '{time_str}', expected 24h HH:MM")
        if time_str not in seen:
            seen.add(time_str)
            deduped.append(time_str)

    return ",".join(deduped)
