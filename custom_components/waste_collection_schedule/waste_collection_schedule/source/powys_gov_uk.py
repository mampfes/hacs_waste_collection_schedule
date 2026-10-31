"""Powys County Council (Wales) bin collection dates."""

from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, uprn
from waste_collection_schedule.service.GossForm import (
    GossFormDataParser,
    GossFormRetriever,
    GossStep,
)
from waste_collection_schedule.transformers import HtmlTransformer

# A GOSS form that takes the postcode and UPRN on one page. The answer carries
# the schedule as HTML in the page's FormData (COLLECTIONDATES_1 /
# COLLECTIONDATES): one card per round, its class naming the round
# ("bdl-card--refuse"), with an <li> per date ("Thursday 19th November 2026").
FORM_URL = "https://en.powys.gov.uk/binday"
_FORM = "BINDAYLOOKUP"
_STATE = (
    "PAGESESSIONID",
    "SESSIONID",
    "NONCE",
    "VARIABLES",
    "PAGENAME",
    "PAGEINSTANCE",
)
_ROUNDS = ("bdl-card--refuse", "bdl-card--recycling", "bdl-card--garden")


def _round(item) -> str:
    card = item.find_parent("div", class_="bdl-card")
    classes = card.get("class", []) if card else []
    return next((name for name in classes if name in _ROUNDS), "")


@final
class Source(BaseSource):
    TITLE = "Powys County Council"
    DESCRIPTION = "Source for en.powys.gov.uk services for Powys"
    URL = "https://en.powys.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "15 Market Street, Newtown": {
            "postcode": "SY16 2PQ",
            "uprn": "100100307820",
        },
        "3 Brookfields, Llandrindod Wells": {
            "postcode": "LD1 5LF",
            "uprn": "10011732434",
        },
    }

    PARAMS = (postcode(), uprn())

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your postcode (e.g. SY16 2PQ) and the Unique Property "
            "Reference Number (UPRN) of your property. You can find your UPRN at "
            "https://www.findmyaddress.co.uk/. Since the v3 pipeline migration, "
            "waste types use canonical, localised names, and the weekly "
            "recycling and food waste round is reported as two collections. "
            "Update filters, automations and customisations using the old labels."
        ),
    }

    WASTE_TYPES: ClassVar[list] = [
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
    ]

    retrieve = GossFormRetriever(
        FORM_URL,
        form=_FORM,
        state_fields=_STATE,
        steps=(
            GossStep(
                "ADDRESSLOOKUP_ADDRESSLOOKUPBUTTONS",
                fields=lambda response, postcode, uprn, **_: {
                    "VARIABLES": "",
                    "ADDRESSLOOKUP_ADDRESSLOOKUPPOSTCODE": postcode,
                    "ADDRESSLOOKUP_ADDRESSLOOKUP": "0",
                    "ADDRESSLOOKUP_POSTALADDRESS": "",
                    "ADDRESSLOOKUP_UPRN": str(uprn).strip(),
                },
            ),
        ),
    )

    parse = GossFormDataParser(
        "COLLECTIONDATES",
        pages=["COLLECTIONDATES_1"],
        parser=parsers.HtmlParser("div.bdl-card ul > li"),
    )

    transform = HtmlTransformer(
        date_getter=lambda item: item.get_text(strip=True),
        type_getter=_round,
        parse_date=date_parsers.without_ordinals(
            date_parsers.for_format("%A %d %B %Y")
        ),
        type_value_map={
            "bdl-card--refuse": wt.GENERAL_WASTE,
            "bdl-card--recycling": [wt.RECYCLABLES, wt.FOOD_WASTE],
            "bdl-card--garden": wt.GARDEN_WASTE,
        },
    )
