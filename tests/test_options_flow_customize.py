"""
Unit tests for the customize step of the options flow.

Note: This test file is not auto-discovered by pytest due to pytest.ini configuration
(python_files = test_source_components.py). Run it explicitly:

    pytest tests/test_options_flow_customize.py
    pytest tests/test_options_flow_customize.py -v
"""

import asyncio
import importlib.util
import os
import sys
from unittest.mock import MagicMock

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
INTEGRATION = os.path.join(REPO_ROOT, "custom_components", "waste_collection_schedule")
LIBRARY = os.path.join(INTEGRATION, "waste_collection_schedule")

# The core library and the integration share the name waste_collection_schedule.
# Home Assistant imports the library as the top level name and the integration as
# custom_components.waste_collection_schedule. Do the same here. Load the library
# by file, because putting the integration directory on sys.path would shadow the
# standard library calendar module with the integration calendar platform.
_spec = importlib.util.spec_from_file_location(
    "waste_collection_schedule",
    os.path.join(LIBRARY, "__init__.py"),
    submodule_search_locations=[LIBRARY],
)
assert _spec is not None
assert _spec.loader is not None
_library = importlib.util.module_from_spec(_spec)
sys.modules["waste_collection_schedule"] = _library
_spec.loader.exec_module(_library)

sys.path.insert(0, REPO_ROOT)

from custom_components.waste_collection_schedule.config_flow import (  # noqa: E402
    WasteCollectionOptionsFlow,
)

CUSTOMIZE = {
    "Paper": {"show": True},
    "Glass": {"show": True},
}


def _flow(customize_select):
    """Build an options flow that is already past its init step."""
    entry = MagicMock()
    entry.options = {"customize": dict(CUSTOMIZE), "sensors": []}

    flow = WasteCollectionOptionsFlow(entry)
    flow.async_create_entry = lambda data: {"type": "create_entry", "data": data}
    flow._customize_select = customize_select
    flow._customize_select_idx = 0
    flow._sensor_select = []
    flow._sensor_select_idx = 0
    flow._options = {
        "customize": {k: v for k, v in CUSTOMIZE.items() if k not in customize_select},
        "sensors": [],
    }
    return flow


def test_delete_advances_to_the_next_customization():
    flow = _flow(["Paper", "Glass"])

    # delete the first customization
    result = asyncio.run(flow.async_step_customize({"delete": True}))

    assert result["type"] == "form"
    assert result["description_placeholders"]["type"] == "Glass"
    assert flow._customize_select_idx == 1


def test_delete_of_the_last_customization_finishes_the_flow():
    flow = _flow(["Paper"])

    result = asyncio.run(flow.async_step_customize({"delete": True}))

    assert result["type"] == "create_entry"
    assert "Paper" not in result["data"]["customize"]
    assert result["data"]["customize"] == {"Glass": {"show": True}}


def test_keeping_a_customization_still_advances():
    flow = _flow(["Paper"])

    result = asyncio.run(flow.async_step_customize({"show": False}))

    assert result["type"] == "create_entry"
    assert result["data"]["customize"]["Paper"] == {"show": False}


def test_every_customization_is_visited_once():
    flow = _flow(["Paper", "Glass"])

    first = asyncio.run(flow.async_step_customize())
    assert first["description_placeholders"]["type"] == "Paper"

    second = asyncio.run(flow.async_step_customize({"delete": True}))
    assert second["description_placeholders"]["type"] == "Glass"

    last = asyncio.run(flow.async_step_customize({"show": True}))
    assert last["type"] == "create_entry"
    assert last["data"]["customize"] == {"Glass": {"show": True}}
