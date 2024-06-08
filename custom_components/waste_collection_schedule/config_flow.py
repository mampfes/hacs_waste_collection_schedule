import importlib
import inspect
import json
import logging
import re
import types
from datetime import date, datetime
from pathlib import Path
from typing import Any, Tuple

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, OptionsFlow
from homeassistant.const import CONF_NAME, CONF_VALUE_TEMPLATE
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
    CONF_ADD_DAYS_TO,
    CONF_COLLECTION_TYPES,
    CONF_COUNT,
    CONF_COUNTRY_NAME,
    CONF_DATE_TEMPLATE,
    CONF_DAY_SWITCH_TIME,
    CONF_DAY_SWITCH_TIME_DEFAULT,
    CONF_DETAILS_FORMAT,
    CONF_EVENT_INDEX,
    CONF_FETCH_TIME,
    CONF_FETCH_TIME_DEFAULT,
    CONF_LEADTIME,
    CONF_RANDOM_FETCH_TIME_OFFSET,
    CONF_RANDOM_FETCH_TIME_OFFSET_DEFAULT,
    CONF_SENSORS,
    CONF_SEPARATOR,
    CONF_SEPARATOR_DEFAULT,
    CONF_SOURCE_ARGS,
    CONF_SOURCE_CALENDAR_TITLE,
    CONF_SOURCE_NAME,
    CONFIG_VERSION,
    DOMAIN,
)
from .sensor import DetailsFormat

_LOGGER = logging.getLogger(__name__)

SUPPORTED_ARG_TYPES = {
    str: cv.string,
    int: cv.positive_int,
    bool: cv.boolean,
    list: TextSelector(TextSelectorConfig(multiple=True)),
    date: cv.date,
    datetime: cv.datetime,
}


class WasteCollectionConfigFlow(ConfigFlow, domain=DOMAIN):  # type: ignore[call-arg]
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
            self._extra_info_default_params = next(
                (
                    x["default_params"]
                    for x in self._sources[self._country]
                    if f"{x['module']}\t({x['title']})" == info[CONF_SOURCE_NAME]
                ),
                {},
            )
            return await self.async_step_args()

        return self.async_show_form(step_id="source", data_schema=SCHEMA)

    async def __get_arg_schema(
        self,
        source: str,
        pre_filled: dict[str, Any],
        args_input: dict[str, Any] | None,
        include_title=True,
    ) -> Tuple[vol.Schema, types.ModuleType]:
        """Get schema for source arguments.

        Args:
            source (str): source name
            pre_filled (dict[str, Any]): arguments that are pre-filled (description suggested_value)
            args_input (dict[str, Any] | None): user input used to pre-fill the form with higher priority than pre_filled
            include_title (bool, optional): weather to include the title name field (only used on initial configure not on reconfigure). Defaults to True.

        Returns:
            Tuple[vol.Schema, types.ModuleType]: schema, module
        """
        # Import source and get arguments
        module = await self.hass.async_add_executor_job(
            importlib.import_module, f"waste_collection_schedule.source.{source}"
        )

        args = dict(inspect.signature(module.Source.__init__).parameters)
        del args["self"]  # Remove self
        # Convert schema for vol
        vol_args = {}
        if include_title:
            description = None
            if args_input is not None and CONF_SOURCE_CALENDAR_TITLE in args_input:
                description = {
                    "suggested_value": args_input[CONF_SOURCE_CALENDAR_TITLE]
                }
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
            elif args[arg].name in pre_filled:
                _LOGGER.debug(
                    f"Setting default value for {args[arg].name} to {pre_filled[args[arg].name]}"
                )
                description = {
                    "suggested_value": pre_filled[args[arg].name],
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
                            if a == str:  # prefer str over other types
                                break
            if default == inspect.Signature.empty:
                vol_args[vol.Required(args[arg].name, description=description)] = str
                _LOGGER.debug(f"Required: {args[arg].name} as default type: str")

            elif type(default) in SUPPORTED_ARG_TYPES or default is None:
                # Handle boolean, int, string, date, datetime, list defaults
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
        return schema, module

    async def __validate_args_user_input(
        self, source: str, args_input: dict[str, Any], module: types.ModuleType
    ) -> Tuple[dict, dict, dict]:
        """Validate user input for source arguments.

        Args:
            source (str): source name
            args_input (dict[str, Any]): user input
            module (types.ModuleType): the module of the source

        Returns:
            Tuple[dict, dict, dict]: errors, description_placeholders, options
        """
        errors = {}
        description_placeholders: dict = {}

        if hasattr(module, "validate_params"):
            errors.update(module.validate_params(args_input))
        options = {}

        # Pop title if provided
        if CONF_SOURCE_CALENDAR_TITLE in args_input:
            options[CONF_SOURCE_CALENDAR_TITLE] = args_input.pop(
                CONF_SOURCE_CALENDAR_TITLE
            )

        await self.async_set_unique_id(source + json.dumps(args_input))
        self._abort_if_unique_id_configured()

        try:
            instance = module.Source(**args_input)
            resp = await self.hass.async_add_executor_job(instance.fetch)

            if len(resp) == 0:
                errors["base"] = "fetch_empty"
            self._fetched_types = list({x.type for x in resp})
        except Exception as e:
            errors["base"] = "fetch_error"
            description_placeholders["fetch_error_message"] = str(e)
        return errors, description_placeholders, options

    # Step 3: User fills in source arguments
    async def async_step_args(self, args_input=None):
        schema, module = await self.__get_arg_schema(
            self._source, self._extra_info_default_params, args_input
        )
        self._title = module.TITLE
        errors = {}
        description_placeholders = {}
        # If all args are filled in
        if args_input is not None:
            # if contains method:
            (
                errors,
                description_placeholders,
                options,
            ) = await self.__validate_args_user_input(self._source, args_input, module)
            if len(errors) == 0:
                self._args_data = {
                    CONF_SOURCE_NAME: self._source,
                    CONF_SOURCE_ARGS: args_input,
                }
                self._options = options
                self.async_show_form(step_id="options")
                return await self.async_step_sensor()
        return self.async_show_form(
            step_id="args",
            data_schema=schema,
            errors=errors,
            description_placeholders=description_placeholders,
        )

    def async_get_options_flow(self):
        return WasteCollectionOptionsFlow(self)

    def __validate_sensor_user_input(
        self, sensor_input: dict[str, Any]
    ) -> Tuple[dict, dict]:
        """
        Validate sensor user input.

        Args:
            sensor_input (dict[str, Any]): user input

        Returns:
            Tuple[dict, dict]: errors, extracted args
        """
        errors = {}
        args = sensor_input.copy()

        # validate value_template and date_template against cv.template
        for key in [CONF_VALUE_TEMPLATE, CONF_DATE_TEMPLATE]:
            if key in sensor_input:
                try:
                    cv.template(args[key])
                except vol.Invalid:
                    errors[key] = "invalid_template"

        if sensor_input["skip"] and sensor_input["additional"]:
            errors["base"] = "skip_additional"

        if CONF_COLLECTION_TYPES in args:
            args[CONF_COLLECTION_TYPES].extend(
                args.pop(CONF_COLLECTION_TYPES + "_custom", [])
            )

        # map CONF_DETAILS_FORMAT to enum DetailsFormat
        if CONF_DETAILS_FORMAT in args:
            args[CONF_DETAILS_FORMAT] = DetailsFormat[args[CONF_DETAILS_FORMAT]]

        # enforce unique Name
        if any([x[CONF_NAME] == args[CONF_NAME] for x in self.sensors]):
            errors[CONF_NAME] = "name_exists"

        return args, errors if args["skip"] is False else {}

    def __get_sensor_schema(self):
        return vol.Schema(
            {
                vol.Required(CONF_NAME): cv.string,
                vol.Optional(CONF_DETAILS_FORMAT, default="upcoming"): vol.In(
                    list(DetailsFormat.__members__.keys())
                ),
                vol.Optional(CONF_COUNT): vol.All(vol.Coerce(int), vol.Range(min=1)),
                vol.Optional(CONF_LEADTIME): int,
                vol.Optional(CONF_VALUE_TEMPLATE): cv.string,
                vol.Optional(CONF_DATE_TEMPLATE): cv.string,
                vol.Optional(CONF_ADD_DAYS_TO): cv.boolean,
                vol.Optional(CONF_EVENT_INDEX): int,
                vol.Optional(CONF_COLLECTION_TYPES): cv.multi_select(
                    self._fetched_types
                ),
                vol.Optional(CONF_COLLECTION_TYPES + "_custom"): TextSelector(
                    TextSelectorConfig(multiple=True)
                ),
                vol.Optional("skip", default=False): cv.boolean,
                vol.Optional("additional", default=False): cv.boolean,
            }
        )

    async def async_step_sensor(self, sensor_input: dict[str, Any] | None = None):
        if not hasattr(self, "sensors"):
            self.sensors = []
        errors = {}
        if sensor_input is not None:
            args, errors = self.__validate_sensor_user_input(sensor_input)
            if len(errors) == 0 or args["skip"] is True:
                if args["skip"] is False:
                    self.sensors.append(args)
                if args["additional"] is False:
                    self._args_data.update({CONF_SENSORS: self.sensors})
                    _LOGGER.debug("sensor_data:")
                    _LOGGER.debug(self._args_data[CONF_SENSORS])
                    return self.async_create_entry(
                        title=self._title,
                        data=self._args_data,
                        options=self._options,
                    )

        return self.async_show_form(
            step_id="sensor",
            data_schema=self.__get_sensor_schema(),
            errors=errors,
            description_placeholders={"sensor_number": str(len(self.sensors) + 1)},
        )

    async def async_step_reconfigure(self, args_input: dict[str, Any] | None = None):
        config_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        if config_entry is None:
            return self.async_abort(reason="reconfigure_failed")

        source = config_entry.data["name"]
        schema, module = await self.__get_arg_schema(
            source, config_entry.data["args"], args_input, include_title=False
        )
        title = module.TITLE
        errors: dict[str, str] = {}
        description_placeholders: dict[str, str] = {}
        # If all args are filled in
        if args_input is not None:
            # if contains method:
            (
                errors,
                description_placeholders,
                options,
            ) = await self.__validate_args_user_input(source, args_input, module)
            if len(errors) == 0:
                data = {**config_entry.data}
                data.update({CONF_SOURCE_NAME: source, CONF_SOURCE_ARGS: args_input})
                _LOGGER.debug("reconfigured_data:")
                _LOGGER.debug(data)
                return self.async_update_reload_and_abort(
                    config_entry,
                    title=title,
                    unique_id=config_entry.unique_id,
                    data=data,
                    options=options,
                    reason="reconfigure_successful",
                )
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=schema,
            errors=errors,
            description_placeholders=description_placeholders,
        )


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
