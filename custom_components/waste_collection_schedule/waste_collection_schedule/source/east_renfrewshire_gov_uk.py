"""East Renfrewshire Council (Scotland) bin collection dates."""

from typing import ClassVar, final

from bs4 import BeautifulSoup
from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, uprn
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.service.GossForm import GossFormRetriever, GossStep
from waste_collection_schedule.transformers import HtmlTransformer

# A GOSS form: page one takes the postcode, page two offers that postcode's
# addresses (option values are 12-digit UPRNs) and answers with a table of the
# next collections, one <img alt="Green bin icon"> per bin due that day.
FORM_URL = "https://eastrenfrewshire.gov.uk/bin-days"
_FORM = "BINDAYSV2"
_STATE = (
    "PAGESESSIONID",
    "SESSIONID",
    "NONCE",
    "VARIABLES",
    "PAGENAME",
    "PAGEINSTANCE",
)
_NO_VARIABLES = "e30="  # base64 of "{}"


def _uprn(value) -> str:
    return str(value).strip().zfill(12)


def _choose_address(response, *, uprn, **_) -> dict[str, str]:
    """Page two's answer: the UPRN, checked against the postcode's addresses."""
    soup = BeautifulSoup(response.text, "html.parser")
    offered = [
        str(option["value"])
        for option in soup.select(f"select[name={_FORM}_PAGE2_UPRN] option[value]")
        if option["value"]
    ]
    if offered and _uprn(uprn) not in offered:
        raise SourceArgumentNotFoundWithSuggestions("uprn", uprn, offered)
    return {
        "VARIABLES": _NO_VARIABLES,
        "PAGE2_FIELD293": "true",
        "PAGE2_UPRN": _uprn(uprn),
        "PAGE2_FIELD295": "false",
        "PAGE2_FIELD297": "false",
    }


def _bin(img) -> str:
    """The bin colour from the icon's alt text ("Green bin icon")."""
    return str(img.get("alt", "")).split(" ")[0]


@final
class Source(BaseSource):
    TITLE = "East Renfrewshire Council"
    DESCRIPTION = "Source for eastrenfrewshire.gov.uk services for East Renfrewshire"
    URL = "https://eastrenfrewshire.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"postcode": "G78 2TJ", "uprn": "131016859"},
        "Test_002": {"postcode": "g775ar", "uprn": 131019331},
        "Test_003": {"postcode": "g78 3er", "uprn": "000131020112"},
    }

    PARAMS = (postcode(), uprn())

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your postcode and the Unique Property Reference Number (UPRN) "
            "of your property. You can find your UPRN at "
            "https://www.findmyaddress.co.uk/. Since the v3 pipeline migration, "
            "waste types use canonical, localised names. Update filters, "
            "automations and customisations using the old labels."
        ),
    }

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    retrieve = GossFormRetriever(
        FORM_URL,
        form=_FORM,
        state_fields=_STATE,
        steps=(
            GossStep(
                "PAGE1_FIELD290",
                fields=lambda response, postcode, **_: {
                    "VARIABLES": _NO_VARIABLES,
                    "PAGE1_POSTCODE": postcode,
                },
                argument="postcode",
            ),
            GossStep("PAGE2_FIELD294", fields=_choose_address),
        ),
    )

    parse = parsers.ArgumentGuard(
        parsers.HtmlParser(f"#{_FORM}_RESULTS_NEXTCOLLECTIONLISTV4 tr td img"),
        argument="uprn",
        contains=f"{_FORM}_RESULTS_NEXTCOLLECTIONLISTV4",
    )

    # Each icon is followed by its label ("Green - Plastic recycling").
    transform = HtmlTransformer(
        date_getter=lambda img: img.find_parent("tr").find("td").get_text(strip=True),
        type_getter=_bin,
        description_getter=lambda img: str(img.next_sibling or "").strip(),
        parse_date=date_parsers.for_format("%d/%m/%Y"),
        type_value_map={
            "Grey": wt.GENERAL_WASTE,
            "Brown": wt.ORGANIC,
            "Blue": wt.PAPER,
            "Green": wt.RECYCLABLES,
        },
    )
