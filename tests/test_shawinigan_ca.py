"""Unit tests for Shawinigan waste collection schedule source."""

import os
import sys
from datetime import date, datetime, timedelta
from unittest.mock import patch

import pytest

from custom_components.waste_collection_schedule.waste_collection_schedule.source import (
    shawinigan_ca,
)

# Add project root to path
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), ".")))


class TestShawiniganMetadata:
    """Test module metadata"""

    def test_title_exists(self):
        """Test that TITLE is defined"""
        assert hasattr(shawinigan_ca, "TITLE")
        assert shawinigan_ca.TITLE == "Shawinigan"

    def test_description_exists(self):
        """Test that DESCRIPTION is defined"""
        assert hasattr(shawinigan_ca, "DESCRIPTION")
        assert len(shawinigan_ca.DESCRIPTION) > 0

    def test_url_exists(self):
        """Test that URL is defined"""
        assert hasattr(shawinigan_ca, "URL")
        assert shawinigan_ca.URL.startswith("https://")

    def test_country_exists(self):
        """Test that COUNTRY is defined"""
        assert hasattr(shawinigan_ca, "COUNTRY")
        assert shawinigan_ca.COUNTRY == "CA"

    def test_test_cases_defined(self):
        """Test that TEST_CASES are defined"""
        assert hasattr(shawinigan_ca, "TEST_CASES")
        assert isinstance(shawinigan_ca.TEST_CASES, dict)
        assert len(shawinigan_ca.TEST_CASES) > 0

    def test_layers_map_defined(self):
        """Test that LAYERS map is defined"""
        assert hasattr(shawinigan_ca, "LAYERS")
        assert 0 in shawinigan_ca.LAYERS  # Recyclage
        assert 1 in shawinigan_ca.LAYERS  # Ordures
        assert 2 in shawinigan_ca.LAYERS  # Sapin de Noël
        assert 3 in shawinigan_ca.LAYERS  # Collecte de feuilles
        assert 4 in shawinigan_ca.LAYERS  # Compost


class TestSourceInstantiation:
    """Test Source class instantiation"""

    def test_source_init_with_address(self):
        """Test Source can be instantiated with address"""
        source = shawinigan_ca.Source(address="123 Main St, Shawinigan, QC")
        assert source._address == "123 Main St, Shawinigan, QC"

    def test_source_init_strips_whitespace(self):
        """Test that address is stripped of whitespace"""
        source = shawinigan_ca.Source(address="  456 Oak Ave  ")
        assert source._address == "456 Oak Ave"

    def test_all_test_cases_instantiate(self):
        """Test that all TEST_CASES can create a Source"""
        for test_name, params in shawinigan_ca.TEST_CASES.items():
            source = shawinigan_ca.Source(**params)
            assert source is not None
            assert hasattr(source, "fetch")


class TestWasteTypeMapping:
    """Test waste type icon mapping"""

    def test_layer_0_recyclage(self):
        """Test Layer 0 is recyclage with correct icon"""
        assert shawinigan_ca.LAYERS[0]["type"] == "RECYCLAGE"
        assert shawinigan_ca.LAYERS[0]["icon"] == "mdi:recycle"

    def test_layer_1_ordures(self):
        """Test Layer 1 is ordures with correct icon"""
        assert shawinigan_ca.LAYERS[1]["type"] == "ORDURES"
        assert shawinigan_ca.LAYERS[1]["icon"] == "mdi:trash-can"

    def test_layer_2_sapin(self):
        """Test Layer 2 is Sapin (Christmas tree) with correct icon"""
        assert shawinigan_ca.LAYERS[2]["type"] == "SAPIN"
        assert shawinigan_ca.LAYERS[2]["icon"] == "mdi:pine-tree"

    def test_layer_3_feuilles(self):
        """Test Layer 3 is Feuilles (leaf pickup) with correct icon"""
        assert shawinigan_ca.LAYERS[3]["type"] == "FEUILLES"
        assert shawinigan_ca.LAYERS[3]["icon"] == "mdi:leaf-maple"

    def test_layer_4_compost(self):
        """Test Layer 4 is compost with correct icon"""
        assert shawinigan_ca.LAYERS[4]["type"] == "COMPOST"
        assert shawinigan_ca.LAYERS[4]["icon"] == "mdi:leaf"


class TestFetchMethod:
    """Test fetch() method with mocked data"""

    @patch(
        "custom_components.waste_collection_schedule.waste_collection_schedule.source.shawinigan_ca.geocode"
    )
    @patch(
        "custom_components.waste_collection_schedule.waste_collection_schedule.source.shawinigan_ca.query_feature_layer"
    )
    def test_fetch_returns_collection_list(self, mock_query, mock_geocode):
        """Test that fetch returns a list of Collections"""
        # Mock geocode to return coordinates
        mock_geocode.return_value = {"x": -8096727.38, "y": 5865698.33}

        # Mock query responses for layers 0, 1, 4 - with dates in valid range
        def query_side_effect(url, **kwargs):
            if "/0" in url:  # Recyclage
                return [
                    {
                        "DISTRICTID": "S2",
                        "SCHEDULE": "0001000",
                        "SCHEDULETYPE": "2 Week",
                        "NAME": "Wednesday",
                    }
                ]
            elif "/1" in url:  # Ordures
                # Use dates within the next year from today
                return [
                    {
                        "DISTRICTID": "S2",
                        "SCHEDULE": "2026-05-13,2026-05-27,2026-06-10",
                        "SCHEDULETYPE": "Irregularly",
                        "NAME": "Wednesday",
                    }
                ]
            elif "/4" in url:  # Compost
                return []
            elif "/6" in url:  # Holidays
                return []
            return []

        mock_query.side_effect = query_side_effect

        source = shawinigan_ca.Source(address="test address")
        collections = source.fetch()

        assert isinstance(collections, list)
        assert len(collections) > 0

    @patch(
        "custom_components.waste_collection_schedule.waste_collection_schedule.source.shawinigan_ca.geocode"
    )
    @patch(
        "custom_components.waste_collection_schedule.waste_collection_schedule.source.shawinigan_ca.query_feature_layer"
    )
    def test_fetch_collection_has_required_fields(self, mock_query, mock_geocode):
        """Test that Collection objects have required fields"""
        mock_geocode.return_value = {"x": -8096727.38, "y": 5865698.33}

        def query_side_effect(url, **kwargs):
            if "/1" in url:  # Ordures
                return [
                    {
                        "DISTRICTID": "S2",
                        "SCHEDULE": "2026-05-13,2026-05-27",
                        "SCHEDULETYPE": "Irregularly",
                        "NAME": "Wednesday",
                    }
                ]
            elif "/6" in url:  # Holidays
                return []
            return []

        mock_query.side_effect = query_side_effect

        source = shawinigan_ca.Source(address="test")
        collections = source.fetch()

        assert len(collections) >= 1
        collection = collections[0]
        assert hasattr(collection, "date")
        assert hasattr(collection, "type")
        assert hasattr(collection, "icon")
        assert isinstance(collection.date, date)

    @patch(
        "custom_components.waste_collection_schedule.waste_collection_schedule.source.shawinigan_ca.geocode"
    )
    def test_fetch_with_geocode_error(self, mock_geocode):
        """Test fetch raises exception when geocoding fails"""
        from waste_collection_schedule.exceptions import SourceArgumentNotFound
        from waste_collection_schedule.service.ArcGis import ArcGisError

        mock_geocode.side_effect = ArcGisError("Geocode failed")

        source = shawinigan_ca.Source(address="nonexistent address")

        with pytest.raises(SourceArgumentNotFound):
            source.fetch()

    @patch(
        "custom_components.waste_collection_schedule.waste_collection_schedule.source.shawinigan_ca.geocode"
    )
    @patch(
        "custom_components.waste_collection_schedule.waste_collection_schedule.source.shawinigan_ca.query_feature_layer"
    )
    def test_fetch_with_no_results(self, mock_query, mock_geocode):
        """Test fetch raises exception when no data returned"""
        from waste_collection_schedule.exceptions import SourceArgumentNotFound

        mock_geocode.return_value = {"x": -8096727.38, "y": 5865698.33}
        mock_query.return_value = []

        source = shawinigan_ca.Source(address="test")

        with pytest.raises(SourceArgumentNotFound):
            source.fetch()


class TestScheduleParsing:
    """Test schedule parsing logic"""

    @patch(
        "custom_components.waste_collection_schedule.waste_collection_schedule.source.shawinigan_ca.geocode"
    )
    @patch(
        "custom_components.waste_collection_schedule.waste_collection_schedule.source.shawinigan_ca.query_feature_layer"
    )
    def test_parse_irregular_schedule(self, mock_query, mock_geocode):
        """Test parsing irregularly scheduled dates"""
        mock_geocode.return_value = {"x": -8096727.38, "y": 5865698.33}

        today = date.today()
        d1 = today + timedelta(days=7)
        d2 = today + timedelta(days=21)
        d3 = today + timedelta(days=35)
        schedule = f"{d1},{d2},{d3}"

        def query_side_effect(url, **kwargs):
            if "/1" in url:  # Ordures
                return [
                    {
                        "DISTRICTID": "S2",
                        "SCHEDULE": schedule,
                        "SCHEDULETYPE": "Irregularly",
                        "NAME": "Friday",
                    }
                ]
            elif "/6" in url:  # Holidays
                return []
            return []

        mock_query.side_effect = query_side_effect

        source = shawinigan_ca.Source(address="test")
        collections = source.fetch()

        dates = {c.date for c in collections}
        assert d1 in dates
        assert d2 in dates
        assert d3 in dates

    def test_parse_schedule_irregular(self):
        """Test _parse_schedule with irregular schedule"""
        source = shawinigan_ca.Source(address="test")

        today = date.today()
        d1 = today + timedelta(days=7)
        d2 = today + timedelta(days=21)
        d3 = today + timedelta(days=35)
        schedule = f"{d1},{d2},{d3}"

        dates = source._parse_schedule(
            schedule,
            "irregularly",
            "Friday",
            today,
            today + timedelta(days=365),
        )

        assert d1 in dates
        assert d2 in dates
        assert d3 in dates


class TestBiweeklyCalibration:
    """Regression tests for bi-weekly anchor calibration.

    RECYCLAGE is bi-weekly and alternates with ORDURES on the SAME weekday
    (mercredi / Wednesday in Shawinigan).  The code must pick the sequence
    that does NOT overlap with the explicit ORDURES dates.
    """

    def test_biweekly_picks_non_overlapping_sequence(self):
        """RECYCLAGE sequence must not overlap with ORDURES explicit dates."""
        # Wednesday = weekday 2 in Python (0=Monday)
        # ORDURES: Apr 29, May 13, May 27  → even Wednesdays from today
        # RECYCLAGE expected: May 6, May 20, Jun 3  → odd Wednesdays
        ordures_dates = {date(2026, 4, 29), date(
            2026, 5, 13), date(2026, 5, 27)}
        exclude = {2: ordures_dates}  # weekday 2 = Wednesday

        # Start from April 29 (a Wednesday itself → anchor_a = Apr 29)
        dates = shawinigan_ca._parse_schedule(
            "0001000",
            "2 week",
            "mercredi",
            date(2026, 4, 29),
            date(2026, 6, 30),
            exclude_dates=exclude,
        )

        date_set = set(dates)
        # Should NOT overlap with ORDURES
        assert (
            not date_set & ordures_dates
        ), "RECYCLAGE must not share dates with ORDURES"
        # Should contain the expected Shawinigan dates
        assert date(2026, 5, 6) in date_set
        assert date(2026, 5, 20) in date_set
        assert date(2026, 6, 3) in date_set

    def test_biweekly_fallback_without_exclude_data(self):
        """Without calibration data the code must still return a bi-weekly sequence."""
        dates = shawinigan_ca._parse_schedule(
            "0001000",
            "2 week",
            "Wednesday",
            date(2026, 5, 1),
            date(2026, 6, 30),
            exclude_dates=None,
        )
        assert len(dates) >= 3
        # Consecutive dates must be 14 days apart
        sorted_dates = sorted(dates)
        gaps = {
            (sorted_dates[i + 1] - sorted_dates[i]).days
            for i in range(len(sorted_dates) - 1)
        }
        assert gaps == {14}

    def test_biweekly_alternates_with_ordures_in_fetch(self):
        """Integration-style: RECYCLAGE result must alternate with ORDURES.

        ORDURES dates are built relative to today so this test never expires.
        The RECYCLAGE SCHEDULE digit is chosen dynamically so it targets the
        opposite ISO-week parity from ORDURES, matching the city's own encoding.
        """
        import unittest.mock as mock

        today = date.today()
        # Find the most recent Wednesday on or before today
        days_since_wed = (today.weekday() - 2) % 7
        last_wed = today - timedelta(days=days_since_wed)
        # Three consecutive bi-weekly Wednesdays for ORDURES
        ordures_d1 = last_wed - timedelta(days=14)
        ordures_d2 = last_wed
        ordures_d3 = last_wed + timedelta(days=14)
        ordures_schedule = f"{ordures_d1},{ordures_d2},{ordures_d3}"
        # Choose RECYCLAGE digit with opposite ISO-week parity to ORDURES.
        # digit=1 → odd ISO weeks, digit=2 → even ISO weeks.
        last_wed_parity = last_wed.isocalendar().week % 2  # 1=odd, 0=even
        recyclage_digit = 2 if last_wed_parity == 1 else 1
        recyclage_schedule = f"000{recyclage_digit}000"  # pos 3 = Wednesday
        # RECYCLAGE+7 days from last_wed is always on the opposite parity
        expected_first_recyclage = last_wed + timedelta(days=7)

        with (
            mock.patch(
                "custom_components.waste_collection_schedule.waste_collection_schedule.source.shawinigan_ca.geocode"
            ) as mock_geocode,
            mock.patch(
                "custom_components.waste_collection_schedule.waste_collection_schedule.source.shawinigan_ca.query_feature_layer"
            ) as mock_query,
        ):
            mock_geocode.return_value = {"x": -8096727.38, "y": 5865698.33}

            def query_side_effect(url, **kwargs):
                if "/0" in url:  # RECYCLAGE – bi-weekly Wednesday
                    return [
                        {
                            "DISTRICTID": "S2",
                            "SCHEDULE": recyclage_schedule,
                            "SCHEDULETYPE": "2 Week",
                            "NAME": "mercredi",
                            "HOLIDAYFIELD": "IMPACTRECY",
                        }
                    ]
                if "/1" in url:  # ORDURES – explicit Wednesday dates
                    return [
                        {
                            "DISTRICTID": "SHS1",
                            "SCHEDULE": ordures_schedule,
                            "SCHEDULETYPE": "Irregularly",
                            "NAME": "mercredi",
                            "HOLIDAYFIELD": "IMPACTGARB",
                        }
                    ]
                if "/4" in url:  # COMPOST – no data
                    return []
                if "/6" in url:  # Holidays – no holidays
                    return []
                return []

            mock_query.side_effect = query_side_effect

            source = shawinigan_ca.Source(
                address="2230 Rue du Prieuré, Shawinigan")
            collections = source.fetch()

        recyclage = sorted(
            c.date for c in collections if c.type == "RECYCLAGE")
        ordures = sorted(c.date for c in collections if c.type == "ORDURES")

        # No date should appear in both
        assert not set(recyclage) & set(
            ordures
        ), "RECYCLAGE and ORDURES must not share dates"
        # All RECYCLAGE dates must be Wednesdays
        for d in recyclage:
            assert d.weekday() == 2, f"{d} is not a Wednesday"
        # The first future RECYCLAGE must be the Wednesday between the two future ORDURES
        assert recyclage[0] == expected_first_recyclage


class TestParseScheduleEdgeCases:
    """Edge cases for _parse_schedule."""

    def test_empty_schedule_returns_empty(self):
        """Empty SCHEDULE string must return no dates."""
        assert (
            shawinigan_ca._parse_schedule(
                "",
                "2 week",
                "mercredi",
                date.today(),
                date.today() + timedelta(days=90),
            )
            == []
        )

    def test_unknown_scheduletype_returns_empty(self):
        """An unrecognised SCHEDULETYPE must return no dates."""
        assert (
            shawinigan_ca._parse_schedule(
                "some_value",
                "monthly",
                "mercredi",
                date.today(),
                date.today() + timedelta(days=90),
            )
            == []
        )

    def test_weekly_schedule_7day_gaps(self):
        """A plain '1 week' pattern must produce dates 7 days apart."""
        today = date.today()
        dates = shawinigan_ca._parse_schedule(
            "0001000",
            "1 week",
            "mercredi",
            today,
            today + timedelta(days=60),
        )
        assert len(dates) >= 2
        sorted_dates = sorted(dates)
        gaps = {
            (sorted_dates[i + 1] - sorted_dates[i]).days
            for i in range(len(sorted_dates) - 1)
        }
        assert gaps == {7}

    def test_weekly_all_dates_are_correct_weekday(self):
        """Every date from a weekly schedule must fall on the named weekday."""
        today = date.today()
        dates = shawinigan_ca._parse_schedule(
            "0001000",
            "week",
            "lundi",
            today,
            today + timedelta(days=60),
        )
        for d in dates:
            assert d.weekday() == 0, f"{d} is not a Monday"

    def test_unknown_day_name_returns_empty(self):
        """An unrecognised day name must return no dates for weekly patterns."""
        today = date.today()
        assert (
            shawinigan_ca._parse_schedule(
                "0001000", "week", "funday", today, today + timedelta(days=60)
            )
            == []
        )


class TestHolidayHandling:
    """Regression tests for holiday attribute access and impact string parsing."""

    def test_holidays_read_flat_attrs_dict(self):
        """_get_holidays_by_field must handle flat attrs dicts (not nested)."""
        import unittest.mock as mock

        # query_feature_layer returns FLAT attrs dicts (ArcGis.py: line 143)
        sample_features = [
            {
                "HOLIDAYDATE": 1766620800000,  # Dec 25, 2025 UTC
                "IMPACTRECY": "OneDayFrwd",
                "IMPACTGARB": "OneDayFrwd",
                "IMPACTCOMP": "None",
            }
        ]

        with mock.patch(
            "custom_components.waste_collection_schedule.waste_collection_schedule.source.shawinigan_ca.query_feature_layer",
            return_value=sample_features,
        ):
            result = shawinigan_ca._get_holidays_by_field()

        # Should have entries for IMPACTRECY and IMPACTGARB
        assert "IMPACTRECY" in result, "IMPACTRECY holidays missing"
        assert "IMPACTGARB" in result, "IMPACTGARB holidays missing"
        assert "IMPACTCOMP" not in result, "IMPACTCOMP should be absent (value=None)"

        dec25 = date(2025, 12, 25)
        dec26 = date(2025, 12, 26)
        assert result["IMPACTRECY"].get(dec25) == dec26
        assert result["IMPACTGARB"].get(dec25) == dec26

    def test_holiday_impact_onedayfrwd_parsed(self):
        """'OneDayFrwd' must push the date forward by 1 day."""
        import unittest.mock as mock

        # Dec 25 2025 in epoch ms
        christmas_ms = 1766620800000

        with mock.patch(
            "custom_components.waste_collection_schedule.waste_collection_schedule.source.shawinigan_ca.query_feature_layer",
            return_value=[
                {
                    "HOLIDAYDATE": christmas_ms,
                    "IMPACTRECY": "OneDayFrwd",
                    "IMPACTGARB": "None",
                    "IMPACTCOMP": None,
                }
            ],
        ):
            result = shawinigan_ca._get_holidays_by_field()

        dec25 = date(2025, 12, 25)
        assert result["IMPACTRECY"][dec25] == date(2025, 12, 26)

    def test_holiday_impact_none_not_stored(self):
        """Impact value 'None' must NOT produce an entry in the result."""
        import unittest.mock as mock

        with mock.patch(
            "custom_components.waste_collection_schedule.waste_collection_schedule.source.shawinigan_ca.query_feature_layer",
            return_value=[
                {
                    "HOLIDAYDATE": 1766620800000,
                    "IMPACTRECY": "None",
                    "IMPACTGARB": "None",
                    "IMPACTCOMP": "None",
                }
            ],
        ):
            result = shawinigan_ca._get_holidays_by_field()

        assert result == {}, "No holidays expected when impact is None"

    def test_holiday_impact_onedayback_parsed(self):
        """'OneDayBack' must shift the collection date back by 1 day."""
        import unittest.mock as mock

        christmas_ms = 1766620800000  # Dec 25 2025

        with mock.patch(
            "custom_components.waste_collection_schedule.waste_collection_schedule.source.shawinigan_ca.query_feature_layer",
            return_value=[
                {
                    "HOLIDAYDATE": christmas_ms,
                    "IMPACTRECY": "OneDayBack",
                    "IMPACTGARB": "None",
                    "IMPACTCOMP": None,
                }
            ],
        ):
            result = shawinigan_ca._get_holidays_by_field()

        dec25 = date(2025, 12, 25)
        assert result["IMPACTRECY"][dec25] == date(2025, 12, 24)

    def test_holiday_impact_twodayfrwd_shifts_two_days(self):
        """'TwoDayFrwd' must push the collection date forward by 2 days (not 1)."""
        import unittest.mock as mock

        christmas_ms = 1766620800000  # Dec 25 2025

        with mock.patch(
            "custom_components.waste_collection_schedule.waste_collection_schedule.source.shawinigan_ca.query_feature_layer",
            return_value=[
                {
                    "HOLIDAYDATE": christmas_ms,
                    "IMPACTGARB": "TwoDayFrwd",
                }
            ],
        ):
            result = shawinigan_ca._get_holidays_by_field()

        dec25 = date(2025, 12, 25)
        assert result["IMPACTGARB"][dec25] == date(
            2025, 12, 27
        ), "TwoDayFrwd must shift +2 days, not +1"

    def test_holiday_impact_shift_forw_parsed(self):
        """'Shift Forw' (city synonym) must push the date forward by 1 day."""
        import unittest.mock as mock

        christmas_ms = 1766620800000  # Dec 25 2025

        with mock.patch(
            "custom_components.waste_collection_schedule.waste_collection_schedule.source.shawinigan_ca.query_feature_layer",
            return_value=[
                {
                    "HOLIDAYDATE": christmas_ms,
                    "IMPACTGARB": "Shift Forw",  # actual code returned by the API domain
                }
            ],
        ):
            result = shawinigan_ca._get_holidays_by_field()

        dec25 = date(2025, 12, 25)
        assert result["IMPACTGARB"][dec25] == date(
            2025, 12, 26
        ), "'Shift Forw' must be treated as +1 day"

    def test_holiday_impact_cancel_removes_collection(self):
        """'Cancel' must map the holiday date to None so the collection is skipped."""
        import unittest.mock as mock

        christmas_ms = 1766620800000  # Dec 25 2025

        with mock.patch(
            "custom_components.waste_collection_schedule.waste_collection_schedule.source.shawinigan_ca.query_feature_layer",
            return_value=[
                {
                    "HOLIDAYDATE": christmas_ms,
                    "IMPACTGARB": "Cancel",
                    "IMPACTRECY": "None",
                }
            ],
        ):
            result = shawinigan_ca._get_holidays_by_field()

        dec25 = date(2025, 12, 25)
        assert "IMPACTGARB" in result, "Cancel must still produce an entry"
        assert (
            result["IMPACTGARB"][dec25] is None
        ), "Cancel must map to None (collection removed)"
        assert "IMPACTRECY" not in result, "None must not produce an entry"

    def test_cancelled_collection_not_in_fetch_results(self):
        """A collection whose HOLIDAYFIELD maps to Cancel must not appear in fetch()."""
        base = date.today() + timedelta(days=30)
        base_ms = int(datetime(base.year, base.month,
                      base.day).timestamp() * 1000)

        def side_effect(url, **kwargs):
            tail = url.rstrip("/").split("/")[-1]
            if tail == "1":  # ORDURES on `base`
                return [
                    {
                        "SCHEDULE": str(base),
                        "SCHEDULETYPE": "Irregularly",
                        "NAME": "mercredi",
                        "HOLIDAYFIELD": "IMPACTGARB",
                    }
                ]
            if tail == "6":  # Holiday: ORDURES cancelled
                return [
                    {
                        "HOLIDAYDATE": base_ms,
                        "IMPACTGARB": "Cancel",
                        "IMPACTRECY": "None",
                    }
                ]
            return []

        with (
            patch(
                "custom_components.waste_collection_schedule.waste_collection_schedule.source.shawinigan_ca.geocode",
                return_value={"x": -8096727.38, "y": 5865698.33},
            ),
            patch(
                "custom_components.waste_collection_schedule.waste_collection_schedule.source.shawinigan_ca.query_feature_layer",
                side_effect=side_effect,
            ),
        ):
            source = shawinigan_ca.Source(address="test")
            # fetch() will raise SourceArgumentNotFound because all entries are cancelled
            from waste_collection_schedule.exceptions import SourceArgumentNotFound

            with pytest.raises(SourceArgumentNotFound):
                source.fetch()

    def test_arcgis_error_on_holidays_returns_empty(self):
        """ArcGisError while fetching holidays must return empty dict, not raise."""
        import unittest.mock as mock

        from waste_collection_schedule.service.ArcGis import ArcGisError

        with mock.patch(
            "custom_components.waste_collection_schedule.waste_collection_schedule.source.shawinigan_ca.query_feature_layer",
            side_effect=ArcGisError("network error"),
        ):
            result = shawinigan_ca._get_holidays_by_field()

        assert result == {}

    def test_missing_holidayfield_defaults_to_impactgarb(self):
        """When HOLIDAYFIELD is absent, the layer must default to IMPACTGARB."""
        import unittest.mock as mock

        today = date.today()
        future = today + timedelta(days=14)

        def query_side_effect(url, **kwargs):
            if "/1" in url:  # ORDURES – no HOLIDAYFIELD key
                return [
                    {
                        "DISTRICTID": "S1",
                        "SCHEDULE": str(future),
                        "SCHEDULETYPE": "Irregularly",
                        "NAME": "mercredi",
                    }
                ]  # no HOLIDAYFIELD
            if "/6" in url:
                return [
                    {
                        "HOLIDAYDATE": (
                            int(future.strftime("%s")) * 1000
                            if hasattr(future, "strftime")
                            else 0
                        ),
                        "IMPACTRECY": "None",
                        "IMPACTGARB": "OneDayFrwd",
                        "IMPACTCOMP": "None",
                    }
                ]
            return []

        with (
            mock.patch(
                "custom_components.waste_collection_schedule.waste_collection_schedule.source.shawinigan_ca.geocode",
                return_value={"x": -8096727.38, "y": 5865698.33},
            ),
            mock.patch(
                "custom_components.waste_collection_schedule.waste_collection_schedule.source.shawinigan_ca.query_feature_layer",
                side_effect=query_side_effect,
            ),
        ):
            source = shawinigan_ca.Source(address="test")
            # Should not raise
            collections = source.fetch()

        assert len(collections) >= 1

    def test_one_layer_arcgis_error_others_succeed(self):
        """If one collection layer raises ArcGisError, the other layers must still return results."""
        import unittest.mock as mock

        from waste_collection_schedule.service.ArcGis import ArcGisError

        today = date.today()
        future = today + timedelta(days=10)

        def query_side_effect(url, **kwargs):
            if "/0" in url:  # RECYCLAGE – raises
                raise ArcGisError("layer unavailable")
            if "/1" in url:  # ORDURES – succeeds
                return [
                    {
                        "DISTRICTID": "S1",
                        "SCHEDULE": str(future),
                        "SCHEDULETYPE": "Irregularly",
                        "NAME": "mercredi",
                        "HOLIDAYFIELD": "IMPACTGARB",
                    }
                ]
            if "/6" in url:
                return []
            return []

        with (
            mock.patch(
                "custom_components.waste_collection_schedule.waste_collection_schedule.source.shawinigan_ca.geocode",
                return_value={"x": -8096727.38, "y": 5865698.33},
            ),
            mock.patch(
                "custom_components.waste_collection_schedule.waste_collection_schedule.source.shawinigan_ca.query_feature_layer",
                side_effect=query_side_effect,
            ),
        ):
            source = shawinigan_ca.Source(address="test")
            collections = source.fetch()

        types = {c.type for c in collections}
        assert "ORDURES" in types
        assert "RECYCLAGE" not in types

    def test_holiday_applied_per_layer_field(self):
        """Each layer must use its own HOLIDAYFIELD to apply adjustments."""
        import unittest.mock as mock

        christmas_ms = 1766620800000

        def query_side_effect(url, **kwargs):
            if "/6" in url:  # Holidays layer
                return [
                    {
                        "HOLIDAYDATE": christmas_ms,
                        "IMPACTRECY": "OneDayFrwd",  # RECYCLAGE pushed +1
                        "IMPACTGARB": "None",  # ORDURES unchanged
                        "IMPACTCOMP": "None",
                    }
                ]
            if "/0" in url:  # RECYCLAGE on Dec 25
                return [
                    {
                        "DISTRICTID": "S2",
                        "SCHEDULE": "2025-12-25",
                        "SCHEDULETYPE": "Irregularly",
                        "NAME": "mercredi",
                        "HOLIDAYFIELD": "IMPACTRECY",
                    }
                ]
            if "/1" in url:  # ORDURES on Dec 25
                return [
                    {
                        "DISTRICTID": "SHS1",
                        "SCHEDULE": "2025-12-25",
                        "SCHEDULETYPE": "Irregularly",
                        "NAME": "mercredi",
                        "HOLIDAYFIELD": "IMPACTGARB",
                    }
                ]
            return []

        with (
            mock.patch(
                "custom_components.waste_collection_schedule.waste_collection_schedule.source.shawinigan_ca.geocode",
                return_value={"x": -8096727.38, "y": 5865698.33},
            ),
            mock.patch(
                "custom_components.waste_collection_schedule.waste_collection_schedule.source.shawinigan_ca.query_feature_layer",
                side_effect=query_side_effect,
            ),
        ):
            source = shawinigan_ca.Source(address="test")
            # Need today <= Dec 25 2025 for dates to be in range
            with mock.patch(
                "custom_components.waste_collection_schedule.waste_collection_schedule.source.shawinigan_ca.date"
            ) as mock_date:
                mock_date.today.return_value = date(2025, 12, 1)
                mock_date.side_effect = lambda *args, **kw: date(*args, **kw)
                collections = source.fetch()

        recyclage_dates = {
            c.date for c in collections if c.type == "RECYCLAGE"}
        ordures_dates = {c.date for c in collections if c.type == "ORDURES"}

        # RECYCLAGE (IMPACTRECY=OneDayFrwd): Dec 25 → Dec 26
        assert (
            date(2025, 12, 26) in recyclage_dates
        ), "RECYCLAGE must be shifted to Dec 26"
        assert date(2025, 12, 25) not in recyclage_dates

        # ORDURES (IMPACTGARB=None): stays Dec 25
        assert date(
            2025, 12, 25) in ordures_dates, "ORDURES must stay on Dec 25"

    def test_dynamic_impact_field_detection(self):
        """Unknown IMPACT* fields (e.g. IMPACTYARD) must be detected automatically.

        This covers the out_fields='*' + dynamic k.startswith('IMPACT') change.
        If a new collection type adds a new IMPACT field, it must be picked up
        without any code change.
        """
        import unittest.mock as mock

        christmas_ms = 1766620800000  # Dec 25 2025

        with mock.patch(
            "custom_components.waste_collection_schedule.waste_collection_schedule.source.shawinigan_ca.query_feature_layer",
            return_value=[
                {
                    "HOLIDAYDATE": christmas_ms,
                    "IMPACTYARD": "OneDayFrwd",  # new field, not in old hardcoded list
                    "IMPACTPAPE": "OneDayBack",  # another new field
                    "IMPACTRECY": "None",
                    "IMPACTGARB": "None",
                }
            ],
        ):
            result = shawinigan_ca._get_holidays_by_field()

        dec25 = date(2025, 12, 25)
        assert "IMPACTYARD" in result, "Dynamic IMPACTYARD must be detected"
        assert result["IMPACTYARD"][dec25] == date(2025, 12, 26)
        assert "IMPACTPAPE" in result, "Dynamic IMPACTPAPE must be detected"
        assert result["IMPACTPAPE"][dec25] == date(2025, 12, 24)
        assert "IMPACTRECY" not in result, "IMPACTRECY=None must not appear"
        assert "IMPACTGARB" not in result, "IMPACTGARB=None must not appear"

    def test_collection_layers_queried_with_wildcard_outfields(self):
        """query_feature_layer for collection layers must use out_fields='*'.

        This ensures all fields (including future ones) are always fetched.
        """
        import unittest.mock as mock

        calls = []

        def query_side_effect(url, **kwargs):
            calls.append((url, kwargs))
            if "/1" in url:
                today = date.today()
                return [
                    {
                        "SCHEDULE": str(today + timedelta(days=10)),
                        "SCHEDULETYPE": "Irregularly",
                        "NAME": "mercredi",
                        "HOLIDAYFIELD": "IMPACTGARB",
                    }
                ]
            return []

        with (
            mock.patch(
                "custom_components.waste_collection_schedule.waste_collection_schedule.source.shawinigan_ca.geocode",
                return_value={"x": -8096727.38, "y": 5865698.33},
            ),
            mock.patch(
                "custom_components.waste_collection_schedule.waste_collection_schedule.source.shawinigan_ca.query_feature_layer",
                side_effect=query_side_effect,
            ),
        ):
            source = shawinigan_ca.Source(address="test")
            source.fetch()

        collection_calls = [(url, kw) for url, kw in calls if "/6" not in url]
        for url, kw in collection_calls:
            assert (
                kw.get("out_fields") == "*"
            ), f"Layer {url} must use out_fields='*', got {kw.get('out_fields')!r}"


class TestSeasonalLayers:
    """Tests for seasonal layers: SAPIN (layer 2) and FEUILLES (layer 3)."""

    _MOCK_GEO = {"x": -8096727.38, "y": 5865698.33}
    _PATCH_GEO = (
        "custom_components.waste_collection_schedule"
        ".waste_collection_schedule.source.shawinigan_ca.geocode"
    )
    _PATCH_QFL = (
        "custom_components.waste_collection_schedule"
        ".waste_collection_schedule.source.shawinigan_ca.query_feature_layer"
    )

    def _future_dates(self, n=3, offset=30):
        """Return n comma-separated date strings starting offset days from today."""
        start = date.today() + timedelta(days=offset)
        return ",".join(str(start + timedelta(days=i)) for i in range(n))

    def _make_side_effect(self, layer_id: int, schedule: str, holiday_field: str):
        """Build a mock side-effect that returns data only for the given layer."""

        def side_effect(url, **kwargs):
            # Match exactly the layer we want to test
            tail = url.rstrip("/").split("/")[-1]
            if tail == str(layer_id):
                return [
                    {
                        "SCHEDULE": schedule,
                        "SCHEDULETYPE": "Irregularly",
                        "NAME": "mercredi",
                        "HOLIDAYFIELD": holiday_field,
                    }
                ]
            return []  # all other layers (including /6 holidays) return empty

        return side_effect

    def test_sapin_layer_returns_sapin_type(self):
        """Layer 2 features must produce SAPIN collection entries."""
        schedule = self._future_dates()
        with (
            patch(self._PATCH_GEO, return_value=self._MOCK_GEO),
            patch(
                self._PATCH_QFL,
                side_effect=self._make_side_effect(2, schedule, "IMPACTYARD"),
            ),
        ):
            source = shawinigan_ca.Source(address="test")
            collections = source.fetch()

        types = {c.type for c in collections}
        assert "SAPIN" in types, "Layer 2 must produce SAPIN entries"
        assert len([c for c in collections if c.type == "SAPIN"]) == 3

    def test_feuilles_layer_returns_feuilles_type(self):
        """Layer 3 features must produce FEUILLES collection entries."""
        schedule = self._future_dates(n=4, offset=60)
        with (
            patch(self._PATCH_GEO, return_value=self._MOCK_GEO),
            patch(
                self._PATCH_QFL,
                side_effect=self._make_side_effect(3, schedule, "IMPACTYARD"),
            ),
        ):
            source = shawinigan_ca.Source(address="test")
            collections = source.fetch()

        types = {c.type for c in collections}
        assert "FEUILLES" in types, "Layer 3 must produce FEUILLES entries"
        assert len([c for c in collections if c.type == "FEUILLES"]) == 4

    def test_sapin_icon_in_collections(self):
        """SAPIN entries must carry the mdi:pine-tree icon."""
        schedule = self._future_dates(n=2)
        with (
            patch(self._PATCH_GEO, return_value=self._MOCK_GEO),
            patch(
                self._PATCH_QFL,
                side_effect=self._make_side_effect(2, schedule, "IMPACTYARD"),
            ),
        ):
            source = shawinigan_ca.Source(address="test")
            collections = source.fetch()

        for c in collections:
            if c.type == "SAPIN":
                assert c.icon == "mdi:pine-tree"

    def test_feuilles_icon_in_collections(self):
        """FEUILLES entries must carry the mdi:leaf-maple icon."""
        schedule = self._future_dates(n=2, offset=60)
        with (
            patch(self._PATCH_GEO, return_value=self._MOCK_GEO),
            patch(
                self._PATCH_QFL,
                side_effect=self._make_side_effect(3, schedule, "IMPACTYARD"),
            ),
        ):
            source = shawinigan_ca.Source(address="test")
            collections = source.fetch()

        for c in collections:
            if c.type == "FEUILLES":
                assert c.icon == "mdi:leaf-maple"

    def test_sapin_absent_when_layer_returns_no_features(self):
        """If layer 2 returns no features, no SAPIN entry must appear."""
        sapin_schedule = self._future_dates()

        def side_effect(url, **kwargs):
            tail = url.rstrip("/").split("/")[-1]
            if tail == "1":  # ORDURES: keep something so fetch() doesn't raise
                return [
                    {
                        "SCHEDULE": sapin_schedule,
                        "SCHEDULETYPE": "Irregularly",
                        "NAME": "mercredi",
                        "HOLIDAYFIELD": "IMPACTGARB",
                    }
                ]
            return []  # layer 2 absent

        with (
            patch(self._PATCH_GEO, return_value=self._MOCK_GEO),
            patch(self._PATCH_QFL, side_effect=side_effect),
        ):
            source = shawinigan_ca.Source(address="test")
            collections = source.fetch()

        assert "SAPIN" not in {c.type for c in collections}

    def test_feuilles_absent_when_layer_returns_no_features(self):
        """If layer 3 returns no features, no FEUILLES entry must appear."""
        sapin_schedule = self._future_dates()

        def side_effect(url, **kwargs):
            tail = url.rstrip("/").split("/")[-1]
            if tail == "1":  # ORDURES: keep something so fetch() doesn't raise
                return [
                    {
                        "SCHEDULE": sapin_schedule,
                        "SCHEDULETYPE": "Irregularly",
                        "NAME": "mercredi",
                        "HOLIDAYFIELD": "IMPACTGARB",
                    }
                ]
            return []  # layer 3 absent

        with (
            patch(self._PATCH_GEO, return_value=self._MOCK_GEO),
            patch(self._PATCH_QFL, side_effect=side_effect),
        ):
            source = shawinigan_ca.Source(address="test")
            collections = source.fetch()

        assert "FEUILLES" not in {c.type for c in collections}

    def test_sapin_holiday_adjusted_via_impactyard(self):
        """SAPIN must use IMPACTYARD to apply holiday date shifts."""
        # Use a fixed base date in the far future to avoid expiry
        base = date.today() + timedelta(days=90)
        base_ms = int(datetime(base.year, base.month,
                      base.day).timestamp() * 1000)
        schedule_str = str(base)  # Sapin on that day

        def side_effect(url, **kwargs):
            tail = url.rstrip("/").split("/")[-1]
            if tail == "2":  # SAPIN
                return [
                    {
                        "SCHEDULE": schedule_str,
                        "SCHEDULETYPE": "Irregularly",
                        "NAME": "mercredi",
                        "HOLIDAYFIELD": "IMPACTYARD",
                    }
                ]
            if tail == "6":  # Holidays: base day shifted forward
                return [
                    {
                        "HOLIDAYDATE": base_ms,
                        "IMPACTYARD": "OneDayFrwd",
                        "IMPACTGARB": "None",
                        "IMPACTRECY": "None",
                    }
                ]
            return []

        with (
            patch(self._PATCH_GEO, return_value=self._MOCK_GEO),
            patch(self._PATCH_QFL, side_effect=side_effect),
        ):
            source = shawinigan_ca.Source(address="test")
            collections = source.fetch()

        sapin_dates = {c.date for c in collections if c.type == "SAPIN"}
        assert (
            base + timedelta(days=1) in sapin_dates
        ), "SAPIN must be shifted +1 day via IMPACTYARD"
        assert (
            base not in sapin_dates
        ), "Original SAPIN date must be replaced by shifted date"

    def test_feuilles_holiday_adjusted_via_impactyard(self):
        """FEUILLES must use IMPACTYARD to apply holiday date shifts."""
        base = date.today() + timedelta(days=120)
        base_ms = int(datetime(base.year, base.month,
                      base.day).timestamp() * 1000)
        schedule_str = str(base)

        def side_effect(url, **kwargs):
            tail = url.rstrip("/").split("/")[-1]
            if tail == "3":  # FEUILLES
                return [
                    {
                        "SCHEDULE": schedule_str,
                        "SCHEDULETYPE": "Irregularly",
                        "NAME": "mercredi",
                        "HOLIDAYFIELD": "IMPACTYARD",
                    }
                ]
            if tail == "6":  # Holidays: base day shifted back
                return [
                    {
                        "HOLIDAYDATE": base_ms,
                        "IMPACTYARD": "OneDayBack",
                        "IMPACTGARB": "None",
                        "IMPACTRECY": "None",
                    }
                ]
            return []

        with (
            patch(self._PATCH_GEO, return_value=self._MOCK_GEO),
            patch(self._PATCH_QFL, side_effect=side_effect),
        ):
            source = shawinigan_ca.Source(address="test")
            collections = source.fetch()

        feuilles_dates = {c.date for c in collections if c.type == "FEUILLES"}
        assert (
            base - timedelta(days=1) in feuilles_dates
        ), "FEUILLES must be shifted -1 day via IMPACTYARD"
        assert (
            base not in feuilles_dates
        ), "Original FEUILLES date must be replaced by shifted date"

    def _make_side_effect_with_descript(
        self, layer_id: int, schedule: str, holiday_field: str, descript: str
    ):
        """Like _make_side_effect but includes DESCRIPT field."""

        def side_effect(url, **kwargs):
            tail = url.rstrip("/").split("/")[-1]
            if tail == str(layer_id):
                return [
                    {
                        "SCHEDULE": schedule,
                        "SCHEDULETYPE": "Irregularly",
                        "NAME": "mercredi",
                        "HOLIDAYFIELD": holiday_field,
                        "DESCRIPT": descript,
                    }
                ]
            return []

        return side_effect

    def test_sapin_descript_propagated_to_collection_description(self):
        """DESCRIPT from layer 2 must appear as Collection.description."""
        schedule = self._future_dates(n=2)
        descript = "Inscription obligatoire avant le 9 janvier : https://www.shawinigan.ca/sapin"
        with (
            patch(self._PATCH_GEO, return_value=self._MOCK_GEO),
            patch(
                self._PATCH_QFL,
                side_effect=self._make_side_effect_with_descript(
                    2, schedule, "IMPACTYARD", descript
                ),
            ),
        ):
            source = shawinigan_ca.Source(address="test")
            collections = source.fetch()

        for c in collections:
            if c.type == "SAPIN":
                assert (
                    c.description == descript
                ), "SAPIN must carry DESCRIPT as description"

    def test_feuilles_descript_propagated_to_collection_description(self):
        """DESCRIPT from layer 3 must appear as Collection.description."""
        schedule = self._future_dates(n=2, offset=60)
        descript = "Automne 2026 : inscription obligatoire!"
        with (
            patch(self._PATCH_GEO, return_value=self._MOCK_GEO),
            patch(
                self._PATCH_QFL,
                side_effect=self._make_side_effect_with_descript(
                    3, schedule, "IMPACTYARD", descript
                ),
            ),
        ):
            source = shawinigan_ca.Source(address="test")
            collections = source.fetch()

        for c in collections:
            if c.type == "FEUILLES":
                assert (
                    c.description == descript
                ), "FEUILLES must carry DESCRIPT as description"

    def test_ordures_without_descript_has_no_description(self):
        """Layer 1 (ORDURES) without DESCRIPT must produce entries with no description."""
        schedule = self._future_dates(n=2)
        with (
            patch(self._PATCH_GEO, return_value=self._MOCK_GEO),
            patch(
                self._PATCH_QFL,
                side_effect=self._make_side_effect(1, schedule, "IMPACTGARB"),
            ),
        ):
            source = shawinigan_ca.Source(address="test")
            collections = source.fetch()

        for c in collections:
            if c.type == "ORDURES":
                assert (
                    c.description is None
                ), "ORDURES without DESCRIPT must have no description"
