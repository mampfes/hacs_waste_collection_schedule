#!/usr/bin/env python3
"""Generate ``doc/source/<id>.md`` for new-architecture (BaseSource) sources.

Legacy sources hand-write their doc file; ``update_docu_links.py`` only reads
those. New-style sources (subclasses of ``BaseSource``) carry structured
metadata (TITLE, DESCRIPTION, URL, PARAMS, HOWTO, TEST_CASES) that makes the
whole file derivable, so contributors no longer need to write it by hand when
migrating a source.

The single entry point is :func:`render_source_doc`, a pure function returning
the full markdown text. ``update_docu_links.py`` wires it into the generation
flow (see ``generate_base_source_doc``), writing the file for BaseSource
sources only and leaving legacy sources untouched.
"""

from typing import Any

import yaml

# Map a ConfigParam widget to the type label shown in the doc, mirroring the
# phrasing used in the existing hand-written files (e.g. "(string)").
_WIDGET_TYPE: dict[str, str] = {
    "map": "float",
}


def _field_type(widget: str) -> str:
    """Return the type label for a param field, defaulting to ``string``."""
    return _WIDGET_TYPE.get(widget, "string")


def _is_base_source(source_cls: Any) -> bool:
    """True if ``source_cls`` is a new-architecture ``BaseSource`` subclass."""
    try:
        from waste_collection_schedule.base_source import BaseSource
    except Exception:
        return False
    return isinstance(source_cls, type) and issubclass(source_cls, BaseSource)


def _representative_test_case(test_cases: dict[str, dict]) -> dict[str, Any] | None:
    """Pick one representative TEST_CASE's kwargs.

    Prefers the first case that actually carries arguments (so the example
    shows a realistic ``args:`` block); falls back to the first case otherwise.
    Returns ``None`` when there are no test cases.
    """
    if not test_cases:
        return None
    for kwargs in test_cases.values():
        if kwargs:
            return kwargs
    return next(iter(test_cases.values()))


def _yaml_args_block(kwargs: dict[str, Any], indent: int = 8) -> str:
    """Render a kwargs dict as an indented YAML mapping for an ``args:`` block."""
    dumped = yaml.dump(kwargs, default_flow_style=False, sort_keys=False).rstrip("\n")
    pad = " " * indent
    return "\n".join(f"{pad}{line}" for line in dumped.split("\n"))


def _alternatives_groups(params: list[Any]) -> tuple[tuple[str, ...], ...]:
    """Return the mutually-exclusive field groups if the source declares any.

    An ``alternatives()`` param carries ``groups`` (one tuple of field names per
    mutually-exclusive input option). Sources without alternatives return ``()``.
    """
    for param in params:
        groups = getattr(param, "groups", ()) or ()
        if groups:
            return groups
    return ()


def _base_fields(params: list[Any]) -> list[str]:
    """Field names from params that are NOT part of an alternatives group."""
    base: list[str] = []
    for param in params:
        if getattr(param, "groups", ()):
            continue
        base.extend(param.fields)
    return base


def _human_join(names: tuple[str, ...]) -> str:
    """``('lat', 'lon')`` -> ``'lat and lon'``; ``('address',)`` -> ``'address'``."""
    items = list(names)
    if len(items) <= 1:
        return items[0] if items else ""
    return ", ".join(items[:-1]) + " and " + items[-1]


def _test_case_for(test_cases: dict[str, dict], field_names: list[str]) -> dict | None:
    """First test case whose kwargs cover every name in ``field_names``."""
    for kwargs in test_cases.values():
        if field_names and all(name in kwargs for name in field_names):
            return kwargs
    return None


def render_source_doc(source_id: str, source_cls: Any) -> str:
    """Render the full ``doc/source/<id>.md`` text for a BaseSource source.

    Args:
        source_id: the source module stem (the ``name:`` used in YAML config).
        source_cls: the source's ``Source`` class (a ``BaseSource`` subclass).

    Returns:
        The complete markdown document as a string.
    """
    title = getattr(source_cls, "TITLE", "") or source_id
    description = getattr(source_cls, "DESCRIPTION", "") or ""
    url = getattr(source_cls, "URL", "") or ""
    params = list(getattr(source_cls, "PARAMS", []) or [])
    howto = dict(getattr(source_cls, "HOWTO", {}) or {})
    test_cases = dict(getattr(source_cls, "TEST_CASES", {}) or {})

    # Flatten PARAMS into ordered (field_name, type_label, required) entries.
    fields: list[tuple[str, str, bool]] = []
    for param in params:
        type_label = _field_type(getattr(param, "widget", "text"))
        required = getattr(param, "required", True)
        for field_name in getattr(param, "fields", {}):
            fields.append((field_name, type_label, required))

    lines: list[str] = []

    # --- Title + support line ---
    lines.append(f"# {title}")
    lines.append("")
    if url:
        lines.append(f"Support for schedules provided by [{title}]({url}).")
    else:
        lines.append(f"Support for schedules provided by {title}.")
    lines.append("")
    if description:
        lines.append(description)
        lines.append("")

    # A source with an alternatives() param accepts one of several mutually
    # exclusive input groups (e.g. a UPRN OR a postcode plus house number), so
    # the config and example blocks are rendered once per group.
    alt_groups = _alternatives_groups(params)
    base = _base_fields(params)
    all_fields = [name for name, _type, _req in fields]

    # --- Configuration via configuration.yaml ---
    lines.append("## Configuration via configuration.yaml")
    lines.append("")
    config_scenarios: list[tuple[tuple[str, ...] | None, list[str]]]
    if alt_groups:
        config_scenarios = [(group, base + list(group)) for group in alt_groups]
    else:
        config_scenarios = [(None, all_fields)]
    for group, field_names in config_scenarios:
        if group is not None:
            lines.append(f"### Using {_human_join(group)}")
            lines.append("")
        lines.append("```yaml")
        lines.append("waste_collection_schedule:")
        lines.append("  sources:")
        lines.append(f"    - name: {source_id}")
        if field_names:
            lines.append("      args:")
            for field_name in field_names:
                lines.append(f"        {field_name}: {field_name.upper()}")
        lines.append("```")
        lines.append("")

    # --- Configuration Variables ---
    grouped = {name for group in alt_groups for name in group}
    lines.append("### Configuration Variables")
    lines.append("")
    if fields:
        for field_name, type_label, required in fields:
            if field_name in grouped:
                requirement = "alternative"
            elif required:
                requirement = "required"
            else:
                requirement = "optional"
            lines.append(f"**{field_name}**  ")
            lines.append(f"*({type_label}) ({requirement})*")
            lines.append("")
        if alt_groups:
            opts = " or ".join("`" + "` + `".join(group) + "`" for group in alt_groups)
            lines.append(f"Provide one of: {opts}.")
            lines.append("")
    else:
        lines.append("No configuration arguments are required.")
        lines.append("")

    # --- Example ---
    lines.append("## Example")
    lines.append("")
    if alt_groups:
        for group in alt_groups:
            field_names = base + list(group)
            kwargs = _test_case_for(test_cases, field_names)
            if not kwargs:
                continue
            lines.append(f"### Using {_human_join(group)}")
            lines.append("")
            lines.append("```yaml")
            lines.append("waste_collection_schedule:")
            lines.append("  sources:")
            lines.append(f"    - name: {source_id}")
            shown = {k: kwargs[k] for k in field_names if k in kwargs}
            if shown:
                lines.append("      args:")
                lines.append(_yaml_args_block(shown))
            lines.append("```")
            lines.append("")
    else:
        representative = _representative_test_case(test_cases)
        lines.append("```yaml")
        lines.append("waste_collection_schedule:")
        lines.append("  sources:")
        lines.append(f"    - name: {source_id}")
        if representative:
            lines.append("      args:")
            lines.append(_yaml_args_block(representative))
        lines.append("```")
        lines.append("")

    # --- How to get the source arguments ---
    howto_text = howto.get("en") or next(iter(howto.values()), "")
    if howto_text:
        lines.append("## How to get the source arguments")
        lines.append("")
        lines.append(howto_text.strip())
        lines.append("")

    # Single trailing newline, like the hand-written files.
    return "\n".join(lines).rstrip("\n") + "\n"
