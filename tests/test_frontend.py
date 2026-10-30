"""Dashboard resource lifecycle tests (no upstream provider traffic)."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from custom_components.waste_collection_schedule import frontend

pytestmark = pytest.mark.skipif(
    frontend.StaticPathConfig is None, reason="Older HA has no async static paths"
)


class Resources:
    """Use the real HA resource storage call signatures."""

    def __init__(self, items=None):
        self.items = items or []
        self.async_get_info = AsyncMock()
        self.async_create_item = AsyncMock()
        self.async_update_item = AsyncMock()

    def async_items(self):
        return self.items


@pytest.fixture
def setup_frontend():
    """Keep HA lifecycle dependencies at the HTTP/resource boundary."""
    resources = Resources()
    hass = SimpleNamespace(
        data={frontend.LOVELACE_DATA: SimpleNamespace(resources=resources)},
        config=SimpleNamespace(components={"http", "frontend", "lovelace"}),
        http=SimpleNamespace(async_register_static_paths=AsyncMock()),
        async_add_executor_job=AsyncMock(side_effect=lambda func, *args: func(*args)),
    )
    with (
        patch.object(frontend, "ResourceStorageCollection", Resources),
        patch.object(
            frontend,
            "async_get_integration",
            AsyncMock(return_value=SimpleNamespace(version="2.36.0")),
        ),
        patch.object(frontend, "add_extra_js_url") as add_js,
    ):
        yield hass, resources, add_js


def test_registration_is_idempotent(setup_frontend):
    hass, resources, add_js = setup_frontend

    async def run():
        await frontend.async_register_frontend(hass)
        await frontend.async_register_frontend(hass)

    asyncio.run(run())
    hass.http.async_register_static_paths.assert_awaited_once()
    config = hass.http.async_register_static_paths.await_args.args[0][0]
    assert config.cache_headers is False
    resources.async_get_info.assert_awaited_once()
    resources.async_create_item.assert_awaited_once()
    data = resources.async_create_item.await_args.args[0]
    assert data["res_type"] == "module"
    assert data["url"].startswith(
        "/waste_collection_schedule/waste-collection-cards.js?v=2.36.0-"
    )
    add_js.assert_not_called()


def test_rebuild_updates_owned_resource_only(setup_frontend):
    hass, resources, _ = setup_frontend
    resources.items = [
        {
            "id": "owned",
            "url": "/waste_collection_schedule/waste-collection-cards.js?v=old",
            "type": "module",
        },
        {"id": "foreign", "url": "/other/card.js", "type": "module"},
    ]
    asyncio.run(frontend.async_register_frontend(hass))
    resources.async_create_item.assert_not_called()
    resources.async_update_item.assert_awaited_once()
    assert resources.async_update_item.await_args.args[0] == "owned"


def test_yaml_mode_falls_back_to_extra_module(setup_frontend):
    hass, resources, add_js = setup_frontend
    hass.data[frontend.LOVELACE_DATA].resources = None
    asyncio.run(frontend.async_register_frontend(hass))
    add_js.assert_called_once()
    assert add_js.call_args.args[1].startswith("/waste_collection_schedule/")
    resources.async_create_item.assert_not_called()


def test_missing_frontend_does_not_break_headless_setup(setup_frontend):
    hass, _, _ = setup_frontend
    hass.config.components.clear()
    asyncio.run(frontend.async_register_frontend(hass))
    hass.http.async_register_static_paths.assert_not_awaited()
    assert not hass.data.get(frontend._REGISTERED)


def test_resource_failure_can_retry_without_duplicate_static_paths(setup_frontend):
    hass, resources, _ = setup_frontend
    resources.async_get_info.side_effect = [RuntimeError("storage unavailable"), None]

    async def run():
        await frontend.async_register_frontend(hass)
        assert not hass.data.get(frontend._REGISTERED)
        await frontend.async_register_frontend(hass)

    asyncio.run(run())
    hass.http.async_register_static_paths.assert_awaited_once()
    assert hass.data[frontend._REGISTERED]


def test_ui_and_yaml_both_register_cards_before_yaml_branch():
    from custom_components.waste_collection_schedule import init_yaml

    hass = SimpleNamespace()
    with patch.object(init_yaml, "async_register_frontend", AsyncMock()) as register:
        assert asyncio.run(init_yaml.async_setup(hass, {}))
    register.assert_awaited_once_with(hass)
