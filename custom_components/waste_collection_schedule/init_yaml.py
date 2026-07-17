"""YAML setup logic."""

import logging
import site
from pathlib import Path

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.const import CONF_NAME, CONF_VALUE_TEMPLATE
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


def _time_value(value):
    """Validate a time-of-day config value.

    Works around a YAML 1.1 quirk: PyYAML's implicit "sexagesimal" (base60)
    resolver turns an *unquoted* ``HH:MM`` value such as ``10:00`` into the
    integer ``600`` (10 * 60 + 0) instead of the string ``"10:00"``, which
    then fails Home Assistant's ``cv.time`` validator. Times with a leading
    zero (e.g. ``09:59``) are unaffected because the resolver requires the
    first digit to be 1-9, so this only bites hours 10-23.

    If we receive such an integer, reconstruct the original ``HH:MM`` (or
    ``HH:MM:SS``) string before validating. The two possible value ranges
    (60-1439 for ``H:MM``, 3600-86399 for ``H:MM:SS``) never overlap, so the
    original format can be recovered unambiguously.

    See https://github.com/mampfes/hacs_waste_collection_schedule/issues/5065
    """
    if isinstance(value, int) and not isinstance(value, bool):
        if 60 <= value <= 1439:
            value = f"{value // 60:02d}:{value % 60:02d}:00"
        elif 3600 <= value <= 86399:
            hours, remainder = divmod(value, 3600)
            minutes, seconds = divmod(remainder, 60)
            value = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return cv.time(value)


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

SENSOR_CONFIG = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Optional(const.CONF_SOURCE_INDEX, default=0): vol.Any(
            cv.positive_int, vol.All(cv.ensure_list, [cv.positive_int])
        ),
        vol.Optional(const.CONF_DETAILS_FORMAT, default="upcoming"): cv.string,
        vol.Optional(const.CONF_COUNT): cv.positive_int,
        vol.Optional(const.CONF_LEADTIME): cv.positive_int,
        vol.Optional(const.CONF_COLLECTION_TYPES): cv.ensure_list,
        vol.Optional(CONF_VALUE_TEMPLATE): cv.template,
        vol.Optional(const.CONF_DATE_TEMPLATE): cv.template,
        vol.Optional(const.CONF_ADD_DAYS_TO, default=False): cv.boolean,
        vol.Optional(const.CONF_EVENT_INDEX, default=0): cv.positive_int,
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
        vol.Optional(const.CONF_DAY_OFFSET, default=const.CONF_DAY_OFFSET_DEFAULT): int,
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
                ): _time_value,
                vol.Optional(
                    const.CONF_FETCH_INTERVAL_DAYS,
                    default=const.CONF_FETCH_INTERVAL_DAYS_DEFAULT,
                ): cv.positive_int,
                vol.Optional(
                    const.CONF_RANDOM_FETCH_TIME_OFFSET,
                    default=const.CONF_RANDOM_FETCH_TIME_OFFSET_DEFAULT,
                ): cv.positive_int,
                vol.Optional(
                    const.CONF_DAY_SWITCH_TIME,
                    default=const.CONF_DAY_SWITCH_TIME_DEFAULT,
                ): _time_value,
                vol.Optional(const.CONF_SENSORS, default=[]): vol.All(
                    cv.ensure_list, [SENSOR_CONFIG]
                ),
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
        fetch_interval_days=config[const.DOMAIN][const.CONF_FETCH_INTERVAL_DAYS],
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

    # perform initial fetch so collection types are known before platform setup
    await hass.async_add_executor_job(api._fetch)

    # load calendar platform
    await async_load_platform(hass, "calendar", const.DOMAIN, {"api": api}, config)

    # load sensor platform for each sensor defined in the config
    for sensor_config in config[const.DOMAIN].get(const.CONF_SENSORS, []):
        await async_load_platform(
            hass,
            "sensor",
            const.DOMAIN,
            {"api": api, "sensor_config": sensor_config},
            config,
        )

    # Register new Service fetch_data
    hass.services.async_register(
        const.DOMAIN, "fetch_data", get_fetch_all_service(hass), schema=vol.Schema({})
    )

    return True
