"""Offline unit tests for the ``beachwood_oh_us`` source.

The cassette gates only prove the pipeline runs and yields well-formed
Collections; they do not pin which weekday a street resolves to, how a holiday
shifts it, or the PDF-typo repair. These tests do, without touching the
network: the PDF text layout is exercised through a literal fixture string and
the holiday rules through the pure ``_adjust`` helper.

Not in ``pytest.ini``'s ``python_files`` allowlist, so a bare ``pytest`` run
(and CI) does not collect it — matching the other per-source test files and
discussion #7252. Run it directly::

    pytest tests/test_beachwood_oh_us.py
"""

import datetime
import os
import sys

import pytest
from freezegun import freeze_time

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "custom_components",
        "waste_collection_schedule",
    ),
)

from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequiredWithSuggestions,
)
from waste_collection_schedule.response_shape import ResponseShapeError
from waste_collection_schedule.source import beachwood_oh_us as m

# A miniature of the real PDF's text layer: the three-line header repeats per
# page, one street name spans three lines, and there is one entry per weekday.
_PDF_TEXT = "\n".join(
    [
        "City of Beachwood",
        "Rubbish Pick Up Days",
        "5/9/2018",
        "Beacon Drive",
        "Monday",
        "Fairmount Boulevard (East bound from Sulgrave,",
        "and",
        "West bound to Richmond)",
        "Tuesday",
        "East Silsby Road",
        "Thursday",
        # page break — header repeats
        "City of Beachwood",
        "Rubbish Pick Up Days",
        "5/9/2018",
        "Fernwood Road",
        "Wednesday",
        "Woodside Lane",
        "Monday",
    ]
)


# The real PDF's Cedar Road block: the second section's entry is missing its
# opening parenthesis (a city typo). Both sections mean "Cedar Road".
_PDF_TEXT_CEDAR = "\n".join(
    [
        "City of Beachwood",
        "Rubbish Pick Up Days",
        "5/9/2018",
        "Cedar Road (East bound from Community to Richmond)",
        "Tuesday",
        "Cedar Road East bound from Fenway to Community)",
        "Thursday",
        "Cedarview Road",
        "Thursday",
    ]
)


class _FakeSource:
    def __init__(self, **params):
        self.params = params


@pytest.fixture(autouse=True)
def _clear_holiday_cache():
    m._observed_holidays.cache_clear()
    yield
    m._observed_holidays.cache_clear()


class TestParseStreetTable:
    def test_pairs_each_street_with_its_weekday(self):
        table = m._parse_street_table(_PDF_TEXT)
        assert table["Beacon Drive"] == "Monday"
        assert table["East Silsby Road"] == "Thursday"
        assert table["Fernwood Road"] == "Wednesday"
        assert table["Woodside Lane"] == "Monday"

    def test_multiline_street_name_is_joined(self):
        table = m._parse_street_table(_PDF_TEXT)
        assert (
            table[
                "Fairmount Boulevard "
                "(East bound from Sulgrave, and West bound to Richmond)"
            ]
            == "Tuesday"
        )

    def test_repeated_page_header_is_filtered(self):
        table = m._parse_street_table(_PDF_TEXT)
        assert "City of Beachwood" not in table
        assert not any("Rubbish Pick Up Days" in street for street in table)

    def test_unrecognisable_text_raises(self):
        with pytest.raises(ResponseShapeError):
            m._parse_street_table("nothing here looks like a schedule")


class TestMalformedCedarRoadEntry:
    """The city's PDF drops the opening parenthesis on one Cedar Road section."""

    def test_the_typo_is_repaired_into_the_normal_cascade(self):
        table = m._parse_street_table(_PDF_TEXT_CEDAR)
        assert "Cedar Road East bound from Fenway to Community)" not in table
        assert table["Cedar Road (East bound from Community to Richmond)"] == "Tuesday"
        assert table["Cedar Road (East bound from Fenway to Community)"] == "Thursday"

    def test_both_sections_share_one_base(self):
        table = m._parse_street_table(_PDF_TEXT_CEDAR)
        bases = {m._split_street(s)[0] for s in table if s.startswith("Cedar Road")}
        assert bases == {"Cedar Road"}

    def test_the_repaired_section_resolves(self):
        source = _FakeSource(
            street_base="Cedar Road",
            street_qualifier="(East bound from Fenway to Community)",
        )
        assert m._resolve_street(_PDF_TEXT_CEDAR, source) == ["Thursday"]

    def test_a_split_street_with_no_section_asks_for_the_section(self):
        source = _FakeSource(street_base="Cedar Road", street_qualifier="")
        with pytest.raises(SourceArgumentRequiredWithSuggestions) as excinfo:
            m._resolve_street(_PDF_TEXT_CEDAR, source)
        assert excinfo.value.argument == "street_qualifier"
        assert sorted(excinfo.value.suggestions) == [
            "(East bound from Community to Richmond)",
            "(East bound from Fenway to Community)",
        ]

    def test_a_wrong_section_is_blamed_on_the_section_field(self):
        # A valid street with the wrong section — blame street_qualifier, not
        # street_base, and offer the real sections.
        source = _FakeSource(
            street_base="Cedar Road", street_qualifier="(not a real section)"
        )
        with pytest.raises(SourceArgumentRequiredWithSuggestions) as excinfo:
            m._resolve_street(_PDF_TEXT_CEDAR, source)
        assert excinfo.value.argument == "street_qualifier"


class TestSingleSectionStreet:
    def test_base_with_no_qualifier_resolves_when_one_entry_matches(self):
        # A single "Foo Road (only section)" entry — the config flow would not
        # surface a qualifier, so the base must resolve on its own.
        text = "\n".join(["Foo Road (only section)", "Friday"])
        source = _FakeSource(street_base="Foo Road", street_qualifier="")
        assert m._resolve_street(text, source) == ["Friday"]


class TestStreetSplitJoin:
    @pytest.mark.parametrize(
        "full, base, qualifier",
        [
            ("Beacon Drive", "Beacon Drive", ""),
            (
                "Fairmount Boulevard (West bound from 24471)",
                "Fairmount Boulevard",
                "(West bound from 24471)",
            ),
        ],
    )
    def test_split_then_join_roundtrips(self, full, base, qualifier):
        assert m._split_street(full) == (base, qualifier)
        assert m._join_street(base, qualifier) == full


class TestResolveStreet:
    def test_returns_the_weekday_for_a_plain_street(self):
        source = _FakeSource(street_base="Beacon Drive", street_qualifier="")
        assert m._resolve_street(_PDF_TEXT, source) == ["Monday"]

    def test_returns_the_weekday_for_the_selected_qualifier(self):
        source = _FakeSource(
            street_base="Fairmount Boulevard",
            street_qualifier=("(East bound from Sulgrave, and West bound to Richmond)"),
        )
        assert m._resolve_street(_PDF_TEXT, source) == ["Tuesday"]

    def test_unknown_street_raises_on_the_base_with_base_name_suggestions(self):
        source = _FakeSource(street_base="Nowhere Avenue", street_qualifier="")
        with pytest.raises(SourceArgumentNotFoundWithSuggestions) as excinfo:
            m._resolve_street(_PDF_TEXT, source)
        assert excinfo.value.argument == "street_base"
        # Suggestions are clean base names, not full "Street (section)" strings.
        assert "Beacon Drive" in excinfo.value.suggestions
        assert not any("(" in s for s in excinfo.value.suggestions)

    def test_a_section_on_a_street_that_has_none_is_an_error(self):
        source = _FakeSource(street_base="Beacon Drive", street_qualifier="(nope)")
        with pytest.raises(SourceArgumentNotFound) as excinfo:
            m._resolve_street(_PDF_TEXT, source)
        assert excinfo.value.argument == "street_qualifier"


class TestConstants:
    def test_thursday_index_matches_the_datetime_convention(self):
        assert m._THURSDAY == datetime.date(2026, 11, 26).weekday() == 3

    @pytest.mark.parametrize(
        "stem", ["_THANKSGIVING", "_COLUMBUS_DAY", "_VETERANS_DAY"]
    )
    def test_every_holiday_stem_still_matches_the_ohio_calendar(self, stem):
        """Each stem must be a substring of exactly one real OH holiday name —
        the guard against another "Thanksgiving" -> "Thanksgiving Day" rename."""
        stem_value = getattr(m, stem)
        names = set(
            m.recurrence.us_federal_holidays(
                range(2025, 2028), subdiv="OH", observed=True
            ).values()
        )
        matches = [name for name in names if stem_value in name]
        assert len(matches) == 1, f"{stem}={stem_value!r} matched {matches}"


class TestDescribe:
    @freeze_time("2026-08-30")  # a Sunday
    def test_yields_rubbish_and_recycling_across_the_rest_of_the_year(self):
        schedules = list(m._describe("Monday", None))
        assert [s.key for s in schedules] == ["Rubbish", "Recycling"]
        for schedule in schedules:
            assert schedule.start == datetime.date(2026, 8, 31)  # next Monday
            assert schedule.until == datetime.date(2026, 12, 31)


class TestHolidayShift:
    # _adjust and _observed_holidays are keyed off the collection date, not the
    # wall clock, so these need no frozen time.

    def test_thanksgiving_moves_thursday_to_the_wednesday_before(self):
        # Thanksgiving 2026 is Thursday 2026-11-26.
        assert m._adjust(datetime.date(2026, 11, 26), "Rubbish", None) == datetime.date(
            2026, 11, 25
        )

    def test_thanksgiving_leaves_other_days_that_week_untouched(self):
        for day in (datetime.date(2026, 11, 23), datetime.date(2026, 11, 25)):
            assert m._adjust(day, "Rubbish", None) == day

    def test_a_monday_holiday_delays_that_week_by_one_day(self):
        # Labor Day 2026 is Monday 2026-09-07.
        assert m._adjust(datetime.date(2026, 9, 7), "Rubbish", None) == datetime.date(
            2026, 9, 8
        )
        assert m._adjust(datetime.date(2026, 9, 10), "Rubbish", None) == datetime.date(
            2026, 9, 11
        )

    def test_columbus_and_veterans_day_are_not_observed(self):
        assert m._adjust(
            datetime.date(2026, 10, 12),
            "Rubbish",
            None,  # Columbus Day (Mon)
        ) == datetime.date(2026, 10, 12)
        assert m._adjust(
            datetime.date(2026, 11, 11),
            "Rubbish",
            None,  # Veterans Day (Wed)
        ) == datetime.date(2026, 11, 11)

    def test_a_week_with_no_holiday_is_unchanged(self):
        day = datetime.date(2026, 10, 5)
        assert m._adjust(day, "Rubbish", None) == day

    def test_holidays_are_keyed_by_year_not_frozen_to_process_start(self):
        # A long-running HA process must still shift a collection in a later
        # year — the cache is keyed by year, so a date far from "now" resolves
        # against its own calendar. Thanksgiving 2031 is Thursday 2031-11-27.
        assert m._adjust(datetime.date(2031, 11, 27), "Rubbish", None) == datetime.date(
            2031, 11, 26
        )
        assert datetime.date(2031, 1, 1) in m._observed_holidays(2031)
