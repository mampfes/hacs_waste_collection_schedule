"""Upgrade name-based sensors without replacing their registry entities."""

import logging

from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import issue_registry as ir

from .const import DOMAIN
from .default_sensors import LEGACY_VALUE_TEMPLATE
from .sensor_model import SensorConfig, catalogue_id, migrate_filter
from .waste_collection_schedule.waste_types import ALL_TYPES

_LOGGER = logging.getLogger(__name__)


def migrate_records(options: dict) -> dict:
    """Convert legacy sensor dictionaries; never guess at custom Jinja or bin labels."""
    from .config_flow import EXAMPLE_DATE_TEMPLATES, EXAMPLE_VALUE_TEMPLATES

    result = {
        k: v
        for k, v in options.items()
        if k not in ("sensor_select", "customize_select")
    }
    result["auto_add_types"] = False
    result["device_controls"] = False
    records = []
    origins = set()
    customize = options.get("customize", {})
    for old in options.get("sensors", []):
        if "id" in old and "origin" in old:
            records.append(SensorConfig.from_dict(old).as_dict())
            origins.add(old["origin"])
            continue
        details = old.get("details_format", "upcoming")
        details = getattr(details, "value", details)
        kind = old.get("mode") or "schedule"
        types = [migrate_filter(t, customize) for t in old.get("types") or []]
        value = (old.get("value_template") or "").strip()
        date = (old.get("date_template") or "").strip()
        origin = "custom"
        if kind == "days_to":
            origin = "days_until"
        elif kind == "last_update":
            origin = "last_update"
        elif (
            not types
            and details == "hidden"
            and value == EXAMPLE_VALUE_TEMPLATES["next collections"]
        ):
            origin = "next_collection"
        elif (
            len(types) == 1
            and (
                types[0] in {wt.id for wt in ALL_TYPES}
                or types[0].startswith("preserved:")
            )
            and details == "upcoming"
            and value == LEGACY_VALUE_TEMPLATE
        ):
            origin = "type:" + types[0]
        if origin in origins:
            origin = "custom"
        origins.add(origin)
        record = SensorConfig(
            name=old["name"],
            origin=origin,
            kind=kind,
            types=types,
            details_format=details,
            count=old.get("count"),
            leadtime=old.get("leadtime"),
            event_index=old.get("event_index") or 0,
            exclude_types=[
                migrate_filter(t, customize) for t in old.get("exclude_types") or []
            ],
            unique_types=old.get("unique_types", False),
        )
        if origin != "custom":
            record.id = catalogue_id(origin)
        formats = {
            "in .. days": "in_days",
            ".. in .. days": "types_in_days",
            "numeric daysTo": "days",
            "in .. days / Tomorrow / Today": "relative",
            "on Weekday, dd.mm.yyyy": "date",
            "on Weekday, yyyy-mm-dd": "date",
            "next collections": "types",
        }
        if value:
            # Keep comma-joining templates custom when the entry uses a
            # different separator; otherwise migrating changes visible text.
            preset = next(
                (k for k, v in EXAMPLE_VALUE_TEMPLATES.items() if v == value), None
            )
            if preset and (
                "join" not in value or options.get("separator", ", ") == ", "
            ):
                record.state_format = formats[preset]
                if record.state_format == "date":
                    record.date_format = (
                        "weekday_iso" if "yyyy-mm-dd" in preset else "weekday_dmy"
                    )
            else:
                record.state_format = "custom"
                record.value_template = value
        if date:
            formats_date = dict(
                zip(
                    list(EXAMPLE_DATE_TEMPLATES.values())[1:],
                    ("dmy", "weekday_dmy", "mdy", "weekday_mdy", "iso", "weekday_iso"),
                    strict=True,
                )
            )
            # A single date_format controls date states and detail keys. Keep
            # a conflicting old date template instead of changing either.
            style = formats_date.get(date)
            if style and (record.state_format != "date" or style == record.date_format):
                record.date_format = style
            else:
                record.date_template = date
        records.append(record.as_dict())
    result["sensors"] = records
    return result


async def async_migrate_sensors(hass, entry) -> dict:
    options = migrate_records(dict(entry.options))
    registry = er.async_get(hass)
    for old, record in zip(
        entry.options.get("sensors", []), options["sensors"], strict=True
    ):
        old_uid = f"{entry.entry_id}_ui_sensor_{old['name']}"
        new_uid = f"{entry.entry_id}_sensor_{record['id']}"
        candidates = [old_uid]
        if old.get("sensor_id"):
            candidates.append(f"{entry.entry_id}_ui_sensor_{old['sensor_id']}")
        # The published opt-in preview stored a frozen legacy unique id.
        frozen_id = old.get("sensor_legacy_unique_id")
        if isinstance(frozen_id, str) and "_ui_sensor_" in frozen_id:
            candidates.append(
                entry.entry_id + "_ui_sensor_" + frozen_id.split("_ui_sensor_", 1)[1]
            )
        entity_id = next(
            (
                found
                for uid in candidates
                if (found := registry.async_get_entity_id("sensor", DOMAIN, uid))
            ),
            None,
        )
        if not entity_id:
            continue
        registered = registry.async_get(entity_id)
        if registered is not None and registered.disabled_by is not None:
            record["enabled"] = False
        target = registry.async_get_entity_id("sensor", DOMAIN, new_uid)
        if target is not None and target != entity_id:
            _LOGGER.warning(
                "Sensor migration retained %s: target identity already exists",
                entity_id,
            )
            continue
        registry.async_update_entity(entity_id, new_unique_id=new_uid)
    report_legacy_orphans(hass, entry)
    return options


def report_legacy_orphans(hass, entry):
    registry = er.async_get(hass)
    entities = [
        e.entity_id
        for e in er.async_entries_for_config_entry(registry, entry.entry_id)
        if e.domain == "sensor"
        and e.platform == DOMAIN
        and e.unique_id.startswith(f"{entry.entry_id}_ui_sensor_")
    ]
    if entities:
        ir.async_create_issue(
            hass,
            DOMAIN,
            "legacy_sensors_" + entry.entry_id,
            is_fixable=True,
            severity=ir.IssueSeverity.WARNING,
            translation_key="legacy_sensors",
            translation_placeholders={"entities": ", ".join(entities)},
            data={"entry_id": entry.entry_id},
        )
