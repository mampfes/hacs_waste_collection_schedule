"""City of Lincoln, California (Placer County).

The city's "Garbage Schedule" map is an ArcGIS app over its public address
point layer, which carries each address's collection weekday and, for green
waste, a Blue or Yellow week. Garbage ("One & Done") is weekly on that day;
green waste is the same weekday every other week.

Blue/Yellow -> ISO-week parity: the layer gives only the colour. The city's
printed 2026 calendar colours every week, and all 53 match Blue = odd ISO week,
Yellow = even (the city services holidays, so nothing shifts). Mapping a zone
label onto a parity follows northernbeaches_nsw_gov_au. Open question: 2026 has
53 ISO weeks, so parity makes the weeks of 2026-12-28 (wk53) and 2027-01-04
(wk1) both Blue, where strict alternation would make the latter Yellow. If the
2027 calendar shows strict alternation, switch green waste to an anchored
FORTNIGHTLY Schedule from a documented Blue Monday (as moretonbay_qld_gov_au).
"""

import re
from collections.abc import Iterator
from typing import Any, ClassVar, final

from waste_collection_schedule import recurrence
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.preprocessors import (
    Compose,
    Deduplicate,
    RecurrenceExpander,
    RequireRecords,
    RowFilter,
    Schedule,
    SelectExactMatch,
)
from waste_collection_schedule.service.ArcGis import (
    ArcGisCodedValueParser,
    ArcGisDistinctValues,
    ArcGisFeatureRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer

_FEATURE_URL = (
    "https://services6.arcgis.com/ojAwglArv2d3JM03/arcgis/rest/services"
    "/Master_Address_Points_Public_View/FeatureServer/5"
)
_WEEKS_AHEAD = 26

# RouteWeek coded-value domain: 1 = Blue, 2 = Yellow (see module docstring).
_GREEN_WASTE_PARITY = {1: "odd", 2: "even"}


def _split(street_address: str) -> tuple[int, list[str]] | None:
    """House number and upper-cased street tokens, ignoring city/ZIP and unit."""
    line = street_address.split(",")[0]
    line = re.sub(r"#\s*\S+", " ", line).upper()
    match = re.match(r"\s*(\d+)\s+(.+)", line)
    if not match:
        return None
    return int(match.group(1)), re.sub(r"[^A-Z0-9 ]", " ", match.group(2)).split()


def _number_clause(street_address: str, **_: Any) -> str:
    """Every address point at the house number (an int, so nothing to quote)."""
    parts = _split(street_address)
    return f"StreetNum = {parts[0]}" if parts else "1=0"


def _abbreviates(typed: str, full: str) -> bool:
    """'CT' for COURT, 'PKWY' for PARKWAY: same first letter, letters in order."""
    if not typed or not full or typed[0] != full[0]:
        return False
    rest = iter(full)
    return all(letter in rest for letter in typed)


def _names_this_street(record: dict[str, Any], source: Any) -> bool:
    """Whether the typed street is this point's street.

    The layer stores the street type spelled out ("EAST AVENUE"); a resident
    types "East Ave". The name must match word for word; whatever follows may
    only be the street type (in full or abbreviated) and a direction suffix.
    """
    parts = _split(source.params["street_address"])
    if parts is None:
        return False
    typed = parts[1]
    name = " ".join(
        filter(None, [record.get("StreetPreDir"), record.get("StreetName")])
    ).split()
    if typed[: len(name)] != name:
        return False
    rest = typed[len(name) :]
    post_dir = record.get("StreetPostDir")
    if rest and post_dir and rest[-1] == post_dir:
        rest = rest[:-1]
    if not rest:
        return True
    return len(rest) == 1 and _abbreviates(rest[0], record.get("StreetType") or "")


def _building(record: dict[str, Any]) -> str:
    """The address without its unit, so a building's units are one entity."""
    return (record.get("Full_Street_Address") or "").split(" #")[0]


def _describe(record: dict[str, Any], source: Any) -> Iterator[Schedule]:
    weekday = recurrence.weekday(record.get("CollectionDayName") or "")
    if weekday is None:
        return
    start = recurrence.next_weekday(weekday)
    yield Schedule("One & Done", start, recurrence.WEEKLY, _WEEKS_AHEAD)
    parity = _GREEN_WASTE_PARITY.get(record.get("RouteWeek"))  # type: ignore[arg-type]
    if record.get("Res_GW_Allowed") == 1 and parity:
        yield Schedule(
            "Green Waste",
            start,
            recurrence.WEEKLY,
            _WEEKS_AHEAD,
            iso_week_parity=parity,
        )


@final
class Source(BaseSource):
    TITLE = "Lincoln, CA"
    DESCRIPTION = (
        "Source for City of Lincoln, California (Placer County) garbage and "
        "green waste collection."
    )
    URL = "https://www.lincolnca.gov/recycling"
    COUNTRY = "us"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@chmsant"]
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.GARDEN_WASTE]

    TEST_CASES: ClassVar[dict] = {
        "Grace Life Church - Tuesday, Blue week": {"street_address": "671 East Avenue"},
        "First Street Community Church - Monday, Yellow week": {
            "street_address": "1545 1st St"
        },
        "Lincoln Area Archives Museum - Tuesday, no green waste": {
            "street_address": "640 5th Street, Lincoln, CA 95648"
        },
    }

    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unknown address": {"street_address": "9999 East Avenue"},
    }

    PARAMS = (street_address("street_address"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter the house number and street (e.g. '671 East Avenue' or "
            "'671 East Ave'); city and ZIP are optional. Directions are stored "
            "as N/E/S/W. You can check your collection day and green waste "
            "colour on the City's Garbage Schedule map at "
            "https://www.lincolnca.gov/recycling."
        ),
    }

    retrieve = ArcGisFeatureRetriever(
        _FEATURE_URL,
        where=_number_clause,
        out_fields=(
            "Full_Street_Address,StreetPreDir,StreetName,StreetType,"
            "StreetPostDir,CollectionDay,RouteWeek,Res_GW_Allowed"
        ),
    )
    parse = ArcGisCodedValueParser(
        _FEATURE_URL,
        "CollectionDay",
        into="CollectionDayName",
        argument="street_address",
    )
    preprocess = Compose(
        RowFilter(_names_this_street),
        RequireRecords(
            argument="street_address",
            suggestions=ArcGisDistinctValues(
                _FEATURE_URL, "Full_Street_Address", where=_number_clause, limit=10
            ),
        ),
        SelectExactMatch(argument="street_address", key=_building),
        RowFilter(lambda record, _source: record.get("CollectionDay") is not None),
        RequireRecords(
            argument="street_address",
            hint=(
                "the City has not assigned a collection day to this address yet; "
                "call Lincoln Public Works at (916) 434-2450"
            ),
        ),
        RecurrenceExpander(_describe),
        Deduplicate(),
    )
    transform = ICSTransformer(
        type_value_map={
            "One & Done": wt.GENERAL_WASTE,
            "Green Waste": wt.GARDEN_WASTE,
        }
    )
