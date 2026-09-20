"""Default sensors created for a config entry.

One place decides what a default sensor is, so the config flow (new entry) and
the options flow (adding defaults to an existing entry) create the same ones.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from homeassistant.const import CONF_NAME, CONF_VALUE_TEMPLATE
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    CONF_COLLECTION_TYPES,
    CONF_DETAILS_FORMAT,
    CONF_SENSOR_MODE,
    SENSOR_MODE_DAYS_TO,
    SENSOR_MODE_LAST_UPDATE,
)

# One sensor per waste type, exactly as the config flow always created them.
KIND_LEGACY = "legacy"

# Value template of the per-type default sensors. Stored with the sensor, so
# changing it here never alters an existing entry.
LEGACY_VALUE_TEMPLATE = (
    'on {{value.date.strftime("%a")}}, {{value.date.strftime("%d.%m.%Y")}}'
)

# The sensors that expose language-neutral raw values for cards and templates.
KIND_NEW = "new"

# English on purpose: the name fixes the entity id, so every user gets the same
# ids and the documentation examples work when copied. Users can rename them.
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


def build_default_sensors(
    kinds: Iterable[str],
    fetched_types: Iterable[str],
    existing: Iterable[dict[str, Any]] = (),
) -> list[dict[str, Any]]:
    """Return the default sensors to add next to the ``existing`` ones.

    A default is skipped when a sensor with the same name already exists, so a
    custom sensor named like a waste type replaces that default and re-running
    this for an entry never duplicates a sensor.
    """
    kinds = set(kinds)
    taken = {s.get(CONF_NAME) for s in existing}
    sensors: list[dict[str, Any]] = []

    if KIND_LEGACY in kinds:
        for t in fetched_types:
            if not t or t in taken:
                continue
            taken.add(t)
            sensors.append(
                {
                    CONF_NAME: t,
                    CONF_DETAILS_FORMAT: "upcoming",
                    CONF_COLLECTION_TYPES: [t],
                    CONF_VALUE_TEMPLATE: LEGACY_VALUE_TEMPLATE,
                }
            )

    if KIND_NEW in kinds:
        for sensor in _new_sensors():
            if sensor[CONF_NAME] not in taken:
                taken.add(sensor[CONF_NAME])
                sensors.append(sensor)

    return sensors


def _new_sensors() -> list[dict[str, Any]]:
    """The overview sensors, all over every waste type.

    `hidden` keeps their attributes to the raw values (daysTo, date,
    next_types, color) instead of a list of upcoming dates.
    """
    return [
        # State = the types collected on the next day.
        {
            CONF_NAME: NEXT_COLLECTION_NAME,
            CONF_DETAILS_FORMAT: "hidden",
            CONF_VALUE_TEMPLATE: '{{value.types|join(", ")}}',
        },
        # State = a number of days, for automations.
        {
            CONF_NAME: DAYS_TO_NAME,
            CONF_DETAILS_FORMAT: "hidden",
            CONF_SENSOR_MODE: SENSOR_MODE_DAYS_TO,
        },
        # State = when the schedule was last fetched (diagnostic).
        {
            CONF_NAME: LAST_UPDATE_NAME,
            CONF_DETAILS_FORMAT: "hidden",
            CONF_SENSOR_MODE: SENSOR_MODE_LAST_UPDATE,
        },
    ]
