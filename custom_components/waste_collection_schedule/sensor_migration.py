"""Upgrade name-based sensors without replacing their registry entities."""

import logging
from hashlib import sha256

from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import issue_registry as ir

from .const import DOMAIN
from .default_sensors import LEGACY_VALUE_TEMPLATE
from .sensor_model import SensorConfig, catalogue_id, migrate_filter
from .waste_collection_schedule.source_shell import _load_source_class
from .waste_collection_schedule.waste_types import ALL_TYPES

_LOGGER = logging.getLogger(__name__)


def migrate_records(
    options: dict, type_ids: set[str] | frozenset[str] = frozenset()
) -> dict:
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
    # Older UI flows saved canonical display names as customization keys.
    # Normalize those alongside their sensor filters; explicit ids win collisions.
    customize = {
        migrate_filter(key, {}, type_ids): customize[key]
        for key in sorted(customize, key=lambda key: key in type_ids)
    }
    if "customize" in options:
        result["customize"] = customize
    for old in options.get("sensors", []):
        if "id" in old and "origin" in old:
            records.append(SensorConfig.from_dict(old).as_dict())
            origins.add(old["origin"])
            continue
        details = old.get("details_format", "upcoming")
        details = getattr(details, "value", details)
        kind = old.get("mode") or "schedule"
        types = [migrate_filter(t, customize, type_ids) for t in old.get("types") or []]
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
                migrate_filter(t, customize, type_ids)
                for t in old.get("exclude_types") or []
            ],
            unique_types=old.get("unique_types", False),
        )
        if origin != "custom":
            record.id = catalogue_id(origin)
        else:
            # A registry write can survive a crash before the options write.
            # Reconstruct the same custom id when migrating those old options again.
            identity = (
                old.get("sensor_id")
                or old.get("sensor_legacy_unique_id")
                or old["name"]
            )
            record.id = "c_" + sha256(identity.encode()).hexdigest()[:8]
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
        elif record.state_format == "date" and record.date_format != "iso":
            # Old detail keys defaulted to ISO independently of the state template.
            # Preserve that implicit format through the existing template override.
            record.date_template = EXAMPLE_DATE_TEMPLATES["2020-03-20"]
        records.append(record.as_dict())
    result["sensors"] = records
    return result


async def async_migrate_sensors(hass, entry, *, source_name=None) -> dict:
    source_cls, _ = await hass.async_add_executor_job(
        _load_source_class, source_name or entry.data.get("name", "")
    )
    # Raw-string sources such as ICS/static do not declare canonical categories.
    # A matching vocabulary name alone cannot prove their provider label is an id.
    type_ids = {wt.id for wt in getattr(source_cls, "WASTE_TYPES", ())}
    options = migrate_records(dict(entry.options), type_ids)
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
        target = registry.async_get_entity_id("sensor", DOMAIN, new_uid)
        if not entity_id and not target:
            continue
        registered = registry.async_get(target or entity_id)
        if registered is not None and registered.disabled_by is not None:
            record["enabled"] = False
        if not entity_id:
            continue
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
