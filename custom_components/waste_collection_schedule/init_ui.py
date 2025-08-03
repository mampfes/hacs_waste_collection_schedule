"""Config flow setup logic."""

import logging
from typing import Any

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .service import get_fetch_all_service
from .wcs_coordinator import WCSCoordinator
from .waste_collection_schedule.service.DeviceKeyStore import initialize_device_key_store

from . import const  # type: ignore # isort:skip # noqa: E402
from .waste_collection_schedule import SourceShell, Customize  # type: ignore # isort:skip # noqa: E402

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["calendar", "sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up component from a config entry, entry contains data from config entry database."""
    options = entry.options
    _LOGGER.debug(
        "Setting up entry %s, with data %s and options %s",
        entry.entry_id,
        entry.data,
        options,
    )

    # Initialize and load device key store
    device_store = initialize_device_key_store(hass)
    await device_store.async_load()

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
        options.get(const.CONF_DAY_OFFSET, const.CONF_DAY_OFFSET_DEFAULT),
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


async def async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    # Reload this instance
    await hass.config_entries.async_reload(entry.entry_id)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate old entry."""
    _LOGGER.debug("Migrating from version %s", config_entry.version)
    _LOGGER.debug("minor version %s", config_entry.minor_version)

    # Version number has gone backwards
    if const.CONFIG_VERSION < config_entry.version:
        _LOGGER.error(
            "Backwards migration not possible. Please update the integration."
        )
        return False

    # Version number has gone up
    if config_entry.version < const.CONFIG_VERSION or (
        config_entry.version == const.CONFIG_VERSION
        and config_entry.minor_version < const.CONFIG_MINOR_VERSION
    ):
        _LOGGER.debug("Migrating from version %s", config_entry.version)
        new_data = {**config_entry.data}

        if config_entry.version < 2 and const.CONFIG_VERSION >= 2:
            # Migrate from wychavon_gov_uk to roundlookup_uk
            if new_data.get("name", "") == "wychavon_gov_uk":
                _LOGGER.debug("Migrating from wychavon_gov_uk to roundlookup_uk")
                new_data["name"] = "roundlookup_uk"
                new_data["args"]["council"] = "Wychavon"

        # Implicitly migrate from any version <= 2.1 to 2.2 (or higher)
        if config_entry.version < 2 or (
            config_entry.version == 2 and config_entry.minor_version < 2
        ):
            # Migrate from chiltern_gov_uk to iapp_itouchvision_com
            if new_data.get("name", "") == "chiltern_gov_uk":
                _LOGGER.debug("Migrating from chiltern_gov_uk to iapp_itouchvision_com")
                new_data["name"] = "iapp_itouchvision_com"
                new_data["args"]["municipality"] = "BUCKINGHAMSHIRE"
        if config_entry.version < 2 or (
            config_entry.version == 2 and config_entry.minor_version < 3
        ):
            # Migrate from sicaapp_lu to sica_lu
            if new_data.get("name", "") == "sicaapp_lu":
                if not new_data["args"].get("commune"):
                    return False
                _LOGGER.debug("Migrating from sicaapp_lu to sica_lu")
                new_data["name"] = "sica_lu"
                new_data["args"]["municipality"] = new_data["args"].get("commune")
                del new_data["args"]["commune"]

        if config_entry.version < 2 or (
            config_entry.version == 2 and config_entry.minor_version < 4
        ):
            # remove version from ics source
            if new_data.get("name", "") == "ics":
                _LOGGER.debug("Migrating ics source")
                if new_data["args"].get("version"):
                    del new_data["args"]["version"]
        if config_entry.version < 2 or (
            config_entry.version == 2 and config_entry.minor_version < 5
        ):
            # Migrate was_wolfsburg_de remove city argument
            if new_data.get("name", "") == "was_wolfsburg_de":
                _LOGGER.debug("Migrating was_wolfsburg_de source")
                if new_data["args"].get("city"):
                    del new_data["args"]["city"]

        if config_entry.version < 2 or (
            config_entry.version == 2 and config_entry.minor_version < 5
        ):
            # source name change from fkf_bp_hu to mohu_bp_hu
            if new_data.get("name", "") == "fkf_bp_hu":
                new_data["name"] = "mohu_bp_hu"
                _LOGGER.debug("Migrating fkf_bp_hu to mohu_bp_hu")

        # Migrate aylesburyvaledc_gov_uk to iapp_itouchvision_com.py
        if config_entry.version < 2 or (
            config_entry.version == 2 and config_entry.minor_version < 6
        ):
            if new_data.get("name", "") == "aylesburyvaledc_gov_uk":
                _LOGGER.info(
                    "Migrating from aylesburyvaledc_gov_uk to iapp_itouchvision_com"
                )
                new_data["name"] = "iapp_itouchvision_com"
                new_data["args"]["municipality"] = "AYLESBURY VALE"

        hass.config_entries.async_update_entry(
            config_entry,
            data=new_data,
            version=const.CONFIG_VERSION,
            minor_version=const.CONFIG_MINOR_VERSION,
        )

        _LOGGER.debug("Migration to version %s successful", config_entry.version)

    return True
