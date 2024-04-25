"""Waste Collection Schedule Component."""
import logging
import site
from pathlib import Path
from random import randrange

import homeassistant.helpers.config_validation as cv
import homeassistant.util.dt as dt_util
import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers.dispatcher import dispatcher_send

from .const import *

from homeassistant.helpers.event import async_call_later  # isort:skip
from homeassistant.helpers.event import async_track_time_change  # isort:skip

# add module directory to path
package_dir = Path(__file__).resolve().parents[0]
site.addsitedir(str(package_dir))
from waste_collection_schedule import Customize, SourceShell  # type: ignore # isort:skip # noqa: E402

_LOGGER = logging.getLogger(__name__)

CONFIG_FLOW_ENTITY_TYPES = ["calendar"]

CUSTOMIZE_CONFIG = vol.Schema(
    {
        vol.Optional(CONF_TYPE): cv.string,
        vol.Optional(CONF_ALIAS): cv.string,
        vol.Optional(CONF_SHOW): cv.boolean,
        vol.Optional(CONF_ICON): cv.icon,
        vol.Optional(CONF_PICTURE): cv.string,
        vol.Optional(CONF_USE_DEDICATED_CALENDAR): cv.boolean,
        vol.Optional(CONF_DEDICATED_CALENDAR_TITLE): cv.string,
    }
)

SOURCE_CONFIG = vol.Schema(
    {
        vol.Required(CONF_SOURCE_NAME): cv.string,
        vol.Required(CONF_SOURCE_ARGS): dict,
        vol.Optional(CONF_CUSTOMIZE, default=[]): vol.All(
            cv.ensure_list, [CUSTOMIZE_CONFIG]
        ),
        vol.Optional(CONF_SOURCE_CALENDAR_TITLE): cv.string,
    }
)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_SOURCES): vol.All(cv.ensure_list, [SOURCE_CONFIG]),
                vol.Optional(CONF_SEPARATOR, default=CONF_SEPARATOR_DEFAULT): cv.string,
                vol.Optional(CONF_FETCH_TIME, default=CONF_FETCH_TIME_DEFAULT): cv.time,
                vol.Optional(
                    CONF_RANDOM_FETCH_TIME_OFFSET, default=CONF_RANDOM_FETCH_TIME_OFFSET_DEFAULT
                ): cv.positive_int,
                vol.Optional(CONF_DAY_SWITCH_TIME, default=CONF_DAY_SWITCH_TIME_DEFAULT): cv.time,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

# YAML config logic

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the component. config contains data from configuration.yaml."""
    # Skip for config flow
    if DOMAIN not in config:
        return True

    # create empty api object as singleton
    api = WasteCollectionApi(
        hass,
        separator=config[DOMAIN][CONF_SEPARATOR],
        fetch_time=config[DOMAIN][CONF_FETCH_TIME],
        random_fetch_time_offset=config[DOMAIN][CONF_RANDOM_FETCH_TIME_OFFSET],
        day_switch_time=config[DOMAIN][CONF_DAY_SWITCH_TIME],
    )

    # create shells for source(s)
    for source in config[DOMAIN][CONF_SOURCES]:
        # create customize object
        customize = {}
        for c in source.get(CONF_CUSTOMIZE, {}):
            customize[c[CONF_TYPE]] = Customize(
                waste_type=c[CONF_TYPE],
                alias=c.get(CONF_ALIAS),
                show=c.get(CONF_SHOW, True),
                icon=c.get(CONF_ICON),
                picture=c.get(CONF_PICTURE),
                use_dedicated_calendar=c.get(CONF_USE_DEDICATED_CALENDAR, False),
                dedicated_calendar_title=c.get(CONF_DEDICATED_CALENDAR_TITLE, False),
            )
        api.add_source_shell(
            source_name=source[CONF_SOURCE_NAME],
            customize=customize,
            calendar_title=source.get(CONF_SOURCE_CALENDAR_TITLE),
            source_args=source.get(CONF_SOURCE_ARGS, {}),
        )

    # store api object
    hass.data.setdefault(DOMAIN, api)

    # load calendar platform
    await hass.helpers.discovery.async_load_platform(
        "calendar", DOMAIN, {"api": api}, config
    )

    # initial fetch of all data
    hass.add_job(api._fetch)

    async def async_fetch_data(service: ServiceCall) -> None:
        hass.add_job(api._fetch)

    # Register new Service fetch_data
    hass.services.async_register(
        DOMAIN, "fetch_data", async_fetch_data, schema=vol.Schema({})
    )

    return True


# Config flow logic

async def async_setup_entry(hass, entry):
    """This is called from the config flow."""
    config = dict(entry.data)

    # _LOGGER.debug("Initialising entities")
    for component in CONFIG_FLOW_ENTITY_TYPES:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, component)
        )

    entry.async_on_unload(entry.add_update_listener(async_update_listener))

    return True

async def async_update_listener(hass, entry):
    # Reload this instance
    await hass.config_entries.async_reload(entry.entry_id)

    return True

async def async_unload_entry(hass, entry):
    """Unload a config entry."""

    return await hass.config_entries.async_unload_platforms(entry, CONFIG_FLOW_ENTITY_TYPES)

async def async_migrate_entry(hass, config_entry) -> bool:
    """Migrate old entry."""
    # Version number has gone backwards
    if CONFIG_VERSION < config_entry.version:
        _LOGGER.error(
            "Backwards migration not possible. Please update the integration.")
        return False

    # Version number has gone up
    if config_entry.version < CONFIG_VERSION:
        _LOGGER.debug("Migrating from version %s", config_entry.version)
        new_data = config_entry.data

        config_entry.version = CONFIG_VERSION
        hass.config_entries.async_update_entry(config_entry, data=new_data)

        _LOGGER.debug("Migration to version %s successful",
                      config_entry.version)

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
    ):
        new_shell = SourceShell.create(
            source_name=source_name,
            customize=customize,
            source_args=source_args,
            calendar_title=calendar_title,
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
        dispatcher_send(self._hass, UPDATE_SENSORS_SIGNAL)
