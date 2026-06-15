"""Helpers for device-page configuration entities tied to waste sensors."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from copy import deepcopy
from typing import TYPE_CHECKING, Any
from uuid import uuid4

try:
    from .const import CONF_DETAILS_FORMAT, CONF_SENSOR_ID, CONF_SENSORS, DOMAIN
    from .waste_collection_schedule.type_aliases import expand_requested_types
except ImportError:  # pragma: no cover - fallback for direct test imports
    from const import CONF_DETAILS_FORMAT, CONF_SENSOR_ID, CONF_SENSORS, DOMAIN
    from waste_collection_schedule.type_aliases import expand_requested_types

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

CONF_NAME = "name"
COMBINED_SENSOR_NAME = "Next waste pickup"


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


def build_remove_ui_sensor_action_unique_id(
    shell_unique_id: str, sensor_id: str
) -> str:
    """Return the stable unique ID for a per-sensor remove action."""
    return f"{shell_unique_id}_ui_sensor_action_remove_{sensor_id}"


def parse_stable_ui_sensor_id(shell_unique_id: str, unique_id: str) -> str | None:
    """Extract a stable sensor ID from one of this integration's UI sensor entities."""
    main_prefix = f"{shell_unique_id}_ui_sensor_"
    control_prefix = f"{shell_unique_id}_ui_sensor_control_"
    remove_prefix = f"{shell_unique_id}_ui_sensor_action_remove_"

    if unique_id.startswith(control_prefix):
        suffix = unique_id.removeprefix(control_prefix)
        sensor_id, _, _ = suffix.partition("_")
        return sensor_id or None

    if unique_id.startswith(remove_prefix):
        sensor_id = unique_id.removeprefix(remove_prefix)
        return sensor_id or None

    if unique_id.startswith(main_prefix) and "_ui_sensor_action_" not in unique_id:
        sensor_id = unique_id.removeprefix(main_prefix)
        return sensor_id or None

    return None


def build_ui_sensor_unique_id(
    shell_unique_id: str, sensor_name: str, sensor_id: str | None
) -> str:
    """Return the preferred UI sensor unique ID, with legacy fallback."""
    if sensor_id:
        return build_stable_ui_sensor_unique_id(shell_unique_id, sensor_id)
    return build_legacy_ui_sensor_unique_id(shell_unique_id, sensor_name)


def iter_ui_sensor_unique_id_migrations(
    shell_unique_id: str, sensors: list[dict[str, Any]]
) -> list[tuple[str, str]]:
    """Return legacy-to-stable unique ID migrations for configured sensors."""
    migrations = []
    for sensor in sensors:
        sensor_name = sensor.get(CONF_NAME)
        sensor_id = sensor.get(CONF_SENSOR_ID)
        if not sensor_name or not sensor_id:
            continue

        old_unique_id = build_legacy_ui_sensor_unique_id(shell_unique_id, sensor_name)
        new_unique_id = build_stable_ui_sensor_unique_id(shell_unique_id, sensor_id)
        if old_unique_id != new_unique_id:
            migrations.append((old_unique_id, new_unique_id))

    return migrations


def configured_sensor_ids(sensors: list[dict[str, Any]]) -> set[str]:
    """Return stable sensor IDs that are still configured."""
    return {
        sensor_id
        for sensor in sensors
        if (sensor_id := sensor.get(CONF_SENSOR_ID))
    }


def update_sensor_config_list(
    sensors: list[dict[str, Any]],
    sensor_name: str,
    updates: dict[str, Any] | None = None,
    removals: tuple[str, ...] = (),
) -> list[dict[str, Any]]:
    """Return a new sensor list with updates applied to one sensor by name."""
    updated_sensors = deepcopy(sensors)
    for sensor in updated_sensors:
        if sensor.get(CONF_NAME) != sensor_name:
            continue

        for key in removals:
            sensor.pop(key, None)

        if updates:
            sensor.update(updates)

        return updated_sensors

    raise KeyError(f"Sensor '{sensor_name}' not found")


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
    """Return sensors with stable IDs ensured for every configured sensor."""
    updated_sensors = deepcopy(sensors)
    changed = False
    factory = id_factory or (lambda: uuid4().hex)

    for sensor in updated_sensors:
        if sensor.get(CONF_SENSOR_ID):
            continue
        sensor[CONF_SENSOR_ID] = factory()
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
    available_types: set[str],
    sensors: list[dict[str, Any]],
    customizations: Mapping[str, Any] | None = None,
) -> list[str]:
    """Return available collection types not already covered by a sensor."""
    configured_types = configured_collection_types(sensors)
    expanded_configured_types = expand_requested_types(
        configured_types, customizations
    )
    return sorted(available_types - (expanded_configured_types or set()))


def build_sensor_for_collection_type(
    collection_type: str,
    id_factory: Callable[[], str] | None = None,
) -> dict[str, Any]:
    """Build a default per-type waste pickup sensor configuration."""
    factory = id_factory or (lambda: uuid4().hex)
    return {
        CONF_NAME: collection_type,
        CONF_SENSOR_ID: factory(),
        CONF_DETAILS_FORMAT: "upcoming",
        "types": [collection_type],
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


def replace_sensor_config(
    sensors: list[dict[str, Any]],
    original_sensor_name: str,
    replacement: dict[str, Any],
) -> list[dict[str, Any]]:
    """Return a new sensor list with one sensor fully replaced by name."""
    updated_sensors = deepcopy(sensors)
    for idx, sensor in enumerate(updated_sensors):
        if sensor.get(CONF_NAME) != original_sensor_name:
            continue

        updated_sensors[idx] = deepcopy(replacement)
        return updated_sensors

    raise KeyError(f"Sensor '{original_sensor_name}' not found")


def build_updated_options(
    entry: ConfigEntry,
    sensor_name: str,
    updates: dict[str, Any] | None = None,
    removals: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Build a new config entry options payload for one sensor update."""
    options = deepcopy(dict(entry.options))
    options[CONF_SENSORS] = update_sensor_config_list(
        options.get(CONF_SENSORS, []),
        sensor_name=sensor_name,
        updates=updates,
        removals=removals,
    )
    return options


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


def build_replaced_sensor_options(
    entry: ConfigEntry,
    original_sensor_name: str,
    replacement: dict[str, Any],
) -> dict[str, Any]:
    """Build a new config entry options payload with one sensor fully replaced."""
    options = deepcopy(dict(entry.options))
    options[CONF_SENSORS] = replace_sensor_config(
        options.get(CONF_SENSORS, []),
        original_sensor_name=original_sensor_name,
        replacement=replacement,
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
    collection_type: str,
    id_factory: Callable[[], str] | None = None,
) -> dict[str, Any]:
    """Build a new config entry options payload with one per-type sensor added."""
    options = deepcopy(dict(entry.options))
    sensors = deepcopy(options.get(CONF_SENSORS, []))
    sensors.append(build_sensor_for_collection_type(collection_type, id_factory))
    options[CONF_SENSORS] = sensors
    return options


def build_added_combined_sensor_options(
    entry: ConfigEntry,
    id_factory: Callable[[], str] | None = None,
) -> dict[str, Any]:
    """Build a new config entry options payload with one combined sensor added."""
    options = deepcopy(dict(entry.options))
    sensors = deepcopy(options.get(CONF_SENSORS, []))
    sensors.append(build_combined_waste_sensor(id_factory))
    options[CONF_SENSORS] = sensors
    return options
