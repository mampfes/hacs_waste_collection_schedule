"""Dashboard resource lifecycle tests (no upstream provider traffic)."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

from custom_components.waste_collection_schedule import (
    frontend_registration as frontend,
)

requires_registration = pytest.mark.skipif(
    frontend.StaticPathConfig is None, reason="Older HA has no async static paths"
)


class Resources:
    """Use the real HA resource storage call signatures."""

    def __init__(self, items=None):
        self.items = items or []
        self.async_get_info = AsyncMock()
        self.async_create_item = AsyncMock()
        self.async_update_item = AsyncMock()
        self.async_delete_item = AsyncMock()

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
            AsyncMock(return_value=SimpleNamespace(version="3.0.0-beta.8")),
        ),
        patch.object(frontend, "add_extra_js_url") as add_js,
    ):
        yield hass, resources, add_js


@requires_registration
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
        "/waste_collection_schedule/waste-collection-cards.js?v=3.0.0-beta.8-"
    )
    add_js.assert_not_called()


@requires_registration
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


@requires_registration
def test_yaml_mode_falls_back_to_extra_module(setup_frontend):
    hass, resources, add_js = setup_frontend
    hass.data[frontend.LOVELACE_DATA].resources = None
    asyncio.run(frontend.async_register_frontend(hass))
    add_js.assert_called_once()
    assert add_js.call_args.args[1].startswith("/waste_collection_schedule/")
    resources.async_create_item.assert_not_called()
    with patch.object(frontend, "remove_extra_js_url") as remove_js:
        asyncio.run(frontend.async_unregister_frontend(hass))
    remove_js.assert_called_once_with(hass, add_js.call_args.args[1])
    assert frontend._EXTRA_URLS not in hass.data


def test_missing_frontend_does_not_break_headless_setup(setup_frontend):
    hass, _, _ = setup_frontend
    hass.config.components.clear()
    asyncio.run(frontend.async_register_frontend(hass))
    hass.http.async_register_static_paths.assert_not_awaited()
    assert not hass.data.get(frontend._REGISTERED)


@requires_registration
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

    hass = SimpleNamespace(config=SimpleNamespace(language="en"))
    with patch.object(init_yaml, "async_register_frontend", AsyncMock()) as register:
        assert asyncio.run(init_yaml.async_setup(hass, {}))
    register.assert_awaited_once_with(hass)


def test_unregister_removes_only_the_owned_resource(setup_frontend):
    hass, resources, _ = setup_frontend
    resources.items = [
        {
            "id": "owned",
            "url": "/waste_collection_schedule/waste-collection-cards.js?v=1",
            "type": "module",
        },
        {"id": "foreign", "url": "/other/card.js", "type": "module"},
    ]
    hass.data[frontend._REGISTERED] = True
    asyncio.run(frontend.async_unregister_frontend(hass))
    resources.async_delete_item.assert_awaited_once_with("owned")
    assert not hass.data.get(frontend._REGISTERED)


def test_unregister_accepts_legacy_lovelace_dictionary(caplog):
    hass = SimpleNamespace(
        data={frontend.LOVELACE_DATA: {}, frontend._REGISTERED: True}
    )
    asyncio.run(frontend.async_unregister_frontend(hass))
    assert frontend._REGISTERED not in hass.data
    assert not caplog.records


def test_unregister_removes_tracked_yaml_url_on_all_supported_versions():
    url = "/waste_collection_schedule/waste-collection-cards.js?v=test"
    manager = SimpleNamespace(remove=Mock())
    hass = SimpleNamespace(
        data={frontend.DATA_EXTRA_MODULE_URL: manager, frontend._EXTRA_URLS: {url}}
    )
    asyncio.run(frontend.async_unregister_frontend(hass))
    manager.remove.assert_called_once_with(url)
    assert frontend._EXTRA_URLS not in hass.data


def test_registration_skips_unsupported_home_assistant(setup_frontend):
    hass, resources, add_js = setup_frontend
    with patch.object(frontend, "StaticPathConfig", None):
        asyncio.run(frontend.async_register_frontend(hass))
    hass.http.async_register_static_paths.assert_not_awaited()
    resources.async_create_item.assert_not_awaited()
    add_js.assert_not_called()


def _remove_entry(hass, entries, removed):
    from custom_components.waste_collection_schedule import init_ui

    hass.config_entries = SimpleNamespace(async_entries=lambda domain: entries)
    with (
        patch.object(init_ui, "async_unregister_frontend", AsyncMock()) as drop,
        patch.object(
            init_ui,
            "cache_store",
            return_value=SimpleNamespace(async_remove=AsyncMock()),
        ) as store,
        patch(
            "homeassistant.helpers.issue_registry.async_delete_issue"
        ) as delete_issue,
    ):
        asyncio.run(init_ui.async_remove_entry(hass, removed))
        store.return_value.async_remove.assert_awaited_once()
        delete_issue.assert_called_once()
    return drop


def test_removing_last_entry_drops_the_resource():
    last = SimpleNamespace(entry_id="a")
    hass = SimpleNamespace(data={})
    _remove_entry(hass, [last], last).assert_awaited_once_with(hass)


def test_resource_stays_while_entries_or_yaml_remain():
    a, b = SimpleNamespace(entry_id="a"), SimpleNamespace(entry_id="b")
    _remove_entry(SimpleNamespace(data={}), [a, b], a).assert_not_awaited()
    yaml_hass = SimpleNamespace(data={frontend.YAML_CONFIGURED: True})
    _remove_entry(yaml_hass, [a], a).assert_not_awaited()


def test_calendar_publishes_customized_icons_for_the_cards():
    from custom_components.waste_collection_schedule.calendar import (
        WasteCollectionCalendar,
    )

    collections = [
        {"type": "Paper", "icon": None, "picture": None, "color": "#795548"},
        {
            "type": "Paper",
            "icon": "mdi:package-variant",
            "picture": None,
            "color": "#795548",
        },
        {
            "type": "Glass",
            "icon": None,
            "picture": "/local/glass.png",
            "color": "#009688",
        },
        {"type": "General", "icon": None, "picture": None, "color": "#6B6B6B"},
    ]
    aggregator = SimpleNamespace(
        get_upcoming=lambda **kwargs: [
            SimpleNamespace(
                **c, waste_type=SimpleNamespace(id=c["type"], names={"en": c["type"]})
            )
            for c in collections
        ]
    )
    calendar = WasteCollectionCalendar(aggregator, "Waste", "uid")
    assert calendar.extra_state_attributes == {
        "waste_types": {
            "Paper": {"icon": "mdi:package-variant", "color": "#795548"},
            "Glass": {"picture": "/local/glass.png", "color": "#009688"},
            "General": {"color": "#6B6B6B"},
        }
    }
    assert "waste_types" in calendar._unrecorded_attributes


def test_release_collection_attributes_use_calendar_alias_filters():
    from datetime import date

    from custom_components.waste_collection_schedule.calendar import (
        WasteCollectionCalendar,
    )
    from custom_components.waste_collection_schedule.waste_collection_schedule.collection import (
        Collection,
    )
    from custom_components.waste_collection_schedule.waste_collection_schedule.waste_types import (
        GLASS,
        PAPER,
    )

    paper = Collection(date.today(), PAPER)
    paper.set_icon("mdi:package-variant")
    paper.set_picture("/local/paper.png")
    glass = Collection(date.today(), GLASS)
    records = [paper, glass]

    def upcoming(**kwargs):
        included = kwargs.get("include_types")
        return [c for c in records if included is None or c.waste_type.id in included]

    calendar = WasteCollectionCalendar(
        SimpleNamespace(get_upcoming=upcoming),
        "Waste",
        "uid",
        include_types={paper.type},
    )
    assert calendar.extra_state_attributes == {
        "waste_types": {
            paper.type: {
                "icon": "mdi:package-variant",
                "picture": "/local/paper.png",
                "color": paper.color,
            }
        }
    }


def test_calendar_publishes_collection_color_with_customize_precedence():
    from datetime import date

    from custom_components.waste_collection_schedule.calendar import (
        WasteCollectionCalendar,
    )
    from custom_components.waste_collection_schedule.waste_collection_schedule.collection import (
        Collection,
    )
    from custom_components.waste_collection_schedule.waste_collection_schedule.waste_types import (
        PAPER,
    )

    paper = Collection(date.today(), PAPER, color="#abcdef")
    paper.set_color("#112233", source="customize")
    calendar = WasteCollectionCalendar(
        SimpleNamespace(get_upcoming=lambda **kwargs: [paper]),
        "Waste",
        "uid",
    )
    assert calendar.extra_state_attributes == {
        "waste_types": {paper.type: {"icon": paper.icon, "color": "#112233"}}
    }


def test_registration_imports_share_the_module_and_keep_asset_directory():
    from custom_components.waste_collection_schedule import init_ui, init_yaml

    assert init_ui.async_register_frontend is frontend.async_register_frontend
    assert init_yaml.async_register_frontend is frontend.async_register_frontend
    assert init_ui.async_unregister_frontend is frontend.async_unregister_frontend
    assert frontend.FRONTEND_PATH.name == "frontend"
    assert (frontend.FRONTEND_PATH / "waste-collection-cards.js").is_file()
