import datetime
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, uprn
from waste_collection_schedule.retrievers import (
    Branch,
    FallbackRetriever,
    Request,
)
from waste_collection_schedule.service.JaduXfp import XfpFormRetriever
from waste_collection_schedule.transformers import HtmlTransformer

CHECK_URL = "https://www.birmingham.gov.uk/info/50388/check_your_collection_day"
LEGACY_FORM_URL = "https://www.birmingham.gov.uk/xfp/form/619"

_ROW = "table.data-table tbody tr"

_YEARLESS_DATE = date_parsers.nearest_year("%A %d %B")
_LEGACY_DATE = date_parsers.for_format("%a %d/%m/%Y")


def _is_legacy(row) -> bool:
    """The legacy form lists "service | next date"; the new page "date | service | status"."""
    return len(row.find_all("td")) == 1


def _date_text(row) -> str:
    cells = row.find_all(["th", "td"])
    return cells[1 if _is_legacy(row) else 0].get_text(strip=True)


def _label(row) -> str:
    cells = row.find_all(["th", "td"])
    return cells[0 if _is_legacy(row) else 1].get_text(strip=True)


def _parse_date(*args: str) -> datetime.date:
    """ "Wednesday 07 October" (no year) or, from the legacy form, "Wed 07/10/2026"."""
    text = args[-1]
    return _LEGACY_DATE(text) if "/" in text else _YEARLESS_DATE(text)


@final
class Source(BaseSource):
    TITLE = "Birmingham City Council"
    DESCRIPTION = "Source for birmingham.gov.uk services for Birmingham, UK."
    URL = "https://birmingham.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE]

    TEST_CASES: ClassVar[dict] = {
        "Cherry Tree Croft": {"uprn": 100070321799, "postcode": "B27 6TF"},
        "Ludgate Loft Apartments": {"uprn": 10033389698, "postcode": "B3 1DW"},
        "Victoria Road": {"uprn": 100070548572, "postcode": "B17 0AH"},
        "Windermere Road": {"uprn": "100070566109", "postcode": "B13 9JP"},
        "Park Hill": {"uprn": "100070475114", "postcode": "B13 8DS"},
    }

    PARAMS = (uprn(), postcode())

    HOWTO: ClassVar[dict] = {
        "en": (
            "You can find your UPRN by visiting https://www.findmyaddress.co.uk/ "
            "and entering your address details. Enter it together with your "
            "postcode."
        ),
    }

    # The council's "check your collection day" page; an address it cannot find
    # there may still be served by the older form, which is asked second.
    retrieve = FallbackRetriever(
        Branch(
            "check",
            Request(
                CHECK_URL,
                params=lambda postcode, uprn, **_: {
                    "postcode": postcode,
                    "uprn": uprn,
                    "next": "Next",
                },
            ),
        ),
        Branch(
            "legacy",
            XfpFormRetriever(
                LEGACY_FORM_URL,
                page="491",
                question="q1f8ccce1d1e2f58649b4069712be6879a839233f",
            ),
        ),
    )
    parse = parsers.FirstNonEmptyBranch(
        {
            "check": parsers.HtmlParser(_ROW),
            "legacy": parsers.HtmlParser(_ROW),
        }
    )

    transform = HtmlTransformer(
        date_getter=_date_text,
        type_getter=_label,
        parse_date=_parse_date,
        type_value_map={
            "Rubbish": wt.GENERAL_WASTE,
            "Household Collection": wt.GENERAL_WASTE,
            "Food": wt.FOOD_WASTE,
            "Mixed recycling": wt.RECYCLABLES,
        },
    )
