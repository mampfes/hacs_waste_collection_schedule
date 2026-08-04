"""Tests for tools/loc_report.py's pipeline-source detection.

The interesting case is a source whose base class is *another source*. Matching
the literal text ``class Source(BaseSource)`` counted those as legacy, which
understated the migration by three sources; following the base class instead has
to keep excluding the seven whose parent is itself legacy.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from loc_report import is_pipeline_source

BASE = "from waste_collection_schedule.base_source import BaseSource\n"


def test_direct_subclass_is_pipeline():
    text = BASE + "class Source(BaseSource):\n    pass\n"
    assert is_pipeline_source(text, {})


def test_plain_class_is_legacy():
    assert not is_pipeline_source("class Source:\n    def fetch(self): ...\n", {})


def test_no_source_class_at_all():
    assert not is_pipeline_source("PARAMS = []\n", {})


def test_subclass_of_a_pipeline_source_is_pipeline():
    """offenbach_de -> insert_it_de, rh_entsorgung_de -> jumomind_de."""
    parent = BASE + "class Source(BaseSource):\n    pass\n"
    child = (
        "from waste_collection_schedule.source.parent_mod import Source as ParentSource\n"
        "class Source(ParentSource):\n    pass\n"
    )
    assert is_pipeline_source(child, {"parent_mod": parent})


def test_subclass_of_a_legacy_source_is_legacy():
    """chiltern_gov_uk -> iapp_itouchvision_com, and five more like it."""
    parent = "class Source:\n    def fetch(self): ...\n"
    child = (
        "from waste_collection_schedule.source.parent_mod import Source as ParentSource\n"
        "class Source(ParentSource):\n    pass\n"
    )
    assert not is_pipeline_source(child, {"parent_mod": parent})


def test_relative_import_is_followed():
    """ssam_se and uppsalavatten_se import their base as ``from .edpevent_se``."""
    parent = BASE + "class Source(BaseSource):\n    pass\n"
    child = (
        "from .parent_mod import Source as ParentSource\n"
        "class Source(ParentSource):\n    pass\n"
    )
    assert is_pipeline_source(child, {"parent_mod": parent})


def test_parenthesised_import_is_followed():
    """Several of these imports are wrapped by the formatter."""
    parent = BASE + "class Source(BaseSource):\n    pass\n"
    child = (
        "from waste_collection_schedule.source.parent_mod import (\n"
        "    Source as ParentSource,\n"
        ")\n"
        "class Source(ParentSource):\n    pass\n"
    )
    assert is_pipeline_source(child, {"parent_mod": parent})


def test_base_from_a_service_module_is_not_followed():
    """mils_tirol_at subclasses RiSKommunalSource, which is a plain class."""
    child = (
        "from waste_collection_schedule.service.RiSKommunalAT import RiSKommunalSource\n"
        "class Source(RiSKommunalSource):\n    pass\n"
    )
    assert not is_pipeline_source(child, {})


def test_a_cycle_terminates():
    a = (
        "from waste_collection_schedule.source.b import Source as BSource\n"
        "class Source(BSource):\n    pass\n"
    )
    b = (
        "from waste_collection_schedule.source.a import Source as ASource\n"
        "class Source(ASource):\n    pass\n"
    )
    assert not is_pipeline_source(a, {"a": a, "b": b})


def test_missing_parent_module_is_not_pipeline():
    child = (
        "from waste_collection_schedule.source.gone import Source as GoneSource\n"
        "class Source(GoneSource):\n    pass\n"
    )
    assert not is_pipeline_source(child, {})


@pytest.mark.parametrize(
    "stem",
    ["offenbach_de", "rh_entsorgung_de", "stadt_kerpen_de"],
)
def test_the_three_real_indirect_pipeline_sources(stem):
    """These are the sources the literal marker missed, checked against the tree."""
    source_dir = (
        Path(__file__).resolve().parent.parent
        / "custom_components/waste_collection_schedule/waste_collection_schedule/source"
    )
    texts = {p.stem: p.read_text(encoding="utf-8") for p in source_dir.glob("*.py")}
    assert "class Source(BaseSource)" not in texts[stem], (
        f"{stem} now subclasses BaseSource directly, so it no longer exercises "
        "the indirect case this test exists for"
    )
    assert is_pipeline_source(texts[stem], texts)
