"""Native options forms over the shared sensor record and manager."""

from copy import deepcopy

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.config_entries import OptionsFlow
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TimeSelector,
)

from .config_flow import get_customize_schema
from .const import DOMAIN
from .default_sensors import catalogue
from .sensor_model import (
    DATE_FORMATS,
    DETAILS_FORMATS,
    KINDS,
    LANGUAGES,
    STATE_FORMATS,
    SensorConfig,
)
from .waste_collection_schedule.source_shell import (
    default_ignore_duplicates,
    source_supports_show_original_label,
)


def choices(values, *, multiple=False, custom_value=False):
    sets = {
        "state_format": STATE_FORMATS,
        "date_format": DATE_FORMATS,
        "details_format": DETAILS_FORMATS,
        "language": LANGUAGES,
        "kind": KINDS,
    }
    translation_key = next(
        (key for key, options in sets.items() if tuple(values) == options), "action"
    )
    return SelectSelector(
        SelectSelectorConfig(
            options=list(values),
            mode=SelectSelectorMode.LIST
            if multiple and not custom_value
            else SelectSelectorMode.DROPDOWN,
            multiple=multiple,
            custom_value=custom_value,
            translation_key=translation_key,
        )
    )


class SensorOptionsFlow(OptionsFlow):
    def __init__(self, entry):
        self._entry = entry

    @property
    def manager(self):
        coordinator = self.hass.data.get(DOMAIN, {}).get(self._entry.entry_id)
        return getattr(coordinator, "sensor_manager", None)

    @property
    def type_labels(self):
        if self.manager:
            return self.manager.type_labels
        from waste_collection_schedule.waste_types import ALL_TYPES, display_name

        known = {wt.id: display_name(wt) for wt in ALL_TYPES}
        customizations = self._entry.options.get("customize", {})
        return {
            key: customizations.get(key, {}).get("alias") or known.get(key, key)
            for record in self._entry.options.get("sensors", [])
            for key in record["types"]
        }

    @property
    def raw_labels(self):
        return self.manager.coordinator.shell.raw_labels if self.manager else []

    @property
    def catalogue(self):
        return self.manager.catalogue if self.manager else catalogue(self.type_labels)

    async def async_step_init(self, user_input=None):
        return self.async_show_menu(
            step_id="init", menu_options=["source_settings", "sensors", "waste_types"]
        )

    async def async_step_source_settings(self, user_input=None):
        errors = {}
        if user_input is not None:
            try:
                cv.time(user_input["fetch_time"])
                cv.time(user_input["day_switch_time"])
                return self.async_create_entry(
                    data={**self._entry.options, **user_input}
                )
            except vol.Invalid:
                errors["base"] = "time_format"
        options = self._entry.options
        source_name = self._entry.data["name"]
        schema = {
            vol.Optional(
                "calendar_title",
                default=options.get("calendar_title", self._entry.title),
            ): str,
            vol.Required("separator", default=options.get("separator", ", ")): str,
            vol.Required(
                "fetch_time", default=options.get("fetch_time", "01:00")
            ): TimeSelector(),
            vol.Required(
                "day_switch_time", default=options.get("day_switch_time", "10:00")
            ): TimeSelector(),
            vol.Required(
                "fetch_interval_days", default=options.get("fetch_interval_days", 1)
            ): vol.All(int, vol.Range(min=1)),
            vol.Required(
                "random_fetch_time_offset",
                default=options.get("random_fetch_time_offset", 60),
            ): vol.All(int, vol.Range(min=0)),
            vol.Required("day_offset", default=options.get("day_offset", 0)): int,
            vol.Required(
                "ignore_duplicates",
                default=options.get(
                    "ignore_duplicates", default_ignore_duplicates(source_name)
                ),
            ): bool,
        }
        if source_supports_show_original_label(source_name):
            schema[
                vol.Required(
                    "show_original_label",
                    default=options.get("show_original_label", True),
                )
            ] = bool
        return self.async_show_form(
            step_id="source_settings", data_schema=vol.Schema(schema), errors=errors
        )

    async def async_step_sensors(self, user_input=None):
        self._records = deepcopy(self._entry.options.get("sensors", []))
        offered = self.catalogue
        for record in self._records:
            if record["origin"] != "custom":
                offered.setdefault(record["origin"], record)
        if user_input is not None:
            enabled = set(user_input.get("predefined", []))
            for record in self._records:
                if record["origin"] != "custom":
                    record["enabled"] = record["origin"] in enabled
            present = {r["origin"] for r in self._records}
            self._records.extend(deepcopy(offered[key]) for key in enabled - present)
            self._pending_options = {
                **self._entry.options,
                "sensors": self._records,
                "device_controls": user_input.get("device_controls", False),
                "auto_add_types": user_input.get("auto_add_types", False),
            }
            selection = user_input.get("edit_sensor")
            if selection:
                self._editing = next(
                    (r for r in self._records if r["id"] == selection), None
                )
                if self._editing is None:
                    self._editing = SensorConfig(
                        name="", state_format="relative", language="auto"
                    ).__dict__.copy()
                return await self.async_step_edit_sensor()
            return self.async_create_entry(data=self._pending_options)
        schema = {
            vol.Optional(
                "predefined",
                default=[
                    r["origin"]
                    for r in self._records
                    if r["origin"] != "custom" and r["enabled"]
                ],
            ): choices(
                [{"value": key, "label": r["name"]} for key, r in offered.items()],
                multiple=True,
            ),
            vol.Optional("edit_sensor"): choices(
                [{"value": r["id"], "label": r["name"]} for r in self._records]
                + [{"value": "add_custom", "label": "Add custom sensor"}]
            ),
            vol.Optional(
                "device_controls",
                default=self._entry.options.get("device_controls", False),
            ): bool,
            vol.Optional(
                "auto_add_types",
                default=self._entry.options.get("auto_add_types", False),
            ): bool,
        }
        return self.async_show_form(step_id="sensors", data_schema=vol.Schema(schema))

    def _filter_choices(self):
        labels = {key: f"{label} ({key})" for key, label in self.type_labels.items()}
        labels.update({label: label for label in self.raw_labels})
        for record in self._entry.options.get("sensors", []):
            for label in (*record["types"], *record["exclude_types"]):
                labels.setdefault(label, label)
        return [{"value": key, "label": label} for key, label in labels.items()]

    def _format_choices(self, record, *, date_only=False):
        from datetime import timedelta
        from types import SimpleNamespace

        from homeassistant.util import dt as dt_util

        from .sensor_format import language_for, render_date, render_state

        language = language_for(record["language"], self.hass.config.language)
        labels = [self.type_labels.get(t, t) for t in record["types"]] or list(
            self.type_labels.values()
        )
        example = SimpleNamespace(
            date=dt_util.now().date() + timedelta(days=3), daysTo=3, types=labels[:2]
        )
        if date_only:
            options = [
                {"value": style, "label": render_date(example.date, style, language)}
                for style in DATE_FORMATS
            ]
        else:
            options = [
                {
                    "value": style,
                    "label": "Custom template"
                    if style == "custom"
                    else str(
                        render_state(
                            example,
                            style,
                            record["date_format"],
                            language,
                            self._entry.options.get("separator", ", "),
                        )
                    ),
                }
                for style in STATE_FORMATS
            ]
        return SelectSelector(
            SelectSelectorConfig(options=options, mode=SelectSelectorMode.DROPDOWN)
        )

    async def async_step_edit_sensor(self, user_input=None):
        record = self._editing
        custom = record["origin"] == "custom"
        errors = {}
        if user_input is not None:
            user_input = dict(user_input)
            action = user_input.pop("action", "save")
            advanced = user_input.pop("advanced", False)
            if action == "delete" and custom:
                self._records[:] = [r for r in self._records if r["id"] != record["id"]]
                return self.async_create_entry(data=self._pending_options)
            if action == "duplicate":
                duplicate = {
                    **record,
                    "id": SensorConfig(name=record["name"]).id,
                    "origin": "custom",
                    "name": record["name"] + " copy",
                }
                self._editing = duplicate
                return self._save_sensor()
            if action == "reset" and not custom:
                default = self.catalogue.get(record["origin"])
                if default:
                    self._editing = {**default, "enabled": record["enabled"]}
                    return self._save_sensor()
            try:
                if not custom:
                    user_input.pop("types", None)
                    user_input.pop("kind", None)
                if record["kind"] != "last_update":
                    for key in ("count", "leadtime"):
                        user_input[key] = user_input.get(key)
                if (
                    user_input.get("state_format", "custom") != "custom"
                    and user_input.get("state_format") != record["state_format"]
                ):
                    user_input["value_template"] = None
                if (
                    user_input.get("date_format", record["date_format"])
                    != record["date_format"]
                ):
                    user_input["date_template"] = None
                self._editing = SensorConfig.from_dict(
                    {**record, **user_input}
                ).as_dict()
                if advanced or (
                    self._editing["state_format"] == "custom"
                    and not self._editing["value_template"]
                ):
                    return await self.async_step_sensor_advanced()
                return self._save_sensor()
            except vol.Invalid:
                errors["base"] = "invalid_sensor"
        schema = {
            vol.Required("name", default=record["name"]): cv.string,
            vol.Required("enabled", default=record["enabled"]): bool,
            vol.Required(
                "state_format", default=record["state_format"]
            ): self._format_choices(record),
            vol.Required("language", default=record["language"]): choices(LANGUAGES),
            vol.Required(
                "date_format", default=record["date_format"]
            ): self._format_choices(record, date_only=True),
            vol.Required("details_format", default=record["details_format"]): choices(
                DETAILS_FORMATS
            ),
            vol.Optional(
                "count", description={"suggested_value": record["count"]}
            ): vol.All(int, vol.Range(min=1)),
            vol.Optional(
                "leadtime", description={"suggested_value": record["leadtime"]}
            ): vol.All(int, vol.Range(min=0)),
            vol.Required("unique_types", default=record["unique_types"]): bool,
            vol.Optional(
                "exclude_types", default=record["exclude_types"]
            ): SelectSelector(
                SelectSelectorConfig(
                    options=self._filter_choices(),
                    multiple=True,
                    custom_value=True,
                )
            ),
            vol.Optional("advanced", default=False): bool,
            vol.Optional("action", default="save"): choices(
                ["save", "delete"] if custom else ["save", "reset", "duplicate"]
            ),
        }
        if custom:
            schema[vol.Optional("types", default=record["types"])] = SelectSelector(
                SelectSelectorConfig(
                    options=self._filter_choices(),
                    multiple=True,
                    custom_value=True,
                )
            )
            schema[vol.Required("kind", default=record["kind"])] = choices(KINDS)
        if record["kind"] == "last_update":
            schema = {
                key: value
                for key, value in schema.items()
                if str(key) in ("name", "enabled", "kind", "action")
            }
        elif record["kind"] == "days_to":
            schema = {
                key: value
                for key, value in schema.items()
                if str(key) != "state_format"
            }
        return self.async_show_form(
            step_id="edit_sensor", data_schema=vol.Schema(schema), errors=errors
        )

    async def async_step_sensor_advanced(self, user_input=None):
        from .waste_collection_schedule.colors import validate_color

        record = self._editing
        errors = {}
        if user_input is not None:
            try:
                patch = dict(user_input)
                for key in ("value_template", "date_template"):
                    patch[key] = patch.get(key) or None
                    if patch[key]:
                        cv.template(patch[key])
                patch["color"] = (
                    validate_color(patch["color"]) if patch.get("color") else None
                )
                if patch["value_template"]:
                    patch["state_format"] = "custom"
                elif record["state_format"] == "custom":
                    patch["state_format"] = "types_in_days"
                self._editing = SensorConfig.from_dict({**record, **patch}).as_dict()
                return self._save_sensor()
            except (vol.Invalid, ValueError):
                errors["base"] = "invalid_sensor"
        return self.async_show_form(
            step_id="sensor_advanced",
            data_schema=vol.Schema(
                {
                    vol.Required("event_index", default=record["event_index"]): vol.All(
                        int, vol.Range(min=0)
                    ),
                    vol.Optional(
                        "value_template", default=record["value_template"] or ""
                    ): str,
                    vol.Optional(
                        "date_template", default=record["date_template"] or ""
                    ): str,
                    vol.Optional("color", default=record["color"] or ""): str,
                }
            ),
            errors=errors,
        )

    def _save_sensor(self):
        record = self._editing
        self._records[:] = [
            record if r["id"] == record["id"] else r for r in self._records
        ]
        if not any(r["id"] == record["id"] for r in self._records):
            self._records.append(record)
        return self.async_create_entry(data=self._pending_options)

    async def async_step_waste_types(self, user_input=None):
        labels = {**self.type_labels}
        labels.update({label: label for label in self.raw_labels})
        labels.update({key: key for key in self._entry.options.get("customize", {})})
        if user_input is not None:
            self._options = deepcopy(dict(self._entry.options))
            self._customize_select = user_input.get("types", [])
            self._customize_select_idx = 0
            return await self.async_step_customize()
        return self.async_show_form(
            step_id="waste_types",
            data_schema=vol.Schema(
                {
                    vol.Optional("types"): choices(
                        [{"value": k, "label": v} for k, v in labels.items()],
                        multiple=True,
                        custom_value=True,
                    )
                }
            ),
        )

    async def async_step_customize(self, user_input=None):
        from .waste_collection_schedule.colors import validate_color

        if self._customize_select_idx >= len(self._customize_select):
            return self.async_create_entry(data=self._options)
        key = self._customize_select[self._customize_select_idx]
        current = self._options.get("customize", {}).get(key, {})
        errors = {}
        if user_input is not None:
            values = {k: v for k, v in user_input.items() if k != "delete"}
            try:
                if values.get("color") and not user_input.get("delete"):
                    values["color"] = validate_color(values["color"])
                else:
                    values.pop("color", None)
            except ValueError:
                errors["base"] = "invalid_sensor"
            else:
                customizations = self._options.setdefault("customize", {})
                if user_input.get("delete"):
                    customizations.pop(key, None)
                else:
                    customizations[key] = values
                self._customize_select_idx += 1
                return await self.async_step_customize()
        schema = get_customize_schema({**current, **(user_input or {})})
        schema[vol.Optional("delete", default=False)] = bool
        return self.async_show_form(
            step_id="customize",
            data_schema=vol.Schema(schema),
            errors=errors,
            description_placeholders={
                "type": key,
                "index": str(self._customize_select_idx + 1),
                "total": str(len(self._customize_select)),
            },
        )
