from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    alternatives,
    postcode,
    street_address,
    uprn,
)
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.preprocessors import Compose, ExplodeList, RowFilter
from waste_collection_schedule.transformers import JsonTransformer

API = "https://www.thanet.gov.uk/wp-content/mu-plugins/collection-day/incl/mu-collection-day-calls.php"

_TYPE_MAP = {
    "Refuse": wt.GENERAL_WASTE,
    "BlueRecycling": wt.RECYCLABLES,
    "RedRecycling": wt.PAPER,
    "Food": wt.FOOD_WASTE,
    "Garden": wt.GARDEN_WASTE,
}


def _pick_uprn(response, *keys, postcode, street_address, **_) -> str:
    """The lookup answers ``{uprn: "HOUSE, STREET, TOWN, POSTCODE"}``."""
    addresses = response.json()
    wanted = str(street_address).upper()
    # A numbered house is listed as "6, GORDON SQUARE, ..." (comma after the
    # number), a named one as "FORUS, GORDON SQUARE, ...": compare without commas.
    plain = wanted.replace(",", "")
    for key, value in addresses.items():
        if value.upper().replace(",", "").startswith(plain):
            return key
    raise SourceArgumentNotFoundWithSuggestions(
        "street_address",
        wanted,
        [value.split(",")[0] for value in addresses.values()],
    )


def _dates(record, source) -> list[str]:
    """Each service reports its next and its previous collection, "28/09/2026 at 6:00am"."""
    return [record["nextDate"][:10], record["previousDate"][:10]]


@final
class Source(BaseSource):
    TITLE = "Thanet District Council"
    DESCRIPTION = "Source for thanet.gov.uk services for Thanet District Council"
    URL = "https://thanet.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.PAPER,
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "uprn": {"uprn": "100061108233"},
        "houseName": {"postcode": "CT7 9SL", "street_address": "Forus"},
        "houseNumber": {"postcode": "CT7 9SL", "street_address": "6 Gordon Square"},
    }

    PARAMS = (
        alternatives(
            [uprn()],
            [postcode(), street_address("street_address")],
        ),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter either your UPRN (available from "
            "[FindMyAddress.co.uk](https://www.findmyaddress.co.uk/)) OR your "
            "postcode and the first line of your address, e.g. '2 London Road' "
            "(anything before the first comma of the address on the council's "
            "site). UPRNs work every time; a postcode and street address work "
            "when a match can be found."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                API,
                params=lambda postcode=None, **_: {"searchAddress": postcode},
                given=lambda uprn=None, **_: uprn,
                pick=_pick_uprn,
            ),
        ),
        url=API,
        params=lambda key, **_: {"pAddress": key},
    )

    parse = parsers.JsonParser()

    preprocess = Compose(
        RowFilter(lambda record, source: record["type"] in _TYPE_MAP),
        ExplodeList(_dates, into="date"),
    )

    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map=_TYPE_MAP,
        parse_date=date_parsers.for_format("%d/%m/%Y"),
    )
