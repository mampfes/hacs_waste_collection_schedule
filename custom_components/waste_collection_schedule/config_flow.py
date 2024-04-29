import voluptuous as vol
from pathlib import Path
import inspect
import importlib
import json
import re
import logging
from voluptuous.schema_builder import UNDEFINED
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.selector import SelectSelector, SelectSelectorConfig, SelectSelectorMode, SelectOptionDict
from homeassistant.config_entries import (ConfigFlow, OptionsFlow)
from .const import DOMAIN, CONFIG_VERSION, CONF_COUNTRY_NAME, CONF_SOURCE_NAME, CONF_SOURCE_ARGS, CONF_SOURCE_CALENDAR_TITLE, CONF_SEPARATOR, CONF_FETCH_TIME, CONF_RANDOM_FETCH_TIME_OFFSET, CONF_DAY_SWITCH_TIME, CONF_SEPARATOR_DEFAULT, CONF_RANDOM_FETCH_TIME_OFFSET_DEFAULT, CONF_FETCH_TIME_DEFAULT, CONF_DAY_SWITCH_TIME_DEFAULT

_LOGGER = logging.getLogger(__name__)

class WasteCollectionConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow."""
    VERSION = CONFIG_VERSION
    _country = None
    _source = None
    
    _sources = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._sources = self._get_source_list()

    # Get source list from JSON
    def _get_source_list(self):
        p = Path(__file__).with_name('sources.json')
        with p.open(encoding="utf-8") as json_file:
            return json.load(json_file)

    # Step 1: User selects country
    async def async_step_user(self, info):
        SCHEMA = vol.Schema({
            vol.Required(CONF_COUNTRY_NAME): SelectSelector(
                SelectSelectorConfig(
                    options=[""] + list(self._sources.keys()),
                    mode=SelectSelectorMode.DROPDOWN,
                    sort=True
                )
            )
        })

        if info is not None:
            self._country = info[CONF_COUNTRY_NAME]
            return await self.async_step_source()

        return self.async_show_form(
            step_id="user", data_schema=SCHEMA
        )

    # Step 2: User selects country
    async def async_step_source(self, info=None):
        sources = self._sources[self._country]
        sources = [SelectOptionDict(value="", label="")] + [
            SelectOptionDict(value=x['module'], label=f"{x['title']} ({x['module']})") for x in sources
        ]

        SCHEMA = vol.Schema({
            vol.Required(CONF_SOURCE_NAME): SelectSelector(
                SelectSelectorConfig(
                    options=sources,
                    mode=SelectSelectorMode.DROPDOWN,
                    sort=True
                )
            )
        })

        if info is not None:
            self._source = info[CONF_SOURCE_NAME]
            return await self.async_step_args()

        return self.async_show_form(
            step_id="source", data_schema=SCHEMA
        )

    # Step 3: User fills in source arguments
    async def async_step_args(self, args_input=None):
        # Import source and get arguments
        module = importlib.import_module(f"waste_collection_schedule.source.{self._source}")
        title = module.TITLE

        args = dict(inspect.signature(module.Source.__init__).parameters)
        del args["self"] # Remove self
        # Convert schema for vol
        vol_args = {}
        for arg in args:
            default = args[arg].default
            # Field is required if no default
            if default == inspect.Signature.empty:
                vol_args[vol.Required(args[arg].name)] = str
            elif type(default) in [bool, str, int] or default is None:
                cv_map = {
                    str: cv.string,
                    int: cv.positive_int,
                    bool: cv.boolean
                }

                # Handle boolean, int and string defaults
                vol_args[
                    vol.Optional(
                        args[arg].name, default=UNDEFINED if default is None else default
                    )
                ] = cv.string if default is None else cv_map[type(default)]

        SCHEMA = vol.Schema(vol_args)
        errors = {}
        
        # If all args are filled in
        if args_input is not None:
            await self.async_set_unique_id(self._source + json.dumps(args_input))
            self._abort_if_unique_id_configured()
            
            try:
                instance = module.Source(**args_input)
                resp = await self.hass.async_add_executor_job(instance.fetch)
                
                if len(resp) == 0:
                    errors['base'] = "fetch_empty"
            except:
                errors['base'] = 'fetch_error'
            
            if len(errors) == 0:
                return self.async_create_entry(
                    title=title,
                    data={
                        CONF_SOURCE_NAME: self._source,
                        CONF_SOURCE_ARGS: args_input
                    }
                )

        return self.async_show_form(
            step_id="args", data_schema=SCHEMA, errors=errors
        )

    def async_get_options_flow(self):
        return WasteCollectionOptionsFlow(self)


class WasteCollectionOptionsFlow(OptionsFlow):
    """Options flow."""
    def __init__(self, entry) -> None:
        self._entry = entry

    async def async_step_init(self, options):
        SCHEMA = vol.Schema({
                vol.Optional(
                    CONF_SOURCE_CALENDAR_TITLE
                ): cv.string,
                vol.Optional(
                    CONF_SEPARATOR,
                    default=self._entry.options.get(CONF_SEPARATOR, CONF_SEPARATOR_DEFAULT)
                ): cv.string,
                vol.Optional(
                    CONF_FETCH_TIME,
                    default=self._entry.options.get(CONF_FETCH_TIME, CONF_FETCH_TIME_DEFAULT)
                ): cv.string,
                vol.Optional(
                    CONF_RANDOM_FETCH_TIME_OFFSET,
                    default=self._entry.options.get(CONF_RANDOM_FETCH_TIME_OFFSET, CONF_RANDOM_FETCH_TIME_OFFSET_DEFAULT)
                ): cv.positive_int,
                vol.Optional(
                    CONF_DAY_SWITCH_TIME,
                    default=self._entry.options.get(CONF_DAY_SWITCH_TIME, CONF_DAY_SWITCH_TIME_DEFAULT)
                ): cv.string
        })
        errors = {}

        # If form filled, update options
        if options is not None:
            time_pattern = re.compile(r'^([01]\d|2[0-3]):([0-5]\d)$')

            # Check if the times are valid format
            if not (time_pattern.match(options[CONF_FETCH_TIME]) and time_pattern.match(options[CONF_DAY_SWITCH_TIME])):
                errors['base'] = "time_format"
            else:
                return self.async_create_entry(
                    title="",
                    data=options
                )

        return self.async_show_form(
            step_id="init", data_schema=SCHEMA, errors=errors
        )
