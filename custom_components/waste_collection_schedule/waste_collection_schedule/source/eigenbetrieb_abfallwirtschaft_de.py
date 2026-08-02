"""Eigenbetrieb Abfallwirtschaft Landkreis Spree-Neiße (eigenbetrieb-abfallwirtschaft.de).

Demonstrates: a year-in-URL calendar page whose actual ICS download is behind a
same-page form (an ``<input name="ics">`` marks the form to scrape and
resubmit) rather than a direct link, plus best-effort fetching of next year's
calendar near year-end (the provider often publishes it early; swallowed if not
yet available). Both halves are shared components:
``retrievers.submit_page_form`` replays the form, ``retrievers.YearlyRetriever``
handles the per-year fetch and the December rollover, and
``parsers.EachResponse`` folds the one-or-two ICS downloads into one record
list. The legacy icon lookup tried the title's first word, falling back to the
whole title for the one multi-word label ("Gelbe(r) Sack/Tonne"); that is
``preprocessors.RowRelabel(vocabulary=...)`` ahead of a plain ICSTransformer
using the same map.
"""

from typing import ClassVar, final

from waste_collection_schedule import parsers, retrievers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city_id, location_id
from waste_collection_schedule.preprocessors import RowRelabel
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GENERAL_WASTE,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_BASE_URL = "https://www.eigenbetrieb-abfallwirtschaft.de"

_TYPE_VALUE_MAP = {
    "Restmüll": GENERAL_WASTE,
    "Biotonne": ORGANIC,
    "Papiercontainer": PAPER,
    "Gelbe(r) Sack/Tonne": RECYCLABLES,
}


def _calendar_for_year(source, year: int, _context):
    """Download one year's ICS by resubmitting the year page's own form."""
    city = source.params["city"]
    street = source.params["street"]
    return retrievers.submit_page_form(
        source,
        f"{_BASE_URL}/termine/abfuhrtermine/{year}/{city}/{street}.html",
        marker="ics",
        base_url=_BASE_URL,
        encoding="utf-8",
    )


@final
class Source(BaseSource):
    TITLE = "Eigenbetrieb Abfallwirtschaft Landkreis Spree-Neiße"
    DESCRIPTION = "Source for Eigenbetrieb Abfallwirtschaft Landkreis Spree-Neiße."
    URL = _BASE_URL
    COUNTRY = "de"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Forst (Lausitz), Rosenweg": {"city": "4", "street": "344"},
        "Peitz, Am See": {"city": "8", "street": "1077"},
        "Guben, Altsprucke": {"city": "5", "street": "410"},
        "Spremberg, Gartenstrasse": {"city": 10, "street": 701},
    }

    PARAMS = (
        city_id(field="city"),
        location_id(field="street"),
    )

    retrieve = retrievers.YearlyRetriever(fetch=_calendar_for_year)
    parse = parsers.EachResponse(parsers.IcsParser())
    # SUMMARY is the bin name plus trailing detail; narrow it back to the name.
    preprocess = RowRelabel(vocabulary=_TYPE_VALUE_MAP)
    transform = ICSTransformer(type_value_map=_TYPE_VALUE_MAP)

    def __init__(self, city: "str | int", street: "str | int"):
        super().__init__(city=str(city), street=str(street))
