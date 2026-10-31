"""Gateshead Council (England) bin collection dates."""

import re
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.service.GossForm import (
    GossFormDataParser,
    GossFormRetriever,
    GossStep,
)
from waste_collection_schedule.transformers import HtmlTransformer

# A GOSS form that takes the UPRN on its first page. The answer carries the
# schedule as HTML in the page's FormData (HOUSEHOLDCOLLECTIONS_1 /
# DISPLAYHOUSEHOLD): a table with a <th> per month ("November") and a row per
# collection day (day of month, weekday, round), without a year.
FORM_URL = "https://www.gateshead.gov.uk/article/3150/Bin-collection-day-checker"
_FORM = "BINCOLLECTIONCHECKER"
_DAY_CHANGE = re.compile(r"\s*-?\s*DAY CHANGE\s*$", re.IGNORECASE)


def _cells(row) -> list[str]:
    return [" ".join(td.get_text().split()) for td in row.find_all("td")]


def _date(row) -> str:
    """The day of month with the month of the heading above it ("04 November")."""
    month = row.find_previous("th").get_text(strip=True).split(" ")[0]
    return f"{_cells(row)[0]} {month}"


@final
class Source(BaseSource):
    TITLE = "Gateshead Council"
    DESCRIPTION = "Source for gateshead.gov.uk services for Gateshead"
    URL = "https://www.gateshead.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Test_002": {"uprn": 100000058404},
    }

    PARAMS = (uprn(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter the Unique Property Reference Number (UPRN) of your property. "
            "You can find it at https://www.findmyaddress.co.uk/. Since the v3 "
            "pipeline migration, waste types use canonical, localised names. "
            "Update filters, automations and customisations using the old labels."
        ),
    }

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
    ]

    retrieve = GossFormRetriever(
        FORM_URL,
        form=_FORM,
        state_fields=("PAGESESSIONID", "SESSIONID", "NONCE"),
        steps=(
            GossStep(
                "ADDRESSSEARCH_NEXTBUTTON",
                fields=lambda response, uprn, **_: {
                    "ADDRESSSEARCH_UPRN": str(uprn).strip(),
                    "ADDRESSSEARCH_ADDRESSTEXT": " ",
                },
            ),
        ),
    )

    parse = GossFormDataParser(
        "DISPLAYHOUSEHOLD",
        pages=["HOUSEHOLDCOLLECTIONS_1"],
        parser=parsers.HtmlParser("table.bincollections__table tr:has(> td)"),
    )

    transform = HtmlTransformer(
        date_getter=_date,
        type_getter=lambda row: _DAY_CHANGE.sub("", _cells(row)[-1]),
        parse_date=date_parsers.nearest_year("%d %B"),
        type_value_map={
            "Household Waste": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Garden Waste": wt.GARDEN_WASTE,
            "Recycling and Garden Waste": [wt.RECYCLABLES, wt.GARDEN_WASTE],
            "Household Waste and Garden Waste": [wt.GENERAL_WASTE, wt.GARDEN_WASTE],
        },
    )
