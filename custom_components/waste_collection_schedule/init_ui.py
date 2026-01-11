"""Config flow setup logic."""

import logging
from typing import Any

import homeassistant.helpers.config_validation as cv
import requests
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .service import get_fetch_all_service
from .waste_collection_schedule.service.DeviceKeyStore import (
    initialize_device_key_store,
)
from .wcs_coordinator import WCSCoordinator

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

        if config_entry.version < 2 or (
            config_entry.version == 2 and config_entry.minor_version < 7
        ):
            # Migrate bsr_de source to new format
            if new_data.get("name", "") == "bsr_de":
                _LOGGER.info("Migrating bsr_de source to new format")
                try:
                    abf_strasse = new_data["args"]["abf_strasse"]
                    abf_hausnr = new_data["args"]["abf_hausnr"]
                    abf_strasse_as_list = abf_strasse.split(",", 1)
                    street_only = abf_strasse_as_list[0].strip()
                    postal_code_and_area = (
                        abf_strasse_as_list[1].strip()
                        if len(abf_strasse_as_list) > 1
                        else ""
                    )

                    params = {"searchQuery": f"{street_only}:::{abf_hausnr}"}
                    with requests.Session() as bsr_de_migrate_session:
                        bsr_de_migrate_response = bsr_de_migrate_session.get(
                            "https://umnewforms.bsr.de/p/de.bsr.adressen.app//plzSet/plzSet",
                            params=params,
                        )
                        bsr_de_migrate_response.raise_for_status()
                    data = bsr_de_migrate_response.json()
                except Exception:
                    _LOGGER.exception(
                        "Error migrating bsr_de source. Please reconfigure bsr_de."
                    )
                else:
                    candidates = [
                        candidate["value"]
                        for candidate in data
                        if postal_code_and_area in candidate["label"]
                    ]
                    if len(candidates) == 1:
                        # we have a single candidate, use it
                        del new_data["args"]["abf_strasse"]
                        del new_data["args"]["abf_hausnr"]
                        new_data["args"]["schedule_id"] = candidates[0]
                        _LOGGER.info(
                            "Migrated bsr_de source to new format. schedule_id is %s.",
                            candidates[0],
                        )
                    else:
                        # we have multiple candidates or none
                        _LOGGER.error(
                            "Cannot migrate bsr_de source, found %d candidates for street %s and house number %s. Please reconfigure bsr_de.",
                            len(candidates),
                            abf_strasse,
                            abf_hausnr,
                        )

        if config_entry.version < 2 or (
            config_entry.version == 2 and config_entry.minor_version < 8
        ):
            # Migrate iweb_itouchvision_com to iapp_itouchvision_com
            if new_data.get("name", "") == "iweb_itouchvision_com":
                _LOGGER.info(
                    "Migrating from iweb_itouchvision_com to iapp_itouchvision_com"
                )
                if not new_data["args"].get("council"):
                    return False
                new_data["name"] = "iapp_itouchvision_com"
                new_data["args"]["municipality"] = (
                    new_data["args"].get("council").replace("_", " ")
                )  # "TEST_VALLEY" to "TEST VALLEY"
                # only uprn and municipality args required, so delete council and postcode args
                del new_data["args"]["council"]
                del new_data["args"]["postcode"]

        if config_entry.version < 2 or (
            config_entry.version == 2 and config_entry.minor_version < 9
        ):
            # Migrate kuringgai_nsw_gov_au to impactapps.com_au
            if new_data.get("name", "") == "kuringgai_nsw_gov_au":
                _LOGGER.info("Migrating from kuringgai_nsw_gov_au to impactapps_com_au")
                new_data["name"] = "impactapps_com_au"
                new_data["args"]["service"] = "ku-ring-gai"
                # postcode arg no longer needed, so delete it
                del new_data["args"]["postcode"]

        if config_entry.version < 2 or (
            config_entry.version == 2 and config_entry.minor_version < 10
        ):
            # Migrate from birmingham_gov_uk to roundlookup_uk
            if new_data.get("name", "") == "peterborough_gov_uk":
                _LOGGER.debug("Migrating from peterborough_gov_uk to ics configuration")

                new_data["args"]["post_code"] = new_data["args"].get("post_code")
                new_data["args"]["uprn"] = new_data["args"].get("uprn")
                if "number" in new_data["args"]:
                    del new_data["args"]["number"]
                if "name" in new_data["args"]:
                    del new_data["args"]["name"]

        if config_entry.version < 2 or (
            config_entry.version == 2 and config_entry.minor_version < 11
        ):
            # Migrate Cambridge City and South Cambs to Greater Cambridge Waste
            if (
                new_data.get("name", "") == "cambridge_gov_uk"
                or new_data.get("name", "") == "scambs_gov_uk"
            ):
                _LOGGER.info(
                    "Migrating cambridge_gov_uk and scambs_gov_uk to greater_cambridge_waste_org"
                )
                new_data["name"] = "greater_cambridge_waste_org"
                # map across old args
                new_data["args"]["postcode"] = new_data["args"]["post_code"]
                new_data["args"]["name_or_number"] = new_data["args"]["number"]
                new_data["args"]["uprn"] = None
                # remove old args
                del new_data["args"]["post_code"]
                del new_data["args"]["number"]

        if config_entry.version < 2 or (
            config_entry.version == 2 and config_entry.minor_version < 12
        ):
            # Migrate Cambridge City and South Cambs to Greater Cambridge Waste
            if new_data.get("name", "") == "abfall_lippe_de":
                _LOGGER.info("Migrating abfall_lippe_de to abfallnavi_de")
                new_data["name"] = "abfallnavi_de"
                # map across old args
                new_data["args"]["ort"] = new_data["args"]["gemeinde"]
                del new_data["args"]["gemeinde"]
                new_data["args"]["service"] = "awvlippe"
                # remove old args
                if "bezirk" in new_data["args"]:
                    del new_data["args"]["bezirk"]

        if config_entry.version < 2 or (
            config_entry.version == 2 and config_entry.minor_version < 13
        ):
            # Remove deprecated region arg for afvalstoffendienst_nl
            if new_data.get("name", "") == "afvalstoffendienst_nl":
                if "region" in new_data["args"]:
                    _LOGGER.info(
                        "Migrating afvalstoffendienst_nl source by dropping region argument"
                    )
                    del new_data["args"]["region"]
            # Migrate Cambridge City and South Cambs to Greater Cambridge Waste
            if new_data.get("name", "") == "alw_wf_de":
                _LOGGER.info("Migrating alw_wf_de to jumomind_de")
                new_data["name"] = "jumomind_de"

                new_data["args"]["service_id"] = "wol"
                # map across old args
                new_data["args"]["city"] = new_data["args"]["ort"]
                del new_data["args"]["ort"]
                new_data["args"]["street"] = new_data["args"]["strasse"]
                del new_data["args"]["strasse"]

        hass.config_entries.async_update_entry(
            config_entry,
            data=new_data,
            version=const.CONFIG_VERSION,
            minor_version=const.CONFIG_MINOR_VERSION,
        )

        _LOGGER.debug("Migration to version %s successful", config_entry.version)

    return True
