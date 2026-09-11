"""Color values shared by sources and Home Assistant customization."""

import re

_HEX_COLOR = re.compile(r"#[0-9a-fA-F]{6}\Z")


def normalize_color(value: object) -> str | None:
    """Return an RGB hex color, or None for missing/invalid provider metadata."""
    if not isinstance(value, str):
        return None
    value = value.strip()
    return value.upper() if _HEX_COLOR.fullmatch(value) else None


def validate_color(value: object) -> str:
    """Validate an explicit user override instead of silently ignoring a typo."""
    color = normalize_color(value)
    if color is None:
        raise ValueError("Use an RGB hex color such as #795548")
    return color
