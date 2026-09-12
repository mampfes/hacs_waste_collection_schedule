"""Matamata-Piako District Council (mpdc.govt.nz).

The council publishes one year-independent Joomla JEvents ICS feed per town
group. Those categories also contain unrelated community events, so the
pipeline normalises the two known collection summaries, filters everything
else, and fans each combined event out into its canonical waste types.
"""

from datetime import date
from typing import ClassVar, final

from waste_collection_schedule import lookups
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import dropdown
from waste_collection_schedule.parsers import IcsParser
from waste_collection_schedule.preprocessors import Compose, RowFilter, RowRelabel
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import ICSTransformer

_RUBBISH_SUMMARY = "Rubbish and food scraps collection"
_RECYCLING_SUMMARY = "Recycling, glass, and food scraps collection"
_RECYCLING_SUMMARY_VARIANT = "Recycling, glass and food scraps collection"

_COLLECTION_SUMMARIES = frozenset({_RUBBISH_SUMMARY, _RECYCLING_SUMMARY})

_AREA_URLS = {
    "Matamata, Waharoa, Walton and Tamihana": (
        "https://mpdc.govt.nz/calendar-export-test/icals.export/-?catids=142&"
        "format=ical&k=619cab9664e4d71d738288612668f8e2&years=0"
    ),
    "Morrinsville, Mangateparu and Tahuna": (
        "https://mpdc.govt.nz/calendar-export-test/icals.export/-?catids=143&"
        "format=ical&k=bf45523c10cd816fd644f3b5cfbd415a&years=0"
    ),
    "Te Aroha, Waihou and Waitoa": (
        "https://mpdc.govt.nz/calendar-export-test/icals.export/-?catids=141&"
        "format=ical&k=81379e2f52a3fbdc2603c79c28da4fa4&years=0"
    ),
}

_TYPE_VALUE_MAP = {
    _RUBBISH_SUMMARY: [wt.GENERAL_WASTE, wt.FOOD_WASTE],
    _RECYCLING_SUMMARY: [wt.RECYCLABLES, wt.GLASS, wt.FOOD_WASTE],
}


def _calendar_url(area: str, **_: object) -> str:
    return lookups.resolve(_AREA_URLS, area, argument="area")


def _keep_collection_summary(row: tuple[date, str], _source: BaseSource | None) -> bool:
    return row[1] in _COLLECTION_SUMMARIES


@final
class Source(BaseSource):
    TITLE = "Matamata-Piako District Council"
    DESCRIPTION = "Source for Matamata-Piako District Council kerbside collections."
    URL = "https://www.mpdc.govt.nz/calendar"
    COUNTRY = "nz"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Matamata": {"area": "Matamata, Waharoa, Walton and Tamihana"},
        "Morrinsville": {"area": "Morrinsville, Mangateparu and Tahuna"},
        "Te Aroha": {"area": "Te Aroha, Waihou and Waitoa"},
    }

    HOWTO: ClassVar[dict] = {
        "en": (
            "Visit https://www.mpdc.govt.nz/calendar and select the rubbish and "
            "recycling group containing your town."
        ),
    }

    PARAMS = (dropdown("area", list(_AREA_URLS), label="Collection area"),)

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GLASS,
        wt.FOOD_WASTE,
    ]

    retrieve = HttpGetRetriever(url=_calendar_url)
    parse = IcsParser(min_events=1)
    preprocess = Compose(
        RowRelabel(
            strip=r"\s*\*\s*$",
            rename={_RECYCLING_SUMMARY_VARIANT: _RECYCLING_SUMMARY},
        ),
        RowFilter(_keep_collection_summary),
    )
    transform = ICSTransformer(type_value_map=_TYPE_VALUE_MAP)
