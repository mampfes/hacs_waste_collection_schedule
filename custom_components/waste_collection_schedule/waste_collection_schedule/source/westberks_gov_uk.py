import datetime
import re
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, preprocessors
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    alternatives,
    house_number,
    postcode,
    uprn,
)
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.retrievers import FanOutRetriever, Lookup
from waste_collection_schedule.service.JaduApiserver import rpc
from waste_collection_schedule.transformers import RowTransformer

_API_URL = "https://www.westberks.gov.uk/apiserver/ajaxlibrary"
_METHOD = "goss.echo.westberks.forms.getNext{}CollectionDate"
_ROUNDS = ("Rubbish", "Recycling", "FoodWaste")

_NEXT_DATE = date_parsers.next_weekday("%A %d %B")

_TYPE_MAP = {
    "Rubbish": wt.GENERAL_WASTE,
    "Recycling": wt.RECYCLABLES,
    "FoodWaste": wt.FOOD_WASTE,
}


def _property_uprn(response, *_, housenumberorname, **__) -> str:
    """The UPRN of the one property at the postcode whose address starts with the name or number."""
    wanted = str(housenumberorname).strip()
    properties = response.json()["result"]
    start = re.compile(rf"{re.escape(wanted)}(?!\w)", re.IGNORECASE)
    matches = [
        item
        for item in properties
        if start.match(item["line1"]) or start.match(item["buildingnumber"])
    ]
    if len(matches) == 1:
        return matches[0]["udprn"]
    names = [item["line1"] for item in matches or properties]
    if matches:
        raise SourceArgAmbiguousWithSuggestions("housenumberorname", wanted, names)
    raise SourceArgumentNotFoundWithSuggestions("housenumberorname", wanted, names)


def _next_date(value) -> datetime.date | None:
    """The date a "Friday 30 October" text names, or ``None`` for no date."""
    try:
        return _NEXT_DATE(str(value).strip()) if str(value).strip() else None
    except ValueError:
        return None


@final
class Source(BaseSource):
    TITLE = "West Berkshire Council"
    DESCRIPTION = "Source for westberks.gov.uk services for West Berkshire Council"
    URL = "https://westberks.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.FOOD_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "known_uprn": {"uprn": "100080241094"},
        "known_uprn as number": {"uprn": 100081026602},
        "unknown_uprn_by_name": {
            "postcode": "RG7 6NZ",
            "housenumberorname": "PARROG HOUSE",
        },
        "unknown_uprn_by_number": {"postcode": "RG18 4QU", "housenumberorname": "6"},
        "unknown_uprn_mews": {
            "postcode": "RG18 4GE",
            "housenumberorname": "3, Mangan Mews",
        },
    }

    PARAMS = (alternatives([uprn()], [postcode(), house_number("housenumberorname")]),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Provide your UPRN, or your postcode plus your house name or number. "
            "Find your UPRN at https://www.findmyaddress.co.uk/"
        ),
    }

    retrieve = FanOutRetriever(
        prepare=Lookup(
            rpc(
                _API_URL,
                "location.westberks.echoPostcodeFinder",
                lambda postcode, **_: {"provider": "", "postcode": postcode.strip()},
            ),
            given=lambda uprn=None, **_: (
                str(uprn).zfill(12) if uprn is not None else None
            ),
            pick=_property_uprn,
        ),
        targets=lambda source, property_uprn: _ROUNDS,
        fetch=rpc(
            _API_URL,
            lambda target, property_uprn, **_: _METHOD.format(target),
            lambda target, property_uprn, **_: {"uprn": property_uprn},
        ),
    )
    # One reply per round, each with its own date field; DateFields reads each
    # reply on its own, since a lone record would otherwise be flattened.
    parse = parsers.EachResponse(
        parsers.JsonParser("result"),
        then=preprocessors.DateFields(
            fields={
                "nextRubbishDateText": "Rubbish",
                "nextRubbishDateSubText": "Rubbish",
                "nextRecyclingDateText": "Recycling",
                "nextRecyclingDateSubText": "Recycling",
                "nextFoodWasteDateText": "FoodWaste",
                "nextFoodWasteDateSubText": "FoodWaste",
            },
            parse_date=_next_date,
        ),
    )
    transform = RowTransformer(type_value_map=_TYPE_MAP)
