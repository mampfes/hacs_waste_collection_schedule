"""Config flow for 1-Wire component."""
import json
import logging
import site
from pathlib import Path

import homeassistant.helpers.config_validation as cv
import requests
import voluptuous as vol
from homeassistant.config_entries import (CONN_CLASS_CLOUD_POLL, ConfigEntry,
                                          ConfigFlow, OptionsFlow)
from homeassistant.core import callback
from homeassistant.helpers.typing import HomeAssistantType

from .config_flow_const import (CONF_COUNTRY, DATA_SCHEMA_COUNTRY_LIST,
                                DATA_SCHEMA_SOURCE_CONFIG,
                                DATA_SCHEMA_SOURCE_LIST)
from .const import CONF_COUNTRY, CONF_SOURCE_ARGS, CONF_SOURCE_NAME, DOMAIN

# add module directory to path
# package_dir = Path(__file__).resolve().parents[0]
# site.addsitedir(str(package_dir))
from waste_collection_schedule import Customize, SourceShell  # type: ignore # isort:skip # noqa: E402

_LOGGER = logging.getLogger(__name__)


class WasteCollectionScheduleFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle config flow."""

    VERSION = 1
    CONNECTION_CLASS = CONN_CLASS_CLOUD_POLL

    _source_name = None

    def __init__(self):
        """Initialize config flow."""
        # self._config = { CONF_SOURCES: [] }
        pass

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        """Handle start of config flow.

        Let user select country.
        """
        errors = {}

        # select country (including generic for ICS + static)
        return self.async_show_form(
            step_id="select_country",
            data_schema=DATA_SCHEMA_COUNTRY_LIST,
            errors=errors,
            last_step=False,
        )

    async def async_step_select_country(self, user_input):
        """Select country step done, now select source"""
        errors = {}

        return self.async_show_form(
            step_id=f"select_source",
            data_schema=DATA_SCHEMA_SOURCE_LIST[user_input[CONF_COUNTRY]],
            errors=errors,
            last_step=False,
        )

    async def async_step_select_source(self, user_input):
        """Select source step done, now configure source"""
        errors = {}

        self._source_name = user_input[CONF_SOURCE_NAME]
        print(f"source_name = {self._source_name}")

        return self.async_show_form(
            step_id=f"configure_source",
            data_schema=DATA_SCHEMA_SOURCE_CONFIG[self._source_name],
            errors=errors,
            last_step=True,
            description_placeholders={"source_name": self._source_name},
        )

    async def async_step_configure_source(self, user_input):
        """Configure source step done, store config entry"""
        print(user_input)

        shell = SourceShell.create(
            source_name=self._source_name, customize={}, source_args=user_input
        )

        await self.hass.async_add_job(shell.fetch)

        # TODO: exception handling?
        # TODO: test if entries found!

        await self.async_set_unique_id(f"{DOMAIN}-{shell.unique_id}")
        self._abort_if_unique_id_configured()
        return self.async_create_entry(
            title=f"{self._source_name}",
            data={CONF_SOURCE_NAME: self._source_name, CONF_SOURCE_ARGS: user_input},
        )

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
                waste_types = await self.hass.async_add_executor_job(
                    self._test_scraper, SERVICE_ICS, user_input
                )
                if len(waste_types) == 0:
                    errors["base"] = "scraper_test_failed"
                else:
                    self._config[CONF_SOURCES].append(
                        {CONF_SOURCE_NAME: SERVICE_ICS, CONF_SOURCE_ARGS: user_input}
                    )

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
            step_id=SERVICE_ICS, data_schema=DATA_SCHEMA, errors=error
        )

    async def async_step_abfallnavi_de(self, user_input=None):
        """First step of service specific flow.

        Select service operator.
        """

        errors = {}
        if user_input:
            self._config[CONF_SOURCES][-1][CONF_SOURCE_ARGS][CONF_SERVICE] = user_input[
                CONF_SERVICE
            ]
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

        DATA_SCHEMA = vol.Schema({vol.Required(CONF_SERVICE): vol.In(DOMAIN_CHOICES)})

        return self.async_show_form(
            step_id=SERVICE_ABFALLNAVI_DE, data_schema=DATA_SCHEMA, errors=errors
        )

    async def async_step_abfallnavi_de_select_city(self, user_input=None):
        """Configure specific service."""
        service = self._config[CONF_SOURCES][-1][CONF_SOURCE_ARGS][CONF_SERVICE]
        SERVICE_URL = f"https://{service}-abfallapp.regioit.de/abfall-app-{service}"

        errors = {}
        if user_input:
            self._config[CONF_SOURCES][-1][CONF_SOURCE_ARGS][CONF_CITY_ID] = user_input[
                CONF_CITY_ID
            ]
            return await self.async_step_abfallnavi_de_select_street()

        r = requests.get(f"{SERVICE_URL}/rest/orte")
        r.encoding = "utf-8"  # requests doesn't guess the encoding correctly
        cities = json.loads(r.text)
        CITY_CHOICES = {}
        for city in cities:
            CITY_CHOICES[city["id"]] = city["name"]

        DATA_SCHEMA = vol.Schema({vol.Required(CONF_CITY_ID): vol.In(CITY_CHOICES)})

        return self.async_show_form(
            step_id=SERVICE_ABFALLNAVI_DE + "_select_city",
            data_schema=DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_abfallnavi_de_select_street(self, user_input=None):
        """Configure specific service."""
        service = self._config[CONF_SOURCES][-1][CONF_SOURCE_ARGS][CONF_SERVICE]
        SERVICE_URL = f"https://{service}-abfallapp.regioit.de/abfall-app-{service}"

        errors = {}
        if user_input:
            self._config[CONF_SOURCES][-1][CONF_SOURCE_ARGS][CONF_CITY_ID] = user_input[
                CONF_CITY_ID
            ]
            return await self.async_step_abfallnavi_de_select_house_number()

        r = requests.get(f"{SERVICE_URL}/rest/orte{ort}/strassen")
        r.encoding = "utf-8"  # requests doesn't guess the encoding correctly
        cities = json.loads(r.text)
        CITY_CHOICES = {}
        for city in cities:
            CITY_CHOICES[city["id"]] = city["name"]

        DATA_SCHEMA = vol.Schema({vol.Required(CONF_CITY_ID): vol.In(CITY_CHOICES)})

        return self.async_show_form(
            step_id=SERVICE_ABFALLNAVI_DE + "_select_house_number",
            data_schema=DATA_SCHEMA,
            errors=errors,
        )


class OptionsFlowHandler(OptionsFlow):
    def __init__(self, config_entry):
        """Initialize AccuWeather options flow."""
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        errors = {}
        pass
