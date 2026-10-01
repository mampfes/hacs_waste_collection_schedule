import re
from typing import ClassVar, final

from bs4 import BeautifulSoup
from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, uprn
from waste_collection_schedule.transformers import HtmlTransformer

URL = "https://www.npt.gov.uk/"
FORM_URL = f"{URL}bins-and-recycling/equipment-and-collections/bin-day-finder/"
_HEADERS = {"Referer": FORM_URL, "Origin": URL.rstrip("/")}

# "Thursday, 23 October (Today)" with a non-breaking space: only day and month.
_DAY_MONTH_RE = re.compile(r"(\d{1,2})\s+([A-Za-z]+)")


def _tokens(response, *_, **__) -> dict:
    """The anti-forgery fields every step of the form must post back."""
    soup = BeautifulSoup(response.text, "html.parser")
    found = {}
    for name in ("__RequestVerificationToken", "ufprt"):
        element = soup.find("input", {"name": name})
        if element is None or not element.get("value"):
            raise ValueError(f"Failed to find {name} in the bin day finder form.")
        found[name] = str(element["value"])
    return found


def _date_text(link) -> str:
    """The date heading ("Thursday, 23 October") above the card's row."""
    row = link.find_parent("div", class_="alert")
    heading = row.find_previous_sibling("h2") if row is not None else None
    text = " ".join(heading.get_text().split()) if heading is not None else ""
    match = _DAY_MONTH_RE.search(text)
    if match is None:
        raise ValueError(f"No date in heading {text!r}")
    return f"{match.group(1)} {match.group(2)}"


@final
class Source(BaseSource):
    TITLE = "Neath Port Talbot Council"
    DESCRIPTION = "Source for waste collection services for Neath Port Talbot Council"
    URL = URL
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.GARDEN_WASTE,
        wt.RECYCLABLES,
        wt.PAPER,
        wt.GLASS,
        wt.FOOD_WASTE,
        wt.OTHER,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"postcode": "SA11 3HW", "uprn": 100100601042},
        "Test_002": {"postcode": "SA11 3HY", "uprn": "100100599841"},
        "Test_003": {"postcode": "SA11 3DY", "uprn": "100100600279"},
    }

    PARAMS = (postcode(), uprn())

    HOWTO: ClassVar[dict] = {
        "en": (
            "An easy way to discover your Unique Property Reference Number (UPRN) "
            "is by going to https://www.findmyaddress.co.uk/ and entering in your "
            "address details, or by searching for your address at "
            "https://uprn.uk/. The council's site asks for the postcode before "
            "the property, so both are needed. Collection dates are only given "
            "for the next two weeks."
        ),
    }

    # The site is a three-page form: the form page, the postcode submitted for
    # the address list, the chosen property submitted for the bin days. Each
    # page carries the anti-forgery tokens the next submission must send back.
    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(FORM_URL, pick=_tokens, headers=_HEADERS),
            retrievers.Lookup(
                FORM_URL,
                method="POST",
                headers=_HEADERS,
                data=lambda tokens, postcode, **_: {
                    **tokens,
                    "PostCode": postcode,
                    "action": "Find address",
                },
                pick=_tokens,
            ),
        ),
        url=FORM_URL,
        method="POST",
        headers=_HEADERS,
        data=lambda first, tokens, uprn, **_: {
            **tokens,
            "Address": str(uprn).zfill(12),
            "action": "Show my bin days",
        },
        raise_for_status=True,
    )

    parse = parsers.HtmlParser(
        "#contentInner div.bin-card > div.card-body > a", require=["#contentInner"]
    )

    transform = HtmlTransformer(
        date_getter=_date_text,
        type_getter=lambda link: " ".join(link.get_text().split()),
        parse_date=date_parsers.nearest_year("%d %B"),
        carry_raw_label=True,
        type_value_map={
            "General Household Rubbish": wt.GENERAL_WASTE,
            "Garden Waste": wt.GARDEN_WASTE,
            "Plastic / Tins / Cans": wt.RECYCLABLES,
            "Cardboard, Cartons and Paper": wt.PAPER,
            "Glass": wt.GLASS,
            "Food Waste": wt.FOOD_WASTE,
            "Batteries": wt.OTHER,
        },
    )
