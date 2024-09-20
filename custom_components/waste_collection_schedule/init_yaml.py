"""YAML setup logic."""

import logging
import site
from pathlib import Path

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.core import HomeAssistant
from homeassistant.helpers.discovery import async_load_platform

from .service import get_fetch_all_service
from .waste_collection_api import WasteCollectionApi

# add module directory to path
package_dir = Path(__file__).resolve().parents[0]
site.addsitedir(str(package_dir))
from . import const  # type: ignore # isort:skip # noqa: E402
from waste_collection_schedule import Customize  # type: ignore # isort:skip # noqa: E402

_LOGGER = logging.getLogger(__name__)

CUSTOMIZE_CONFIG = vol.Schema(
    {
        vol.Optional(const.CONF_TYPE): cv.string,
        vol.Optional(const.CONF_ALIAS): cv.string,
        vol.Optional(const.CONF_SHOW): cv.boolean,
        vol.Optional(const.CONF_ICON): cv.icon,
        vol.Optional(const.CONF_PICTURE): cv.string,
        vol.Optional(const.CONF_USE_DEDICATED_CALENDAR): cv.boolean,
        vol.Optional(const.CONF_DEDICATED_CALENDAR_TITLE): cv.string,
    }
)

SOURCE_CONFIG = vol.Schema(
    {
        vol.Required(const.CONF_SOURCE_NAME): cv.string,
        vol.Required(const.CONF_SOURCE_ARGS): dict,
        vol.Optional(const.CONF_CUSTOMIZE, default=[]): vol.All(
            cv.ensure_list, [CUSTOMIZE_CONFIG]
        ),
        vol.Optional(const.CONF_SOURCE_CALENDAR_TITLE): cv.string,
    }
)

CONFIG_SCHEMA = vol.Schema(
    {
        const.DOMAIN: vol.Schema(
            {
                vol.Required(const.CONF_SOURCES): vol.All(
                    cv.ensure_list, [SOURCE_CONFIG]
                ),
                vol.Optional(
                    const.CONF_SEPARATOR, default=const.CONF_SEPARATOR_DEFAULT
                ): cv.string,
                vol.Optional(
                    const.CONF_FETCH_TIME, default=const.CONF_FETCH_TIME_DEFAULT
                ): cv.time,
                vol.Optional(
                    const.CONF_RANDOM_FETCH_TIME_OFFSET,
                    default=const.CONF_RANDOM_FETCH_TIME_OFFSET_DEFAULT,
                ): cv.positive_int,
                vol.Optional(
                    const.CONF_DAY_SWITCH_TIME,
                    default=const.CONF_DAY_SWITCH_TIME_DEFAULT,
                ): cv.time,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the component. config contains data from configuration.yaml."""
    # Skip for config flow
    if const.DOMAIN not in config:
        return True

    # create empty api object as singleton
    api = WasteCollectionApi(
        hass,
        separator=config[const.DOMAIN][const.CONF_SEPARATOR],
        fetch_time=config[const.DOMAIN][const.CONF_FETCH_TIME],
        random_fetch_time_offset=config[const.DOMAIN][
            const.CONF_RANDOM_FETCH_TIME_OFFSET
        ],
        day_switch_time=config[const.DOMAIN][const.CONF_DAY_SWITCH_TIME],
    )

    # create shells for source(s)
    for source in config[const.DOMAIN][const.CONF_SOURCES]:
        # create customize object
        customize = {}
        for c in source.get(const.CONF_CUSTOMIZE, {}):
            customize[c[const.CONF_TYPE]] = Customize(
                waste_type=c[const.CONF_TYPE],
                alias=c.get(const.CONF_ALIAS),
                show=c.get(const.CONF_SHOW, True),
                icon=c.get(const.CONF_ICON),
                picture=c.get(const.CONF_PICTURE),
                use_dedicated_calendar=c.get(const.CONF_USE_DEDICATED_CALENDAR, False),
                dedicated_calendar_title=c.get(
                    const.CONF_DEDICATED_CALENDAR_TITLE, False
                ),
            )

        await hass.async_add_executor_job(
            api.add_source_shell,
            source[const.CONF_SOURCE_NAME],
            customize,
            source.get(const.CONF_SOURCE_ARGS, {}),
            source.get(const.CONF_SOURCE_CALENDAR_TITLE),
            source.get(const.CONF_DAY_OFFSET, 0),
        )

    # store api object
    hass.data.setdefault(const.DOMAIN, {})["YAML_CONFIG"] = api

    # load calendar platform
    await async_load_platform(hass, "calendar", const.DOMAIN, {"api": api}, config)

    # initial fetch of all data
    hass.add_job(api._fetch)

    # Register new Service fetch_data
    hass.services.async_register(
        const.DOMAIN, "fetch_data", get_fetch_all_service(hass), schema=vol.Schema({})
    )

    return True
