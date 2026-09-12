import re
from datetime import datetime, timedelta

import requests
from dateutil import rrule
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Sunshine Coast Queensland (QLD)"
DESCRIPTION = "Source script for Sunshine Coast Queensland (QLD)."
COUNTRY = "au"
URL = "https://www.sunshinecoast.qld.gov.au/living-and-community/waste-and-recycling/bin-collection-days"
TEST_CASES = {
    "Hospital Rd": {"street_name": "hospital rd"},
    "Great Keppel Way": {"street_name": "great keppel way"},
    "House number and suburb": {"street_name": "12 Hospital Rd, Nambour"},
    "Street type spelled out": {"street_name": "hospital road"},
    "Street in several suburbs": {"street_name": "Main St", "locality": "Eumundi"},
}

API_URL = "https://www.sunshinecoast.qld.gov.au/__server__/api/v1"
ICON_MAP = {
    "Garbage": Icons.GENERAL_WASTE,
    "Recycle": Icons.RECYCLING,
    "Organic": Icons.ORGANIC,
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Use the street name as the council's bin collection page spells it, e.g. "
        "'Hospital Rd'. A house number and suburb are ignored if you include them. "
        "Set `locality` to the suburb when the same street name occurs in more than "
        "one suburb; the error message lists the suburbs to choose from."
    )
}

PARAM_DESCRIPTIONS = {
    "en": {
        "street_name": "Street name, e.g. Hospital Rd.",
        "locality": "Suburb, needed only when the street name is not unique.",
    }
}

PARAM_TRANSLATIONS = {
    "en": {
        "street_name": "Street Name",
        "locality": "Suburb",
    }
}

"""
    WEEK TYPES
        sunshine coast uses a week setting
        week 1 and week 2 starting from a set date


    RETURNED VALUES FROM API Query
        JSON DATA:
            [{"id":"<id>","street":"<Street Name>","locality":"<Town>","day":"Wednesday","week":"1","instructions":""}]
"""

BASE_DATE = datetime(2021, 12, 11)

# The API matches a substring of its own street names, which are abbreviated
# ("Hospital Rd", "Pacific Bvd"), so a spelled-out type finds nothing.
STREET_TYPE_ABBREVIATIONS = {
    "avenue": "ave",
    "boulevard": "bvd",
    "circuit": "cct",
    "close": "cl",
    "court": "ct",
    "crescent": "cres",
    "drive": "dr",
    "esplanade": "esp",
    "highway": "hwy",
    "parade": "pde",
    "place": "pl",
    "road": "rd",
    "street": "st",
    "terrace": "tce",
}

_HOUSE_NUMBER = re.compile(r"^\d+[a-z]?(?:\s*[-/]\s*\d+[a-z]?)?\s+", re.IGNORECASE)


def split_locality(street_name: str) -> tuple[str, str | None]:
    """Split a "<street>, <suburb>" string into its two parts."""
    street, _, locality = street_name.partition(",")
    return street.strip(), locality.strip() or None


def query_candidates(street_name: str) -> list[str]:
    """Return the API queries to try for a user-supplied street name.

    Users copy the address from the council's page, so the street name can carry
    a house number, a suburb, or a spelled-out street type. None of those match
    the API, which searches its abbreviated street names for a substring.
    """
    street = _HOUSE_NUMBER.sub("", split_locality(street_name)[0], count=1).strip()
    street = " ".join(street.split())

    candidates = [street]
    words = street.split()
    if words:
        last = words[-1].lower()
        abbreviated = STREET_TYPE_ABBREVIATIONS.get(last)
        if abbreviated:
            candidates.append(" ".join([*words[:-1], abbreviated]))
        # drop the street type entirely as a last resort
        if len(words) > 1 and (
            abbreviated or last in STREET_TYPE_ABBREVIATIONS.values()
        ):
            candidates.append(" ".join(words[:-1]))

    ordered: list[str] = []
    for candidate in candidates:
        if candidate and candidate.casefold() not in {o.casefold() for o in ordered}:
            ordered.append(candidate)
    return ordered


def start_date(day_name: str, week: str) -> datetime:
    """First collection day of a street's week 1 / week 2 cycle."""
    day = BASE_DATE
    for _ in range(7):
        if day.strftime("%A") == day_name:
            break
        day += timedelta(days=1)
    return day + timedelta(weeks=int(week) - 1)


class Source:
    def __init__(self, street_name, locality=None):
        self.street_name = str(street_name).strip()
        self._locality = str(locality).strip() if locality else None
        if self._locality is None:
            self._locality = split_locality(self.street_name)[1]

    def _query(self, street: str) -> list[dict]:
        r = requests.get(f"{API_URL}/streets/{street}", timeout=30)
        r.raise_for_status()
        results = r.json()
        return results if isinstance(results, list) else []

    def _street(self) -> dict:
        """Find the one street record matching the configured arguments."""
        results: list[dict] = []
        for candidate in query_candidates(self.street_name):
            results = self._query(candidate)
            if results:
                break

        if not results:
            raise SourceArgumentNotFoundWithSuggestions(
                "street_name", self.street_name, []
            )

        matches = results
        if self._locality:
            wanted = self._locality.casefold()
            matches = [r for r in results if r.get("locality", "").casefold() == wanted]
            if not matches:
                raise SourceArgumentNotFoundWithSuggestions(
                    "locality",
                    self._locality,
                    sorted({r["locality"] for r in results}),
                )

        if len(matches) > 1:
            raise SourceArgAmbiguousWithSuggestions(
                "street_name",
                self.street_name,
                sorted(f"{r['street']}, {r['locality']}" for r in matches),
            )

        return matches[0]

    def fetch(self):
        data = self._street()

        day = start_date(data["day"], data["week"])
        today = datetime.today()

        general_dates = rrule.rrule(rrule.WEEKLY, dtstart=day).xafter(today, 10, True)
        recycling_dates = rrule.rrule(rrule.WEEKLY, interval=2, dtstart=day).xafter(
            today, 10, True
        )
        garden_dates = rrule.rrule(
            rrule.WEEKLY, interval=2, dtstart=day + timedelta(weeks=1)
        ).xafter(today, 10, True)

        entries = []
        for text, dates in [
            ("Garbage", general_dates),
            ("Recycle", recycling_dates),
            ("Organic", garden_dates),
        ]:
            for date in dates:
                entries.append(
                    Collection(
                        date=date.date(),
                        t=text,
                        icon=ICON_MAP[text],
                    )
                )

        return entries
