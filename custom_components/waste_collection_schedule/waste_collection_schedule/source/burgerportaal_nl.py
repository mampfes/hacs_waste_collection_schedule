from typing import ClassVar, final

from waste_collection_schedule import parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    dropdown,
    house_number,
    postcode,
    text_field,
)
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.regions import region
from waste_collection_schedule.transformers import JsonTransformer

_API_KEY = "AIzaSyA6NkRqJypTfP-cjWzrZNFJzPUbBaGjOdk"
_API = "https://europe-west3-burgerportaal-production.cloudfunctions.net/exposed"

# organization -> (title, url, BurgerPortaal organisation id)
_ORGANIZATIONS = {
    "assen": ("Gemeente Assen", "https://www.assen.nl/", "138204213565303512"),
    "afvalbeheer": (
        "Barendrecht Albrandswaard Ridderkerk",
        "https://www.bar-afvalbeheer.nl/",
        "138204213564933497",
    ),
    "bat": ("BAT Tilburg", "https://www.batafvalbeheer.nl/", "452048812597339353"),
    "breda": ("Gemeente Breda", "https://www.breda.nl/", "452048812597352613"),
    "groningen": (
        "Gemeente Groningen",
        "https://gemeente.groningen.nl/",
        "452048812597326549",
    ),
    "rmn": (
        "Reinigingsdienst Midden Nederland",
        "https://www.rmn.nl/",
        "138204213564933597",
    ),
    "utrecht": ("Gemeente Utrecht", "https://www.utrecht.nl/", "452048812597339479"),
}


def _id_token(response, **_):
    token = response.json().get("idToken")
    if not token:
        raise ValueError("Authentication token could not be retrieved")
    return token


def _address_id(response, token, *, addition="", **params):
    addresses = response.json()
    if not addresses:
        raise SourceArgumentNotFound("post_code", params["post_code"])
    for address in addresses:
        if address.get("addition") == str(addition or "").upper():
            return address["addressId"]
    return addresses[-1]["addressId"]


@final
class Source(BaseSource):
    TITLE = "BurgerPortaal"
    DESCRIPTION = "Source for BurgerPortaal."
    URL = "https://21burgerportaal.mendixcloud.com/"
    COUNTRY = "nl"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
        wt.HAZARDOUS,
        wt.OTHER,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Assen": {"organization": "assen", "post_code": "9401LN", "house_number": 6},
        "RMN": {
            "organization": "rmn",
            "post_code": "3437GS",
            "house_number": 2,
            "addition": "A",
        },
        "Barendrecht Albrandswaard Ridderkerk": {
            "organization": "afvalbeheer",
            "post_code": "2991AA",
            "house_number": 1,
        },
        "BAT Tilburg": {
            "organization": "bat",
            "post_code": "5071EN",
            "house_number": 122,
        },
        "Breda": {
            "organization": "breda",
            "post_code": "4762BD",
            "house_number": 21,
        },
        "Groningen": {
            "organization": "groningen",
            "post_code": "9733AH",
            "house_number": 66,
        },
        "Utrecht": {
            "organization": "utrecht",
            "post_code": "3581GG",
            "house_number": 7,
        },
    }

    PARAMS = (
        dropdown("organization", list(_ORGANIZATIONS)),
        postcode("post_code"),
        house_number(),
        text_field("addition", optional=True),
    )

    REGIONS = tuple(
        region(title, url=url, organization=key)
        for key, (title, url, _) in _ORGANIZATIONS.items()
    )

    retrieve = retrievers.Request(
        lambda token, addr_id, organization, **_: (
            f"{_API}/organisations/{_ORGANIZATIONS[organization][2]}"
            f"/address/{addr_id}/calendar"
        ),
        headers=lambda token, addr_id, **_: {"authorization": token},
        before=[
            retrievers.Lookup(
                "https://www.googleapis.com/identitytoolkit/v3/relyingparty/signupNewUser",
                method="POST",
                params={"key": _API_KEY},
                pick=_id_token,
            ),
            retrievers.Lookup(
                lambda token, organization, **_: (
                    f"{_API}/organisations/{_ORGANIZATIONS[organization][2]}/address"
                ),
                params=lambda token, post_code, house_number, **_: {
                    "zipcode": post_code,
                    "housenumber": house_number,
                },
                headers=lambda token, **_: {"authorization": token},
                pick=_address_id,
            ),
        ],
    )

    parse = parsers.JsonParser()

    transform = JsonTransformer(
        date_key="collectionDate",
        type_key=lambda item: str(item.get("fraction") or "").lower(),
        skip_unparseable_dates=True,
        type_value_map={
            "opk": wt.PAPER,
            "pbd": wt.RECYCLABLES,
            "groen": wt.GARDEN_WASTE,
            "gft+e": wt.ORGANIC,
            "papier-pmd": [wt.PAPER, wt.RECYCLABLES],
            "rest-gfte": [wt.GENERAL_WASTE, wt.ORGANIC],
            "maas": wt.OTHER,
        },
    )
