"""YAML setup logic."""

import logging
import site
from pathlib import Path
from random import randrange

import homeassistant.helpers.config_validation as cv
import homeassistant.util.dt as dt_util
import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers.discovery import async_load_platform
from homeassistant.helpers.dispatcher import dispatcher_send

from homeassistant.helpers.event import async_call_later  # isort:skip
from homeassistant.helpers.event import async_track_time_change  # isort:skip


# add module directory to path
package_dir = Path(__file__).resolve().parents[0]
site.addsitedir(str(package_dir))
from . import const  # type: ignore # isort:skip # noqa: E402
from waste_collection_schedule import Customize, SourceShell  # type: ignore # isort:skip # noqa: E402

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


async def async_setup(hass: HomeAssistant, config: dict):
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

    async def async_fetch_data(service: ServiceCall) -> None:
        hass.add_job(api._fetch)

    # Register new Service fetch_data
    hass.services.async_register(
        const.DOMAIN, "fetch_data", async_fetch_data, schema=vol.Schema({})
    )

    return True


class WasteCollectionApi:
    def __init__(
        self, hass, separator, fetch_time, random_fetch_time_offset, day_switch_time
    ):
        self._hass = hass
        self._source_shells = []
        self._separator = separator
        self._fetch_time = fetch_time
        self._random_fetch_time_offset = random_fetch_time_offset
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
                self._update_sensors_callback,
                self._day_switch_time.hour,
                self._day_switch_time.minute,
                self._day_switch_time.second,
            )

        # add a timer at midnight (if not already there) to update days-to
        midnight = dt_util.parse_time("00:00")
        if midnight != self._fetch_time and midnight != self._day_switch_time:
            async_track_time_change(
                hass,
                self._update_sensors_callback,
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

    def add_source_shell(
        self,
        source_name,
        customize,
        source_args,
        calendar_title,
        day_offset,
    ):
        new_shell = SourceShell.create(
            source_name=source_name,
            customize=customize,
            source_args=source_args,
            calendar_title=calendar_title,
            day_offset=day_offset,
        )

        if new_shell:
            self._source_shells.append(new_shell)
        return new_shell

    def _fetch(self, *_):
        for shell in self._source_shells:
            shell.fetch()

        self._update_sensors_callback()

    @property
    def shells(self):
        return self._source_shells

    def get_shell(self, index):
        return self._source_shells[index] if index < len(self._source_shells) else None

    @callback
    def _fetch_callback(self, *_):
        async_call_later(
            self._hass,
            randrange(0, 60 * self._random_fetch_time_offset),
            self._fetch_now_callback,
        )

    @callback
    def _fetch_now_callback(self, *_):
        self._hass.add_job(self._fetch)

    @callback
    def _update_sensors_callback(self, *_):
        dispatcher_send(self._hass, const.UPDATE_SENSORS_SIGNAL)
