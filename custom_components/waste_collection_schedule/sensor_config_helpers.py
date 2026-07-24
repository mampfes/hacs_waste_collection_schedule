"""Helpers for device-page configuration entities tied to waste sensors."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from copy import deepcopy
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from .const import (
    CONF_DETAILS_FORMAT,
    CONF_DEVICE_SENSOR_CONTROLS,
    CONF_PRESET_LANGUAGE,
    CONF_SENSOR_ID,
    CONF_SENSOR_LEGACY_UNIQUE_ID,
    CONF_SENSORS,
    DOMAIN,
)
from .waste_collection_schedule.waste_types import resolve

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

CONF_NAME = "name"
COMBINED_SENSOR_NAME = "Next waste pickup"
SENSOR_CONTROL_METADATA_KEYS = (
    CONF_SENSOR_ID,
    CONF_SENSOR_LEGACY_UNIQUE_ID,
    CONF_PRESET_LANGUAGE,
)
DEVICE_CONTROL_OPTION_KEYS = (CONF_DEVICE_SENSOR_CONTROLS,)


def preserve_device_control_options(
    existing_options: Mapping[str, Any], submitted_options: Mapping[str, Any]
) -> dict[str, Any]:
    """Preserve device-control metadata omitted by the legacy options form."""
    merged = deepcopy(dict(submitted_options))
    for key in DEVICE_CONTROL_OPTION_KEYS:
        if key in existing_options:
            merged[key] = deepcopy(existing_options[key])
    return merged


def preserve_sensor_control_metadata(
    original_sensor: Mapping[str, Any] | None,
    submitted_sensor: Mapping[str, Any],
) -> dict[str, Any]:
    """Preserve opaque identity metadata through a legacy sensor edit."""
    merged = deepcopy(dict(submitted_sensor))
    if original_sensor is None:
        return merged
    for key in SENSOR_CONTROL_METADATA_KEYS:
        if key in original_sensor:
            merged[key] = deepcopy(original_sensor[key])
    return merged


def build_legacy_ui_sensor_unique_id(shell_unique_id: str, sensor_name: str) -> str:
    """Return the previous name-based UI sensor unique ID."""
    return f"{shell_unique_id}_ui_sensor_{sensor_name}"


def build_stable_ui_sensor_unique_id(shell_unique_id: str, sensor_id: str) -> str:
    """Return the stable UI sensor unique ID."""
    return f"{shell_unique_id}_ui_sensor_{sensor_id}"


def build_ui_sensor_device_identifier(shell_unique_id: str, sensor_id: str) -> str:
    """Return the stable device identifier for a configured UI sensor."""
    return f"{shell_unique_id}_sensor_{sensor_id}"


def parse_ui_sensor_device_identifier(
    shell_unique_id: str, identifier: str
) -> str | None:
    """Extract the stable sensor ID from one of this integration's sensor devices."""
    prefix = f"{shell_unique_id}_sensor_"
    if not identifier.startswith(prefix):
        return None
    sensor_id = identifier.removeprefix(prefix)
    return sensor_id or None


def parse_ui_sensor_device_id(
    shell_unique_id: str, identifiers: Iterable[tuple[str, str]]
) -> str | None:
    """Extract a stable sensor ID from a Home Assistant device identifier set."""
    for domain, identifier in identifiers:
        if domain != DOMAIN:
            continue
        if sensor_id := parse_ui_sensor_device_identifier(shell_unique_id, identifier):
            return sensor_id
    return None


def build_ui_sensor_control_unique_id(
    shell_unique_id: str, sensor_id: str, key_suffix: str
) -> str:
    """Return the stable unique ID for a per-sensor config/control entity."""
    return f"{shell_unique_id}_ui_sensor_control_{sensor_id}_{key_suffix}"


def build_create_combined_ui_sensor_action_unique_id(shell_unique_id: str) -> str:
    """Return the stable unique ID for the combined-sensor creation action."""
    return f"{shell_unique_id}_ui_sensor_action_create_combined"


def build_create_ui_sensor_action_unique_id(
    shell_unique_id: str, collection_type: str
) -> str:
    """Return the stable unique ID for a collection-type creation action."""
    return f"{shell_unique_id}_ui_sensor_action_create_{collection_type}"


def build_ui_sensor_unique_id(
    shell_unique_id: str,
    sensor_name: str,
    sensor_id: str | None,
    preserve_legacy_unique_id: bool = False,
) -> str:
    """Return a stable ID for new sensors without renaming existing entities."""
    if sensor_id and not preserve_legacy_unique_id:
        return build_stable_ui_sensor_unique_id(shell_unique_id, sensor_id)
    return build_legacy_ui_sensor_unique_id(shell_unique_id, sensor_name)


def configured_sensor_ids(sensors: list[dict[str, Any]]) -> set[str]:
    """Return stable sensor IDs that are still configured."""
    return {
        sensor_id for sensor in sensors if (sensor_id := sensor.get(CONF_SENSOR_ID))
    }


def update_sensor_config_list_by_id(
    sensors: list[dict[str, Any]],
    sensor_id: str,
    updates: dict[str, Any] | None = None,
    removals: tuple[str, ...] = (),
) -> list[dict[str, Any]]:
    """Return a new sensor list with updates applied to one sensor by stable ID."""
    updated_sensors = deepcopy(sensors)
    for sensor in updated_sensors:
        if sensor.get(CONF_SENSOR_ID) != sensor_id:
            continue

        for key in removals:
            sensor.pop(key, None)

        if updates:
            sensor.update(updates)

        return updated_sensors

    raise KeyError(f"Sensor ID '{sensor_id}' not found")


def remove_sensor_config_by_id(
    sensors: list[dict[str, Any]],
    sensor_id: str,
) -> list[dict[str, Any]]:
    """Return a new sensor list without the sensor matching the stable ID."""
    return [
        deepcopy(sensor)
        for sensor in sensors
        if sensor.get(CONF_SENSOR_ID) != sensor_id
    ]


def ensure_sensor_ids(
    sensors: list[dict[str, Any]],
    id_factory: Callable[[], str] | None = None,
) -> tuple[list[dict[str, Any]], bool]:
    """Give existing sensors control IDs without changing their entity identity."""
    updated_sensors = deepcopy(sensors)
    changed = False
    factory = id_factory or (lambda: uuid4().hex)

    for sensor in updated_sensors:
        if sensor.get(CONF_SENSOR_ID):
            continue
        sensor[CONF_SENSOR_ID] = factory()
        sensor[CONF_SENSOR_LEGACY_UNIQUE_ID] = True
        changed = True

    return updated_sensors, changed


def configured_collection_types(sensors: list[dict[str, Any]]) -> set[str]:
    """Return collection types already covered by configured sensors."""
    types: set[str] = set()
    for sensor in sensors:
        sensor_types = sensor.get("types")
        if not sensor_types:
            continue
        types.update(str(sensor_type) for sensor_type in sensor_types)
    return types


def has_combined_sensor(sensors: list[dict[str, Any]]) -> bool:
    """Return True when an all-types/combined waste sensor is configured."""
    return any(not sensor.get("types") for sensor in sensors)


def missing_collection_types(
    available_types: Mapping[str, str],
    sensors: list[dict[str, Any]],
) -> list[tuple[str, str]]:
    """Return stable type IDs and labels not already covered by a sensor.

    Existing sensor filters may contain a localized/display label. New device
    actions persist the locale-independent ID introduced by WasteType in v3.
    """
    configured_ids: set[str] = set()
    normalized_labels = {
        " ".join(label.strip().casefold().split()): type_id
        for type_id, label in available_types.items()
    }
    for configured_type in configured_collection_types(sensors):
        if configured_type in available_types:
            configured_ids.add(configured_type)
            continue
        if canonical := resolve(configured_type):
            if canonical.id in available_types:
                configured_ids.add(canonical.id)
                continue
        normalized = " ".join(configured_type.strip().casefold().split())
        if type_id := normalized_labels.get(normalized):
            configured_ids.add(type_id)
    return sorted(
        (
            (type_id, label)
            for type_id, label in available_types.items()
            if type_id not in configured_ids
        ),
        key=lambda item: item[1].casefold(),
    )


def build_sensor_for_collection_type(
    collection_type_id: str,
    display_name: str,
    id_factory: Callable[[], str] | None = None,
) -> dict[str, Any]:
    """Build a default per-type waste pickup sensor configuration."""
    factory = id_factory or (lambda: uuid4().hex)
    return {
        CONF_NAME: display_name,
        CONF_SENSOR_ID: factory(),
        CONF_DETAILS_FORMAT: "upcoming",
        "types": [collection_type_id],
    }


def build_combined_waste_sensor(
    id_factory: Callable[[], str] | None = None,
) -> dict[str, Any]:
    """Build a default all-types sensor that groups same-day pickups together."""
    factory = id_factory or (lambda: uuid4().hex)
    return {
        CONF_NAME: COMBINED_SENSOR_NAME,
        CONF_SENSOR_ID: factory(),
        CONF_DETAILS_FORMAT: "upcoming",
    }


def build_updated_options_by_sensor_id(
    entry: ConfigEntry,
    sensor_id: str,
    updates: dict[str, Any] | None = None,
    removals: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Build a new config entry options payload for one stable sensor update."""
    options = deepcopy(dict(entry.options))
    options[CONF_SENSORS] = update_sensor_config_list_by_id(
        options.get(CONF_SENSORS, []),
        sensor_id=sensor_id,
        updates=updates,
        removals=removals,
    )
    return options


def build_removed_sensor_options(entry: ConfigEntry, sensor_id: str) -> dict[str, Any]:
    """Build a new config entry options payload without one stable sensor."""
    options = deepcopy(dict(entry.options))
    options[CONF_SENSORS] = remove_sensor_config_by_id(
        options.get(CONF_SENSORS, []), sensor_id=sensor_id
    )
    return options


def build_added_collection_type_sensor_options(
    entry: ConfigEntry,
    collection_type_id: str,
    display_name: str,
    id_factory: Callable[[], str] | None = None,
) -> dict[str, Any]:
    """Build a new config entry options payload with one per-type sensor added."""
    options = deepcopy(dict(entry.options))
    sensors = deepcopy(options.get(CONF_SENSORS, []))
    if not missing_collection_types(
        {collection_type_id: display_name},
        sensors,
    ):
        return options
    sensors.append(
        build_sensor_for_collection_type(
            collection_type_id,
            display_name,
            id_factory,
        )
    )
    options[CONF_SENSORS] = sensors
    return options


def build_added_combined_sensor_options(
    entry: ConfigEntry,
    id_factory: Callable[[], str] | None = None,
) -> dict[str, Any]:
    """Build a new config entry options payload with one combined sensor added."""
    options = deepcopy(dict(entry.options))
    sensors = deepcopy(options.get(CONF_SENSORS, []))
    if has_combined_sensor(sensors):
        return options
    sensors.append(build_combined_waste_sensor(id_factory))
    options[CONF_SENSORS] = sensors
    return options
