from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    city,
    dropdown,
    house_number,
    street,
)
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import IcsParser
from waste_collection_schedule.regions import region
from waste_collection_schedule.retrievers import Lookup, LookupChainRetriever
from waste_collection_schedule.transformers import ICSTransformer

_API = "https://smiecioplan.pl/wp-json/smiecioplan/v1"
_BUILDING_TYPES = ["single", "multi"]


def _street(response, *, street: str, **_) -> str:
    """Resolve the street to the provider's spelling (upper case)."""
    wanted = street.strip().upper()
    streets = [s["street"] for s in response.json()]
    if wanted not in (s.upper() for s in streets):
        raise SourceArgumentNotFoundWithSuggestions("street", wanted, streets)
    return wanted


def _house(response, street_name, *, house: str | int, **_) -> str:
    """Check the house number exists on that street."""
    wanted = str(house).strip()
    houses = response.json()
    if wanted not in houses:
        raise SourceArgumentNotFoundWithSuggestions("house", wanted, houses[:20])
    return wanted


@final
class Source(BaseSource):
    TITLE = "SmiecioPlan"
    DESCRIPTION = "Source for SmiecioPlan.pl waste collection schedules."
    URL = "https://smiecioplan.pl"
    COUNTRY = "pl"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.GLASS,
        wt.RECYCLABLES,
        wt.BULKY_WASTE,
        wt.GARDEN_WASTE,
        wt.OTHER,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Szczecin, Aleja Wojska Polskiego 2": {
            "city": "szczecin",
            "street": "ALEJA WOJSKA POLSKIEGO",
            "house": "2",
        },
        "Gdansk, Antoniego Abrahama 1": {
            "city": "gdansk",
            "street": "ANTONIEGO ABRAHAMA",
            "house": "1",
        },
        "Gdynia, Zrodlo Marii 19H (multi-family)": {
            "city": "gdynia",
            "street": "ŹRÓDŁO MARII",
            "house": "19H",
            "building_type": "multi",
        },
        "Gdynia, Zrodlo Marii 19H (single-family)": {
            "city": "gdynia",
            "street": "ŹRÓDŁO MARII",
            "house": "19H",
            "building_type": "single",
        },
    }

    PARAMS = (
        city("city"),
        street("street"),
        house_number("house"),
        dropdown("building_type", _BUILDING_TYPES, "Building Type", optional=True),
    )

    REGIONS = (
        region("Szczecin", city="szczecin"),
        region("Gdańsk", city="gdansk"),
        region("Gdynia", city="gdynia"),
        region("Sopot", city="sopot"),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Go to [smiecioplan.pl](https://smiecioplan.pl) and search for your "
            "address. Use the city (szczecin, gdansk, gdynia or sopot), the street "
            "name in uppercase and the house number. Some addresses (e.g. in "
            "Gdynia) have separate schedules for single-family (`single`) and "
            "multi-family (`multi`) buildings; leave `building_type` empty if your "
            "address only has one schedule."
        ),
    }

    retrieve = LookupChainRetriever(
        steps=(
            Lookup(
                f"{_API}/search",
                params=lambda city, street, **_: {
                    "q": street.strip().upper(),
                    "city": city.strip().lower(),
                    "limit": 50,
                },
                pick=_street,
            ),
            Lookup(
                f"{_API}/houses",
                params=lambda street_name, city, **_: {
                    "street": street_name,
                    "city": city.strip().lower(),
                    "limit": 500,
                },
                pick=_house,
            ),
        ),
        url=f"{_API}/export/ics",
        params=lambda street_name, house_value, city, building_type=None, **_: {
            "street": street_name,
            "house": house_value,
            "city": city.strip().lower(),
            "types": "mixed,segregated,bio,bulky,green,ash",
            **({"building_type": building_type} if building_type else {}),
        },
    )

    parse = IcsParser()

    transform = ICSTransformer(
        type_value_map={
            "♻️ Odpady zmieszane": wt.GENERAL_WASTE,
            "🌿 Bioodpady": wt.ORGANIC,
            "📦 Odpady segregowane — Papier": wt.PAPER,
            "📦 Odpady segregowane — Szkło": wt.GLASS,
            "📦 Odpady segregowane — Metale i tworzywa sztuczne": wt.RECYCLABLES,
            "🛋️ Odpady wielkogabarytowe": wt.BULKY_WASTE,
            "🌱 Odpady zielone": wt.GARDEN_WASTE,
            "🔥 Popiół": wt.OTHER,
        }
    )
