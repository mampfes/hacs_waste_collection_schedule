"""Default sensors created for a config entry.

One place decides what a default sensor is, so the config flow (new entry) and
the options flow (adding defaults to an existing entry) create the same ones.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from homeassistant.const import CONF_NAME, CONF_VALUE_TEMPLATE

from .const import CONF_COLLECTION_TYPES, CONF_DETAILS_FORMAT

# One sensor per waste type, exactly as the config flow always created them.
KIND_LEGACY = "legacy"

# Value template of the per-type default sensors. Stored with the sensor, so
# changing it here never alters an existing entry.
LEGACY_VALUE_TEMPLATE = (
    'on {{value.date.strftime("%a")}}, {{value.date.strftime("%d.%m.%Y")}}'
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

    return sensors
