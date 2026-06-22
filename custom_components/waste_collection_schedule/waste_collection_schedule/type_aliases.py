from collections.abc import Iterable, Mapping
from typing import Any

CONF_ALIAS = "alias"


def get_customize_alias(customization: Any) -> str | None:
    """Return alias from either runtime Customize objects or stored option dicts."""
    if customization is None:
        return None

    alias = getattr(customization, "alias", None)
    if isinstance(alias, str) and alias:
        return alias

    if isinstance(customization, Mapping):
        alias = customization.get(CONF_ALIAS)
        if isinstance(alias, str) and alias:
            return alias

    return None


def expand_requested_types(
    requested_types: Iterable[str] | None, customizations: Mapping[str, Any] | None
) -> set[str] | None:
    """Treat original and aliased type names as equivalent when filtering."""
    if requested_types is None:
        return None

    expanded = set(requested_types)
    if customizations is None:
        return expanded

    for raw_type, customization in customizations.items():
        alias = get_customize_alias(customization)
        if alias is None:
            continue
        if raw_type in expanded or alias in expanded:
            expanded.add(raw_type)
            expanded.add(alias)

    return expanded


def is_type_customized(type_name: str, customizations: Mapping[str, Any]) -> bool:
    """Return True when a type is already represented by an existing customization."""
    if type_name in customizations:
        return True

    return any(
        get_customize_alias(customization) == type_name
        for customization in customizations.values()
    )


def get_uncustomized_types(
    live_types: Iterable[str], customizations: Mapping[str, Any]
) -> list[str]:
    """Return live types that are not already covered by existing customizations."""
    return [
        type_name
        for type_name in live_types
        if not is_type_customized(type_name, customizations)
    ]


def get_customize_label(raw_type: str, customization: Any) -> str:
    """Return a readable options label for an existing customization."""
    alias = get_customize_alias(customization)
    if alias is not None and alias != raw_type:
        return f"{alias} ({raw_type})"
    return raw_type
