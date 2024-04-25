import voluptuous as vol
from glob import glob
from os import path
import importlib
import json
import re
import logging
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.selector import SelectSelector, SelectSelectorConfig, SelectSelectorMode
from homeassistant.config_entries import (ConfigFlow, OptionsFlow)
from .const import DOMAIN, CONFIG_VERSION, CONF_SOURCE_NAME, CONF_SOURCE_ARGS, CONF_SOURCE_CALENDAR_TITLE, CONF_SEPARATOR, CONF_FETCH_TIME, CONF_RANDOM_FETCH_TIME_OFFSET, CONF_DAY_SWITCH_TIME, CONF_SEPARATOR_DEFAULT, CONF_RANDOM_FETCH_TIME_OFFSET_DEFAULT, CONF_FETCH_TIME_DEFAULT, CONF_DAY_SWITCH_TIME_DEFAULT

_LOGGER = logging.getLogger(__name__)

class WasteCollectionConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow."""
    VERSION = CONFIG_VERSION
    _source = None

    # Get source list from filesystem
    def _get_source_list(self):
        return [path.basename(x).split(".")[0] for x in glob(path.dirname(path.realpath(__file__)) + "/waste_collection_schedule/source/*.py")]

    # Step 1: User selects source from dropdown
    async def async_step_user(self, info):
        SCHEMA = vol.Schema({
            vol.Required(CONF_SOURCE_NAME): SelectSelector(
                SelectSelectorConfig(
                    options=[""] + self._get_source_list(),
                    mode=SelectSelectorMode.DROPDOWN,
                    sort=True
                )
            )
        })

        if info is not None:
            self._source = info[CONF_SOURCE_NAME]
            return await self.async_step_args()

        return self.async_show_form(
            step_id="user", data_schema=SCHEMA
        )

    # Step 2: User fills in source arguments
    async def async_step_args(self, args_input={}):
        # Import source and get arguments
        module = importlib.import_module(f"waste_collection_schedule.source.{self._source}")
        title = module.TITLE

        args = list(module.Source.__init__.__code__.co_varnames)
        args.pop(0) # Remove self

        # Convert schema for vol
        vol_args = {}
        for arg in args:
            vol_args[vol.Required(arg)] = str

        SCHEMA = vol.Schema(vol_args)
        errors = {}
        
        # If all args are filled in
        if len(args_input) == len(args):
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

    def async_get_options_flow(entry):
        return WasteCollectionOptionsFlow(entry)


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
