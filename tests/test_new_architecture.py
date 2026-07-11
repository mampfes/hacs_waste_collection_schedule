"""Tests for the new source architecture.

Validates every step of the pipeline from configuration through to
collection record creation and customisation:

1. Core types: WasteType, Collection, LegacyCollection, CollectionGroup
2. Pipeline steps: retrievers, parsers, date_parsers
3. Configuration: ConfigParam declarations
4. Pipeline orchestration: BaseSource fetch → retrieve → parse → classify
5. Customisation: source_shell filter/customize/day_offset
6. Source validation: auto-discover new-style sources, run TEST_CASES
"""

import calendar  # noqa: F401 — must import stdlib calendar FIRST
import datetime
import os
import sys
from dataclasses import FrozenInstanceError
from typing import ClassVar
from unittest.mock import MagicMock, patch

import pytest

# Ensure source path is available.
# IMPORTANT: stdlib calendar must be imported ABOVE before this path is added,
# because HA's calendar.py in this path shadows the stdlib calendar module.
sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__),
        "../custom_components/waste_collection_schedule",
    ),
)


# =====================================================================
# 1. Core types
# =====================================================================


class TestWasteType:
    """WasteType is a frozen dataclass with id, icon, color, names."""

    def test_attributes(self):
        from waste_collection_schedule.waste_types import GENERAL_WASTE

        assert GENERAL_WASTE.id == "general_waste"
        assert GENERAL_WASTE.icon == "mdi:trash-can"
        assert GENERAL_WASTE.color == "#6B6B6B"
        assert GENERAL_WASTE.names["en"] == "General Waste"
        assert "de" in GENERAL_WASTE.names

    def test_frozen(self):
        from waste_collection_schedule.waste_types import GENERAL_WASTE

        with pytest.raises(FrozenInstanceError):
            GENERAL_WASTE.id = "something_else"

    def test_all_types_have_required_fields(self):
        from waste_collection_schedule.waste_types import ALL_TYPES

        for wt in ALL_TYPES:
            assert wt.id, "WasteType missing id"
            assert wt.icon, f"{wt.id} missing icon"
            assert wt.color, f"{wt.id} missing color"
            assert "en" in wt.names, f"{wt.id} missing English name"

    def test_all_ids_unique(self):
        from waste_collection_schedule.waste_types import ALL_TYPES

        ids = [wt.id for wt in ALL_TYPES]
        assert len(ids) == len(set(ids)), "Duplicate WasteType ids"


class TestWasteTypeResolution:
    """resolve() recognises labels across languages; unknowns are preserved."""

    def test_resolve_across_languages(self):
        from waste_collection_schedule import waste_types as wt

        cases = {
            "Restmüll": "general_waste",  # de display name
            "Restabfall": "general_waste",  # de alias
            "Ordures ménagères": "general_waste",  # fr name
            "Wertstofftonne": "recyclables",  # de alias
            "Gelber Sack": "recyclables",
            "Bioabfall": "organic",
            "Blaue Tonne": "paper",
            "Altglas": "glass",
            "Vetro": "glass",  # it name
            "Sperrmüll": "bulky_waste",
            "Problemstoff": "hazardous",
            "Weiße Ware": "electronics",
            "Grünschnitt": "garden_waste",
            "Déchets verts": "garden_waste",  # fr alias
        }
        for label, expected_id in cases.items():
            resolved = wt.resolve(label)
            assert resolved is not None, f"{label!r} should resolve"
            assert resolved.id == expected_id, f"{label!r} -> {resolved.id}"

    def test_resolve_is_case_and_whitespace_insensitive(self):
        from waste_collection_schedule import waste_types as wt

        assert wt.resolve("  RESTMÜLL  ") is wt.GENERAL_WASTE

    def test_resolve_unknown_returns_none(self):
        from waste_collection_schedule import waste_types as wt

        assert wt.resolve("Frobnitz-Tonne") is None

    def test_preserved_keeps_label_in_every_locale(self):
        from waste_collection_schedule import waste_types as wt

        p = wt.preserved("Frobnitz-Tonne")
        assert p.id == "preserved:frobnitz-tonne"
        assert p.names["en"] == p.names["de"] == "Frobnitz-Tonne"
        assert p.icon == wt.OTHER.icon  # borrows OTHER's icon/colour

    def test_other_is_not_resolvable(self):
        # OTHER is an explicit sink, not part of the recognised vocabulary.
        from waste_collection_schedule import waste_types as wt

        assert wt.resolve("Other") is not wt.OTHER


class TestCollection:
    """Collection(date, waste_type) — new-style primary interface."""

    def test_new_style_creation(self):
        from waste_collection_schedule.collection import Collection
        from waste_collection_schedule.waste_types import RECYCLABLES

        c = Collection(date=datetime.date(2026, 4, 10), waste_type=RECYCLABLES)
        assert c.date == datetime.date(2026, 4, 10)
        assert c.waste_type is RECYCLABLES
        assert c.type == "Recycling"
        assert c.icon == "mdi:recycle"
        assert c.picture is None

    def test_type_derives_from_waste_type(self):
        from waste_collection_schedule.collection import Collection
        from waste_collection_schedule.waste_types import ORGANIC

        c = Collection(date=datetime.date(2026, 1, 1), waste_type=ORGANIC)
        assert c.type == ORGANIC.names["en"]
        assert c.icon == ORGANIC.icon

    def test_set_type_overrides(self):
        from waste_collection_schedule.collection import Collection
        from waste_collection_schedule.waste_types import GENERAL_WASTE

        c = Collection(date=datetime.date(2026, 1, 1), waste_type=GENERAL_WASTE)
        c.set_type("Custom Name")
        assert c.type == "Custom Name"
        # icon unchanged
        assert c.icon == GENERAL_WASTE.icon

    def test_set_icon_overrides(self):
        from waste_collection_schedule.collection import Collection
        from waste_collection_schedule.waste_types import GENERAL_WASTE

        c = Collection(date=datetime.date(2026, 1, 1), waste_type=GENERAL_WASTE)
        c.set_icon("mdi:custom")
        assert c.icon == "mdi:custom"
        # type unchanged
        assert c.type == "General Waste"

    def test_set_picture(self):
        from waste_collection_schedule.collection import Collection
        from waste_collection_schedule.waste_types import GENERAL_WASTE

        c = Collection(date=datetime.date(2026, 1, 1), waste_type=GENERAL_WASTE)
        assert c.picture is None
        c.set_picture("https://example.com/pic.png")
        assert c.picture == "https://example.com/pic.png"

    def test_set_date(self):
        from waste_collection_schedule.collection import Collection
        from waste_collection_schedule.waste_types import GENERAL_WASTE

        c = Collection(date=datetime.date(2026, 1, 1), waste_type=GENERAL_WASTE)
        c.set_date(datetime.date(2026, 6, 15))
        assert c.date == datetime.date(2026, 6, 15)

    def test_as_dict(self):
        from waste_collection_schedule.collection import Collection
        from waste_collection_schedule.waste_types import PAPER

        c = Collection(date=datetime.date(2026, 3, 20), waste_type=PAPER)
        d = c.as_dict()
        assert d["date"] == "2026-03-20"
        assert d["type"] == "Paper & Cardboard"
        assert d["icon"] == "mdi:package-variant"
        assert d["picture"] is None

    def test_equality_and_hash(self):
        from waste_collection_schedule.collection import Collection
        from waste_collection_schedule.waste_types import GLASS

        a = Collection(date=datetime.date(2026, 1, 1), waste_type=GLASS)
        b = Collection(date=datetime.date(2026, 1, 1), waste_type=GLASS)
        assert a == b
        assert hash(a) == hash(b)

    def test_inequality(self):
        from waste_collection_schedule.collection import Collection
        from waste_collection_schedule.waste_types import GLASS, PAPER

        a = Collection(date=datetime.date(2026, 1, 1), waste_type=GLASS)
        b = Collection(date=datetime.date(2026, 1, 1), waste_type=PAPER)
        assert a != b

    def test_days_to(self):
        from waste_collection_schedule.collection import Collection
        from waste_collection_schedule.waste_types import GENERAL_WASTE

        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        c = Collection(date=tomorrow, waste_type=GENERAL_WASTE)
        assert c.daysTo == 1

    def test_location_and_description(self):
        from waste_collection_schedule.collection import Collection
        from waste_collection_schedule.waste_types import GENERAL_WASTE

        c = Collection(date=datetime.date(2026, 1, 1), waste_type=GENERAL_WASTE)
        assert c.location is None
        assert c.description is None
        c.set_location("Zone A")
        c.set_description("Fortnightly")
        assert c.location == "Zone A"
        assert c.description == "Fortnightly"

    def test_location_in_as_dict(self):
        from waste_collection_schedule.collection import Collection
        from waste_collection_schedule.waste_types import GENERAL_WASTE

        c = Collection(date=datetime.date(2026, 1, 1), waste_type=GENERAL_WASTE)
        assert "location" not in c.as_dict()
        c.set_location("Block 3")
        assert c.as_dict()["location"] == "Block 3"

    def test_set_location_strips_whitespace(self):
        from waste_collection_schedule.collection import Collection
        from waste_collection_schedule.waste_types import GENERAL_WASTE

        c = Collection(date=datetime.date(2026, 1, 1), waste_type=GENERAL_WASTE)
        c.set_location("  Zone B  ")
        assert c.location == "Zone B"

    def test_set_location_none_clears(self):
        from waste_collection_schedule.collection import Collection
        from waste_collection_schedule.waste_types import GENERAL_WASTE

        c = Collection(date=datetime.date(2026, 1, 1), waste_type=GENERAL_WASTE)
        c.set_location("Zone A")
        c.set_location(None)
        assert c.location is None


class TestLegacyCollection:
    """LegacyCollection — adapter for old-style sources using t= and icon=."""

    def test_creation(self):
        from waste_collection_schedule.collection import LegacyCollection

        c = LegacyCollection(
            date=datetime.date(2026, 4, 10), t="Refuse", icon="mdi:trash-can"
        )
        assert c.type == "Refuse"
        assert c.icon == "mdi:trash-can"
        assert c.date == datetime.date(2026, 4, 10)

    def test_is_subclass_of_collection(self):
        from waste_collection_schedule.collection import Collection, LegacyCollection

        c = LegacyCollection(date=datetime.date(2026, 1, 1), t="Test")
        assert isinstance(c, Collection)

    def test_default_icon_from_other(self):
        from waste_collection_schedule.collection import LegacyCollection
        from waste_collection_schedule.waste_types import OTHER

        c = LegacyCollection(date=datetime.date(2026, 1, 1), t="Mystery Bin")
        assert c.icon == OTHER.icon

    def test_with_picture(self):
        from waste_collection_schedule.collection import LegacyCollection

        c = LegacyCollection(
            date=datetime.date(2026, 1, 1),
            t="Test",
            picture="https://example.com/bin.jpg",
        )
        assert c.picture == "https://example.com/bin.jpg"

    def test_ad_hoc_waste_type(self):
        from waste_collection_schedule.collection import LegacyCollection

        c = LegacyCollection(date=datetime.date(2026, 1, 1), t="Refuse")
        assert c.waste_type.id == "legacy_Refuse"
        assert c.waste_type.names["en"] == "Refuse"

    def test_location_and_description(self):
        from waste_collection_schedule.collection import LegacyCollection

        c = LegacyCollection(
            date=datetime.date(2026, 1, 1),
            t="Refuse",
            location="Bin bay 2",
            description="Every other week",
        )
        assert c.location == "Bin bay 2"
        assert c.description == "Every other week"
        assert c.as_dict()["location"] == "Bin bay 2"


class TestCollectionFactory:
    """The factory exported as Collection from __init__.py."""

    def test_new_style_dispatch(self):
        from waste_collection_schedule import Collection
        from waste_collection_schedule.collection import Collection as RealCollection
        from waste_collection_schedule.waste_types import GENERAL_WASTE

        c = Collection(date=datetime.date(2026, 1, 1), waste_type=GENERAL_WASTE)
        assert isinstance(c, RealCollection)
        assert c.type == "General Waste"

    def test_legacy_dispatch(self):
        from waste_collection_schedule import Collection
        from waste_collection_schedule.collection import Collection as RealCollection
        from waste_collection_schedule.collection import (
            LegacyCollection,
        )

        c = Collection(date=datetime.date(2026, 1, 1), t="Refuse", icon="mdi:trash-can")
        assert isinstance(c, LegacyCollection)
        assert isinstance(c, RealCollection)

    def test_error_without_type_or_waste_type(self):
        from waste_collection_schedule import Collection

        with pytest.raises(ValueError, match="waste_type or t"):
            Collection(date=datetime.date(2026, 1, 1))

    def test_isinstance_check(self):
        from waste_collection_schedule import Collection
        from waste_collection_schedule.collection import Collection as RealCollection
        from waste_collection_schedule.waste_types import GENERAL_WASTE

        c = Collection(date=datetime.date(2026, 1, 1), waste_type=GENERAL_WASTE)
        # The factory's __instancecheck__ should work
        assert isinstance(c, RealCollection)


class TestCollectionGroup:
    """CollectionGroup — groups collections on the same date."""

    def test_single_collection(self):
        from waste_collection_schedule.collection import Collection, CollectionGroup
        from waste_collection_schedule.waste_types import GENERAL_WASTE

        c = Collection(date=datetime.date(2026, 1, 1), waste_type=GENERAL_WASTE)
        g = CollectionGroup.create([c])
        assert g.date == datetime.date(2026, 1, 1)
        assert g.types == ["General Waste"]
        assert g.icon == "mdi:trash-can"

    def test_multiple_collections(self):
        from waste_collection_schedule.collection import Collection, CollectionGroup
        from waste_collection_schedule.waste_types import GENERAL_WASTE, RECYCLABLES

        collections = [
            Collection(date=datetime.date(2026, 1, 1), waste_type=GENERAL_WASTE),
            Collection(date=datetime.date(2026, 1, 1), waste_type=RECYCLABLES),
        ]
        g = CollectionGroup.create(collections)
        assert g.types == ["General Waste", "Recycling"]
        assert g.icon == "mdi:numeric-2-box-multiple"
        assert g.picture is None

    def test_mixed_new_and_legacy(self):
        from waste_collection_schedule.collection import (
            Collection,
            CollectionGroup,
            LegacyCollection,
        )
        from waste_collection_schedule.waste_types import GENERAL_WASTE

        collections = [
            Collection(date=datetime.date(2026, 1, 1), waste_type=GENERAL_WASTE),
            LegacyCollection(date=datetime.date(2026, 1, 1), t="Bulky Waste"),
        ]
        g = CollectionGroup.create(collections)
        assert len(g.types) == 2
        assert "General Waste" in g.types
        assert "Bulky Waste" in g.types

    def test_location_aggregation(self):
        from waste_collection_schedule.collection import Collection, CollectionGroup
        from waste_collection_schedule.waste_types import GENERAL_WASTE, RECYCLABLES

        c1 = Collection(date=datetime.date(2026, 1, 1), waste_type=GENERAL_WASTE)
        c1.set_location("Zone A")
        c2 = Collection(date=datetime.date(2026, 1, 1), waste_type=RECYCLABLES)
        c2.set_location("Zone B")
        g = CollectionGroup.create([c1, c2])
        assert g.locations == ["Zone A", "Zone B"]
        assert g.location == "Zone A, Zone B"
        assert g.as_dict()["location"] == "Zone A, Zone B"

    def test_location_deduplication(self):
        from waste_collection_schedule.collection import Collection, CollectionGroup
        from waste_collection_schedule.waste_types import GENERAL_WASTE, RECYCLABLES

        c1 = Collection(date=datetime.date(2026, 1, 1), waste_type=GENERAL_WASTE)
        c1.set_location("Zone A")
        c2 = Collection(date=datetime.date(2026, 1, 1), waste_type=RECYCLABLES)
        c2.set_location("Zone A")
        g = CollectionGroup.create([c1, c2])
        assert g.locations == ["Zone A"]

    def test_no_location_omitted_from_as_dict(self):
        from waste_collection_schedule.collection import Collection, CollectionGroup
        from waste_collection_schedule.waste_types import GENERAL_WASTE

        c = Collection(date=datetime.date(2026, 1, 1), waste_type=GENERAL_WASTE)
        g = CollectionGroup.create([c])
        assert "location" not in g.as_dict()
        assert g.locations is None


# =====================================================================
# 2. Pipeline steps
# =====================================================================


class TestDateParsers:
    """date_parsers.auto and date_parsers.for_format."""

    def test_auto_iso(self):
        from waste_collection_schedule.date_parsers import auto

        assert auto(None, "2026-04-10") == datetime.date(2026, 4, 10)

    def test_auto_verbose(self):
        from waste_collection_schedule.date_parsers import auto

        assert auto(None, "10 April 2026") == datetime.date(2026, 4, 10)

    def test_auto_strips_whitespace(self):
        from waste_collection_schedule.date_parsers import auto

        assert auto(None, "  2026-04-10  ") == datetime.date(2026, 4, 10)

    def test_for_format(self):
        from waste_collection_schedule.date_parsers import for_format

        parser = for_format("%d/%m/%Y")
        assert parser(None, "10/04/2026") == datetime.date(2026, 4, 10)

    def test_for_format_strips(self):
        from waste_collection_schedule.date_parsers import for_format

        parser = for_format("%Y-%m-%d")
        assert parser(None, "  2026-04-10  ") == datetime.date(2026, 4, 10)

    def test_for_format_wrong_format_raises(self):
        from waste_collection_schedule.date_parsers import for_format

        parser = for_format("%d/%m/%Y")
        with pytest.raises(ValueError):
            parser(None, "2026-04-10")  # ISO format, not dd/mm/yyyy

    def test_next_weekday_bare_name_rolls_to_next_occurrence(self):
        from waste_collection_schedule.date_parsers import next_weekday

        # 2026-06-15 is a Monday; "Friday" should resolve to that same week.
        parser = next_weekday(on_or_after=datetime.date(2026, 6, 15))
        assert parser("Friday") == datetime.date(2026, 6, 19)

    def test_next_weekday_bare_name_on_the_day_itself(self):
        from waste_collection_schedule.date_parsers import next_weekday

        parser = next_weekday(on_or_after=datetime.date(2026, 6, 15))  # a Monday
        assert parser("Monday") == datetime.date(2026, 6, 15)

    def test_next_weekday_unrecognised_name_raises(self):
        from waste_collection_schedule.date_parsers import next_weekday

        parser = next_weekday(on_or_after=datetime.date(2026, 6, 15))
        with pytest.raises(ValueError):
            parser("Notaday")

    def test_next_weekday_day_month_same_year(self):
        from waste_collection_schedule.date_parsers import next_weekday

        parser = next_weekday("%A %d %B", on_or_after=datetime.date(2026, 7, 1))
        assert parser("Friday 10 July") == datetime.date(2026, 7, 10)

    def test_next_weekday_day_month_rolls_to_next_year(self):
        from waste_collection_schedule.date_parsers import next_weekday

        # "10 January" on/after 1 July should resolve to next year, not a past date.
        parser = next_weekday("%d %B", on_or_after=datetime.date(2026, 7, 1))
        assert parser("10 January") == datetime.date(2027, 1, 10)

    def test_next_weekday_rejects_fmt_with_year(self):
        from waste_collection_schedule.date_parsers import next_weekday

        with pytest.raises(ValueError):
            next_weekday("%Y-%m-%d")


class TestParsers:
    """JsonParser, TextParser, HtmlParser, IcsParser, IcsEventsParser."""

    def _mock_response(self, text, json_data=None):
        resp = MagicMock()
        resp.text = text
        resp.json.return_value = json_data
        return resp

    def test_json_parser_top_level(self):
        from waste_collection_schedule.parsers import JsonParser

        data = [{"date": "2026-01-01", "type": "bin"}]
        resp = self._mock_response("", json_data=data)
        assert JsonParser()(resp) == data

    def test_json_parser_nested_key(self):
        from waste_collection_schedule.parsers import JsonParser

        data = {"collections": [{"date": "2026-01-01", "type": "bin"}]}
        resp = self._mock_response("", json_data=data)
        assert JsonParser("collections")(resp) == data["collections"]

    def test_json_parser_deep_key_path(self):
        from waste_collection_schedule.parsers import JsonParser

        data = {"data": {"items": [{"date": "2026-01-01"}]}}
        resp = self._mock_response("", json_data=data)
        assert JsonParser("data", "items")(resp) == data["data"]["items"]

    def test_text_parser(self):
        from waste_collection_schedule.parsers import TextParser

        resp = self._mock_response("hello world")
        assert TextParser()(resp) == "hello world"

    def test_html_parser_with_selector(self):
        from waste_collection_schedule.parsers import HtmlParser

        resp = self._mock_response(
            "<table><tr><th>H</th></tr><tr><td>2024-01-15</td></tr></table>"
        )
        parser = HtmlParser("tr", skip=1)
        rows = parser(resp)
        assert len(rows) == 1
        assert rows[0].select_one("td").text == "2024-01-15"

    def test_html_parser_skip(self):
        from waste_collection_schedule.parsers import HtmlParser

        resp = self._mock_response("<ul><li>a</li><li>b</li><li>c</li></ul>")
        parser = HtmlParser("li", skip=1)
        items = parser(resp)
        assert len(items) == 2
        assert items[0].text == "b"

    def test_ics_parser_returns_date_summary_tuples(self):
        from waste_collection_schedule.parsers import IcsParser

        resp = MagicMock()
        resp.text = "BEGIN:VCALENDAR\nEND:VCALENDAR"
        expected = [(datetime.date(2026, 1, 15), "General Waste")]

        with patch(
            "waste_collection_schedule.service.ICS.ICS.convert", return_value=expected
        ):
            result = IcsParser()(resp)
            assert result == expected

    def test_ics_events_parser_returns_full_events(self):
        from waste_collection_schedule.parsers import IcsEventsParser
        from waste_collection_schedule.service.ICS import IcsEvent

        resp = MagicMock()
        resp.text = "BEGIN:VCALENDAR\nEND:VCALENDAR"
        expected = [
            IcsEvent(
                datetime.date(2026, 1, 15),
                "General Waste",
                location="Route 1",
                description="weekly",
            )
        ]

        with patch(
            "waste_collection_schedule.service.ICS.ICS.convert_events",
            return_value=expected,
        ):
            result = IcsEventsParser()(resp)
            assert result == expected
            assert result[0].location == "Route 1"


class TestArcGisComponents:
    """ArcGis service contributes a Retriever and a Parser, kept independent."""

    def test_feature_retriever_geocodes_then_queries_raw(self):
        from waste_collection_schedule.service import ArcGis

        source = MagicMock()
        source.params = {"address": "1 Test St"}
        captured = {}

        def fake_get(url, params=None, timeout=None):
            captured["url"] = url
            captured["params"] = params
            return MagicMock()

        retriever = ArcGis.ArcGisFeatureRetriever(
            "https://x/FeatureServer/0", address="address"
        )
        with (
            patch.object(ArcGis, "geocode", return_value={"x": 1.0, "y": 2.0}),
            patch.object(ArcGis.requests, "get", side_effect=fake_get),
        ):
            retriever(source)

        assert captured["url"].endswith("/FeatureServer/0/query")
        assert captured["params"]["f"] == "json"
        assert "geometry" in captured["params"]

    def test_feature_retriever_bad_address_raises_source_argument(self):
        from waste_collection_schedule.exceptions import SourceArgumentNotFound
        from waste_collection_schedule.service import ArcGis

        source = MagicMock()
        source.params = {"address": "nowhere"}
        retriever = ArcGis.ArcGisFeatureRetriever("https://x/FeatureServer/0")
        with patch.object(
            ArcGis, "geocode", side_effect=ArcGis.ArcGisGeocodeError("none")
        ):
            with pytest.raises(SourceArgumentNotFound):
                retriever(source)

    def test_feature_parser_extracts_attributes_from_raw_response(self):
        from waste_collection_schedule.service import ArcGis

        resp = MagicMock()
        resp.raise_for_status.return_value = None
        resp.json.return_value = {
            "features": [{"attributes": {"a": 1}}, {"attributes": {"a": 2}}]
        }
        # Runs standalone against a fixture Response — no retriever involved.
        assert ArcGis.ArcGisFeatureParser()(resp) == [{"a": 1}, {"a": 2}]

    def test_feature_parser_empty_features(self):
        from waste_collection_schedule.service import ArcGis

        resp = MagicMock()
        resp.raise_for_status.return_value = None
        resp.json.return_value = {"features": []}
        assert ArcGis.ArcGisFeatureParser()(resp) == []


class TestPipelineContext:
    """Parser/preprocessor receive the source; source exposes a lazy session."""

    def test_parse_receives_source(self):
        from waste_collection_schedule.base_source import BaseSource
        from waste_collection_schedule.collection import Collection
        from waste_collection_schedule.waste_types import GENERAL_WASTE

        seen = {}

        class Src(BaseSource):
            def __init__(self):
                super().__init__()

            def retrieve(self, source):
                return "raw"

            def parse(self, raw, source):
                # The parser can read params off the source it is handed.
                seen["got_source"] = source is self
                return [raw]

            def classify(self, record):
                return Collection(
                    date=datetime.date(2026, 1, 1), waste_type=GENERAL_WASTE
                )

        Src().fetch()
        assert seen["got_source"] is True

    def test_preprocessor_receives_source(self):
        from waste_collection_schedule.base_source import BaseSource
        from waste_collection_schedule.collection import Collection
        from waste_collection_schedule.waste_types import GENERAL_WASTE

        seen = {}

        class Src(BaseSource):
            def __init__(self):
                super().__init__(town="x")

            def retrieve(self, source):
                return ["a"]

            def parse(self, raw, source):
                return raw

            def preprocess(self, records, source):
                seen["town"] = source.params.get("town")
                return records

            def classify(self, record):
                return Collection(
                    date=datetime.date(2026, 1, 1), waste_type=GENERAL_WASTE
                )

        Src().fetch()
        assert seen["town"] == "x"

    def test_session_is_lazy_and_cached(self):
        from waste_collection_schedule.base_source import BaseSource

        class Src(BaseSource):
            def __init__(self):
                super().__init__()

        src = Src()
        assert src._session is None
        sentinel = object()
        with patch("curl_cffi.requests.Session", return_value=sentinel) as session_cls:
            first = src.session
            second = src.session
        assert first is sentinel
        assert second is sentinel
        session_cls.assert_called_once()  # created once, then cached


class TestRiSKommunalComponents:
    """RiSKommunal contributes a lazy paginating Retriever and a config-aware Parser."""

    _PAGE0 = (
        '<table class="ris_table">'
        "<tr><td>01.07.2026</td><td><a>Restmüll</a></td></tr>"
        "<tr><td>02.07.2026</td><td><a>Bioabfall</a></td></tr>"
        "</table>"
    )
    _EMPTY = "<html><body>no calendar</body></html>"

    def _response(self, text):
        resp = MagicMock()
        resp.text = text
        resp.apparent_encoding = "utf-8"
        resp.raise_for_status.return_value = None
        return resp

    def test_retriever_pages_are_lazy(self):
        """Retriever yields raw pages; only those the parser pulls get fetched."""
        from waste_collection_schedule.service import RiSKommunalAT as R

        calls = {"n": 0}
        outer = self

        class FakeSession:
            def get(self, url, params=None, headers=None, timeout=None):
                calls["n"] += 1
                page = params.get("page", 0)
                return outer._response(outer._PAGE0 if page == 0 else outer._EMPTY)

        source = MagicMock()
        source.params = {}
        retriever = R.RiSKommunalRetriever(
            base_url="https://example.at", query_params={"x": "1"}
        )
        parser = R.RiSKommunalParser()
        with patch.object(R.requests, "Session", return_value=FakeSession()):
            rows = list(parser(retriever(source), source))

        # page 0 (rows) + page 1 (empty -> stop). Pages 2..49 never fetched.
        assert calls["n"] == 2
        assert [t for _, t in rows] == ["Restmüll", "Bioabfall"]

    def test_parser_filters_by_zone_from_params(self):
        from waste_collection_schedule.service import RiSKommunalAT as R

        page = (
            '<table class="ris_table">'
            "<tr><td>10.07.2026</td><td><a>Restmüll</a></td><td>Zone A</td></tr>"
            "<tr><td>11.07.2026</td><td><a>Restmüll</a></td><td>Zone B</td></tr>"
            "<tr><td>12.07.2026</td><td><a>Bioabfall</a></td><td>Gemeinde Alle</td></tr>"
            "</table>"
        )
        source = MagicMock()
        source.params = {"zone": "Zone A"}
        parser = R.RiSKommunalParser(zone_param="zone")
        rows = list(parser([page, self._EMPTY], source))
        days = {d.isoformat() for d, _ in rows}
        assert "2026-07-10" in days  # Zone A kept
        assert "2026-07-12" in days  # "Gemeinde Alle" always kept
        assert "2026-07-11" not in days  # Zone B filtered out

    def test_retriever_lookahead_days_sets_vdatum_and_bdatum(self):
        """lookahead_days adds a dynamically computed vdatum/bdatum window."""
        from waste_collection_schedule.service import RiSKommunalAT as R

        outer = self
        captured: dict = {}

        class FakeSession:
            def get(self, url, params=None, headers=None, timeout=None):
                captured.update(params)
                return outer._response(outer._EMPTY)

        source = MagicMock()
        source.params = {}
        retriever = R.RiSKommunalRetriever(
            base_url="https://example.at",
            query_params={},
            lookahead_days=30,
            max_pages=1,
        )
        with patch.object(R.requests, "Session", return_value=FakeSession()):
            list(retriever(source))

        today = datetime.date.today()
        assert captured["vdatum"] == today.strftime("%d.%m.%Y")
        expected_bdatum = today + datetime.timedelta(days=30)
        assert captured["bdatum"] == expected_bdatum.strftime("%d.%m.%Y")

    def test_retriever_default_omits_vdatum_and_bdatum(self):
        """Default (lookahead_days=None) preserves current behaviour exactly."""
        from waste_collection_schedule.service import RiSKommunalAT as R

        outer = self
        captured: dict = {}

        class FakeSession:
            def get(self, url, params=None, headers=None, timeout=None):
                captured.update(params)
                return outer._response(outer._EMPTY)

        source = MagicMock()
        source.params = {}
        retriever = R.RiSKommunalRetriever(
            base_url="https://example.at", query_params={}, max_pages=1
        )
        with patch.object(R.requests, "Session", return_value=FakeSession()):
            list(retriever(source))

        assert "vdatum" not in captured
        assert "bdatum" not in captured

    def test_parser_paginate_list_keeps_paging(self):
        """paginate_list=True pages through list-style renderings across pages."""
        from waste_collection_schedule.service import RiSKommunalAT as R

        div_id = R._LIST_DIV_ID
        page1 = (
            f'<div id="{div_id}">'
            "<h2>01.07.2026</h2><ul><li><span>Restmüll</span></li></ul>"
            "</div>"
        )
        page2 = (
            f'<div id="{div_id}">'
            "<h2>08.07.2026</h2><ul><li><span>Bioabfall</span></li></ul>"
            "</div>"
        )
        source = MagicMock()
        source.params = {}
        parser = R.RiSKommunalParser(paginate_list=True)
        rows = list(parser([page1, page2, self._EMPTY], source))
        days = {d.isoformat() for d, _ in rows}
        assert days == {"2026-07-01", "2026-07-08"}

    def test_parser_default_stops_after_first_list_page(self):
        """Default behaviour (paginate_list=False) still stops after page one."""
        from waste_collection_schedule.service import RiSKommunalAT as R

        div_id = R._LIST_DIV_ID
        page1 = (
            f'<div id="{div_id}">'
            "<h2>01.07.2026</h2><ul><li><span>Restmüll</span></li></ul>"
            "</div>"
        )
        page2 = (
            f'<div id="{div_id}">'
            "<h2>08.07.2026</h2><ul><li><span>Bioabfall</span></li></ul>"
            "</div>"
        )
        source = MagicMock()
        source.params = {}
        parser = R.RiSKommunalParser()
        rows = list(parser([page1, page2, self._EMPTY], source))
        days = {d.isoformat() for d, _ in rows}
        assert days == {"2026-07-01"}  # second page never consumed

    def test_parser_lookahead_days_drops_rows_past_window_and_stops(self):
        """lookahead_days filters rows past the window even when the server
        doesn't honour bdatum as a hard filter (observed live for Saalfelden:
        the server kept returning rows years past the requested window)."""
        from waste_collection_schedule.service import RiSKommunalAT as R

        today = datetime.date.today()
        in_window = (today + datetime.timedelta(days=10)).strftime("%d.%m.%Y")
        past_window = (today + datetime.timedelta(days=400)).strftime("%d.%m.%Y")
        page = (
            '<table class="ris_table">'
            f"<tr><td>{in_window}</td><td><a>Restmüll</a></td></tr>"
            f"<tr><td>{past_window}</td><td><a>Bioabfall</a></td></tr>"
            "</table>"
        )
        source = MagicMock()
        source.params = {}
        parser = R.RiSKommunalParser(lookahead_days=365)
        # A second page proves pagination stopped: it must remain unconsumed
        # once the first page's last row runs past the window.
        pages = iter([page, self._EMPTY])
        rows = list(parser(pages, source))
        assert [t for _, t in rows] == ["Restmüll"]
        assert next(pages) == self._EMPTY  # second page was never pulled


class TestAbfallnaviComponents:
    """AbfallnaviDe (regio iT): multi-request retriever + cross-referencing parser."""

    # Canned regio iT REST responses keyed by request path.
    _RESPONSES: ClassVar[dict] = {
        "orte": [{"id": 1, "name": "Aachen"}],
        "orte/1/strassen": [{"id": 10, "name": "Abteiplatz"}],
        "strassen/10": {"hausNrList": [{"id": 100, "nr": "7"}]},
        "fraktionen": [
            {"id": 5, "name": "Restmüll"},
            {"id": 6, "name": "Bioabfall"},
        ],
        "hausnummern/100/termine": [
            {"datum": "2026-07-01", "bezirk": {"fraktionId": 5}},
            {"datum": "2026-07-02", "bezirk": {"fraktionId": 6}},
        ],
    }

    def _patched_client(self):
        from waste_collection_schedule.service import AbfallnaviDe as M

        responses = self._RESPONSES

        def fake_fetch_json(self, path, params=None):
            return responses[path]

        return patch.object(M.AbfallnaviDe, "_fetch_json", fake_fetch_json)

    def test_retriever_bundles_raw_termine_and_fraktionen(self):
        from waste_collection_schedule.service import AbfallnaviDe as M

        source = MagicMock()
        source.params = {
            "service": "aachen",
            "ort": "Aachen",
            "strasse": "Abteiplatz",
            "hausnummer": "7",
        }
        retriever = M.AbfallnaviRetriever(
            service="service", city="ort", street="strasse", house_number="hausnummer"
        )
        with self._patched_client():
            raw = retriever(source)
        assert set(raw) == {"termine", "fraktionen"}
        assert raw["fraktionen"] == {5: "Restmüll", 6: "Bioabfall"}
        assert len(raw["termine"]) == 2

    def test_parser_cross_references_without_io(self):
        from waste_collection_schedule.service import AbfallnaviDe as M

        raw = {
            "fraktionen": {5: "Restmüll", 6: "Bioabfall"},
            "termine": [
                {"datum": "2026-07-01", "bezirk": {"fraktionId": 5}},
                {"datum": "2026-07-02", "bezirk": {"fraktionId": 6}},
            ],
        }
        # Standalone, no retriever / no network.
        rows = M.AbfallnaviParser()(raw)
        assert rows == [
            (datetime.date(2026, 7, 1), "Restmüll"),
            (datetime.date(2026, 7, 2), "Bioabfall"),
        ]

    def test_end_to_end_through_basesource(self):
        from waste_collection_schedule.base_source import BaseSource
        from waste_collection_schedule.service.AbfallnaviDe import (
            AbfallnaviParser,
            AbfallnaviRetriever,
        )
        from waste_collection_schedule.transformers import ICSTransformer
        from waste_collection_schedule.waste_types import GENERAL_WASTE, ORGANIC

        class Src(BaseSource):
            retrieve = AbfallnaviRetriever(
                service="service",
                city="ort",
                street="strasse",
                house_number="hausnummer",
            )
            parse = AbfallnaviParser()
            transform = ICSTransformer(
                type_value_map={"Restmüll": GENERAL_WASTE, "Bioabfall": ORGANIC}
            )

            def __init__(self):
                super().__init__(
                    service="aachen", ort="Aachen", strasse="Abteiplatz", hausnummer="7"
                )

        with self._patched_client():
            cols = Src().fetch()
        by_date = {c.date.isoformat(): c.waste_type.id for c in cols}
        assert by_date == {"2026-07-01": "general_waste", "2026-07-02": "organic"}


class TestIntraMapsComponents:
    """IntraMaps: stateful-session retriever + panel parser, kept separate."""

    _RESPONSE: ClassVar[dict] = {
        "infoPanels": {
            "info1": {
                "feature": {
                    "fields": [
                        {
                            "value": {
                                "column": "Rubbish_Collection_Day",
                                "value": "Every Friday",
                            }
                        },
                        {
                            "value": {
                                "column": "Recycle_Collection",
                                "value": "Friday This Week",
                            }
                        },
                        {"value": {"column": "ignored", "value": "x"}},
                    ]
                }
            }
        }
    }

    def _fake_client(self, response=None, error=None):
        resp = self._RESPONSE if response is None else response

        class FakeClient:
            def __init__(self, cfg):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def select_address(self, address, suburb=None):
                if error is not None:
                    raise error
                return {"status": "success", "response": resp}

        return FakeClient

    def test_retriever_runs_handshake_and_returns_raw_panels(self):
        from waste_collection_schedule.service import IntraMaps

        source = MagicMock()
        source.params = {"address": "1 Test St"}
        retriever = IntraMaps.IntraMapsRetriever(
            IntraMaps.MapsClientConfig(base_url="https://x"), address="address"
        )
        with patch.object(IntraMaps, "MapsClient", self._fake_client()):
            raw = retriever(source)
        assert "infoPanels" in raw

    def test_retriever_maps_search_error_to_source_argument(self):
        from waste_collection_schedule.exceptions import SourceArgumentNotFound
        from waste_collection_schedule.service import IntraMaps

        source = MagicMock()
        source.params = {"address": "nowhere"}
        retriever = IntraMaps.IntraMapsRetriever(
            IntraMaps.MapsClientConfig(base_url="https://x"), address="address"
        )
        err = IntraMaps.IntraMapsSearchError("no match")
        with patch.object(IntraMaps, "MapsClient", self._fake_client(error=err)):
            with pytest.raises(SourceArgumentNotFound):
                retriever(source)

    def test_panel_parser_extracts_column_value_records(self):
        from waste_collection_schedule.service import IntraMaps

        records = IntraMaps.IntraMapsPanelParser()(self._RESPONSE)
        assert {"column": "Rubbish_Collection_Day", "value": "Every Friday"} in records
        assert len(records) == 3

    def test_end_to_end_kwinana_projects_schedule(self):
        from waste_collection_schedule.service import IntraMaps
        from waste_collection_schedule.source import kwinana_wa_gov_au as K

        with patch.object(IntraMaps, "MapsClient", self._fake_client()):
            cols = K.Source(address="1 Chisham Avenue KWINANA TOWN CENTRE").fetch()

        types = {c.waste_type.id for c in cols}
        # weekly general waste (26) + fortnightly recycling (13); "ignored" dropped
        assert types == {"general_waste", "recyclables"}
        assert len(cols) == 26 + 13


class TestRecurrence:
    """Core recurrence helpers shared by projection-based sources/services."""

    def test_recurring_steps_by_delta(self):
        from waste_collection_schedule import recurrence

        dates = recurrence.recurring(datetime.date(2026, 1, 1), recurrence.WEEKLY, 3)
        assert dates == [
            datetime.date(2026, 1, 1),
            datetime.date(2026, 1, 8),
            datetime.date(2026, 1, 15),
        ]

    def test_recurring_from_anchor_rolls_forward(self):
        from waste_collection_schedule import recurrence

        anchor = datetime.date(2020, 1, 6)  # long in the past
        after = datetime.date(2026, 1, 1)
        dates = recurrence.recurring_from_anchor(
            anchor, recurrence.FORTNIGHTLY, 2, after=after
        )
        assert len(dates) == 2
        assert dates[0] >= after
        assert dates[0] - recurrence.FORTNIGHTLY < after  # first on/after `after`
        assert (dates[0] - anchor).days % 14 == 0  # still on the anchor's cycle
        assert dates[1] - dates[0] == recurrence.FORTNIGHTLY

    def test_next_weekday(self):
        from waste_collection_schedule import recurrence

        result = recurrence.next_weekday(4, on_or_after=datetime.date(2026, 6, 15))
        assert result.weekday() == 4
        assert result >= datetime.date(2026, 6, 15)
        assert (result - datetime.date(2026, 6, 15)).days < 7

    def test_most_recent_weekday(self):
        from waste_collection_schedule import recurrence

        result = recurrence.most_recent_weekday(
            0, on_or_before=datetime.date(2026, 6, 17)
        )
        assert result.weekday() == 0
        assert result <= datetime.date(2026, 6, 17)
        assert (datetime.date(2026, 6, 17) - result).days < 7

    def test_recurring_within_aligns_and_clips(self):
        from waste_collection_schedule import recurrence

        # Phase fixed to a Wednesday outside the window; weekly within October.
        start = datetime.date(2026, 1, 7)  # a Wednesday, well before the window
        dates = recurrence.recurring_within(
            start,
            recurrence.WEEKLY,
            not_before=datetime.date(2026, 10, 1),
            until=datetime.date(2026, 10, 31),
        )
        assert dates == [
            datetime.date(2026, 10, 7),
            datetime.date(2026, 10, 14),
            datetime.date(2026, 10, 21),
            datetime.date(2026, 10, 28),
        ]
        assert all(d.weekday() == 2 for d in dates)  # still Wednesdays

    def test_recurring_within_keeps_fortnightly_phase(self):
        from waste_collection_schedule import recurrence

        # Anchor pins which fortnight; only the in-window occurrences come back.
        anchor = datetime.date(2026, 5, 2)  # a Saturday
        dates = recurrence.recurring_within(
            anchor,
            recurrence.FORTNIGHTLY,
            not_before=datetime.date(2026, 6, 1),
            until=datetime.date(2026, 7, 31),
        )
        assert dates and all(d.weekday() == 5 for d in dates)
        assert all((d - anchor).days % 14 == 0 for d in dates)  # same fortnight cycle
        assert dates[0] >= datetime.date(2026, 6, 1)
        assert dates[0] - recurrence.FORTNIGHTLY < datetime.date(2026, 6, 1)

    def test_weekday_month_names_multilingual(self):
        from waste_collection_schedule import recurrence

        # Names we previously hand-maintained still resolve...
        assert recurrence.month("january") == 1
        assert recurrence.month("märz") == 3 and recurrence.month("maerz") == 3
        assert recurrence.month("février") == 2 and recurrence.month("fevrier") == 2
        # Polish genitive (format) and nominative (stand-alone) both resolve.
        assert recurrence.month("stycznia") == 1 and recurrence.month("styczeń") == 1
        assert recurrence.weekday("poniedziałek") == 0
        # ...and languages we never hand-added now come from Babel for free.
        assert recurrence.month("enero") == 1  # Spanish
        assert recurrence.month("dezembro") == 12  # Portuguese
        assert recurrence.weekday("maandag") == 0  # Dutch
        assert recurrence.weekday("torsdag") == 3  # Swedish/Danish Thursday
        # Unknown input is still a clean miss.
        assert recurrence.month("not-a-month") is None

    def test_recurring_within_empty_window(self):
        from waste_collection_schedule import recurrence

        dates = recurrence.recurring_within(
            datetime.date(2026, 1, 7),
            recurrence.WEEKLY,
            not_before=datetime.date(2026, 3, 1),
            until=datetime.date(2026, 2, 1),  # until before not_before
        )
        assert dates == []

    def test_monthly_nth_weekday_first_occurrence_in_month(self):
        from waste_collection_schedule import recurrence

        # July 2026: Tuesdays fall on 7, 14, 21, 28 -> 2nd Tuesday is the 14th.
        result = recurrence.monthly_nth_weekday(
            1, 2, on_or_after=datetime.date(2026, 7, 1)
        )
        assert result == datetime.date(2026, 7, 14)

    def test_monthly_nth_weekday_rolls_to_next_month_when_passed(self):
        from waste_collection_schedule import recurrence

        # Asking on/after the 15th means July's 2nd Tuesday (14th) has passed.
        result = recurrence.monthly_nth_weekday(
            1, 2, on_or_after=datetime.date(2026, 7, 15)
        )
        assert result == datetime.date(2026, 8, 11)

    def test_monthly_nth_weekday_on_the_day_itself_is_inclusive(self):
        from waste_collection_schedule import recurrence

        result = recurrence.monthly_nth_weekday(
            1, 2, on_or_after=datetime.date(2026, 7, 14)
        )
        assert result == datetime.date(2026, 7, 14)

    def test_monthly_nth_weekday_last_occurrence(self):
        from waste_collection_schedule import recurrence

        # Memorial Day: last Monday in May 2026 is the 25th (not the 4th Monday).
        result = recurrence.monthly_nth_weekday(
            0, -1, on_or_after=datetime.date(2026, 5, 1)
        )
        assert result == datetime.date(2026, 5, 25)

    def test_monthly_nth_weekday_skips_a_month_without_a_fifth_occurrence(self):
        from waste_collection_schedule import recurrence

        # February 2026 (28 days, starts on a Sunday) has only four Mondays
        # (2, 9, 16, 23): no 5th Monday, so this must roll to the next month
        # that has one (March 2026: Mondays 2, 9, 16, 23, 30).
        result = recurrence.monthly_nth_weekday(
            0, 5, on_or_after=datetime.date(2026, 2, 1)
        )
        assert result == datetime.date(2026, 3, 30)

    def test_monthly_nth_weekday_invalid_n_raises(self):
        from waste_collection_schedule import recurrence

        with pytest.raises(ValueError):
            recurrence.monthly_nth_weekday(0, 0, on_or_after=datetime.date(2026, 1, 1))

    def test_monthly_nth_weekdays_returns_one_per_consecutive_month(self):
        from waste_collection_schedule import recurrence

        dates = recurrence.monthly_nth_weekdays(
            1, 2, 3, on_or_after=datetime.date(2026, 7, 1)
        )
        assert dates == [
            datetime.date(2026, 7, 14),
            datetime.date(2026, 8, 11),
            datetime.date(2026, 9, 8),
        ]
        assert all(d.weekday() == 1 for d in dates)

    def test_us_federal_holidays_matches_known_2026_dates(self):
        from waste_collection_schedule import recurrence

        days = recurrence.us_federal_holidays(2026)
        assert datetime.date(2026, 1, 1) in days  # New Year's Day
        assert datetime.date(2026, 1, 19) in days  # MLK Day (3rd Mon Jan)
        assert datetime.date(2026, 5, 25) in days  # Memorial Day (last Mon May)
        assert datetime.date(2026, 9, 7) in days  # Labor Day (1st Mon Sep)
        assert datetime.date(2026, 10, 12) in days  # Columbus Day (2nd Mon Oct)
        assert datetime.date(2026, 11, 26) in days  # Thanksgiving (4th Thu Nov)

    def test_us_federal_holidays_observed_shift_for_weekend_dates(self):
        from waste_collection_schedule import recurrence

        # July 4 2026 falls on a Saturday; observed=True (default) also
        # yields the Friday-before as a no-collection day.
        with_observed = recurrence.us_federal_holidays(2026)
        assert datetime.date(2026, 7, 3) in with_observed
        assert datetime.date(2026, 7, 4) in with_observed

        without_observed = recurrence.us_federal_holidays(2026, observed=False)
        assert datetime.date(2026, 7, 3) not in without_observed
        assert datetime.date(2026, 7, 4) in without_observed

    def test_us_federal_holidays_subdiv_changes_the_calendar(self):
        from waste_collection_schedule import recurrence

        # Tennessee's calendar adds Good Friday and drops Columbus Day.
        tn = recurrence.us_federal_holidays(2026, subdiv="TN")
        assert datetime.date(2026, 4, 3) in tn  # Good Friday 2026
        assert datetime.date(2026, 10, 12) not in tn  # no Columbus Day

        default = recurrence.us_federal_holidays(2026)
        assert datetime.date(2026, 4, 3) not in default
        assert datetime.date(2026, 10, 12) in default

    def test_us_federal_holidays_accepts_a_year_range(self):
        from waste_collection_schedule import recurrence

        days = recurrence.us_federal_holidays(range(2026, 2028))
        assert datetime.date(2026, 12, 25) in days
        assert datetime.date(2027, 12, 25) in days


class TestPdfImageCalendarBoxMapping:
    """Grid box -> (year, month) mapping incl. financial-year calendars (Gap 4)."""

    def test_jan_dec_calendar(self):
        from waste_collection_schedule.service.PdfImageCalendar import box_year_month

        # start_month=1: box i is month i+1 of the base year, no rollover.
        assert box_year_month(2026, 1, 0) == (2026, 1)
        assert box_year_month(2026, 1, 11) == (2026, 12)

    def test_financial_year_calendar_rolls_over(self):
        from waste_collection_schedule.service.PdfImageCalendar import box_year_month

        # start_month=7 (Jul-Jun): Jul..Dec stay in base year, Jan..Jun roll over.
        assert box_year_month(2025, 7, 0) == (2025, 7)
        assert box_year_month(2025, 7, 5) == (2025, 12)
        assert box_year_month(2025, 7, 6) == (2026, 1)
        assert box_year_month(2025, 7, 11) == (2026, 6)


class TestResponseShape:
    """Typed response-shape validation (logs + raises on a provider change)."""

    def _shape(self):
        from typing import TypedDict

        class Field(TypedDict):
            name: str
            value: str

        return list[list[Field]]

    def test_matching_shape_passes_through(self):
        from waste_collection_schedule import response_shape

        data = [[{"name": "type", "value": "Red"}]]
        assert response_shape.validate(data, self._shape(), source_name="x") is data

    def test_wrong_container_raises(self):
        from waste_collection_schedule import response_shape

        with pytest.raises(response_shape.ResponseShapeError):
            response_shape.validate({"error": "moved"}, self._shape(), source_name="x")

    def test_missing_required_key_raises(self):
        from waste_collection_schedule import response_shape

        with pytest.raises(response_shape.ResponseShapeError):
            response_shape.validate(
                [[{"name": "type"}]], self._shape(), source_name="x"
            )

    def test_extra_keys_are_tolerated(self):
        from waste_collection_schedule import response_shape

        data = [[{"name": "type", "value": "Red", "caption": "type"}]]
        # An added key is not a breaking change, so validation passes.
        assert response_shape.validate(data, self._shape(), source_name="x") is data


class TestToolkitParsers:
    """Phase-2 parser/param additions: CSV, XML, api_key."""

    class _Resp:
        def __init__(self, text):
            self.text = text
            self.content = text.encode("utf-8")

    def test_csv_parser_rows_and_shape(self):
        from waste_collection_schedule import parsers
        from waste_collection_schedule.response_shape import ResponseShapeError

        resp = self._Resp("date,type\n2026-06-24,Red\n2026-07-01,Yellow\n")
        rows = parsers.CsvParser(require=["date", "type"])(resp)
        assert rows == [
            {"date": "2026-06-24", "type": "Red"},
            {"date": "2026-07-01", "type": "Yellow"},
        ]
        with pytest.raises(ResponseShapeError):
            parsers.CsvParser(require=["date", "bin"])(self._Resp("date,type\nx,y\n"))

    def test_xml_parser_selects_and_shape(self):
        from waste_collection_schedule import parsers
        from waste_collection_schedule.response_shape import ResponseShapeError

        xml = "<root><event><d>1</d></event><event><d>2</d></event></root>"
        assert len(parsers.XmlParser("event", min_nodes=1)(self._Resp(xml))) == 2
        with pytest.raises(ResponseShapeError):
            parsers.XmlParser("missing", min_nodes=1)(self._Resp(xml))

    def test_api_key_param(self):
        from waste_collection_schedule.config_params import api_key

        assert "api_key" in api_key().fields

    def test_html_parser_from_json_key(self):
        from waste_collection_schedule import parsers

        class _JsonResp:
            text = ""

            def json(self):
                return {"responseContent": "<article><h3>Rubbish</h3></article>"}

        elements = parsers.HtmlParser("article", from_json_key="responseContent")(
            _JsonResp()
        )
        assert len(elements) == 1
        assert elements[0].h3.string == "Rubbish"

    def test_date_parser_from_epoch(self):
        import datetime

        from waste_collection_schedule import date_parsers

        # Noon UTC so the calendar date is host-timezone independent.
        moment = datetime.datetime(2026, 6, 24, 12, 0, tzinfo=datetime.timezone.utc)
        epoch_s = int(moment.timestamp())
        expected = datetime.date(2026, 6, 24)
        assert date_parsers.from_epoch()(epoch_s) == expected
        assert date_parsers.from_epoch(unit="ms")(epoch_s * 1000) == expected
        # Accepts a numeric string too (JSON APIs vary).
        assert date_parsers.from_epoch()(str(epoch_s)) == expected


class TestLookups:
    """Normalised name lookup with suggestions-on-miss (Gap 5)."""

    def test_resolve_matches_case_insensitively(self):
        from waste_collection_schedule import lookups

        mapping = {"Glenden": 1, "Middlemount": 0}
        assert lookups.resolve(mapping, "  glenden ", argument="town") == 1

    def test_resolve_raises_with_suggestions(self):
        from waste_collection_schedule import lookups
        from waste_collection_schedule.exceptions import (
            SourceArgumentNotFoundWithSuggestions,
        )

        with pytest.raises(SourceArgumentNotFoundWithSuggestions) as exc:
            lookups.resolve({"Glenden": 1, "Nebo": 2}, "Moranbah", argument="town")
        # suggestions list the valid keys
        assert "Glenden" in str(exc.value) and "Nebo" in str(exc.value)

    def test_normalize_text_collapses_whitespace(self):
        from waste_collection_schedule import lookups

        assert lookups.normalize_text("  Main   Street ") == "main street"


class TestSeasonalSchedule:
    """Schedule windowing (Gap 1): season-bounded, per-window cadence."""

    def _expand(self, schedules):
        from waste_collection_schedule.preprocessors import RecurrenceExpander

        expander = RecurrenceExpander(lambda record, source: schedules)
        return list(expander([object()], None))

    def test_windowed_weekly_segment(self):
        from waste_collection_schedule import recurrence
        from waste_collection_schedule.preprocessors import Schedule

        rows = self._expand(
            [
                Schedule(
                    "yard",
                    datetime.date(2026, 1, 7),  # phase only (a Wednesday)
                    recurrence.WEEKLY,
                    not_before=datetime.date(2026, 10, 1),
                    until=datetime.date(2026, 10, 31),
                )
            ]
        )
        assert [d for d, _ in rows] == [
            datetime.date(2026, 10, 7),
            datetime.date(2026, 10, 14),
            datetime.date(2026, 10, 21),
            datetime.date(2026, 10, 28),
        ]
        assert {k for _, k in rows} == {"yard"}

    def test_no_collection_months_yield_nothing(self):
        # A season with no collection is modelled by issuing no Schedule.
        rows = self._expand([])
        assert rows == []

    def test_partial_month_until(self):
        from waste_collection_schedule import recurrence
        from waste_collection_schedule.preprocessors import Schedule

        # "December weeks Dec 1 until week of Dec 14" -> stop mid-month.
        rows = self._expand(
            [
                Schedule(
                    "yard",
                    datetime.date(2026, 12, 2),  # a Wednesday
                    recurrence.WEEKLY,
                    not_before=datetime.date(2026, 12, 1),
                    until=datetime.date(2026, 12, 14),
                )
            ]
        )
        assert [d for d, _ in rows] == [
            datetime.date(2026, 12, 2),
            datetime.date(2026, 12, 9),
        ]

    def test_not_before_clips_count_mode(self):
        from waste_collection_schedule import recurrence
        from waste_collection_schedule.preprocessors import Schedule

        # Without `until`, not_before just drops earlier count-based occurrences.
        rows = self._expand(
            [
                Schedule(
                    "general",
                    datetime.date(2026, 6, 1),
                    recurrence.WEEKLY,
                    count=4,
                    not_before=datetime.date(2026, 6, 15),
                )
            ]
        )
        assert [d for d, _ in rows] == [
            datetime.date(2026, 6, 15),
            datetime.date(2026, 6, 22),
        ]

    def test_iso_week_parity_selects_even_weeks(self):
        from waste_collection_schedule import recurrence
        from waste_collection_schedule.preprocessors import Schedule

        # A weekly window thinned to ISO-even weeks (an "A week / B week" cadence).
        rows = self._expand(
            [
                Schedule(
                    "blue",
                    datetime.date(2026, 1, 7),  # a Wednesday, ISO W02 (even)
                    recurrence.WEEKLY,
                    not_before=datetime.date(2026, 1, 5),
                    until=datetime.date(2026, 2, 1),
                    iso_week_parity="even",
                )
            ]
        )
        dates = [d for d, _ in rows]
        assert dates == [datetime.date(2026, 1, 7), datetime.date(2026, 1, 21)]
        assert all(d.isocalendar().week % 2 == 0 for d in dates)

    def test_iso_week_parity_correct_across_53_week_year(self):
        from waste_collection_schedule import recurrence
        from waste_collection_schedule.preprocessors import Schedule

        # 2026 is a 53-week ISO year. Naive fortnightly stepping from Dec 23
        # would land on Jan 6 (W01, odd) and drift; ISO parity recomputed per
        # date skips W53 and W01 and resumes on W02 — a 21-day gap, not 14.
        rows = self._expand(
            [
                Schedule(
                    "blue",
                    datetime.date(2026, 12, 23),  # Wednesday, W52 (even)
                    recurrence.WEEKLY,
                    not_before=datetime.date(2026, 12, 21),
                    until=datetime.date(2027, 1, 20),
                    iso_week_parity="even",
                )
            ]
        )
        dates = [d for d, _ in rows]
        assert dates == [datetime.date(2026, 12, 23), datetime.date(2027, 1, 13)]
        assert (dates[1] - dates[0]).days == 21
        assert all(d.isocalendar().week % 2 == 0 for d in dates)


class TestRetrievers:
    """Zero-config http_get/http_post (curl_cffi) and configured/legacy retrievers."""

    def test_http_get_uses_shared_session(self):
        """The zero-config http_get issues the request via the shared session."""
        from waste_collection_schedule.retrievers import http_get

        source = MagicMock()
        source.API_URL = "https://example.com/api"
        source._params = {"key": "val"}
        source._headers = {"X-Custom": "yes"}
        source.TIMEOUT = 15

        http_get(source)
        source.session.get.assert_called_once_with(
            "https://example.com/api",
            params={"key": "val"},
            headers={"X-Custom": "yes"},
            timeout=15,
        )

    def test_http_post_uses_shared_session(self):
        """The zero-config http_post issues the request via the shared session."""
        from waste_collection_schedule.retrievers import http_post

        source = MagicMock()
        source.API_URL = "https://example.com/api"
        source._params = None
        source._data = "body"
        source._json = None
        source._headers = None
        source.TIMEOUT = 30

        http_post(source)
        source.session.post.assert_called_once_with(
            "https://example.com/api",
            params=None,
            data="body",
            json=None,
            headers=None,
            timeout=30,
        )

    def test_base_source_session_impersonates_chrome(self):
        """The one place a curl_cffi session is built is BaseSource.session."""
        from waste_collection_schedule.base_source import BaseSource

        class _S(BaseSource):
            pass

        src = _S()
        with patch("curl_cffi.requests.Session", return_value=MagicMock()) as mk:
            _ = src.session
            mk.assert_called_once_with(impersonate="chrome")

    def test_configured_http_get_resolves_callable_url(self):
        """Resolve callable retriever args against source.params."""
        from waste_collection_schedule.retrievers import HttpGetRetriever

        source = MagicMock()
        source.params = {"uprn": "123"}

        retriever = HttpGetRetriever(
            url=lambda uprn: f"https://example.com/{uprn}",
            params={"key": "val"},
        )

        retriever(source)
        source.session.get.assert_called_once_with(
            "https://example.com/123",
            params={"key": "val"},
            headers=None,
            timeout=30,
        )

    def test_legacy_http_get_uses_plain_requests(self):
        from waste_collection_schedule.retrievers import LegacyHttpGetRetriever

        source = MagicMock()
        source.params = {}

        retriever = LegacyHttpGetRetriever(
            url="https://example.com/api", params={"key": "val"}
        )

        with patch("waste_collection_schedule.retrievers._plain_requests") as mock_req:
            retriever(source)
            mock_req.get.assert_called_once_with(
                "https://example.com/api",
                params={"key": "val"},
                headers=None,
                timeout=30,
            )

    def test_legacy_http_post_uses_plain_requests(self):
        from waste_collection_schedule.retrievers import LegacyHttpPostRetriever

        source = MagicMock()
        source.params = {}

        retriever = LegacyHttpPostRetriever(url="https://example.com/api", data="body")

        with patch("waste_collection_schedule.retrievers._plain_requests") as mock_req:
            retriever(source)
            mock_req.post.assert_called_once_with(
                "https://example.com/api",
                params=None,
                data="body",
                json=None,
                headers=None,
                timeout=30,
            )


# =====================================================================
# 3. Configuration
# =====================================================================


class TestConfigParams:
    """ConfigParam declarations for source configuration."""

    def test_coords(self):
        from waste_collection_schedule.config_params import coords

        p = coords(lat="latitude", lon="longitude")
        assert p.widget == "map"
        assert "latitude" in p.fields
        assert "longitude" in p.fields
        assert p.labels["en"]["latitude"] == "Latitude"

    def test_coords_default_names(self):
        from waste_collection_schedule.config_params import coords

        p = coords()
        assert "lat" in p.fields
        assert "lon" in p.fields

    def test_uprn(self):
        from waste_collection_schedule.config_params import uprn

        p = uprn()
        assert p.widget == "uprn_lookup"
        assert "uprn" in p.fields

    def test_postcode_with_house(self):
        from waste_collection_schedule.config_params import postcode

        p = postcode(house_field="house")
        assert "postcode" in p.fields
        assert "house" in p.fields
        assert p.labels["en"]["house"] == "House Number"

    def test_postcode_without_house(self):
        from waste_collection_schedule.config_params import postcode

        p = postcode()
        assert "postcode" in p.fields
        assert len(p.fields) == 1

    def test_address(self):
        from waste_collection_schedule.config_params import address

        p = address(city_field="city")
        assert "street" in p.fields
        assert "house_number" in p.fields
        assert "postcode" in p.fields
        assert "city" in p.fields
        # Standard term labels are now multilingual (incl. nl).
        assert p.labels["nl"]["street"] == "Straat"

    def test_municipality(self):
        from waste_collection_schedule.config_params import district, municipality

        p = municipality(field="f_id_kommune")
        assert "f_id_kommune" in p.fields
        assert p.labels["de"]["f_id_kommune"] == "Gemeinde"

        d = district(field="f_id_bezirk")
        assert "f_id_bezirk" in d.fields
        assert d.labels["fr"]["f_id_bezirk"] == "Quartier"

    def test_dropdown(self):
        from waste_collection_schedule.config_params import dropdown

        p = dropdown("region", ["North", "South"])
        assert p.widget == "select"
        assert "region" in p.fields

    def test_text_field(self):
        from waste_collection_schedule.config_params import text_field

        p = text_field("api_key", label="API Key")
        assert p.widget == "text"
        assert p.fields["api_key"] == "API Key"

    def test_multilingual_labels(self):
        from waste_collection_schedule.config_params import coords

        p = coords()
        for lang in ["en", "de", "fr", "it"]:
            assert lang in p.labels, f"Missing {lang} labels for coords"

    def test_cascading_select_declares_ordered_levels(self):
        from waste_collection_schedule.config_params import cascading_select

        p = cascading_select(
            ("f_id_kommune", "Kommune"),
            ("f_id_bezirk", "Bezirk"),
            "f_id_strasse",
        )
        assert p.widget == "cascading_select"
        # Ordered levels; a bare name gets a title-cased label.
        assert list(p.fields) == ["f_id_kommune", "f_id_bezirk", "f_id_strasse"]
        assert p.fields["f_id_kommune"] == "Kommune"
        assert p.fields["f_id_strasse"] == "F Id Strasse"
        # Levels are individually optional (the cascade shape is data-dependent).
        assert p.required is False


class TestRegions:
    """The structure-plus-regions model (Region / region() / legacy adapter)."""

    def test_region_factory_collects_params(self):
        from waste_collection_schedule.regions import Region, region

        r = region("Mulhouse", commune="Mulhouse", quartier="Centre Ville")
        assert isinstance(r, Region)
        assert r.title == "Mulhouse"
        assert r.params == {"commune": "Mulhouse", "quartier": "Centre Ville"}
        assert r.url is None and r.country is None

    def test_region_display_overrides(self):
        from waste_collection_schedule.regions import region

        r = region("Somewhere", url="https://x.example", country="fr", code="42")
        assert r.url == "https://x.example"
        assert r.country == "fr"
        assert r.params == {"code": "42"}

    def test_from_extra_info_adapts_legacy_dicts(self):
        from waste_collection_schedule.regions import Region, from_extra_info

        regions = from_extra_info(
            [
                {"title": "A", "default_params": {"city": "A"}},
                {"title": "B", "url": "https://b.example", "country": "de"},
            ]
        )
        assert regions == [
            Region(title="A", params={"city": "A"}),
            Region(title="B", params={}, url="https://b.example", country="de"),
        ]
        # Accepts a callable (legacy EXTRA_INFO could be a function) and empties.
        assert from_extra_info(list) == []
        assert from_extra_info(None) == []


class TestDisplayLanguage:
    """Collection.type localises to the configured display language."""

    def test_collection_type_follows_display_language(self):
        from waste_collection_schedule import waste_types as w
        from waste_collection_schedule.collection import Collection

        day = datetime.date(2026, 1, 1)
        try:
            # Default is English.
            assert Collection(date=day, waste_type=w.GENERAL_WASTE).type == (
                "General Waste"
            )
            # A French instance sees the French canonical name.
            w.set_display_language("fr")
            assert Collection(date=day, waste_type=w.GENERAL_WASTE).type == (
                "Ordures ménagères"
            )
            # A full locale falls back to the base language.
            w.set_display_language("de-DE")
            assert Collection(date=day, waste_type=w.GENERAL_WASTE).type == "Restmüll"
            # An unsupported language falls back to English.
            w.set_display_language("es")
            assert Collection(date=day, waste_type=w.GENERAL_WASTE).type == (
                "General Waste"
            )
        finally:
            # Restore the default so other tests keep seeing English labels.
            w.set_display_language("en")


class TestConfigParamValidation:
    """Defaults, alternatives, and validate() rules for ConfigParam."""

    def test_text_field_default_makes_optional(self):
        from waste_collection_schedule.config_params import api_key, text_field

        p = text_field("key", default="EMBEDDED")
        assert p.required is False
        assert p.defaults == {"key": "EMBEDDED"}
        # No default => required, no defaults recorded.
        assert text_field("key").required is True
        assert text_field("key").defaults == {}
        # api_key wraps text_field with the same default behaviour.
        assert api_key(default="X").defaults == {"api_key": "X"}

    def test_optional_without_default(self):
        from waste_collection_schedule.config_params import (
            dropdown,
            text_field,
            validate,
        )

        # optional=True makes a field optional with no pre-filled value.
        p = text_field("strasse", optional=True)
        assert p.required is False
        assert p.defaults == {}
        assert dropdown("day", ["Mon"], optional=True).required is False
        # An optional field absent from the values passes validation.
        validate([p], {})

    def test_apply_defaults_fills_only_missing(self):
        from waste_collection_schedule.config_params import apply_defaults, text_field

        params = [text_field("key", default="EMBEDDED")]
        # Missing/empty fields get the default; a supplied value is kept.
        assert apply_defaults(params, {}) == {"key": "EMBEDDED"}
        assert apply_defaults(params, {"key": ""}) == {"key": "EMBEDDED"}
        assert apply_defaults(params, {"key": "mine"}) == {"key": "mine"}

    def test_validate_required_raises_when_missing(self):
        from waste_collection_schedule.config_params import uprn, validate
        from waste_collection_schedule.exceptions import SourceArgumentRequired

        with pytest.raises(SourceArgumentRequired):
            validate([uprn()], {})

    def test_alternatives_declares_union_and_groups(self):
        from waste_collection_schedule.config_params import (
            alternatives,
            postcode,
            text_field,
            uprn,
        )

        p = alternatives([uprn()], [postcode(), text_field("house")])
        assert p.widget == "alternatives"
        assert p.required is False
        # Every field of every group is declared (so __init__ accepts them).
        assert set(p.fields) == {"uprn", "postcode", "house"}
        assert p.groups == (("uprn",), ("postcode", "house"))

    def test_validate_alternatives_requires_exactly_one_full_group(self):
        from waste_collection_schedule.config_params import (
            alternatives,
            postcode,
            text_field,
            uprn,
            validate,
        )
        from waste_collection_schedule.exceptions import (
            SourceArgumentExceptionMultiple,
        )

        params = [alternatives([uprn()], [postcode(), text_field("house")])]
        # One full group satisfies validation.
        validate(params, {"uprn": "123"})
        validate(params, {"postcode": "AB1", "house": "5"})
        # No group, or only a partial group, fails.
        with pytest.raises(SourceArgumentExceptionMultiple):
            validate(params, {})
        with pytest.raises(SourceArgumentExceptionMultiple):
            validate(params, {"postcode": "AB1"})


# =====================================================================
# 4. Pipeline orchestration (BaseSource)
# =====================================================================


class TestBaseSourcePipeline:
    """BaseSource fetch → retrieve → parse → classify orchestration."""

    def _make_source_class(self, records, classify_fn):
        """Create a BaseSource subclass with mocked retrieve/parse."""
        from waste_collection_schedule.base_source import BaseSource

        class TestSource(BaseSource):
            TITLE = "Test"
            COUNTRY = "au"

            def __init__(self):
                pass

            def retrieve(self, source):
                return MagicMock()  # mock response

            def parse(self, response, source=None):
                return records

            classify = classify_fn

        return TestSource

    def test_full_pipeline(self):
        from waste_collection_schedule.collection import Collection
        from waste_collection_schedule.waste_types import GENERAL_WASTE

        def classify(self, record):
            return Collection(
                date=datetime.date(2026, 1, int(record["day"])),
                waste_type=GENERAL_WASTE,
            )

        Source = self._make_source_class([{"day": "1"}, {"day": "15"}], classify)
        results = Source().fetch()
        assert len(results) == 2
        assert all(isinstance(r, Collection) for r in results)
        assert results[0].date == datetime.date(2026, 1, 1)
        assert results[1].date == datetime.date(2026, 1, 15)

    def test_classify_returning_none_skips_record(self):
        def classify(self, record):
            if record.get("skip"):
                return None
            from waste_collection_schedule.collection import Collection
            from waste_collection_schedule.waste_types import GENERAL_WASTE

            return Collection(date=datetime.date(2026, 1, 1), waste_type=GENERAL_WASTE)

        Source = self._make_source_class([{"skip": True}, {"skip": False}], classify)
        results = Source().fetch()
        assert len(results) == 1

    def test_empty_records_returns_empty(self):
        Source = self._make_source_class([], lambda self, r: None)
        assert Source().fetch() == []

    def test_none_records_returns_empty(self):
        Source = self._make_source_class(None, lambda self, r: None)
        assert Source().fetch() == []

    def test_single_dict_record_wrapped_in_list(self):
        from waste_collection_schedule.collection import Collection
        from waste_collection_schedule.waste_types import RECYCLABLES

        def classify(self, record):
            return Collection(date=datetime.date(2026, 3, 1), waste_type=RECYCLABLES)

        Source = self._make_source_class({"single": "record"}, classify)
        results = Source().fetch()
        assert len(results) == 1

    def test_override_retrieve(self):
        """Source can override retrieve to use a different HTTP method."""
        from waste_collection_schedule.base_source import BaseSource
        from waste_collection_schedule.collection import Collection
        from waste_collection_schedule.waste_types import GENERAL_WASTE

        call_log = []

        class CustomSource(BaseSource):
            TITLE = "Custom"

            def __init__(self):
                pass

            def retrieve(self, source):
                call_log.append("custom_retrieve")
                return MagicMock()

            def parse(self, response, source=None):
                return [{"date": "2026-01-01"}]

            def classify(self, record):
                return Collection(
                    date=datetime.date(2026, 1, 1), waste_type=GENERAL_WASTE
                )

        CustomSource().fetch()
        assert "custom_retrieve" in call_log

    def test_override_parse(self):
        """Source can override parse to handle custom response formats."""
        from waste_collection_schedule.base_source import BaseSource
        from waste_collection_schedule.collection import Collection
        from waste_collection_schedule.waste_types import GENERAL_WASTE

        class CustomSource(BaseSource):
            TITLE = "Custom"

            def __init__(self):
                pass

            def retrieve(self, source):
                return "raw,csv,data"

            def parse(self, response, source=None):
                return [{"val": v} for v in response.split(",")]

            def classify(self, record):
                return Collection(
                    date=datetime.date(2026, 1, 1), waste_type=GENERAL_WASTE
                )

        results = CustomSource().fetch()
        assert len(results) == 3

    def test_override_parse_date(self):
        """Source can override parse_date for custom date formats."""
        from waste_collection_schedule.base_source import BaseSource
        from waste_collection_schedule.collection import Collection
        from waste_collection_schedule.date_parsers import for_format
        from waste_collection_schedule.waste_types import GENERAL_WASTE

        class CustomSource(BaseSource):
            TITLE = "Custom"
            parse_date = for_format("%d.%m.%Y")

            def __init__(self):
                pass

            def retrieve(self, source):
                return MagicMock()

            def parse(self, response, source=None):
                return [{"date": "10.04.2026"}]

            def classify(self, record):
                date = self.parse_date(record["date"])
                return Collection(date=date, waste_type=GENERAL_WASTE)

        results = CustomSource().fetch()
        assert results[0].date == datetime.date(2026, 4, 10)

    def test_transformer_used_when_set(self):
        """When transformer is declared, fetch() uses it instead of classify()."""
        from waste_collection_schedule.base_source import BaseSource
        from waste_collection_schedule.transformers import JsonTransformer
        from waste_collection_schedule.waste_types import GENERAL_WASTE

        class TestSource(BaseSource):
            transform = JsonTransformer(
                date_key="date",
                type_key="bin",
                type_value_map={"refuse": GENERAL_WASTE},
            )

            def __init__(self):
                pass

            def retrieve(self, source):
                return MagicMock()

            def parse(self, response, source=None):
                return [{"date": "2026-03-01", "bin": "refuse"}]

        results = TestSource().fetch()
        assert len(results) == 1
        assert results[0].date == datetime.date(2026, 3, 1)
        assert results[0].waste_type is GENERAL_WASTE

    def test_fetch_flattens_transformer_list_into_separate_collections(self):
        """A list-valued mapping (combined round) becomes several collections."""
        from waste_collection_schedule.base_source import BaseSource
        from waste_collection_schedule.transformers import JsonTransformer
        from waste_collection_schedule.waste_types import GLASS, PAPER, RECYCLABLES

        class TestSource(BaseSource):
            transform = JsonTransformer(
                date_key="date",
                type_key="type",
                type_value_map={"V / PC": [GLASS, PAPER], "PMC": RECYCLABLES},
            )

            def __init__(self):
                pass

            def retrieve(self, source):
                return MagicMock()

            def parse(self, response, source=None):
                return [
                    {"date": "2026-03-01", "type": "V / PC"},
                    {"date": "2026-03-08", "type": "PMC"},
                ]

        results = TestSource().fetch()
        # One combined row -> two collections; one scalar row -> one. Total 3.
        assert len(results) == 3
        by_date = {}
        for c in results:
            by_date.setdefault(c.date.isoformat(), []).append(c.waste_type.id)
        assert by_date["2026-03-01"] == ["glass", "paper"]
        assert by_date["2026-03-08"] == ["recyclables"]

    def test_fetch_flattens_classify_list(self):
        """classify() may also return a list, which fetch flattens."""
        from waste_collection_schedule.collection import Collection
        from waste_collection_schedule.waste_types import GLASS, PAPER

        def classify(self, record):
            d = datetime.date(2026, 1, int(record["day"]))
            return [
                Collection(date=d, waste_type=GLASS),
                Collection(date=d, waste_type=PAPER),
            ]

        Source = self._make_source_class([{"day": "1"}], classify)
        results = Source().fetch()
        assert [c.waste_type.id for c in results] == ["glass", "paper"]

    def test_waste_types_derived_from_transformer(self):
        """WASTE_TYPES is auto-derived from transformer.waste_types."""
        from waste_collection_schedule.base_source import BaseSource
        from waste_collection_schedule.transformers import JsonTransformer
        from waste_collection_schedule.waste_types import GENERAL_WASTE, RECYCLABLES

        class TestSource(BaseSource):
            transform = JsonTransformer(
                date_key="date",
                type_key="bin",
                type_value_map={"refuse": GENERAL_WASTE, "recycling": RECYCLABLES},
            )

        assert TestSource.WASTE_TYPES == [GENERAL_WASTE, RECYCLABLES]

    def test_waste_types_derived_includes_combined_round_members(self):
        """A list-valued mapping contributes each of its types to WASTE_TYPES."""
        from waste_collection_schedule.base_source import BaseSource
        from waste_collection_schedule.transformers import JsonTransformer
        from waste_collection_schedule.waste_types import GLASS, PAPER, RECYCLABLES

        class TestSource(BaseSource):
            transform = JsonTransformer(
                date_key="date",
                type_key="type",
                type_value_map={"V / PC": [GLASS, PAPER], "PMC": RECYCLABLES},
            )

        assert TestSource.WASTE_TYPES == [GLASS, PAPER, RECYCLABLES]

    def test_waste_types_explicit_overrides_transformer(self):
        """Explicit WASTE_TYPES declaration takes precedence over transformer derivation."""
        from waste_collection_schedule.base_source import BaseSource
        from waste_collection_schedule.transformers import JsonTransformer
        from waste_collection_schedule.waste_types import (
            GENERAL_WASTE,
            OTHER,
            RECYCLABLES,
        )

        class TestSource(BaseSource):
            transform = JsonTransformer(
                date_key="date",
                type_key="bin",
                type_value_map={"refuse": GENERAL_WASTE},
            )
            WASTE_TYPES: ClassVar[list] = [GENERAL_WASTE, RECYCLABLES, OTHER]

        assert TestSource.WASTE_TYPES == [GENERAL_WASTE, RECYCLABLES, OTHER]


# =====================================================================
# 4b. Transformers
# =====================================================================


class TestTransformers:
    """JsonTransformer, KeyValueTransformer, ICSTransformer, HtmlTransformer."""

    def test_json_transformer_basic(self):
        from waste_collection_schedule.transformers import JsonTransformer
        from waste_collection_schedule.waste_types import GENERAL_WASTE

        t = JsonTransformer("date", "bin", {"refuse": GENERAL_WASTE})
        record = {"date": "2026-01-15", "bin": "refuse"}
        result = t(record)
        assert result is not None
        assert result.date == datetime.date(2026, 1, 15)
        assert result.waste_type is GENERAL_WASTE

    def test_json_transformer_case_insensitive(self):
        from waste_collection_schedule.transformers import JsonTransformer
        from waste_collection_schedule.waste_types import GENERAL_WASTE

        t = JsonTransformer("date", "bin", {"Refuse": GENERAL_WASTE})
        result = t({"date": "2026-01-15", "bin": "REFUSE"})
        assert result is not None
        assert result.waste_type is GENERAL_WASTE

    def test_json_transformer_missing_date_returns_none(self):
        from waste_collection_schedule.transformers import JsonTransformer
        from waste_collection_schedule.waste_types import GENERAL_WASTE

        t = JsonTransformer("date", "bin", {"refuse": GENERAL_WASTE})
        assert t({"bin": "refuse"}) is None

    def test_json_transformer_unknown_type_is_preserved_not_other(self):
        from waste_collection_schedule.transformers import JsonTransformer
        from waste_collection_schedule.waste_types import GENERAL_WASTE, OTHER

        t = JsonTransformer("date", "bin", {"refuse": GENERAL_WASTE})
        result = t({"date": "2026-01-15", "bin": "Frobnitz-Tonne"})
        assert result is not None
        # Unknown labels are preserved verbatim, never collapsed to OTHER.
        assert result.waste_type is not OTHER
        assert result.waste_type.id.startswith("preserved:")
        assert result.type == "Frobnitz-Tonne"

    def test_json_transformer_resolves_known_type_without_map_entry(self):
        from waste_collection_schedule.transformers import JsonTransformer
        from waste_collection_schedule.waste_types import RECYCLABLES

        # No map entry for "Wertstofftonne", but the shared vocabulary resolves it.
        t = JsonTransformer("date", "bin")
        result = t({"date": "2026-01-15", "bin": "Wertstofftonne"})
        assert result is not None
        assert result.waste_type is RECYCLABLES

    def test_json_transformer_unknown_type_emits_warning(self, caplog):
        import logging

        from waste_collection_schedule.transformers import JsonTransformer
        from waste_collection_schedule.waste_types import GENERAL_WASTE

        t = JsonTransformer("date", "bin", {"refuse": GENERAL_WASTE})
        with caplog.at_level(logging.WARNING):
            t({"date": "2026-01-15", "bin": "mystery_bin"})
        assert any("mystery_bin" in r.message for r in caplog.records)
        assert any("preserving" in r.message for r in caplog.records)

    def test_known_type_does_not_warn(self, caplog):
        import logging

        from waste_collection_schedule.transformers import JsonTransformer
        from waste_collection_schedule.waste_types import GENERAL_WASTE

        t = JsonTransformer("date", "bin", {"refuse": GENERAL_WASTE})
        with caplog.at_level(logging.WARNING):
            t({"date": "2026-01-15", "bin": "refuse"})
        assert not any("type_value_map" in r.message for r in caplog.records)

    def test_json_transformer_parse_date(self):
        from waste_collection_schedule import date_parsers
        from waste_collection_schedule.transformers import JsonTransformer
        from waste_collection_schedule.waste_types import GENERAL_WASTE

        t = JsonTransformer(
            "date",
            "bin",
            {"refuse": GENERAL_WASTE},
            parse_date=date_parsers.for_format("%d/%m/%Y"),
        )
        result = t({"date": "15/01/2026", "bin": "refuse"})
        assert result.date == datetime.date(2026, 1, 15)

    def test_json_transformer_waste_types_property(self):
        from waste_collection_schedule.transformers import JsonTransformer
        from waste_collection_schedule.waste_types import GENERAL_WASTE, RECYCLABLES

        t = JsonTransformer(
            "date", "bin", {"refuse": GENERAL_WASTE, "recycling": RECYCLABLES}
        )
        assert t.waste_types == [GENERAL_WASTE, RECYCLABLES]

    def test_json_transformer_waste_types_deduplicated(self):
        from waste_collection_schedule.transformers import JsonTransformer
        from waste_collection_schedule.waste_types import GENERAL_WASTE

        t = JsonTransformer(
            "date", "bin", {"black": GENERAL_WASTE, "grey": GENERAL_WASTE}
        )
        assert t.waste_types == [GENERAL_WASTE]

    def test_json_transformer_list_value_yields_multiple_collections(self):
        # A combined round: one raw label -> several types on the same date.
        from waste_collection_schedule.transformers import JsonTransformer
        from waste_collection_schedule.waste_types import GLASS, PAPER

        t = JsonTransformer("date", "type", {"V / PC": [GLASS, PAPER]})
        result = t({"date": "2026-01-15", "type": "V / PC"})
        assert isinstance(result, list)
        assert [c.waste_type for c in result] == [GLASS, PAPER]
        # Same date on every emitted collection.
        assert all(c.date == datetime.date(2026, 1, 15) for c in result)

    def test_json_transformer_scalar_value_still_yields_single_collection(self):
        # The scalar path is unchanged: a single Collection, not a list.
        from waste_collection_schedule.collection import Collection
        from waste_collection_schedule.transformers import JsonTransformer
        from waste_collection_schedule.waste_types import RECYCLABLES

        t = JsonTransformer("date", "type", {"PMC": RECYCLABLES})
        result = t({"date": "2026-01-15", "type": "PMC"})
        assert isinstance(result, Collection)
        assert result.waste_type is RECYCLABLES

    def test_waste_types_flattens_list_values(self):
        # waste_types reports each member of a combined round, in order, deduped.
        from waste_collection_schedule.transformers import JsonTransformer
        from waste_collection_schedule.waste_types import GLASS, PAPER, RECYCLABLES

        t = JsonTransformer(
            "date", "type", {"V / PC": [GLASS, PAPER], "PMC": RECYCLABLES}
        )
        assert t.waste_types == [GLASS, PAPER, RECYCLABLES]

    def test_ics_transformer_list_value_yields_multiple_collections(self):
        from waste_collection_schedule.transformers import ICSTransformer
        from waste_collection_schedule.waste_types import GLASS, PAPER

        t = ICSTransformer({"glass and paper": [GLASS, PAPER]})
        result = t((datetime.date(2026, 3, 1), "Glass and Paper"))
        assert isinstance(result, list)
        assert [c.waste_type for c in result] == [GLASS, PAPER]
        assert all(c.date == datetime.date(2026, 3, 1) for c in result)

    def test_key_value_transformer_basic(self):
        from waste_collection_schedule.transformers import KeyValueTransformer
        from waste_collection_schedule.waste_types import GENERAL_WASTE

        t = KeyValueTransformer("date", "type", {"red": GENERAL_WASTE})
        record = [
            {"name": "date", "value": "2026-01-15"},
            {"name": "type", "value": "red"},
        ]
        result = t(record)
        assert result is not None
        assert result.date == datetime.date(2026, 1, 15)
        assert result.waste_type is GENERAL_WASTE

    def test_key_value_transformer_normalises_whitespace(self):
        from waste_collection_schedule.transformers import KeyValueTransformer
        from waste_collection_schedule.waste_types import GENERAL_WASTE

        t = KeyValueTransformer("date", "type", {"red": GENERAL_WASTE})
        record = [
            {"name": "date", "value": "15  Jan  2026"},
            {"name": "type", "value": "red"},
        ]
        result = t(record)
        assert result is not None
        assert result.date == datetime.date(2026, 1, 15)

    def test_key_value_transformer_missing_date_returns_none(self):
        from waste_collection_schedule.transformers import KeyValueTransformer
        from waste_collection_schedule.waste_types import GENERAL_WASTE

        t = KeyValueTransformer("date", "type", {"red": GENERAL_WASTE})
        assert t([{"name": "type", "value": "red"}]) is None

    def test_ics_transformer_basic(self):
        from waste_collection_schedule.transformers import ICSTransformer
        from waste_collection_schedule.waste_types import GENERAL_WASTE

        t = ICSTransformer({"general waste": GENERAL_WASTE})
        record = (datetime.date(2026, 3, 1), "General Waste")
        result = t(record)
        assert result is not None
        assert result.date == datetime.date(2026, 3, 1)
        assert result.waste_type is GENERAL_WASTE

    def test_html_transformer_basic(self):
        from waste_collection_schedule.transformers import HtmlTransformer
        from waste_collection_schedule.waste_types import GENERAL_WASTE

        t = HtmlTransformer(
            date_getter=lambda el: el["date"],
            type_getter=lambda el: el["type"],
            type_value_map={"refuse": GENERAL_WASTE},
        )
        result = t({"date": "2026-01-15", "type": "refuse"})
        assert result is not None
        assert result.date == datetime.date(2026, 1, 15)

    def test_html_transformer_getter_exception_returns_none(self):
        from waste_collection_schedule.transformers import HtmlTransformer
        from waste_collection_schedule.waste_types import GENERAL_WASTE

        t = HtmlTransformer(
            date_getter=lambda el: el["missing_key"],
            type_getter=lambda el: "refuse",
            type_value_map={"refuse": GENERAL_WASTE},
        )
        assert t({}) is None

    def test_html_transformer_accepts_date_object_directly(self):
        from waste_collection_schedule.transformers import HtmlTransformer
        from waste_collection_schedule.waste_types import GENERAL_WASTE

        t = HtmlTransformer(
            date_getter=lambda el: datetime.date(2026, 6, 1),
            type_getter=lambda el: "refuse",
            type_value_map={"refuse": GENERAL_WASTE},
        )
        result = t({})
        assert result.date == datetime.date(2026, 6, 1)


# =====================================================================
# 5. Customisation (source_shell)
# =====================================================================


class TestSourceShellCustomize:
    """source_shell filter, customize, and day offset functions."""

    def test_customize_key_new_style(self):
        from waste_collection_schedule.collection import Collection
        from waste_collection_schedule.source_shell import _get_customize_key
        from waste_collection_schedule.waste_types import GENERAL_WASTE

        c = Collection(date=datetime.date(2026, 1, 1), waste_type=GENERAL_WASTE)
        assert _get_customize_key(c) == "general_waste"

    def test_customize_key_legacy(self):
        from waste_collection_schedule.collection import LegacyCollection
        from waste_collection_schedule.source_shell import _get_customize_key

        c = LegacyCollection(date=datetime.date(2026, 1, 1), t="Refuse")
        assert _get_customize_key(c) == "Refuse"

    def test_filter_hides_matching(self):
        from waste_collection_schedule.collection import Collection
        from waste_collection_schedule.source_shell import Customize, filter_function
        from waste_collection_schedule.waste_types import GENERAL_WASTE

        c = Collection(date=datetime.date(2026, 1, 1), waste_type=GENERAL_WASTE)
        customize = {"general_waste": Customize("general_waste", show=False)}
        assert filter_function(c, customize) is False

    def test_filter_shows_when_not_hidden(self):
        from waste_collection_schedule.collection import Collection
        from waste_collection_schedule.source_shell import Customize, filter_function
        from waste_collection_schedule.waste_types import GENERAL_WASTE

        c = Collection(date=datetime.date(2026, 1, 1), waste_type=GENERAL_WASTE)
        customize = {"general_waste": Customize("general_waste", show=True)}
        assert filter_function(c, customize) is True

    def test_filter_shows_when_no_customize(self):
        from waste_collection_schedule.collection import Collection
        from waste_collection_schedule.source_shell import filter_function
        from waste_collection_schedule.waste_types import GENERAL_WASTE

        c = Collection(date=datetime.date(2026, 1, 1), waste_type=GENERAL_WASTE)
        assert filter_function(c, {}) is True

    def test_customize_applies_alias(self):
        from waste_collection_schedule.collection import Collection
        from waste_collection_schedule.source_shell import (
            Customize,
            customize_function,
        )
        from waste_collection_schedule.waste_types import GENERAL_WASTE

        c = Collection(date=datetime.date(2026, 1, 1), waste_type=GENERAL_WASTE)
        customize = {"general_waste": Customize("general_waste", alias="Bin Day")}
        customize_function(c, customize)
        assert c.type == "Bin Day"

    def test_customize_applies_icon(self):
        from waste_collection_schedule.collection import Collection
        from waste_collection_schedule.source_shell import (
            Customize,
            customize_function,
        )
        from waste_collection_schedule.waste_types import GENERAL_WASTE

        c = Collection(date=datetime.date(2026, 1, 1), waste_type=GENERAL_WASTE)
        customize = {"general_waste": Customize("general_waste", icon="mdi:custom-bin")}
        customize_function(c, customize)
        assert c.icon == "mdi:custom-bin"

    def test_customize_applies_picture(self):
        from waste_collection_schedule.collection import Collection
        from waste_collection_schedule.source_shell import (
            Customize,
            customize_function,
        )
        from waste_collection_schedule.waste_types import GENERAL_WASTE

        c = Collection(date=datetime.date(2026, 1, 1), waste_type=GENERAL_WASTE)
        customize = {
            "general_waste": Customize(
                "general_waste", picture="https://example.com/bin.jpg"
            )
        }
        customize_function(c, customize)
        assert c.picture == "https://example.com/bin.jpg"

    def test_customize_no_match_leaves_unchanged(self):
        from waste_collection_schedule.collection import Collection
        from waste_collection_schedule.source_shell import (
            Customize,
            customize_function,
        )
        from waste_collection_schedule.waste_types import GENERAL_WASTE

        c = Collection(date=datetime.date(2026, 1, 1), waste_type=GENERAL_WASTE)
        customize = {"recyclables": Customize("recyclables", alias="Recycle")}
        customize_function(c, customize)
        assert c.type == "General Waste"  # unchanged

    def test_customize_legacy_by_display_string(self):
        from waste_collection_schedule.collection import LegacyCollection
        from waste_collection_schedule.source_shell import (
            Customize,
            customize_function,
        )

        c = LegacyCollection(date=datetime.date(2026, 1, 1), t="Refuse")
        customize = {"Refuse": Customize("Refuse", alias="General Bin")}
        customize_function(c, customize)
        assert c.type == "General Bin"

    def test_day_offset(self):
        from waste_collection_schedule.collection import Collection
        from waste_collection_schedule.source_shell import apply_day_offset
        from waste_collection_schedule.waste_types import GENERAL_WASTE

        c = Collection(date=datetime.date(2026, 1, 1), waste_type=GENERAL_WASTE)
        apply_day_offset(c, 3)
        assert c.date == datetime.date(2026, 1, 4)

    def test_day_offset_negative(self):
        from waste_collection_schedule.collection import Collection
        from waste_collection_schedule.source_shell import apply_day_offset
        from waste_collection_schedule.waste_types import GENERAL_WASTE

        c = Collection(date=datetime.date(2026, 1, 10), waste_type=GENERAL_WASTE)
        apply_day_offset(c, -2)
        assert c.date == datetime.date(2026, 1, 8)


class TestSourceShellDedicatedCalendars:
    """Customize dedicated calendar settings."""

    def test_dedicated_calendar_types(self):
        from waste_collection_schedule.source_shell import Customize, SourceShell

        customize = {
            "general_waste": Customize(
                "general_waste", show=True, use_dedicated_calendar=True
            ),
            "recyclables": Customize(
                "recyclables", show=True, use_dedicated_calendar=False
            ),
        }
        shell = SourceShell(
            source=MagicMock(),
            customize=customize,
            title="Test",
            description="",
            url=None,
            calendar_title=None,
            unique_id="test",
            day_offset=0,
        )
        types = shell.get_dedicated_calendar_types()
        assert "general_waste" in types
        assert "recyclables" not in types

    def test_dedicated_calendar_title(self):
        from waste_collection_schedule.source_shell import Customize, SourceShell

        customize = {
            "general_waste": Customize(
                "general_waste",
                use_dedicated_calendar=True,
                dedicated_calendar_title="My Bins",
            ),
        }
        shell = SourceShell(
            source=MagicMock(),
            customize=customize,
            title="Test",
            description="",
            url=None,
            calendar_title=None,
            unique_id="test",
            day_offset=0,
        )
        assert shell.get_calendar_title_for_type("general_waste") == "My Bins"


# =====================================================================
# 6. Source validation — auto-discover and test new-style sources
# =====================================================================


def _discover_new_style_sources():
    """Find all new-style source modules (those with PARAMS)."""
    from pathlib import Path

    source_dir = Path(__file__).resolve().parent.parent / (
        "custom_components/waste_collection_schedule/waste_collection_schedule/source"
    )
    sources = []
    for py_file in source_dir.glob("*.py"):
        if py_file.stem == "__init__":
            continue
        try:
            module = __import__(
                f"waste_collection_schedule.source.{py_file.stem}",
                fromlist=["Source"],
            )
        except Exception:
            continue

        source_cls = getattr(module, "Source", None)
        if source_cls is None:
            continue
        if not getattr(source_cls, "PARAMS", None):
            continue
        sources.append((py_file.stem, source_cls))
    return sources


_NEW_STYLE_SOURCES = _discover_new_style_sources()


@pytest.mark.skipif(
    len(_NEW_STYLE_SOURCES) == 0,
    reason="No new-style sources discoverable (likely missing dependencies)",
)
class TestNewStyleSourceMetadata:
    """Validate metadata declarations on all discovered new-style sources."""

    @pytest.fixture(params=_NEW_STYLE_SOURCES, ids=[s[0] for s in _NEW_STYLE_SOURCES])
    def source_info(self, request):
        return request.param

    def test_has_title(self, source_info):
        name, cls = source_info
        assert getattr(cls, "TITLE", ""), f"{name}: missing TITLE"

    def test_has_country(self, source_info):
        name, cls = source_info
        assert getattr(cls, "COUNTRY", ""), f"{name}: missing COUNTRY"

    def test_has_url(self, source_info):
        name, cls = source_info
        assert getattr(cls, "URL", ""), f"{name}: missing URL"

    def test_has_waste_types(self, source_info):
        name, cls = source_info
        wt = getattr(cls, "WASTE_TYPES", [])
        assert len(wt) > 0, f"{name}: WASTE_TYPES is empty"

    def test_waste_types_are_valid(self, source_info):
        from waste_collection_schedule.waste_types import WasteType

        name, cls = source_info
        for wt in cls.WASTE_TYPES:
            assert isinstance(wt, WasteType), f"{name}: {wt} is not a WasteType"

    def test_params_are_config_params(self, source_info):
        from waste_collection_schedule.config_params import ConfigParam

        name, cls = source_info
        for p in cls.PARAMS:
            assert isinstance(p, ConfigParam), f"{name}: {p} is not a ConfigParam"

    def test_params_fields_match_init(self, source_info):
        """PARAMS field names must match __init__ parameter names.

        Sources that rely on BaseSource.__init__(**kwargs) instead of declaring
        their own __init__ accept exactly the PARAMS fields as keyword args, so
        the check is vacuously satisfied for them.
        """
        import inspect

        name, cls = source_info
        signature = inspect.signature(cls.__init__)
        # A source using the inherited base __init__ exposes only **kwargs.
        if any(
            p.kind is inspect.Parameter.VAR_KEYWORD
            for p in signature.parameters.values()
        ):
            return
        init_params = set(signature.parameters.keys()) - {"self"}
        param_fields = set()
        for p in cls.PARAMS:
            param_fields.update(p.fields.keys())
        assert param_fields == init_params, (
            f"{name}: PARAMS fields {param_fields} don't match "
            f"__init__ params {init_params}"
        )

    def test_has_test_cases(self, source_info):
        name, cls = source_info
        tc = getattr(cls, "TEST_CASES", {})
        assert len(tc) > 0, f"{name}: no TEST_CASES defined"

    def test_classify_or_transformer_is_implemented(self, source_info):
        """Source must either declare a transformer or override classify()."""
        from waste_collection_schedule.base_source import BaseSource

        name, cls = source_info
        has_transform = getattr(cls, "transform", None) is not None
        has_classify = cls.classify is not BaseSource.classify
        assert has_transform or has_classify, (
            f"{name}: must declare a transform or implement classify()"
        )


@pytest.mark.skipif(
    len(_NEW_STYLE_SOURCES) == 0,
    reason="No new-style sources discoverable (likely missing dependencies)",
)
@pytest.mark.live
class TestNewStyleSourceTestCases:
    """Run each new-style source's TEST_CASES through the full pipeline.

    This exercises: retrieve → parse → classify → Collection for each
    test case, validating every step produces the correct types.

    Marked ``live`` because it fetches from real provider endpoints, so it is
    excluded from the gating CI run (``-m "not live"``) to keep CI deterministic
    and offline. An offline fixture-replay harness will supersede the live
    fetch; run locally with ``-m live`` against real providers when needed.
    """

    @staticmethod
    def _get_test_cases():
        cases = []
        for name, cls in _NEW_STYLE_SOURCES:
            for tc_name, tc_args in getattr(cls, "TEST_CASES", {}).items():
                cases.append((name, cls, tc_name, tc_args))
        return cases

    _CASES = _get_test_cases()

    @pytest.fixture(params=_CASES, ids=[f"{c[0]}::{c[2]}" for c in _CASES])
    def test_case(self, request):
        return request.param

    def test_fetch_returns_collections(self, test_case):
        """Full pipeline: instantiate → fetch → validate output types."""
        from waste_collection_schedule.collection import Collection

        name, cls, tc_name, tc_args = test_case
        source = cls(**tc_args)
        results = source.fetch()

        assert isinstance(results, list), f"{name}::{tc_name}: fetch() must return list"

        for i, r in enumerate(results):
            assert isinstance(r, Collection), (
                f"{name}::{tc_name}: result[{i}] is {type(r).__name__}, "
                f"expected Collection"
            )
            assert isinstance(r.date, datetime.date), (
                f"{name}::{tc_name}: result[{i}].date is {type(r.date).__name__}"
            )
            assert r.type, f"{name}::{tc_name}: result[{i}].type is empty"
            assert r.icon, f"{name}::{tc_name}: result[{i}].icon is empty"
            assert r.waste_type is not None, (
                f"{name}::{tc_name}: result[{i}].waste_type is None"
            )

    def test_fetch_returns_non_empty(self, test_case):
        """Test cases should return at least one collection."""
        name, cls, tc_name, tc_args = test_case
        source = cls(**tc_args)
        results = source.fetch()
        assert len(results) > 0, (
            f"{name}::{tc_name}: fetch() returned empty — "
            f"source may be down or test case invalid"
        )

    def test_waste_types_are_declared(self, test_case):
        """All waste types returned by fetch() should be in WASTE_TYPES."""
        name, cls, tc_name, tc_args = test_case
        declared = {wt.id for wt in getattr(cls, "WASTE_TYPES", [])}
        if not declared:
            pytest.skip(f"{name}: no WASTE_TYPES declared")

        source = cls(**tc_args)
        results = source.fetch()
        returned = {r.waste_type.id for r in results}
        # `preserved:` types are intentional: the multilingual resolver keeps an
        # unmapped label verbatim (never collapsing it to OTHER), so it is
        # legitimately absent from the declared set. Only flag other types.
        undeclared = {
            wid for wid in (returned - declared) if not wid.startswith("preserved:")
        }
        assert not undeclared, (
            f"{name}::{tc_name}: returned undeclared waste types: {undeclared}"
        )
