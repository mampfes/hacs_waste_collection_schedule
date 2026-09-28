from typing import ClassVar, NamedTuple, final

from waste_collection_schedule import parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    alternatives,
    area_id,
    dropdown,
    street,
    street_address,
)
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.regions import region
from waste_collection_schedule.transformers import JsonTransformer

_API_URL = "https://wsz-moosburg.at/api"

_MUNICIPAL_IDS = {
    "Moosburg": "20421",
    "Pörtschach": "20424",
    "Techelsberg": "20435",
}


class _Address(NamedTuple):
    """An address node: its id and how many streets sit below it."""

    id: str | int
    sub: int


def _named(response, field: str, name: str) -> dict:
    """The entry called ``name`` in the reply's ``address`` list."""
    entries = [entry["address"] for entry in response.json()["address"]]
    for entry in entries:
        if entry["name"] == name:
            return entry
    raise SourceArgumentNotFoundWithSuggestions(
        field, name, sorted(entry["name"] for entry in entries)
    )


def _address(response, *_, address, **__) -> _Address:
    entry = _named(response, "address", address)
    return _Address(entry["id"], int(entry["sub"]))


def _street_id(response, *_, street=None, **__):
    return _named(response, "street", street or "")["id"]


def _schedule_id(node: _Address, street_id, **_):
    # An address with streets below it resolves to the street; one without
    # already carries the final area id.
    return street_id if street_id is not None else node.id


@final
class Source(BaseSource):
    TITLE = "WSZ Moosburg"
    DESCRIPTION = (
        "Source for WSZ Moosburg/Kärnten, including Moosburg, Pörtschach, Techelsberg"
    )
    URL = "https://wsz-moosburg.at"
    COUNTRY = "at"
    RAISE_ON_EMPTY = True

    REGIONS = (
        region("Moosburg", url=URL),
        region("Pörtschach", url=URL),
        region("Techelsberg", url=URL),
    )

    WASTE_TYPES: ClassVar[list] = [
        wt.PAPER,
        wt.ORGANIC,
        wt.RECYCLABLES,
        wt.GENERAL_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Id: Moosburg, Obergöriach": {"address_id": 70265},
        "Id: Moosburg, Pestalozzistr": {"address_id": 70082},
        "Id: Pörtschach, 10. OktoberStr": {"address_id": 69866},
        "Id: Techelsberg, Südlich der Bahn: Bahnhof Töschling bis Saag Nr. 19": {
            "address_id": 69980
        },
        "Full: Moosburg, Obergöriach": {
            "municipal": "Moosburg",
            "address": "Obergöriach",
            "street": "Obergöriach",
        },
        "Full: Moosburg, Pestalozzistr": {
            "municipal": "Moosburg",
            "address": "Moosburg",
            "street": "Pestalozzistraße",
        },
        "Full: Pörtschach, 10. OktoberStr": {
            "municipal": "Pörtschach",
            "address": "10.-Oktober-Straße",
            "street": "10.-Oktober-Straße",
        },
        "Data: Techelsberg, Südlich der Bahn: Bahnhof Töschling bis Saag Nr. 19": {
            "municipal": "Techelsberg",
            "address": "Südlich der Bahn: Bahnhof Töschling bis Saag Nr. 19",
            "street": "Südlich der Bahn: Bahnhof Töschling bis Saag Nr. 19",
        },
    }

    HOWTO: ClassVar[dict] = {
        "en": (
            "Pick your municipality, then your address and, where the address "
            "has several streets, the street. Alternatively enter the address ID "
            "directly: it is the number in the request "
            "https://wsz-moosburg.at/api/trash/<ID> that the calendar on "
            "wsz-moosburg.at makes for your address."
        ),
        "de": (
            "Wählen Sie Ihre Gemeinde, dann Ihre Adresse und, falls die Adresse "
            "mehrere Straßen hat, die Straße. Alternativ können Sie die "
            "Adressen-ID direkt angeben: das ist die Zahl in der Anfrage "
            "https://wsz-moosburg.at/api/trash/<ID>, die der Kalender auf "
            "wsz-moosburg.at für Ihre Adresse stellt."
        ),
    }

    PARAMS = (
        alternatives(
            [area_id("address_id")],
            [
                dropdown("municipal", list(_MUNICIPAL_IDS)),
                street_address("address"),
                street("street", optional=True),
            ],
        ),
    )

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                lambda municipal, **_: (
                    f"{_API_URL}/address/{_MUNICIPAL_IDS[municipal]}"
                ),
                given=lambda address_id=None, **_: (
                    _Address(address_id, 0) if address_id else None
                ),
                pick=_address,
            ),
            retrievers.Lookup(
                lambda node, municipal, **_: (
                    f"{_API_URL}/address/{_MUNICIPAL_IDS[municipal]}/{node.id}"
                ),
                when=lambda node, **_: node.sub > 0,
                pick=_street_id,
            ),
        ),
        url=lambda node, street_id, **_: (
            f"{_API_URL}/trash/{_schedule_id(node, street_id)}"
        ),
        raise_for_status=True,
    )
    parse = parsers.JsonParser()
    transform = JsonTransformer(
        date_key="start",
        type_key="title",
        type_value_map={
            "Altpapier": wt.PAPER,
            "Biotonne": wt.ORGANIC,
            "Gelber Sack": wt.RECYCLABLES,
            "Restmüll wöchentlich": wt.GENERAL_WASTE,
            "Restmüll 14-tägig": wt.GENERAL_WASTE,
            "Restmüll 4-wöchentlich": wt.GENERAL_WASTE,
        },
        carry_raw_label=True,
    )
