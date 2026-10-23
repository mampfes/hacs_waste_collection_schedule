import re
from typing import ClassVar, final

from waste_collection_schedule import retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    city,
    district,
    house_number,
    street,
)
from waste_collection_schedule.parsers import ArgumentGuard, JsonParser
from waste_collection_schedule.preprocessors import NestedDateGroups
from waste_collection_schedule.transformers import RowTransformer

API_URL = "https://www.egn-abfallkalender.de/kalender"
ADDRESS_URL = "https://www.egn-abfallkalender.de/alexa"


def _csrf_token(response, *_, **__) -> str:
    match = re.search(r'name="csrf-token"\s+content="([^"]+)"', response.text)
    return match.group(1) if match else ""


def _available_cities(response, **_) -> list[str]:
    return response.json().get("available_cities", [])


# The calendar page carries a CSRF token that the lookup POST must echo back.
_TOKEN = retrievers.Lookup(API_URL, pick=_csrf_token)


@final
class Source(BaseSource):
    TITLE = "EGN Abfallkalender"
    DESCRIPTION = "Source for EGN Abfallkalender"
    URL = "https://www.egn-abfallkalender.de"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True

    # EGN labels each round by a short code ("HML" is the residual-waste bin,
    # "HML2" a second residual-waste bin on its own rhythm), and the colours
    # they get differ per municipality, so the codes are the stable key. Both
    # residual codes fall on the same day in places; merge them into one entry
    # by default, keeping the code as the description.
    IGNORE_DUPLICATES_DEFAULT = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.PAPER,
        wt.ORGANIC,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Dormagen": {
            "city": "Dormagen",
            "district": "Hackenbroich",
            "street": "Aggerstraße",
            "housenumber": 2,
        },
        "Grefrath": {
            "city": "Grefrath",
            "district": "Grefrath",
            "street": "An Haus Bruch",
            "housenumber": 18,
        },
        "Nettetal": {
            "city": "Nettetal",
            "district": "Kaldenkirchen",
            "street": "Ahornweg",
            "housenumber": 1,
        },
        "Tönisvorst": {
            "city": "Tönisvorst",
            "district": "St. Tönis",
            "street": "Ackerstraße",
            "housenumber": 1,
        },
    }

    PARAMS = (
        city(),
        district(),
        street(),
        house_number("housenumber"),
    )

    HOWTO: ClassVar[dict] = {
        "de": (
            "Wähle Ort, Ortsteil und Straße wie im EGN-Abfallkalender auf "
            "egn-abfallkalender.de und gib die Hausnummer an."
        ),
    }

    retrieve = retrievers.Request(
        API_URL,
        method="POST",
        before=(_TOKEN,),
        headers=lambda token, **_: {"x-csrf-token": token},
        data=lambda token, city, district, street, housenumber, **_: {
            "city": city,
            "district": district,
            "street": street,
            "street_number": housenumber,
        },
    )
    parse = ArgumentGuard(
        JsonParser("waste_discharge"),
        argument="city",
        contains='"waste_discharge"',
        suggestions=retrievers.Suggestions(
            ADDRESS_URL,
            method="POST",
            before=(_TOKEN,),
            headers=lambda token, **_: {
                "x-csrf-token": token,
                "X-Requested-With": "XMLHttpRequest",
            },
            data=lambda token, **_: {"_token": token},
            pick=_available_cities,
        ),
        hint="check city, district, street and house number on egn-abfallkalender.de",
    )
    preprocess = NestedDateGroups()
    transform = RowTransformer(
        type_value_map={
            "HML": wt.GENERAL_WASTE,
            "HML2": wt.GENERAL_WASTE,
            "LVP": wt.RECYCLABLES,
            "PPK": wt.PAPER,
            "BIO": wt.ORGANIC,
        },
        carry_raw_label=True,
    )
