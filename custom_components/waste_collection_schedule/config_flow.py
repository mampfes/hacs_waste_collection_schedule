import importlib
import inspect
import json
import logging
import re
import types
from datetime import date, datetime
from pathlib import Path

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, OptionsFlow
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
)
from voluptuous.schema_builder import UNDEFINED

from .const import (
    CONF_COUNTRY_NAME,
    CONF_DAY_SWITCH_TIME,
    CONF_DAY_SWITCH_TIME_DEFAULT,
    CONF_FETCH_TIME,
    CONF_FETCH_TIME_DEFAULT,
    CONF_RANDOM_FETCH_TIME_OFFSET,
    CONF_RANDOM_FETCH_TIME_OFFSET_DEFAULT,
    CONF_SEPARATOR,
    CONF_SEPARATOR_DEFAULT,
    CONF_SOURCE_ARGS,
    CONF_SOURCE_CALENDAR_TITLE,
    CONF_SOURCE_NAME,
    CONFIG_VERSION,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

SUPPORTED_ARG_TYPES = {
    str: cv.string,
    int: cv.positive_int,
    bool: cv.boolean,
    list: TextSelector(TextSelectorConfig(multiple=True)),
    date: cv.date,
    datetime: cv.datetime,
}


class WasteCollectionConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow."""

    VERSION = CONFIG_VERSION
    _country = None
    _source = None

    _sources: dict = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._sources = self._get_source_list()

    # Get source list from JSON
    def _get_source_list(self):
        p = Path(__file__).with_name("sources.json")
        with p.open(encoding="utf-8") as json_file:
            return json.load(json_file)

    # Step 1: User selects country
    async def async_step_user(self, info):
        SCHEMA = vol.Schema(
            {
                vol.Required(CONF_COUNTRY_NAME): SelectSelector(
                    SelectSelectorConfig(
                        options=[""] + list(self._sources.keys()),
                        mode=SelectSelectorMode.DROPDOWN,
                        sort=True,
                    )
                )
            }
        )

        if info is not None:
            self._country = info[CONF_COUNTRY_NAME]
            return await self.async_step_source()

        return self.async_show_form(step_id="user", data_schema=SCHEMA)

    # Step 2: User selects country
    async def async_step_source(self, info=None):
        sources = self._sources[self._country]
        sources = [SelectOptionDict(value="", label="")] + [
            SelectOptionDict(
                value=f"{x['module']}\t({x['title']})",
                label=f"{x['title']} ({x['module']})",
            )
            for x in sources
        ]

        SCHEMA = vol.Schema(
            {
                vol.Required(CONF_SOURCE_NAME): SelectSelector(
                    SelectSelectorConfig(
                        options=sources, mode=SelectSelectorMode.DROPDOWN, sort=True
                    )
                )
            }
        )

        if info is not None:
            self._source = info[CONF_SOURCE_NAME].split("\t")[0]
            self._default_params = next(
                (
                    x["default_params"]
                    for x in self._sources[self._country]
                    if f"{x['module']}\t({x['title']})" == info[CONF_SOURCE_NAME]
                ),
                {},
            )
            return await self.async_step_args()

        return self.async_show_form(step_id="source", data_schema=SCHEMA)

    # Step 3: User fills in source arguments
    async def async_step_args(self, args_input=None):
        description_placeholders: dict = {}
        _LOGGER.debug(f"Default params: {self._default_params}")
        # Import source and get arguments
        module = await self.hass.async_add_executor_job(
            importlib.import_module, f"waste_collection_schedule.source.{self._source}"
        )
        title = module.TITLE

        args = dict(inspect.signature(module.Source.__init__).parameters)
        del args["self"]  # Remove self
        # Convert schema for vol
        description = None
        if args_input is not None and CONF_SOURCE_CALENDAR_TITLE in args_input:
            description = {"suggested_value": args_input[CONF_SOURCE_CALENDAR_TITLE]}
        vol_args = {
            vol.Optional(CONF_SOURCE_CALENDAR_TITLE, description=description): str,
        }

        for arg in args:
            default = args[arg].default
            annotation = args[arg].annotation
            description = None
            if args_input is not None and args[arg].name in args_input:
                description = {"suggested_value": args_input[args[arg].name]}
                _LOGGER.debug(
                    f"Setting suggested value for {args[arg].name} to {args_input[args[arg].name]} (previously filled in)"
                )
            elif args[arg].name in self._default_params:
                _LOGGER.debug(
                    f"Setting default value for {args[arg].name} to {self._default_params[args[arg].name]}"
                )
                description = {
                    "suggested_value": self._default_params[args[arg].name],
                    "data_description": "HASLLO LKASJFÖLKJ",
                }

            if default == inspect.Signature.empty and annotation != inspect._empty:
                if annotation in SUPPORTED_ARG_TYPES:
                    default = annotation()
                elif isinstance(annotation, types.UnionType):
                    for a in annotation.__args__:
                        if a in SUPPORTED_ARG_TYPES:
                            default = a()
                            _LOGGER.debug(
                                f"set default to {default} for {args[arg].name} from UnionType"
                            )
                            break
            if default == inspect.Signature.empty:
                vol_args[vol.Required(args[arg].name, description=description)] = str
                _LOGGER.debug(f"Required: {args[arg].name} as default type: str")

            elif type(default) in SUPPORTED_ARG_TYPES or default is None:
                # Handle boolean, int and string defaults
                vol_args[
                    vol.Optional(
                        args[arg].name,
                        default=UNDEFINED if default is None else default,
                        description=description,
                    )
                ] = (
                    cv.string if default is None else SUPPORTED_ARG_TYPES[type(default)]
                )
            else:
                _LOGGER.debug(
                    f"Unsupported type: {type(default)}: {args[arg].name}: {default}"
                )

        schema = vol.Schema(vol_args)

        errors = {}

        # If all args are filled in
        if args_input is not None:
            # if contains method:
            if hasattr(module, "validate_params"):
                errors.update(module.validate_params(args_input))
            options = {}

            # Pop title if provided
            if CONF_SOURCE_CALENDAR_TITLE in args_input:
                options[CONF_SOURCE_CALENDAR_TITLE] = args_input.pop(
                    CONF_SOURCE_CALENDAR_TITLE
                )

            await self.async_set_unique_id(self._source + json.dumps(args_input))
            self._abort_if_unique_id_configured()

            try:
                instance = module.Source(**args_input)
                resp = await self.hass.async_add_executor_job(instance.fetch)

                if len(resp) == 0:
                    errors["base"] = "fetch_empty"
            except Exception as e:
                errors["base"] = "fetch_error"
                description_placeholders["fetch_error_message"] = str(e)

            if len(errors) == 0:
                return self.async_create_entry(
                    title=title,
                    data={CONF_SOURCE_NAME: self._source, CONF_SOURCE_ARGS: args_input},
                    options=options,
                )
        return self.async_show_form(
            step_id="args",
            data_schema=schema,
            errors=errors,
            description_placeholders=description_placeholders,
        )

    def async_get_options_flow(self):
        return WasteCollectionOptionsFlow(self)


class WasteCollectionOptionsFlow(OptionsFlow):
    """Options flow."""

    def __init__(self, entry) -> None:
        self._entry = entry

    async def async_step_init(self, options):
        SCHEMA = vol.Schema(
            {
                vol.Optional(CONF_SOURCE_CALENDAR_TITLE): cv.string,
                vol.Optional(
                    CONF_SEPARATOR,
                    default=self._entry.options.get(
                        CONF_SEPARATOR, CONF_SEPARATOR_DEFAULT
                    ),
                ): cv.string,
                vol.Optional(
                    CONF_FETCH_TIME,
                    default=self._entry.options.get(
                        CONF_FETCH_TIME, CONF_FETCH_TIME_DEFAULT
                    ),
                ): cv.string,
                vol.Optional(
                    CONF_RANDOM_FETCH_TIME_OFFSET,
                    default=self._entry.options.get(
                        CONF_RANDOM_FETCH_TIME_OFFSET,
                        CONF_RANDOM_FETCH_TIME_OFFSET_DEFAULT,
                    ),
                ): cv.positive_int,
                vol.Optional(
                    CONF_DAY_SWITCH_TIME,
                    default=self._entry.options.get(
                        CONF_DAY_SWITCH_TIME, CONF_DAY_SWITCH_TIME_DEFAULT
                    ),
                ): cv.string,
            }
        )
        errors = {}

        # If form filled, update options
        if options is not None:
            time_pattern = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")

            # Check if the times are valid format
            if not (
                time_pattern.match(options[CONF_FETCH_TIME])
                and time_pattern.match(options[CONF_DAY_SWITCH_TIME])
            ):
                errors["base"] = "time_format"
            else:
                return self.async_create_entry(title="", data=options)

        return self.async_show_form(step_id="init", data_schema=SCHEMA, errors=errors)
