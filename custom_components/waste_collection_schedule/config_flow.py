"""Config flow for 1-Wire component."""
import json
import logging

import homeassistant.helpers.config_validation as cv
import requests
import voluptuous as vol
from homeassistant.config_entries import (CONN_CLASS_CLOUD_POLL, ConfigEntry,
                                          ConfigFlow, OptionsFlow)
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_TYPE
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.helpers.typing import HomeAssistantType

from .const import DOMAIN  # pylint: disable=unused-import

# from .package.scraper import Scraper, Customize

_LOGGER = logging.getLogger(__name__)


# schema for initial config flow, entered by "Add Integration"
COUNTRY_LIST = [
    "de",
    "en",
]

CONF_COUNTRY = "country"
DATA_SCHEMA_COUNTRY_LIST = vol.Schema(
    {
        vol.Required(CONF_COUNTRY): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=COUNTRY_LIST,
                mode=selector.SelectSelectorMode.DROPDOWN,
                translation_key="country",
            )
        ),
    }
)


SOURCE_DE_LIST = [
    "de_source_1",
    "de_source_2",
]

SOURCE_EN_LIST = [
    "en_source_1",
    "en_source_2",
]

CONF_SOURCE_NAME = "source_name"
DATA_SCHEMA_SOURCE_LIST = {
    "de": vol.Schema(
        {
            vol.Required(CONF_SOURCE_NAME): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=SOURCE_DE_LIST,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="source_de",
                )
            ),
        }
    ),
    "en": vol.Schema(
        {
            vol.Required(CONF_SOURCE_NAME): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=SOURCE_EN_LIST,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="source_en",
                )
            ),
        }
    ),
}


cfg1 = selector.TextSelectorConfig(
    type=selector.TextSelectorType.SEARCH, suffix="mysuffix"
)
cfg1b = selector.TextSelectorConfig(
    type=selector.TextSelectorType.COLOR, suffix="mysuffix"
)
cfg4 = selector.ConstantSelectorConfig(label="mylabel", value="myvalue")


DATA_SCHEMA_USERx = vol.Schema(
    {
        vol.Required("text-selector", default="default1"): selector.TextSelector(cfg1),
        vol.Required("color-selector", default="default1"): selector.TextSelector(
            cfg1b
        ),
        vol.Required(
            "constant-selector", default="default1"
        ): selector.ConstantSelector(cfg4),
    }
)


class WasteCollectionScheduleFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle config flow."""

    VERSION = 1
    CONNECTION_CLASS = CONN_CLASS_CLOUD_POLL

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
        if user_input is not None:
            return self.async_show_form(
                step_id=f"select_source",
                data_schema=DATA_SCHEMA_SOURCE_LIST[user_input[CONF_COUNTRY]],
                errors=errors,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA_COUNTRY_LIST,
            errors=errors,
        )

    async def async_step_select_source(self, user_input=None):
        print(user_input[CONF_SOURCE_NAME])
        pass

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
