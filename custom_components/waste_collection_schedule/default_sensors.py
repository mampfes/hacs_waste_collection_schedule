"""Default sensors created for a config entry.

One place decides what a default sensor is, so the config flow (new entry) and
the options flow (adding defaults to an existing entry) create the same ones.
"""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .sensor_model import SensorConfig, catalogue_id

# Keep the stored setup-choice names while creating catalogue records.
KIND_LEGACY = "legacy"

# Exact former per-type template, used to recognize defaults during migration.
LEGACY_VALUE_TEMPLATE = (
    'on {{value.date.strftime("%a")}}, {{value.date.strftime("%d.%m.%Y")}}'
)

# The sensors that expose language-neutral raw values for cards and templates.
KIND_NEW = "new"

# English overview names preserve familiar defaults; identity comes from origin.
NEXT_COLLECTION_NAME = "Next collection"
DAYS_TO_NAME = "Days until collection"
LAST_UPDATE_NAME = "Last update"
NEW_SENSOR_NAMES = (NEXT_COLLECTION_NAME, DAYS_TO_NAME, LAST_UPDATE_NAME)

DEFAULT_SENSOR_KINDS = (KIND_LEGACY, KIND_NEW)


def default_sensors_selector() -> SelectSelector:
    """Multi-select over the default sensor sets, labelled by translation."""
    return SelectSelector(
        SelectSelectorConfig(
            options=[SelectOptionDict(label=k, value=k) for k in DEFAULT_SENSOR_KINDS],
            multiple=True,
            mode=SelectSelectorMode.LIST,
            translation_key="default_sensors",
        )
    )


def catalogue(type_labels: dict[str, str]) -> dict[str, dict[str, Any]]:
    """Offer one sensor per canonical category and the three overview sensors."""
    records = {}
    for type_id, label in type_labels.items():
        origin = "type:" + type_id
        records[origin] = SensorConfig(
            name=label,
            id=catalogue_id(origin),
            origin=origin,
            types=[type_id],
            state_format="relative",
            language="auto",
        ).as_dict()
    for origin, name, kind, state_format in (
        ("next_collection", "Next collection", "schedule", "types"),
        ("days_until", "Days until collection", "days_to", "days"),
        ("last_update", "Last update", "last_update", "types_in_days"),
    ):
        records[origin] = SensorConfig(
            name=name,
            id=origin,
            origin=origin,
            kind=kind,
            state_format=state_format,
            language="auto",
            details_format="hidden",
        ).as_dict()
    return records


def build_default_sensors(kinds, fetched_types: dict[str, str], existing=()):
    """Materialize missing catalogue records, deduplicating by origin, not name."""
    kinds = set(kinds)
    present = {s.get("origin") for s in existing}
    return [
        r
        for origin, r in catalogue(fetched_types).items()
        if origin not in present
        and (
            (origin.startswith("type:") and KIND_LEGACY in kinds)
            or (not origin.startswith("type:") and KIND_NEW in kinds)
        )
    ]
