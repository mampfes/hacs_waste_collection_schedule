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

import calendar  # noqa: E402, F401, I001 — must import stdlib calendar FIRST
import datetime
import os
import sys
from dataclasses import FrozenInstanceError
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
            assert wt.id, f"WasteType missing id"
            assert wt.icon, f"{wt.id} missing icon"
            assert wt.color, f"{wt.id} missing color"
            assert "en" in wt.names, f"{wt.id} missing English name"

    def test_all_ids_unique(self):
        from waste_collection_schedule.waste_types import ALL_TYPES

        ids = [wt.id for wt in ALL_TYPES]
        assert len(ids) == len(set(ids)), "Duplicate WasteType ids"


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


class TestParsers:
    """parsers.json, parsers.text, parsers.html."""

    def _mock_response(self, text, json_data=None):
        resp = MagicMock()
        resp.text = text
        resp.json.return_value = json_data
        return resp

    def test_json_parser(self):
        from waste_collection_schedule.parsers import json

        data = [{"date": "2026-01-01", "type": "bin"}]
        resp = self._mock_response("", json_data=data)
        # Parsers take (self, response) — when called standalone, pass a dummy self
        assert json(None, resp) == data

    def test_text_parser(self):
        from waste_collection_schedule.parsers import text

        resp = self._mock_response("hello world")
        assert text(None, resp) == "hello world"

    def test_html_parser(self):
        from waste_collection_schedule.parsers import html

        resp = self._mock_response("<html><body><p>test</p></body></html>")
        soup = html(None, resp)
        assert soup.find("p").text == "test"

    def test_ics_parser_returns_date_summary_tuples(self):
        from waste_collection_schedule.parsers import ics

        resp = MagicMock()
        resp.text = "BEGIN:VCALENDAR\nEND:VCALENDAR"
        expected = [(datetime.date(2026, 1, 15), "General Waste")]

        with patch(
            "waste_collection_schedule.service.ICS.ICS.convert", return_value=expected
        ):
            result = ics(None, resp)
            assert result == expected


class TestRetrievers:
    """retrievers.http_get/post (curl_cffi) and legacy_http_get/post (plain requests)."""

    def test_http_get_uses_cffi_session(self):
        from waste_collection_schedule.retrievers import http_get

        source = MagicMock()
        source.API_URL = "https://example.com/api"
        source._params = {"key": "val"}
        source._headers = {"X-Custom": "yes"}
        source.TIMEOUT = 15

        mock_session = MagicMock()
        with patch(
            "waste_collection_schedule.retrievers._cffi_requests.Session",
            return_value=mock_session,
        ) as mock_session_cls:
            http_get(source)
            mock_session_cls.assert_called_once_with(impersonate="chrome")
            mock_session.get.assert_called_once_with(
                "https://example.com/api",
                params={"key": "val"},
                headers={"X-Custom": "yes"},
                timeout=15,
            )

    def test_http_post_uses_cffi_session(self):
        from waste_collection_schedule.retrievers import http_post

        source = MagicMock()
        source.API_URL = "https://example.com/api"
        source._params = None
        source._data = "body"
        source._json = None
        source._headers = None
        source.TIMEOUT = 30

        mock_session = MagicMock()
        with patch(
            "waste_collection_schedule.retrievers._cffi_requests.Session",
            return_value=mock_session,
        ) as mock_session_cls:
            http_post(source)
            mock_session_cls.assert_called_once_with(impersonate="chrome")
            mock_session.post.assert_called_once_with(
                "https://example.com/api",
                params=None,
                data="body",
                json=None,
                headers=None,
                timeout=30,
            )

    def test_legacy_http_get_uses_plain_requests(self):
        from waste_collection_schedule.retrievers import legacy_http_get

        source = MagicMock()
        source.API_URL = "https://example.com/api"
        source._params = {"key": "val"}
        source._headers = None
        source.TIMEOUT = 30

        with patch("waste_collection_schedule.retrievers._plain_requests") as mock_req:
            legacy_http_get(source)
            mock_req.get.assert_called_once_with(
                "https://example.com/api",
                params={"key": "val"},
                headers=None,
                timeout=30,
            )

    def test_legacy_http_post_uses_plain_requests(self):
        from waste_collection_schedule.retrievers import legacy_http_post

        source = MagicMock()
        source.API_URL = "https://example.com/api"
        source._params = None
        source._data = "body"
        source._json = None
        source._headers = None
        source.TIMEOUT = 30

        with patch("waste_collection_schedule.retrievers._plain_requests") as mock_req:
            legacy_http_post(source)
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

        p = address(city="city")
        assert "street" in p.fields
        assert "house_number" in p.fields
        assert "postcode" in p.fields
        assert "city" in p.fields

    def test_municipality(self):
        from waste_collection_schedule.config_params import municipality

        p = municipality(district="district")
        assert "municipality" in p.fields
        assert "district" in p.fields

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

            def retrieve(self):
                return MagicMock()  # mock response

            def parse(self, response):
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

            def retrieve(self):
                call_log.append("custom_retrieve")
                return MagicMock()

            def parse(self, response):
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

            def retrieve(self):
                return "raw,csv,data"

            def parse(self, response):
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

            def retrieve(self):
                return MagicMock()

            def parse(self, response):
                return [{"date": "10.04.2026"}]

            def classify(self, record):
                date = self.parse_date(record["date"])
                return Collection(date=date, waste_type=GENERAL_WASTE)

        results = CustomSource().fetch()
        assert results[0].date == datetime.date(2026, 4, 10)

    def test_classify_type_matches_type_map(self):
        """_classify_type does case-insensitive TYPE_MAP lookup."""
        from waste_collection_schedule.base_source import BaseSource
        from waste_collection_schedule.waste_types import GENERAL_WASTE, RECYCLABLES

        class TestSource(BaseSource):
            TYPE_MAP = {"general": GENERAL_WASTE, "recycling": RECYCLABLES}

        source = TestSource()
        assert source._classify_type("general") is GENERAL_WASTE
        assert source._classify_type("General") is GENERAL_WASTE
        assert source._classify_type("  RECYCLING  ") is RECYCLABLES

    def test_classify_type_falls_back_to_other(self):
        """_classify_type returns OTHER for unrecognised strings."""
        from waste_collection_schedule.base_source import BaseSource
        from waste_collection_schedule.waste_types import OTHER

        class TestSource(BaseSource):
            TYPE_MAP = {"general": OTHER}

        source = TestSource()
        assert source._classify_type("unknown bin") is OTHER

    def test_classify_type_empty_type_map(self):
        """_classify_type returns OTHER when TYPE_MAP is empty."""
        from waste_collection_schedule.base_source import BaseSource
        from waste_collection_schedule.waste_types import OTHER

        source = BaseSource()
        assert source._classify_type("anything") is OTHER


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
        "custom_components/waste_collection_schedule"
        "/waste_collection_schedule/source"
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
        """PARAMS field names must match __init__ parameter names."""
        import inspect

        name, cls = source_info
        init_params = set(inspect.signature(cls.__init__).parameters.keys()) - {"self"}
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

    def test_classify_is_implemented(self, source_info):
        """Source must override classify()."""
        from waste_collection_schedule.base_source import BaseSource

        name, cls = source_info
        assert (
            cls.classify is not BaseSource.classify
        ), f"{name}: classify() not implemented"


@pytest.mark.skipif(
    len(_NEW_STYLE_SOURCES) == 0,
    reason="No new-style sources discoverable (likely missing dependencies)",
)
class TestNewStyleSourceTestCases:
    """Run each new-style source's TEST_CASES through the full pipeline.

    This exercises: retrieve → parse → classify → Collection for each
    test case, validating every step produces the correct types.
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
            assert isinstance(
                r.date, datetime.date
            ), f"{name}::{tc_name}: result[{i}].date is {type(r.date).__name__}"
            assert r.type, f"{name}::{tc_name}: result[{i}].type is empty"
            assert r.icon, f"{name}::{tc_name}: result[{i}].icon is empty"
            assert (
                r.waste_type is not None
            ), f"{name}::{tc_name}: result[{i}].waste_type is None"

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
        declared = set(wt.id for wt in getattr(cls, "WASTE_TYPES", []))
        if not declared:
            pytest.skip(f"{name}: no WASTE_TYPES declared")

        source = cls(**tc_args)
        results = source.fetch()
        returned = set(r.waste_type.id for r in results)
        undeclared = returned - declared
        assert (
            not undeclared
        ), f"{name}::{tc_name}: returned undeclared waste types: {undeclared}"
