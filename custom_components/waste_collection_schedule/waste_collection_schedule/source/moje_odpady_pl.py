from typing import ClassVar, NamedTuple, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    city,
    house_number,
    street_address,
    text_field,
)
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequiredWithSuggestions,
)
from waste_collection_schedule.parsers import JsonParser
from waste_collection_schedule.preprocessors import ExplodeList
from waste_collection_schedule.retrievers import Lookup, Request
from waste_collection_schedule.transformers import JsonTransformer

_API = "https://waste24.net/client/api/mywaste/v2"


class _Area(NamedTuple):
    org: int
    name: str
    has_addresses: bool


def _comparable(text: str) -> str:
    return text.lower().replace(" ", "").replace(".", "")


def _city(response, *keys, city, voivodeship=None, **_) -> _Area:
    rows = response.json()
    matches = [row for row in rows if _comparable(row["cityName"]) == _comparable(city)]
    if not matches:
        raise SourceArgumentNotFoundWithSuggestions(
            "city", city, [row["cityName"] for row in rows]
        )
    if len(matches) > 1:
        voivodeships = [row["voivodeship"] for row in matches]
        if not voivodeship:
            raise SourceArgumentRequiredWithSuggestions(
                "voivodeship",
                "Voivodeship is required as there are multiple cities with the same name",
                voivodeships,
            )
        matches = [
            row
            for row in matches
            if _comparable(row["voivodeship"]) == _comparable(voivodeship)
        ]
        if not matches:
            raise SourceArgumentNotFoundWithSuggestions(
                "voivodeship", voivodeship, voivodeships
            )
    row = matches[0]
    return _Area(row["org"], row["cityName"], bool(row["countOfChilds"]))


def _address(response, area, *keys, address=None, **_) -> str:
    names = [row["addressName"] for row in response.json()]
    if not address:
        raise SourceArgumentRequiredWithSuggestions(
            "address", "Address is required for this city", names
        )
    for name in names:
        if _comparable(name) == _comparable(address):
            return name
    raise SourceArgumentNotFoundWithSuggestions("address", address, names)


def _number(response, area, matched_address, *keys, house_number=None, **_) -> str:
    numbers = [row["addressNr"] for row in response.json()]
    if not numbers:
        return ""
    if len(numbers) == 1:
        return numbers[0]
    if not house_number:
        raise SourceArgumentRequiredWithSuggestions(
            "house_number", "House number is required for this address", numbers
        )
    for number in numbers:
        if _comparable(number) == _comparable(house_number):
            return number
    raise SourceArgumentNotFoundWithSuggestions("house_number", house_number, numbers)


@final
class Source(BaseSource):
    TITLE = "App Moje Odpady"
    DESCRIPTION = "Source for App Moje Odpady."
    URL = "https://moje-odpady.pl/"
    COUNTRY = "pl"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Aleksandrów woj. śląskie": {
            "city": "Aleksandrów",
            "voivodeship": "woj. śląskie",
        },
        "with address and house_number": {
            "city": "BASZKÓWKA",
            "voivodeship": "woj. mazowieckie",
            "address": "ANTONÓWKI",
            "house_number": "Pozostałe",
        },
        "Marcinów woj. łódzkie": {
            "city": "Marcinów",
            "voivodeship": "woj. łódzkie",
        },
    }

    PARAMS = (
        city("city"),
        text_field("voivodeship", label="Voivodeship", optional=True),
        street_address("address", optional=True),
        house_number("house_number", optional=True),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter the city as listed in the Moje Odpady app. If several cities share "
            "the name, also enter the voivodeship (for example 'woj. mazowieckie'). "
            "Cities that are split into streets additionally need the address "
            "(street) and, where the street has several entries, the house number."
        ),
    }

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.GLASS,
        wt.RECYCLABLES,
        wt.ELECTRONICS,
        wt.BULKY_WASTE,
        wt.TEXTILES,
        wt.OTHER,
    ]

    retrieve = Request(
        f"{_API}/schedule_list.php",
        method="POST",
        before=(
            Lookup(f"{_API}/location_cities.php", method="POST", pick=_city),
            Lookup(
                f"{_API}/location_addresses.php",
                method="POST",
                json=lambda area, **_: {"org": area.org, "city": area.name},
                when=lambda area, **_: area.has_addresses,
                pick=_address,
            ),
            Lookup(
                f"{_API}/location_addresses_nr.php",
                method="POST",
                json=lambda area, matched_address, **_: {
                    "org": area.org,
                    "city": area.name,
                    "address": matched_address,
                },
                when=lambda area, matched_address, **_: matched_address is not None,
                pick=_number,
            ),
        ),
        json=lambda area, matched_address, matched_number, **_: {
            "org": area.org,
            "city": area.name,
            "address": matched_address or "",
            "addressNr": matched_number or "",
        },
    )
    parse = JsonParser()
    preprocess = ExplodeList("containers", into="container")
    transform = JsonTransformer(
        date_key="data",
        type_key=lambda record: record["container"]["containerName"],
        type_value_map={
            "Zmieszane": wt.GENERAL_WASTE,
            "Zmieszane (Worek czarny)": wt.GENERAL_WASTE,
            "Biodegradowalne": wt.ORGANIC,
            "Biodegradowalne (Worek brązowy)": wt.ORGANIC,
            "Bioodpady komunalne": wt.ORGANIC,
            "Bioodpad z roślin": wt.ORGANIC,
            "Papier i tektura": wt.PAPER,
            "Papier i tektura (Worek niebieski)": wt.PAPER,
            "Szkło": wt.GLASS,
            "Szkło (Worek zielony)": wt.GLASS,
            "Metale i tworzywa sztuczne": wt.RECYCLABLES,
            "Metale i tworzywa sztuczne (Worek żółty)": wt.RECYCLABLES,
            "Tworzywa Sztuczne": wt.RECYCLABLES,
            "Elektroodpady": wt.ELECTRONICS,
            "Gabaryty": wt.BULKY_WASTE,
            "Wielkogabarytowe": wt.BULKY_WASTE,
            "Odzież i tekstylia": wt.TEXTILES,
            "Odpady problematyczne": wt.HAZARDOUS,
            # no canonical type: kept under their own label
            "Opony": wt.OTHER,
            "Popiół": wt.OTHER,
            "Popiół i żużel": wt.OTHER,
            "Opłaty": wt.OTHER,
            "Zbiórka objazdowa": wt.OTHER,
        },
        carry_raw_label=True,
    )
