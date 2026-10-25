"""Toowoomba Regional Council (QLD), Australia.

The council's public ArcGIS map service has a "Waste Pickup Days" layer with
one feature per serviced property: its general waste weekday (collected
weekly) and, for the fortnightly recycling and the optional green waste bins,
a weekday plus a "week 1" / "week 2" flag. The council's printed calendar
shades the weeks alternately; the week of Monday 29 December 2025 is a week 1,
so the fortnightly bins are projected from that reference week. (A plain ISO
week parity would agree through 2026 but put two "week 1"s in a row across
the 53-week ISO year 2026/27, which a fortnightly round does not do.) The
layer's free-text day and week fields hold the odd typo or placeholder
("Fir", "na", "0"); a service whose day or week does not resolve is left out
rather than guessed.
"""

import datetime
from collections.abc import Iterable
from typing import ClassVar, final

from waste_collection_schedule import recurrence
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, street_address
from waste_collection_schedule.preprocessors import RecurrenceExpander, Schedule
from waste_collection_schedule.service.ArcGis import (
    ArcGisDistinctValues,
    ArcGisFeatureParser,
    ArcGisFeatureRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer

_LAYER = (
    "https://maps.tr.qld.gov.au/arcgis/rest/services/External/"
    "External_TRMaps/MapServer/1"
)
_FIELDS = (
    "FormattedAddress,Garbage,RecycleBinWeek,RecycleRunDay,GreenRunWeek,GreenRunDay"
)

_GENERAL = "General Waste"
_RECYCLING = "Recycling"
_GREEN = "Green Waste"

#: Monday of a "week 1" on the council's calendar (shaded on the 2026 print);
#: "week 2" is the week after. Only the fortnight's phase is taken from it.
_WEEK_ONE = datetime.date(2025, 12, 29)
_WEEK_OFFSET = {"1": 0, "2": 7}
_WEEKS = 26


def _sql(value: str) -> str:
    """Upper-cased, whitespace-collapsed, quote-escaped, wildcards removed."""
    text = " ".join(str(value).replace("%", " ").replace("_", " ").split())
    return text.upper().replace("'", "''")


def _where(address: str, suburb: str, **_) -> str:
    # FormattedAddress is "<address>\r<SUBURB> QLD <postcode>"; "_" matches the
    # line break. The layer's collation is case-insensitive.
    return f"FormattedAddress LIKE '{_sql(address)}_{_sql(suburb)} QLD %'"


def _similar(address: str, suburb: str, **_) -> str:
    """Addresses on the same street in the suburb, for a no-match suggestion."""
    words = [w for w in _sql(address).split() if not any(c.isdigit() for c in w)]
    street = " ".join(words[:1])
    return f"FormattedAddress LIKE '% {street}%_{_sql(suburb)} QLD %'"


def _weekday(value: object) -> int | None:
    # The layer mostly writes three letters; a four-letter Thursday occurs too.
    text = str(value or "").strip()[:3]
    return recurrence.weekday(text, "en", abbreviated=True) if text else None


def _describe(record: dict, source: BaseSource | None) -> Iterable[Schedule]:
    today = datetime.date.today()
    garbage = _weekday(record.get("Garbage"))
    if garbage is not None:
        start = recurrence.next_weekday(garbage, on_or_after=today)
        yield Schedule(_GENERAL, start, recurrence.WEEKLY, _WEEKS)
    for key, day_field, week_field in (
        (_RECYCLING, "RecycleRunDay", "RecycleBinWeek"),
        (_GREEN, "GreenRunDay", "GreenRunWeek"),
    ):
        weekday = _weekday(record.get(day_field))
        offset = _WEEK_OFFSET.get(str(record.get(week_field) or "").strip())
        if weekday is None or offset is None:
            continue
        anchor = _WEEK_ONE + datetime.timedelta(days=offset + weekday)
        yield Schedule(key, anchor, recurrence.FORTNIGHTLY, _WEEKS // 2, anchor=True)


@final
class Source(BaseSource):
    TITLE = "Toowoomba Regional Council"
    DESCRIPTION = "Source for Toowoomba Regional Council (QLD) kerbside collection."
    URL = "https://www.tr.qld.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES, wt.GARDEN_WASTE]
    TEST_CASES: ClassVar[dict] = {
        "191 Herries Street, Toowoomba City": {
            "address": "191 Herries Street",
            "suburb": "Toowoomba City",
        },
        "2 Ruthven Street, Harlaxton": {
            "address": "2 Ruthven Street",
            "suburb": "Harlaxton",
        },
        "1 McDougall Street, Yarraman (no green waste)": {
            "address": "1 McDougall Street",
            "suburb": "Yarraman",
        },
    }
    PARAMS = (street_address("address"), city("suburb"))
    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            "Enter the street address with the street type written out (e.g. "
            "'191 Herries Street', units as '2/86C Hogg Street') and the suburb "
            "(e.g. 'Toowoomba City'), as the council's 'Find your bin day' map "
            "shows them. Green waste is an optional service: the dates are those "
            "of your area's green waste round, whether or not you have a green "
            "waste bin."
        ),
        "de": (
            "Adresse mit ausgeschriebenem Straßentyp (z. B. '191 Herries "
            "Street', Wohnungen als '2/86C Hogg Street') und den Ort (z. B. "
            "'Toowoomba City') eingeben, wie sie die Karte 'Find your bin day' "
            "der Stadt anzeigt. Die Grünabfalltonne ist ein optionaler Dienst: "
            "die Termine sind die der Grünabfalltour des Gebiets, unabhängig "
            "davon, ob eine Grünabfalltonne vorhanden ist."
        ),
    }

    retrieve = ArcGisFeatureRetriever(
        _LAYER, where=_where, out_fields=_FIELDS, result_record_count=1
    )
    parse = ArcGisFeatureParser(
        argument="address",
        suggestions=ArcGisDistinctValues(
            _LAYER, "FormattedAddress", where=_similar, limit=50
        ),
    )
    preprocess = RecurrenceExpander(_describe)
    transform = ICSTransformer(
        type_value_map={
            _GENERAL: wt.GENERAL_WASTE,
            _RECYCLING: wt.RECYCLABLES,
            _GREEN: wt.GARDEN_WASTE,
        }
    )
