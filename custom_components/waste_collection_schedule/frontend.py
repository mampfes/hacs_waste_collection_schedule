# Copyright (c) 2026 Ruaan Deysel

"""Serve the Lovelace dashboard card bundles from the integration."""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Final

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.lovelace.resources import ResourceStorageCollection
from homeassistant.loader import async_get_integration

# Cards use the asynchronous static-path API introduced after the integration's
# minimum supported HA release. Older, headless installs keep their schedules.
try:
    from homeassistant.components.http import StaticPathConfig
    from homeassistant.components.lovelace.const import LOVELACE_DATA
except ImportError:
    StaticPathConfig = None  # type: ignore[assignment,misc]
    LOVELACE_DATA = "lovelace"

from .const import DOMAIN

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

FRONTEND_URL_BASE: Final = f"/{DOMAIN}"
FRONTEND_PATH: Final = Path(__file__).parent / "frontend"
CARD_FILES: Final = ("waste-collection-cards.js",)
_REGISTERED: str = f"{DOMAIN}_frontend_registered"
_STATIC_REGISTERED: str = f"{DOMAIN}_frontend_static_registered"


def _bundle_digest(path: Path) -> str:
    """Short content hash of one bundle, so rebuilds bust caches too."""
    return hashlib.sha256(path.read_bytes()).hexdigest()[:8]


async def async_register_frontend(hass: HomeAssistant) -> None:
    """Serve the optional cards once, with a content hash for cache updates.

    Storage dashboards get a managed module resource before card creation.
    YAML dashboards use an extra JS URL. Static paths live until HA restarts.
    """
    if StaticPathConfig is None:
        _LOGGER.debug("Dashboard cards need a newer Home Assistant frontend")
        return
    if hass.data.get(_REGISTERED):
        return
    if not {"http", "frontend"} <= hass.config.components:
        _LOGGER.debug("http/frontend not loaded; dashboard bundles not registered")
        return
    try:
        integration = await async_get_integration(hass, DOMAIN)
        if not hass.data.get(_STATIC_REGISTERED):
            await hass.http.async_register_static_paths(
                [
                    StaticPathConfig(
                        FRONTEND_URL_BASE, str(FRONTEND_PATH), cache_headers=False
                    )
                ]
            )
            hass.data[_STATIC_REGISTERED] = True

        urls: dict[str, str] = {}
        for filename in CARD_FILES:
            path = FRONTEND_PATH / filename
            digest = await hass.async_add_executor_job(_bundle_digest, path)
            url = f"{FRONTEND_URL_BASE}/{filename}"
            urls[url] = f"{url}?v={integration.version}-{digest}"

        lovelace = hass.data.get(LOVELACE_DATA)
        resources = lovelace.resources if lovelace is not None else None
        if isinstance(resources, ResourceStorageCollection):
            await resources.async_get_info()  # Load before inspecting items.
            existing_by_url = {
                item["url"].partition("?")[0]: item for item in resources.async_items()
            }
            for base_url, versioned_url in urls.items():
                existing = existing_by_url.get(base_url)
                if existing is None:
                    await resources.async_create_item(
                        {"url": versioned_url, "res_type": "module"}
                    )
                elif existing["url"] != versioned_url or existing["type"] != "module":
                    await resources.async_update_item(
                        existing["id"], {"url": versioned_url, "res_type": "module"}
                    )
        else:
            for url in urls.values():
                add_extra_js_url(hass, url)
    except Exception:
        _LOGGER.exception("Unable to register optional dashboard card frontend")
    else:
        hass.data[_REGISTERED] = True
