"""Waste Collection Schedule Component."""
import asyncio
import logging

import voluptuous as vol

from homeassistant.core import HomeAssistant, callback
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.event import async_track_time_change
import homeassistant.util.dt as dt_util

from .const import DOMAIN
from .package.scraper import Scraper, Customize

_LOGGER = logging.getLogger(__name__)

CONF_SCRAPERS = "scrapers"
CONF_SOURCE_NAME = "source"
CONF_SOURCE_ARGS = "args"  # scraper-source arguments
CONF_SEPARATOR = ", "
CONF_FETCH_TIME = "fetch_time"
CONF_DAY_SWITCH_TIME = "day_switch_time"

CONF_CUSTOMIZE = "customize"
CONF_TYPE = "type"
CONF_ALIAS = "alias"
CONF_SHOW = "show"
CONF_ICON = "icon"
CONF_PICTURE = "picture"

DEFAULT_SEPARATOR = ", "

SCRAPER_CONFIG = vol.Schema(
    {vol.Required(CONF_SOURCE_NAME): cv.string}, extra=vol.ALLOW_EXTRA
)

CUSTOMIZE_CONFIG = vol.Schema(
    {
        vol.Optional(CONF_TYPE): cv.string,
        vol.Optional(CONF_ALIAS): cv.string,
        vol.Optional(CONF_SHOW): cv.boolean,
        vol.Optional(CONF_ICON): cv.icon,
        vol.Optional(CONF_PICTURE): cv.url,
    }
)

CONFIG_SCHEMA = vol.Schema(
    {

        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_SCRAPERS): vol.All(cv.ensure_list, [SCRAPER_CONFIG]),
                vol.Optional(CONF_SEPARATOR, default=DEFAULT_SEPARATOR): cv.string,
                vol.Optional(CONF_FETCH_TIME, default="01:00"): cv.time,
                vol.Optional(CONF_DAY_SWITCH_TIME, default="10:00"): cv.time,
                vol.Optional(CONF_CUSTOMIZE, default=[]): vol.All(
                    cv.ensure_list, [CUSTOMIZE_CONFIG]
                ),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the component. config contains data from configuration.yaml."""

    # create empty api object as singleton
    api = WasteCollectionApi(
        hass,
        separator=config[DOMAIN][CONF_SEPARATOR],
        fetch_time=config[DOMAIN][CONF_FETCH_TIME],
        day_switch_time=config[DOMAIN][CONF_DAY_SWITCH_TIME],
    )

    # create scraper(s)
    for s in config[DOMAIN][CONF_SCRAPERS]:
        # create customize object
        customize = {}
        for c in s.get(CONF_CUSTOMIZE, {}):
            customize[c[CONF_TYPE]] = Customize(
                name=c[CONF_TYPE],
                alias=c.get(CONF_ALIAS),
                show=c.get(CONF_SHOW, True),
                icon=c.get(CONF_ICON),
                picture=c.get(CONF_PICTURE),
            )
        api.add_scraper(s[CONF_SOURCE_NAME], customize, s.get(CONF_SOURCE_ARGS, {}))

    # store api object
    hass.data.setdefault(DOMAIN, api)

    # initial fetch of all data
    await hass.async_add_executor_job(api._fetch)

    return True


class WasteCollectionApi:
    def __init__(self, hass, separator, fetch_time, day_switch_time):
        self._scrapers = []
        self._sensors = []
        self._separator = separator
        self._fetch_time = fetch_time
        self._day_switch_time = day_switch_time

        # start timer to fetch date once per day
        async_track_time_change(
            hass,
            self._fetch_callback,
            self._fetch_time.hour,
            self._fetch_time.minute,
            self._fetch_time.second,
        )

        # start timer for day-switch time
        if self._day_switch_time != self._fetch_time:
            async_track_time_change(
                hass,
                self._day_switch_callback,
                self._day_switch_time.hour,
                self._day_switch_time.minute,
                self._day_switch_time.second,
            )

        # add a timer at midnight (if not already there) to update days-to
        midnight = dt_util.parse_time("00:00")
        if midnight != self._fetch_time and midnight != self._day_switch_time:
            async_track_time_change(
                hass,
                self._midnight_callback,
                midnight.hour,
                midnight.minute,
                midnight.second,
            )

    @property
    def separator(self):
        """Separator string, used to separator waste types."""
        return self._separator

    @property
    def fetch_time(self):
        """When to fetch to data."""
        return self._fetch_time

    @property
    def day_switch_time(self):
        """When to hide entries for today."""
        return self._day_switch_time

    def add_scraper(self, source_name, customize, source_args):
        self._scrapers.append(Scraper.create(
            source_name, -3, customize, source_args
        ))

    def add_sensor(self, sensor):
        self._sensors.append(sensor)

    def _fetch(self):
        for s in self._scrapers:
            try:
                s.fetch()
            except error:
                _LOGGER.error(f"fetch failed for source {s.source}: {error}")

        self._update_sensors()

    def _update_sensors(self):
        for s in self._sensors:
            s.update_sensor()

    def get_scraper(self, index):
        return self._scrapers[index] if index < len(self._scrapers) else None

    @callback
    def _fetch_callback(self, *_):
        self._fetch()

    @callback
    def _day_switch_callback(self, *_):
        self._update_sensors()

    @callback
    def _midnight_callback(self, *_):
        self._update_sensors()
