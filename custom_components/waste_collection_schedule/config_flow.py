import importlib
import inspect
import json
import logging
import types
from datetime import date, datetime
from pathlib import Path
from typing import Any, Tuple

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, OptionsFlow
from homeassistant.const import CONF_NAME, CONF_VALUE_TEMPLATE
from homeassistant.helpers.selector import (
    IconSelector,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TemplateSelector,
    TextSelector,
    TextSelectorConfig,
    TimeSelector,
)
from voluptuous.schema_builder import UNDEFINED

from .const import (
    CONF_ADD_DAYS_TO,
    CONF_ALIAS,
    CONF_COLLECTION_TYPES,
    CONF_COUNT,
    CONF_COUNTRY_NAME,
    CONF_CUSTOMIZE,
    CONF_DATE_TEMPLATE,
    CONF_DAY_SWITCH_TIME,
    CONF_DAY_SWITCH_TIME_DEFAULT,
    CONF_DEDICATED_CALENDAR_TITLE,
    CONF_DETAILS_FORMAT,
    CONF_EVENT_INDEX,
    CONF_FETCH_TIME,
    CONF_FETCH_TIME_DEFAULT,
    CONF_ICON,
    CONF_LEADTIME,
    CONF_PICTURE,
    CONF_RANDOM_FETCH_TIME_OFFSET,
    CONF_RANDOM_FETCH_TIME_OFFSET_DEFAULT,
    CONF_SENSORS,
    CONF_SEPARATOR,
    CONF_SEPARATOR_DEFAULT,
    CONF_SHOW,
    CONF_SOURCE_ARGS,
    CONF_SOURCE_CALENDAR_TITLE,
    CONF_SOURCE_NAME,
    CONF_TYPE,
    CONF_USE_DEDICATED_CALENDAR,
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

CUSTOMIZE_SHEMA = {
    vol.Optional(CONF_ALIAS): str,
    vol.Optional(CONF_SHOW, default=True): cv.boolean,
    vol.Optional(CONF_ICON): IconSelector(),
    vol.Optional(CONF_PICTURE): str,
    vol.Optional(CONF_USE_DEDICATED_CALENDAR): cv.boolean,
    vol.Optional(CONF_DEDICATED_CALENDAR_TITLE): str,
}


EXAMPLE_VALUE_TEMPLATES = {
    "": "",
    "in .. days": "in {{value.daysTo}} days",
    ".. in .. days": '{{value.types|join(", ")}} in {{value.daysTo}} days',
    "numeric daysTo": "{{value.daysTo}}",
    "in .. days / Tomoorow / Today": "{% if value.daysTo == 0 %}Today{% elif value.daysTo == 1 %}Tomorrow{% else %}in {{value.daysTo}} days{% endif %}",
    "on Weekday, dd.mm.yyyy": 'on {{value.date.strftime("%a")}}, {{value.date.strftime("%d.%m.%Y")}}',
    "on Weekday, yyyy-mm-dd": 'on {{value.date.strftime("%a")}}, {{value.date.strftime("%Y-%m-%d")}}',
    "next collections": '{{value.types|join(", ")}}',
}

EXAMPLE_DATE_TEMPLATES = {
    "": "",
    "20.03.2020": '{{value.date.strftime("%d.%m.%Y")}}',
    "Fri, 20.03.2020": '{{value.date.strftime("%a, %d.%m.%Y")}}',
    "03/20/2020": '{{value.date.strftime("%m/%d/%Y")}}',
    "Fri, 03/20/2020": '{{value.date.strftime("%a, %m/%d/%Y")}}',
    "2020-03-20": '{{value.date.strftime("%Y-%m-%d")}}',
    "Fri, 2020-03-20": '{{value.date.strftime("%a, %Y-%m-%d")}}',
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
        self._options: dict = {}

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
        sources_options = [SelectOptionDict(value="", label="")] + [
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
                        options=sources_options,
                        mode=SelectSelectorMode.DROPDOWN,
                        sort=True,
                        multiple=False,
                        custom_value=True,  # allows to properly search while typing in the dropdown
                    )
                )
            }
        )

        errors = {}
        if info is not None:
            if not (
                "\t" in info[CONF_SOURCE_NAME]
                and info[CONF_SOURCE_NAME].split("\t")[0]
                in [x["module"] for x in sources]
            ):
                errors[CONF_SOURCE_NAME] = "invalid_source"
            else:
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

        return self.async_show_form(step_id="source", data_schema=SCHEMA, errors=errors)

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
                vol.Optional(
                    CONF_SOURCE_CALENDAR_TITLE,
                    description=description,
                    default=module.TITLE,
                ): str,
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
                self._options.update(options)
                self.async_show_form(step_id="options")
                return await self.async_step_customize_select()
        return self.async_show_form(
            step_id="args",
            data_schema=schema,
            errors=errors,
            description_placeholders=description_placeholders,
        )

    async def async_step_customize_select(
        self, user_input: dict[str, Any] | None = None
    ):
        schema = vol.Schema(
            {
                vol.Optional(CONF_TYPE): SelectSelector(
                    SelectSelectorConfig(
                        options=self._fetched_types,
                        mode=SelectSelectorMode.DROPDOWN,
                        custom_value=True,
                        multiple=True,
                    )
                ),
            }
        )

        if user_input is not None:
            self._customize_types = list(set(user_input[CONF_TYPE]))
            self._fetched_types = list({*self._fetched_types, *self._customize_types})
            return await self.async_step_customize()
        return self.async_show_form(step_id="customize_select", data_schema=schema)

    async def async_step_customize(self, user_input: dict[str, Any] | None = None):
        types = []
        if hasattr(self, "_customize_types"):
            types = self._customize_types
        if not hasattr(self, "_customize_index"):
            self._customize_index = 0
        if CONF_CUSTOMIZE not in self._options:
            self._options[CONF_CUSTOMIZE] = {}
        if self._customize_index >= len(types):
            return await self.async_step_sensor()

        errors = {}

        if user_input is not None:
            if user_input.get(CONF_DEDICATED_CALENDAR_TITLE, "") and not user_input.get(
                CONF_USE_DEDICATED_CALENDAR, False
            ):
                errors[
                    CONF_DEDICATED_CALENDAR_TITLE
                ] = "dedicated_calendar_title_without_use_dedicated_calendar"
            else:
                if CONF_ALIAS in user_input:
                    self._fetched_types.remove(types[self._customize_index])
                    self._fetched_types.append(user_input[CONF_ALIAS])
                self._options[CONF_CUSTOMIZE][types[self._customize_index]] = user_input
                self._options[CONF_CUSTOMIZE][types[self._customize_index]][
                    CONF_TYPE
                ] = types[self._customize_index]
                self._customize_index += 1
                return await self.async_step_customize()

        schema = vol.Schema(CUSTOMIZE_SHEMA)
        if errors:
            self.add_suggested_values_to_schema(schema, user_input)
        return self.async_show_form(
            step_id="customize",
            data_schema=schema,
            description_placeholders={
                "type": types[self._customize_index],
                "index": self._customize_index + 1,
                "total": len(types),
            },
            errors=errors,
        )

    async def async_step_sensor(self, sensor_input: dict[str, Any] | None = None):
        if not hasattr(self, "sensors"):
            self.sensors = []
        errors: dict[str, str] = {}
        if sensor_input is not None:
            args, errors = self.__validate_sensor_user_input(sensor_input)
            if len(errors) == 0 or args["skip"] is True:
                if args["skip"] is False:
                    self.sensors.append(args)
                if args["additional"] is False:
                    self._args_data.update({CONF_SENSORS: self.sensors})
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
            if key + "_preset" in sensor_input and sensor_input[key + "_preset"]:
                if key in sensor_input:
                    errors[key] = "preset_selected"
                    errors[key + "_preset"] = "preset_selected"
                    continue
                args.pop(key + "_preset")
                args[key] = sensor_input[key + "_preset"]

            if key in sensor_input and key:
                try:
                    cv.template(args[key])
                except vol.Invalid:
                    errors[key] = "invalid_template"

        if sensor_input["skip"] and sensor_input["additional"]:
            errors["base"] = "skip_additional"

        # map CONF_DETAILS_FORMAT to enum DetailsFormat
        if CONF_DETAILS_FORMAT in args:
            args[CONF_DETAILS_FORMAT] = DetailsFormat[args[CONF_DETAILS_FORMAT]]

        if not args.get(CONF_NAME):
            errors[CONF_NAME] = "sensor_name_empty"
        # enforce unique Name
        elif any([x[CONF_NAME] == args[CONF_NAME] for x in self.sensors]):
            errors[CONF_NAME] = "name_exists"

        return args, errors if args["skip"] is False else {}

    def __get_sensor_schema(self):
        return vol.Schema(
            {
                vol.Optional(CONF_NAME): cv.string,
                vol.Optional(CONF_DETAILS_FORMAT, default="upcoming"): SelectSelector(
                    SelectSelectorConfig(
                        options=[
                            SelectOptionDict(
                                label=k,
                                value=k,
                            )
                            for k in DetailsFormat.__members__.keys()
                        ],
                        translation_key="details_format",
                    )
                ),
                vol.Optional(CONF_COUNT): vol.All(vol.Coerce(int), vol.Range(min=1)),
                vol.Optional(CONF_LEADTIME): int,
                vol.Optional(CONF_VALUE_TEMPLATE + "_preset"): SelectSelector(
                    SelectSelectorConfig(
                        options=[
                            SelectOptionDict(label=f"{k}: {v}", value=v)
                            for k, v in EXAMPLE_VALUE_TEMPLATES.items()
                        ],
                        mode=SelectSelectorMode.DROPDOWN,
                        custom_value=False,
                        multiple=False,
                    )
                ),
                vol.Optional(CONF_VALUE_TEMPLATE): TemplateSelector(),
                vol.Optional(CONF_DATE_TEMPLATE): SelectSelector(
                    SelectSelectorConfig(
                        options=[
                            SelectOptionDict(label=f"{k}: {v}", value=v)
                            for k, v in EXAMPLE_DATE_TEMPLATES.items()
                        ],
                        mode=SelectSelectorMode.DROPDOWN,
                        custom_value=True,
                        multiple=False,
                    )
                ),
                vol.Optional(CONF_DATE_TEMPLATE + "_preset"): TemplateSelector(),
                vol.Optional(CONF_ADD_DAYS_TO): cv.boolean,
                vol.Optional(CONF_EVENT_INDEX): int,
                vol.Optional(CONF_COLLECTION_TYPES): SelectSelector(
                    SelectSelectorConfig(
                        options=self._fetched_types,
                        mode=SelectSelectorMode.DROPDOWN,
                        custom_value=True,
                        multiple=True,
                    )
                ),
                vol.Optional("skip", default=False): cv.boolean,
                vol.Optional("additional", default=False): cv.boolean,
            }
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
                vol.Optional(
                    CONF_SOURCE_CALENDAR_TITLE,
                    default=self._entry.options.get(CONF_SOURCE_CALENDAR_TITLE),
                ): cv.string,
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
                ): TimeSelector(),
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
                ): TimeSelector(),
            }
        )
        errors = {}

        # If form filled, update options
        if options is not None:
            # Check if the times are valid format
            try:
                cv.time(options[CONF_FETCH_TIME])
            except vol.Invalid:
                errors[CONF_FETCH_TIME] = "time_format"
            try:
                cv.time(options[CONF_DAY_SWITCH_TIME])
            except vol.Invalid:
                errors[CONF_DAY_SWITCH_TIME] = "time_format"
            if len(errors) == 0:
                return self.async_create_entry(title="", data=options)

        return self.async_show_form(step_id="init", data_schema=SCHEMA, errors=errors)
