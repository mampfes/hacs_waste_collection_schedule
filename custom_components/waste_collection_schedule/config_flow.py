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
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.const import CONF_NAME, CONF_VALUE_TEMPLATE
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    IconSelector,
    ObjectSelector,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TemplateSelector,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
    TimeSelector,
)
from homeassistant.helpers.translation import async_get_translations
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
from .init_ui import WCSCoordinator
from .sensor import DetailsFormat

_LOGGER = logging.getLogger(__name__)

SUPPORTED_ARG_TYPES = {
    str: cv.string,
    int: cv.positive_int,
    bool: cv.boolean,
    list: TextSelector(TextSelectorConfig(multiple=True)),
    list[str]: TextSelector(TextSelectorConfig(multiple=True)),
    list[str | int]: TextSelector(TextSelectorConfig(multiple=True)),
    list[date | str]: TextSelector(
        TextSelectorConfig(multiple=True, type=TextSelectorType.DATE)
    ),
    date | str: TextSelector(TextSelectorConfig(type=TextSelectorType.DATE)),
    date | str | None: TextSelector(TextSelectorConfig(type=TextSelectorType.DATE)),
    dict: ObjectSelector(),
    str | int: cv.string,
    date: cv.date,
    datetime: cv.datetime,
}


def get_customize_schema(defaults: dict[str, Any] = {}):
    schema = {
        vol.Optional(CONF_ALIAS, default=defaults.get(CONF_ALIAS, UNDEFINED)): str,
        vol.Optional(CONF_SHOW, default=defaults.get(CONF_SHOW, True)): cv.boolean,
        vol.Optional(
            CONF_ICON, default=defaults.get(CONF_ICON, UNDEFINED)
        ): IconSelector(),
        vol.Optional(CONF_PICTURE, default=defaults.get(CONF_PICTURE, UNDEFINED)): str,
        vol.Optional(
            CONF_USE_DEDICATED_CALENDAR,
            default=defaults.get(CONF_USE_DEDICATED_CALENDAR, UNDEFINED),
        ): cv.boolean,
        vol.Optional(
            CONF_DEDICATED_CALENDAR_TITLE,
            default=defaults.get(CONF_DEDICATED_CALENDAR_TITLE, UNDEFINED),
        ): str,
    }
    return schema


def get_sensor_schema(fetched_types, add_delete=False, defaults: dict = {}):
    schema = {
        vol.Optional(CONF_NAME, default=defaults.get(CONF_NAME, UNDEFINED)): cv.string,
    }
    if add_delete:
        schema[vol.Optional("delete")] = cv.boolean

    schema.update(
        {
            vol.Optional(
                CONF_DETAILS_FORMAT,
                default=defaults.get(CONF_DETAILS_FORMAT, "upcoming"),
            ): SelectSelector(
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
            vol.Optional(
                CONF_COUNT, default=defaults.get(CONF_COUNT, UNDEFINED)
            ): vol.All(vol.Coerce(int), vol.Range(min=1)),
            vol.Optional(
                CONF_LEADTIME, default=defaults.get(CONF_LEADTIME, UNDEFINED)
            ): int,
            vol.Optional(
                CONF_VALUE_TEMPLATE + "_preset",
                default=defaults.get(CONF_VALUE_TEMPLATE + "_preset", UNDEFINED),
            ): SelectSelector(
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
            vol.Optional(
                CONF_VALUE_TEMPLATE,
                default=defaults.get(CONF_VALUE_TEMPLATE, UNDEFINED),
            ): TemplateSelector(),
            vol.Optional(
                CONF_DATE_TEMPLATE, default=defaults.get(CONF_DATE_TEMPLATE, UNDEFINED)
            ): SelectSelector(
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
            vol.Optional(
                CONF_DATE_TEMPLATE + "_preset",
                default=defaults.get(CONF_DATE_TEMPLATE + "_preset", UNDEFINED),
            ): TemplateSelector(),
            vol.Optional(
                CONF_ADD_DAYS_TO, default=defaults.get(CONF_ADD_DAYS_TO, UNDEFINED)
            ): cv.boolean,
            vol.Optional(
                CONF_EVENT_INDEX, default=defaults.get(CONF_EVENT_INDEX, UNDEFINED)
            ): int,
            vol.Optional(
                CONF_COLLECTION_TYPES,
                default=defaults.get(CONF_COLLECTION_TYPES, UNDEFINED),
            ): SelectSelector(
                SelectSelectorConfig(
                    options=fetched_types,
                    mode=SelectSelectorMode.DROPDOWN,
                    custom_value=True,
                    multiple=True,
                )
            ),
        }
    )
    if not add_delete:
        schema[vol.Optional("skip", default=False)] = cv.boolean
        schema[vol.Optional("additional", default=False)] = cv.boolean

    return vol.Schema(schema)


def validate_sensor_user_input(
    sensor_input: dict[str, Any], existing_sensors
) -> Tuple[dict[str, Any], dict[str, str]]:
    """
    Validate sensor user input.

    Args:
        sensor_input (dict[str, Any]): user input

    Returns:
        Tuple[dict, dict]: errors, extracted args
    """
    errors: dict[str, str] = {}
    args = sensor_input.copy()

    # validate value_template and date_template against cv.template
    for key in [CONF_VALUE_TEMPLATE, CONF_DATE_TEMPLATE]:
        if key + "_preset" in sensor_input and sensor_input[key + "_preset"]:
            if key in sensor_input:
                errors[key] = "preset_selected"
                errors[key + "_preset"] = "preset_selected"
                continue
            args.pop(key + "_preset", None)
            args[key] = sensor_input[key + "_preset"]

        if key in sensor_input and key:
            try:
                cv.template(args[key])
            except vol.Invalid:
                errors[key] = "invalid_template"

    if sensor_input.get("skip", False) and sensor_input.get("additional", False):
        errors["base"] = "skip_additional"

    # map CONF_DETAILS_FORMAT to enum DetailsFormat
    if CONF_DETAILS_FORMAT in args:
        args[CONF_DETAILS_FORMAT] = DetailsFormat[args[CONF_DETAILS_FORMAT]]

    if not args.get(CONF_NAME):
        errors[CONF_NAME] = "sensor_name_empty"
    # enforce unique Name
    elif any([x[CONF_NAME] == args[CONF_NAME] for x in existing_sensors]):
        errors[CONF_NAME] = "name_exists"

    return args, errors if args.get("skip", False) is False else {}


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

    # Step 2: User selects source
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

        MODULE_FLOW_TYPES = (
            module.CONFIG_FLOW_TYPES if hasattr(module, "CONFIG_FLOW_TYPES") else {}
        )

        for arg in args:
            default = args[arg].default
            field_type = None

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

            if (
                default == inspect.Signature.empty or default is None
            ) and annotation != inspect._empty:
                if annotation in SUPPORTED_ARG_TYPES:
                    field_type = SUPPORTED_ARG_TYPES[annotation]
                elif (
                    isinstance(annotation, types.GenericAlias)
                    and annotation.__origin__ in SUPPORTED_ARG_TYPES
                ):
                    field_type = SUPPORTED_ARG_TYPES[annotation.__origin__]
                elif isinstance(annotation, types.UnionType):
                    for a in annotation.__args__:
                        _LOGGER.debug(f"{args[arg].name} UnionType: {a}, {type(a)}")
                        if a in SUPPORTED_ARG_TYPES:
                            field_type = SUPPORTED_ARG_TYPES[a]
                        elif (
                            isinstance(a, types.GenericAlias)
                            and a.__origin__ in SUPPORTED_ARG_TYPES
                        ):
                            field_type = SUPPORTED_ARG_TYPES[a.__origin__]

            _LOGGER.debug(
                f"Default for {args[arg].name}: {type(default) if default is not inspect.Signature.empty else inspect.Signature.empty}"
            )

            if args[arg].name in MODULE_FLOW_TYPES:
                flow_type = MODULE_FLOW_TYPES[args[arg].name]
                if flow_type.get("type") == "SELECT":
                    field_type = SelectSelector(
                        SelectSelectorConfig(
                            options=[
                                SelectOptionDict(label=x, value=x)
                                for x in flow_type.get("values")
                            ],
                            translation_key="custom_flow_types",
                            mode=SelectSelectorMode.DROPDOWN,
                            multiple=flow_type.get("multiple", False),
                        )
                    )

            if field_type is None:
                field_type = SUPPORTED_ARG_TYPES.get(type(default))

            if default == inspect.Signature.empty:
                vol_args[vol.Required(args[arg].name, description=description)] = (
                    field_type or str
                )
                _LOGGER.debug(f"Required: {args[arg].name} as default type: str")

            elif field_type or (default is None):
                # Handle boolean, int, string, date, datetime, list defaults
                vol_args[
                    vol.Optional(
                        args[arg].name,
                        default=UNDEFINED if default is None else default,
                        description=description,
                    )
                ] = (
                    field_type or cv.string
                )
            else:
                _LOGGER.debug(
                    f"Unsupported type: {type(default)}: {args[arg].name}: {default}: {field_type}"
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
            self._customize_types = list(set(user_input.get(CONF_TYPE, [])))
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
                self._customize_index += 1
                return await self.async_step_customize()

        schema = vol.Schema(get_customize_schema())
        if errors:
            schema = self.add_suggested_values_to_schema(schema, user_input)
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
            self.sensors: list[dict[str, Any]] = []
        errors: dict[str, str] = {}
        if sensor_input is not None:
            args, errors = validate_sensor_user_input(sensor_input, self.sensors)
            if len(errors) == 0 or args.get("skip", False) is True:
                if args.get("skip", False) is False:
                    self.sensors.append(args)
                if args.get("additional", False) is False:
                    self._options.update({CONF_SENSORS: self.sensors})
                    return self.async_create_entry(
                        title=self._title,
                        data=self._args_data,
                        options=self._options,
                    )

        return self.async_show_form(
            step_id="sensor",
            data_schema=get_sensor_schema(self._fetched_types),
            errors=errors,
            description_placeholders={"sensor_number": str(len(self.sensors) + 1)},
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry):
        return WasteCollectionOptionsFlow(config_entry)

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
        self._entry: ConfigEntry = entry

    async def translate(self, text: str) -> str:
        user_language = self.hass.config.language
        return await async_get_translations(self.hass, user_language, DOMAIN)(text)

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        # get SourceShells
        collection_types = []
        calendar_title = UNDEFINED
        # get the right coordinator
        coordinator: WCSCoordinator = self.hass.data.get(DOMAIN, {}).get(
            self._entry.entry_id
        )

        if coordinator and isinstance(coordinator, WCSCoordinator):
            collection_types = list(coordinator._aggregator.types)
            calendar_title = coordinator._shell.calendar_title

        customized_types = list(self._entry.options.get(CONF_CUSTOMIZE, {}).keys())
        uncustomized_types = [x for x in collection_types if x not in customized_types]

        SCHEMA = vol.Schema(
            {
                vol.Optional(
                    CONF_SOURCE_CALENDAR_TITLE,
                    default=self._entry.options.get(
                        CONF_SOURCE_CALENDAR_TITLE, calendar_title
                    ),
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
                vol.Optional(
                    "sensor_select",
                ): SelectSelector(
                    SelectSelectorConfig(
                        translation_key="sensor_select",
                        options=[
                            *[
                                SelectOptionDict(label=x[CONF_NAME], value=x[CONF_NAME])
                                for x in self._entry.options.get(CONF_SENSORS, [])
                            ],
                            SelectOptionDict(
                                label="add_new_sensor", value="sensor_select_add_new"
                            ),
                        ],
                        custom_value=False,
                        multiple=True,
                    )
                ),
                vol.Optional(
                    "customize_select",
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=[
                            *[
                                SelectOptionDict(
                                    label=key
                                    + (
                                        f": {value[CONF_ALIAS]}"
                                        if CONF_ALIAS in value
                                        else ""
                                    ),
                                    value=key,
                                )
                                for key, value in self._entry.options.get(
                                    CONF_CUSTOMIZE, {}
                                ).items()
                            ],
                            *[
                                SelectOptionDict(label=x, value=x)
                                for x in uncustomized_types
                            ],
                        ],
                        custom_value=True,
                        multiple=True,
                    )
                ),
            }
        )
        errors = {}

        # If form filled, update options
        if user_input is not None:
            # Check if the times are valid format
            try:
                cv.time(user_input[CONF_FETCH_TIME])
            except vol.Invalid:
                errors[CONF_FETCH_TIME] = "time_format"
            try:
                cv.time(user_input[CONF_DAY_SWITCH_TIME])
            except vol.Invalid:
                errors[CONF_DAY_SWITCH_TIME] = "time_format"
            if len(errors) == 0:
                self._options = user_input

                self._customize_select = user_input.get("customize_select", [])
                self._customize_select_idx = 0
                self._options[CONF_CUSTOMIZE] = {
                    k: v
                    for k, v in self._entry.options.get(CONF_CUSTOMIZE, {}).items()
                    if k not in self._customize_select
                }
                self._sensor_select = user_input.get("sensor_select", [])
                self._sensor_select_idx = 0
                self._options[CONF_SENSORS] = [
                    s
                    for s in self._entry.options.get(CONF_SENSORS, [])
                    if s[CONF_NAME] not in self._sensor_select
                ]
                return await self.async_step_customize()

        return self.async_show_form(step_id="init", data_schema=SCHEMA, errors=errors)

    def get_types_of_sensors_and_customizations(self):
        fetched_types = list(self._entry.options.get(CONF_CUSTOMIZE, {}).keys())
        for c in self._entry.options.get(CONF_SENSORS, []):
            if CONF_TYPE in c:
                fetched_types.extend(
                    c[CONF_TYPE] if isinstance(c[CONF_TYPE], list) else [c[CONF_TYPE]]
                )
        return list(set(fetched_types))

    async def async_step_customize(self, user_input: dict[str, Any] | None = None):
        if self._customize_select is None or self._customize_select_idx >= len(
            self._customize_select
        ):
            return await self.async_step_sensor()

        defaults = self._entry.options.get(CONF_CUSTOMIZE, {}).get(
            self._customize_select[self._customize_select_idx], {}
        )
        is_new = self._customize_select[
            self._customize_select_idx
        ] not in self._entry.options.get(CONF_CUSTOMIZE, {})
        dict_schema: dict[vol.Optional, Any] = get_customize_schema(defaults)
        if not is_new:
            dict_schema[vol.Optional("delete")] = cv.boolean

        schema = self.add_suggested_values_to_schema(
            vol.Schema(dict_schema), user_input
        )
        if user_input is not None:
            if not user_input.get(
                "delete", False
            ):  # only re-add the (modified) customization if not deleted
                user_input.pop("delete", None)
                self._options[CONF_CUSTOMIZE][
                    self._customize_select[self._customize_select_idx]
                ] = user_input
                self._customize_select_idx += 1
            return await self.async_step_customize()

        return self.async_show_form(
            step_id="customize",
            data_schema=schema,
            description_placeholders={
                "index": str(self._customize_select_idx + 1),
                "total": str(len(self._customize_select)),
                "type": self._customize_select[self._customize_select_idx],
            },
        )

    async def async_step_sensor(self, user_input: dict[str, Any] | None = None):
        if self._sensor_select is None or self._sensor_select_idx >= len(
            self._sensor_select
        ):
            _LOGGER.debug("self._options: %s", self._options)
            return self.async_create_entry(data=self._options)

        # find sensor with the same name
        original_sensor = next(
            (
                x
                for x in self._entry.options.get(CONF_SENSORS, [])
                if x[CONF_NAME] == self._sensor_select[self._sensor_select_idx]
            ),
            None,
        )

        schema = self.add_suggested_values_to_schema(
            get_sensor_schema(
                self.get_types_of_sensors_and_customizations(),
                add_delete=True,
                defaults=original_sensor or {},
            ),
            user_input,
        )
        errors: dict[str, str] = {}
        # is_new = self._sensor_select[self._sensor_select_idx] == "sensor_select_add_new"

        if user_input is not None:
            if user_input.get(
                "delete", False
            ):  # only re-add the (modified) sensor if not deleted
                self._sensor_select_idx += 1
                return await self.async_step_sensor()

            user_input.pop("delete", None)
            args, errors = validate_sensor_user_input(
                user_input, self._options[CONF_SENSORS]
            )

            if len(errors) == 0:
                self._options[CONF_SENSORS].append(args)
                self._sensor_select_idx += 1
                return await self.async_step_sensor()

        return self.async_show_form(
            step_id="sensor",
            errors=errors,
            data_schema=schema,
            description_placeholders={
                "sensor_number": str(self._sensor_select_idx + 1),
            },
        )
