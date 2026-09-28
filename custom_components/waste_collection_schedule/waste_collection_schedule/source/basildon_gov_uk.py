# Credit where it's due:
# This is predominantly a refactoring of the Bristol City Council script from the UKBinCollectionData repo
# https://github.com/robbrad/UKBinCollectionData

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
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.preprocessors import ExplodeList
from waste_collection_schedule.transformers import JsonTransformer

API = "https://basildonportal.azurewebsites.net/api"
HEADERS = {
    "Origin": "https://mybasildon.powerappsportals.com",
    "Referer": "https://mybasildon.powerappsportals.com/",
}

_TYPE_MAP = {
    "general_waste": wt.GENERAL_WASTE,
    "green_waste": wt.GARDEN_WASTE,
    "food_waste": wt.FOOD_WASTE,
    "glass_waste": wt.GLASS,
    "papercard_waste": wt.PAPER,
    "plasticcans_waste": wt.RECYCLABLES,
}

_SLOTS = ("current_collection_", "next_collection_", "last_collection_")


def _normalise(address: str) -> str:
    return address.replace(",", "").replace(" ", "").upper()


def _pick_uprn(response, *keys, postcode, address, **_) -> str:
    response.raise_for_status()
    data = response.json()
    if data["result"] != "success" or not data["properties"]:
        raise SourceArgumentNotFound("postcode", postcode)
    for item in data["properties"]:
        if _normalise(item["line1"]) == _normalise(address):
            return item["uprn"]
    raise SourceArgumentNotFoundWithSuggestions(
        "address", address, [item["line1"] for item in data["properties"]]
    )


def _service_rows(services, source) -> list[dict]:
    """One row per active collection slot of every known service."""
    return [
        {"type": service, "date": services[service][slot + "date"]}
        for service in _TYPE_MAP
        if service in services
        for slot in _SLOTS
        if services[service][slot + "active"]
    ]


@final
class Source(BaseSource):
    TITLE = "Basildon Council"
    DESCRIPTION = "Source for basildon.gov.uk services for Basildon Council, UK."
    URL = "https://basildon.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.GARDEN_WASTE,
        wt.FOOD_WASTE,
        wt.GLASS,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_Addres_001": {"postcode": "CM111BJ", "address": "6, HEADLEY ROAD"},
        "Test_Addres_002": {"postcode": "SS14 1QU", "address": "25 LONG RIDING"},
        "Test_UPRN_001": {"uprn": "100090277795"},
        "Test_UPRN_002": {"uprn": 10024197625},
        "Test_UPRN_003": {"uprn": "10090455610"},
    }

    PARAMS = (alternatives([uprn()], [postcode(), street_address("address")]),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Provide your UPRN, or your postcode and the first line of your "
            "address as the council lists it, e.g. '6, HEADLEY ROAD'. Find your "
            "UPRN at https://www.findmyaddress.co.uk/"
        ),
    }

    # The portal's UPRNs are 12 digits, zero-padded.
    retrieve = retrievers.Request(
        f"{API}/getPropertyRefuseInformation",
        method="POST",
        headers=HEADERS,
        json=lambda key, **_: {"uprn": key},
        before=(
            retrievers.Lookup(
                f"{API}/listPropertiesByPostcode",
                method="POST",
                headers=HEADERS,
                json=lambda postcode=None, **_: {"postcode": postcode},
                given=lambda uprn=None, **_: (
                    str(uprn).zfill(12) if uprn is not None else None
                ),
                raise_for_status=False,
                pick=_pick_uprn,
            ),
        ),
    )

    parse = parsers.JsonParser("refuse", "available_services")

    preprocess = ExplodeList(_service_rows)

    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map=_TYPE_MAP,
        parse_date=date_parsers.for_format("%Y-%m-%d"),
    )
