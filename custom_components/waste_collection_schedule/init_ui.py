"""Config flow setup logic."""
import logging
from typing import Any

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .service import get_fetch_all_service
from .wcs_coordinator import WCSCoordinator

from . import const  # type: ignore # isort:skip # noqa: E402
from .waste_collection_schedule import SourceShell, Customize  # type: ignore # isort:skip # noqa: E402

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["calendar", "sensor"]


async def async_setup_entry(hass: HomeAssistant, entry) -> bool:
    """Set up component from a config entry, entry contains data from config entry database."""
    options = entry.options
    _LOGGER.debug(
        "Setting up entry %s, with data %s and options %s",
        entry.entry_id,
        entry.data,
        options,
    )

    customize_dicts: dict[str, dict[str, Any]] = options.get(const.CONF_CUSTOMIZE, {})

    customize: dict[str, Customize] = {}
    for waste_type, c in customize_dicts.items():
        customize[waste_type] = Customize(
            waste_type=waste_type,
            alias=c.get(const.CONF_ALIAS),
            show=c.get(const.CONF_SHOW, True),
            icon=c.get(const.CONF_ICON),
            picture=c.get(const.CONF_PICTURE),
            use_dedicated_calendar=c.get(const.CONF_USE_DEDICATED_CALENDAR, False),
            dedicated_calendar_title=c.get(const.CONF_DEDICATED_CALENDAR_TITLE, False),
        )

    shell = await hass.async_add_executor_job(
        SourceShell.create,
        entry.data[const.CONF_SOURCE_NAME],
        customize,
        entry.data[const.CONF_SOURCE_ARGS],
        options.get(const.CONF_SOURCE_CALENDAR_TITLE),
    )

    coordinator = WCSCoordinator(
        hass,
        source_shell=shell,
        separator=options.get(const.CONF_SEPARATOR, const.CONF_SEPARATOR_DEFAULT),
        fetch_time=cv.time(
            options.get(const.CONF_FETCH_TIME, const.CONF_FETCH_TIME_DEFAULT)
        ),
        random_fetch_time_offset=options.get(
            const.CONF_RANDOM_FETCH_TIME_OFFSET,
            const.CONF_RANDOM_FETCH_TIME_OFFSET_DEFAULT,
        ),
        day_switch_time=cv.time(
            options.get(const.CONF_DAY_SWITCH_TIME, const.CONF_DAY_SWITCH_TIME_DEFAULT)
        ),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(const.DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_update_listener))

    # Register new Service fetch_data
    hass.services.async_register(
        const.DOMAIN, "fetch_data", get_fetch_all_service(hass), schema=vol.Schema({})
    )

    return True


async def async_update_listener(hass, entry):
    # Reload this instance
    await hass.config_entries.async_reload(entry.entry_id)

    return True


async def async_unload_entry(hass, entry):
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_migrate_entry(hass, config_entry: ConfigEntry) -> bool:
    """Migrate old entry."""
    # Version number has gone backwards
    if const.CONFIG_VERSION < config_entry.version:
        _LOGGER.error(
            "Backwards migration not possible. Please update the integration."
        )
        return False

    # Version number has gone up
    if config_entry.version < const.CONFIG_VERSION:
        _LOGGER.debug("Migrating from version %s", config_entry.version)
        new_data = {**config_entry.data}

        if config_entry.version < 2 and const.CONFIG_VERSION >= 2:
            if new_data.get("name", "") == "wychavon_gov_uk":
                _LOGGER.debug("Migrating from wychavon_gov_uk to roundlookup_uk")
                new_data["name"] = "roundlookup_uk"
                new_data["args"]["council"] = "Wychavon"

        hass.config_entries.async_update_entry(
            config_entry, data=new_data, version=const.CONFIG_VERSION
        )

        _LOGGER.debug("Migration to version %s successful", config_entry.version)

    return True
