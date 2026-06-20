"""Tests for the BaseSource doc generator (doc_generator.render_source_doc).

New-architecture (BaseSource) sources derive their doc/source/<id>.md from
class metadata. These tests assert the generated markdown contains the
expected structural pieces (title, URL, each PARAMS field, an example block,
and the HOWTO text where present). They do NOT require a byte-identical match
to the hand-written files, because the prose around the structure varies.
"""

import calendar  # noqa: E402, F401, I001 — stdlib calendar must be imported FIRST
import importlib
import os
import sys

import pytest

# Ensure the inner package path is importable. As in tests/test_new_architecture.py,
# stdlib `calendar` is imported above BEFORE this path is added, because HA's
# calendar.py on this path would otherwise shadow the stdlib module.
sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__),
        "../custom_components/waste_collection_schedule",
    ),
)

# doc_generator lives at the repo root (next to update_docu_links.py).
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from doc_generator import render_source_doc  # noqa: E402


def _load_source(source_id: str):
    module = importlib.import_module(f"waste_collection_schedule.source.{source_id}")
    return module.Source


# (source_id, expects_howto)
_CONVERTED_SOURCES = [
    ("launceston_tas_gov_au", True),
    ("koppl_at", False),
    ("newcastle_nsw_gov_au", True),
    ("reading_gov_uk", False),
]


@pytest.mark.parametrize("source_id,expects_howto", _CONVERTED_SOURCES)
def test_render_contains_title_and_url(source_id, expects_howto):
    source_cls = _load_source(source_id)
    doc = render_source_doc(source_id, source_cls)

    assert doc.startswith(f"# {source_cls.TITLE}\n")
    assert source_cls.URL in doc


@pytest.mark.parametrize("source_id,expects_howto", _CONVERTED_SOURCES)
def test_render_contains_config_block(source_id, expects_howto):
    source_cls = _load_source(source_id)
    doc = render_source_doc(source_id, source_cls)

    assert "## Configuration via configuration.yaml" in doc
    assert f"- name: {source_id}" in doc


@pytest.mark.parametrize("source_id,expects_howto", _CONVERTED_SOURCES)
def test_render_contains_each_param_field(source_id, expects_howto):
    source_cls = _load_source(source_id)
    doc = render_source_doc(source_id, source_cls)

    assert "### Configuration Variables" in doc

    field_names = [
        field_name for param in source_cls.PARAMS for field_name in param.fields
    ]
    if field_names:
        for field_name in field_names:
            # Each field appears as a bold entry with a type/requirement line.
            assert f"**{field_name}**" in doc
            assert field_name.upper() in doc  # placeholder in the config block
    else:
        assert "No configuration arguments are required." in doc


@pytest.mark.parametrize("source_id,expects_howto", _CONVERTED_SOURCES)
def test_render_contains_example_block(source_id, expects_howto):
    source_cls = _load_source(source_id)
    doc = render_source_doc(source_id, source_cls)

    assert "## Example" in doc
    # The example must contain a fenced yaml block naming the source.
    example = doc.split("## Example", 1)[1]
    assert "```yaml" in example
    assert f"- name: {source_id}" in example


@pytest.mark.parametrize("source_id,expects_howto", _CONVERTED_SOURCES)
def test_render_howto_section_presence(source_id, expects_howto):
    source_cls = _load_source(source_id)
    doc = render_source_doc(source_id, source_cls)

    if expects_howto:
        assert "## How to get the source arguments" in doc
        howto_text = source_cls.HOWTO.get("en") or next(iter(source_cls.HOWTO.values()))
        # A distinctive fragment of the howto text should be present.
        assert howto_text.strip()[:20] in doc
    else:
        # Sources without a HOWTO must NOT emit the howto section.
        if not source_cls.HOWTO:
            assert "## How to get the source arguments" not in doc


def test_render_required_param_marked_required():
    """A required param renders as ``(required)``; the bold field name appears."""
    source_cls = _load_source("kwinana_wa_gov_au")
    doc = render_source_doc("kwinana_wa_gov_au", source_cls)
    assert "**address**" in doc
    assert "(required)" in doc


def test_render_no_args_block_when_no_params():
    """A source with empty PARAMS omits the ``args:`` block entirely."""
    source_cls = _load_source("koppl_at")
    doc = render_source_doc("koppl_at", source_cls)
    assert "args:" not in doc
    assert "No configuration arguments are required." in doc
