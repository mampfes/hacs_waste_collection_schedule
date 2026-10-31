"""Great Yarmouth Borough Council (England) bin collection dates."""

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
    encode_variables,
)
from waste_collection_schedule.transformers import HtmlTransformer

# A GOSS form that resolves the UPRN server-side, from the address record the
# page would otherwise put in VARIABLES (without it a default address is
# answered). The schedule comes back as HTML in the page's FormData
# (LOOKUP_1 / SHOWSCHEDULE): one block per bin and date, the bin named by its
# icon ("black bin") and the date without a year ("Friday  6 November").
FORM_URL = "https://myaccount.great-yarmouth.gov.uk/find-my-waste-collection-days"
_FORM = "WASTECOLLECTIONCALENDARV2"


def _confirm_address(response, *, uprn, **_) -> dict[str, str]:
    value = str(uprn).strip()
    return {
        "VARIABLES": encode_variables({"ALcurrentRecord": {"uprn": value}}),
        "ADDRESS_ALSB": "PERFORM SEARCH",
        "ADDRESS_ALNB": "PERFORM A NEW SEARCH",
        "ADDRESS_UPRN": value,
        "ADDRESS_COUNTRY": "United Kingdom",
        "ADDRESS_ADDRESSKNOWN": "true",
        "ADDRESS_FINDANADDRESS": "true",
        "ADDRESS_LOOKUPVBUTTON": "Confirm Address",
    }


def _detail(area) -> str:
    detail = area.select_one(".collection-detail")
    return " ".join(detail.get_text(" ").split()) if detail else ""


@final
class Source(BaseSource):
    TITLE = "Great Yarmouth Borough Council"
    DESCRIPTION = "Source for waste collection services for Great Yarmouth Borough Council, Norfolk, UK."
    URL = "https://myaccount.great-yarmouth.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "64 Black Street Martham NR29 4PR": {"uprn": "100090834016"},
        "1 Hobland Barns Bradwell NR31 9BS": {"uprn": "10023466513"},
    }

    PARAMS = (uprn(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter the Unique Property Reference Number (UPRN) of your property. "
            "You can find it at https://www.findmyaddress.co.uk/. Since the v3 "
            "pipeline migration, waste types use canonical, localised names, and "
            "the dates a bulky collection can be booked are no longer listed as "
            "collections. Update filters, automations and customisations using "
            "the old labels."
        ),
    }

    WASTE_TYPES: ClassVar[list] = [
        wt.GARDEN_WASTE,
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
    ]

    retrieve = GossFormRetriever(
        FORM_URL,
        form=_FORM,
        steps=(GossStep("ADDRESS_LOOKUPVBUTTON", fields=_confirm_address),),
    )

    parse = GossFormDataParser(
        "SHOWSCHEDULE",
        pages=["LOOKUP_1"],
        parser=parsers.HtmlParser("div.collection-area"),
    )

    transform = HtmlTransformer(
        date_getter=lambda area: " ".join(area.select_one("b").get_text().split()),
        type_getter=lambda area: area.select_one("img")["alt"],
        description_getter=lambda area: re.sub(
            r"\s*will be emptied$", "", _detail(area).split(" ", 3)[-1]
        ),
        parse_date=date_parsers.nearest_year("%A %d %B"),
        type_value_map={
            "black bin": wt.GENERAL_WASTE,
            "green bin": wt.RECYCLABLES,
            "brown bin": wt.GARDEN_WASTE,
            # A date a bulky collection can be booked for, not a collection.
            "bulky day": None,
        },
    )
