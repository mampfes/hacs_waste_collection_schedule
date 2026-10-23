import re
from typing import ClassVar, final

from bs4 import BeautifulSoup
from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    alternatives,
    postcode,
    text_field,
    uprn,
)
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.transformers import RowTransformer

_ADDRESS_URL = "https://www.cornwall.gov.uk/my-area/"
_COLLECTION_URL = "https://www.cornwall.gov.uk/umbraco/Surface/Waste/MyCollectionDays"


def _pick_uprn(response, postcode=None, housenumberorname=None, **_) -> str:
    """Address lookup page -> UPRN of the address starting with the house name/number."""
    soup = BeautifulSoup(response.text, "html.parser")
    options = [
        (o.text.strip(), o["value"])
        for o in soup.select('select[name="Uprn"] option')
        if o.get("value") and o["value"] != "UNLISTED"
    ]
    if not options:
        raise SourceArgumentNotFound("postcode", postcode)
    wanted = str(housenumberorname).strip().lower()
    for text, value in options:
        if re.match(re.escape(wanted) + r"(?![0-9A-Za-z])", text.lower()):
            return value
    raise SourceArgumentNotFoundWithSuggestions(
        "housenumberorname",
        housenumberorname,
        list(dict.fromkeys(text for text, _ in options)),
    )


@final
class Source(BaseSource):
    TITLE = "Cornwall Council"
    DESCRIPTION = "Source for cornwall.gov.uk services for Cornwall Council"
    URL = "https://cornwall.gov.uk"
    COUNTRY = "uk"

    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "known_uprn": {"uprn": "100040118005"},
        "unknown_uprn": {"postcode": "TR261SP", "housenumberorname": "7"},
        "unknown_uprn_int": {"postcode": "PL17 8PL", "housenumberorname": 3},
        "uprn_with_garden_int_uprn": {"uprn": 100040080721},
    }

    PARAMS = (
        alternatives(
            [uprn()],
            [
                postcode(),
                text_field("housenumberorname", label="House Name or Number"),
            ],
        ),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Provide your UPRN, or provide both your postcode and house name "
            "or number. Find your UPRN at https://www.findmyaddress.co.uk/"
        ),
    }

    WASTE_TYPES: ClassVar[list] = [
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
    ]

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                _ADDRESS_URL,
                params=lambda postcode=None, **_: {"Postcode": postcode},
                given=lambda uprn=None, **_: uprn,
                pick=_pick_uprn,
            ),
        ),
        url=_COLLECTION_URL,
        params=lambda uprn_key, **_: {"subscribe": "False", "uprn": uprn_key},
    )

    parse = parsers.HtmlLabelledDates(
        "div.collection",
        label="span:nth-of-type(1)",
        date="span:nth-of-type(3)",
        date_pattern=r"(\d{1,2} \w{3})",
    )

    transform = RowTransformer(
        parse_date=date_parsers.nearest_year("%d %b"),
        type_value_map={
            "Food": wt.FOOD_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Rubbish": wt.GENERAL_WASTE,
            "Garden": wt.GARDEN_WASTE,
        },
    )
