"""Config flow for 1-Wire component."""
import voluptuous as vol
import logging

import requests
import json

from homeassistant.config_entries import CONN_CLASS_CLOUD_POLL, ConfigFlow
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_TYPE
from homeassistant.helpers.typing import HomeAssistantType
import homeassistant.helpers.config_validation as cv
from homeassistant.core import callback
from homeassistant import config_entries

from .const import (  # pylint: disable=unused-import
    DOMAIN,
    CONF_SOURCES,
    CONF_SOURCE_NAME,
    CONF_SOURCE_ARGS,
    CONF_SEPARATOR,
    CONF_FETCH_TIME,
    CONF_RANDOM_FETCH_TIME_OFFSET,
    CONF_DAY_SWITCH_TIME,
    DEFAULT_SEPARATOR,
    DEFAULT_FETCH_TIME,
    DEFAULT_RANDOM_FETCH_TIME_OFFSET,
    DEFAULT_DAY_SWITCH_TIME,

    CONF_SERVICE,
    CONF_CITY_ID,
)
from .package.scraper import Scraper, Customize

_LOGGER = logging.getLogger(__name__)

# List of all available services
SERVICE_ICS = "ics"
SERVICE_ABFALLNAVI_DE = "abfallnavi_de"
ALL_SERVICES = {
    SERVICE_ICS: "ICS",
    SERVICE_ABFALLNAVI_DE: "abfallnavi.de (regioit.de)",
}

# options for service: ICS
OPT_ICS_URL = "url"
OPT_ICS_FILE = "file"
OPT_ICS_OFFSET = "offset"


# schema for initial config flow, entered by "Add Integration"
DATA_SCHEMA_USER = vol.Schema(
    {
        vol.Required(CONF_TYPE): vol.In(ALL_SERVICES)
    }
)


class WasteCollectionScheduleFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle config flow."""

    VERSION = 1
    CONNECTION_CLASS = CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize config flow."""
        self._config = { CONF_SOURCES: [] }

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        """Handle start of config flow.

        Let user select service type.
        """
        errors = {}
        if user_input is not None:
            self._config[CONF_SOURCES].append({CONF_SOURCE_NAME: user_input[CONF_TYPE], CONF_SOURCE_ARGS: {}})
            if user_input[CONF_TYPE] == SERVICE_ICS:
                return await self.async_step_ics()
            if user_input[CONF_TYPE] == SERVICE_ABFALLNAVI_DE:
                return await self.async_step_abfallnavi_de()

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA_USER,
            errors=errors,
        )

    def _test_scraper(self, source_name, kwargs):
        scraper = Scraper.create(source_name, -3, {}, kwargs)
        scraper.fetch()
        return scraper.get_types()

    async def async_step_ics(self, user_input=None):
        """Configure specific service"""
        errors = {}
        if user_input:
            # validate user input
            count = 0
            if OPT_ICS_URL in user_input:
                count += 1
            if OPT_ICS_FILE in user_input:
                count += 1
            if count != 1:
                errors["base"] = "ics_specify_either_url_or_file"

            if len(errors) == 0:
                # continue only if no errors detected
                
                # test if scraper can fetch data without errors
#  TODO: remove https://www.edg.de/ical/kalender.ics?Strasse=Dudenstr.&Hausnummer=5&Erinnerung=-1&Abfallart=1,2,3,4
                waste_types = await self.hass.async_add_executor_job(self._test_scraper, SERVICE_ICS, user_input)
                if len(waste_types) == 0:
                    errors["base"] = "scraper_test_failed"
                else:
                    self._config[CONF_SOURCES].append({CONF_SOURCE_NAME: SERVICE_ICS, CONF_SOURCE_ARGS: user_input})

                    return self.async_create_entry(
                        title=ALL_SERVICES[SERVICE_ICS], data=self._config
                    )

        DATA_SCHEMA = vol.Schema(
            {
                vol.Optional(OPT_ICS_URL): str,
                vol.Optional(OPT_ICS_FILE): str,
                vol.Optional(OPT_ICS_OFFSET, default=0): int,
            }
        )

        return self.async_show_form(
            step_id=SERVICE_ICS,
            data_schema=DATA_SCHEMA,
            errors=error
        )

    async def async_step_abfallnavi_de(self, user_input=None):
        """First step of service specific flow.

        Select service operator.
        """

        errors = {}
        if user_input:
            self._config[CONF_SOURCES][-1][CONF_SOURCE_ARGS][CONF_SERVICE] = user_input[CONF_SERVICE]
            return await self.async_step_abfallnavi_de_select_city()

        DOMAIN_CHOICES = {
            "aachen": "Aachen",
            "zew2": "AWA Entsorgungs GmbH",
            "aw-bgl2": "Bergisch Gladbach",
            "bav": "Bergischer Abfallwirtschaftverbund",
            "din": "Dinslaken",
            "dorsten": "Dorsten",
            "gt2": "Gütersloh",
            "hlv": "Halver",
            "coe": "Kreis Coesfeld",
            "krhs": "Kreis Heinsberg",
            "pi": "Kreis Pinneberg",
            "krwaf": "Kreis Warendorf",
            "lindlar": "Lindlar",
            "stl": "Lüdenscheid",
            "nds": "Norderstedt",
            "nuernberg": "Nürnberg",
            "roe": "Roetgen",
            "wml2": "EGW Westmünsterland",
        }

        DATA_SCHEMA = vol.Schema(
            {
                vol.Required(CONF_SERVICE): vol.In(DOMAIN_CHOICES)
            }
        )

        return self.async_show_form(
            step_id=SERVICE_ABFALLNAVI_DE,
            data_schema=DATA_SCHEMA,
            errors=errors
        )


    async def async_step_abfallnavi_de_select_city(self, user_input=None):
        """Configure specific service."""
        service = self._config[CONF_SOURCES][-1][CONF_SOURCE_ARGS][CONF_SERVICE]
        SERVICE_URL = f"https://{service}-abfallapp.regioit.de/abfall-app-{service}"

        errors = {}
        if user_input:
            self._config[CONF_SOURCES][-1][CONF_SOURCE_ARGS][CONF_CITY_ID] = user_input[CONF_CITY_ID]
            return await self.async_step_abfallnavi_de_select_street()


        r = requests.get(f"{SERVICE_URL}/rest/orte")
        r.encoding = "utf-8"  # requests doesn't guess the encoding correctly
        cities = json.loads(r.text)
        CITY_CHOICES = {}
        for city in cities:
            CITY_CHOICES[city["id"]] = city["name"]
      
        DATA_SCHEMA = vol.Schema(
            {
                vol.Required(CONF_CITY_ID): vol.In(CITY_CHOICES)
            }
        )

        return self.async_show_form(
            step_id=SERVICE_ABFALLNAVI_DE + "_select_city",
            data_schema=DATA_SCHEMA,
            errors=errors
        )

    async def async_step_abfallnavi_de_select_street(self, user_input=None):
        """Configure specific service."""
        service = self._config[CONF_SOURCES][-1][CONF_SOURCE_ARGS][CONF_SERVICE]
        SERVICE_URL = f"https://{service}-abfallapp.regioit.de/abfall-app-{service}"

        errors = {}
        if user_input:
            self._config[CONF_SOURCES][-1][CONF_SOURCE_ARGS][CONF_CITY_ID] = user_input[CONF_CITY_ID]
            return await self.async_step_abfallnavi_de_select_house_number()


        r = requests.get(f"{SERVICE_URL}/rest/orte{ort}/strassen")
        r.encoding = "utf-8"  # requests doesn't guess the encoding correctly
        cities = json.loads(r.text)
        CITY_CHOICES = {}
        for city in cities:
            CITY_CHOICES[city["id"]] = city["name"]
      
        DATA_SCHEMA = vol.Schema(
            {
                vol.Required(CONF_CITY_ID): vol.In(CITY_CHOICES)
            }
        )

        return self.async_show_form(
            step_id=SERVICE_ABFALLNAVI_DE + "_select_house_number",
            data_schema=DATA_SCHEMA,
            errors=errors
        )


class OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        """Initialize AccuWeather options flow."""
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        errors = {}
        if user_input is not None:
            # validate user input
            try:
                cv.time(user_input[CONF_FETCH_TIME])
            except:
                errors[CONF_FETCH_TIME] = "invalid_time_format"
            try:
                cv.positive_int(user_input[CONF_RANDOM_FETCH_TIME_OFFSET])
            except:
                errors[CONF_RANDOM_FETCH_TIME_OFFSET] = "invalid_positive_int"
            try:
                cv.time(user_input[CONF_DAY_SWITCH_TIME])
            except:
                errors[CONF_DAY_SWITCH_TIME] = "invalid_time_format"

            if (len(errors) == 0):
                # update options if all checks are ok
                return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_SEPARATOR, default=self._config_entry.options.get(CONF_SEPARATOR, DEFAULT_SEPARATOR)): str,
                    vol.Required(CONF_FETCH_TIME, default=self._config_entry.options.get(CONF_FETCH_TIME, DEFAULT_FETCH_TIME)): str,
                    vol.Required(CONF_RANDOM_FETCH_TIME_OFFSET, default=self._config_entry.options.get(CONF_RANDOM_FETCH_TIME_OFFSET, DEFAULT_RANDOM_FETCH_TIME_OFFSET)): int,
                    vol.Required(CONF_DAY_SWITCH_TIME, default=self._config_entry.options.get(CONF_DAY_SWITCH_TIME, DEFAULT_DAY_SWITCH_TIME)): str,
                }
            ),
            errors=errors,
        )
