from typing import ClassVar, final

from waste_collection_schedule import retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    house_number,
    postcode,
    street,
)
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequiredWithSuggestions,
)
from waste_collection_schedule.transformers import JsonTransformer

API = "https://api.heilbronn.de/garbage-calendar"

_TYPE_MAP = {
    "residual": wt.GENERAL_WASTE,
    "residual_2": wt.GENERAL_WASTE,
    "residual_4": wt.GENERAL_WASTE,
    "residual_big_1": wt.GENERAL_WASTE,
    "residual_big_2": wt.GENERAL_WASTE,
    "residual_big_1_2": wt.GENERAL_WASTE,
    "residual_big_1_3": wt.GENERAL_WASTE,
    "bio": wt.ORGANIC,
    "bio_1": wt.ORGANIC,
    "bio_2": wt.ORGANIC,
    "green": wt.GARDEN_WASTE,
    "light-packaging": wt.RECYCLABLES,
    "paper": wt.PAPER,
    "paper-bundle": wt.PAPER,
    "paper_big_1": wt.PAPER,
    "paper_big_2": wt.PAPER,
    "paper_big_4": wt.PAPER,
    "christmastree": wt.GARDEN_WASTE,
}


def _districts(response, *keys, plz, strasse, hausnr=None, **_) -> list[str]:
    """The collection districts of an address: ``{plz: {street: {number: {...}}}}``."""
    data = response.json()["data"]
    streets = data.get(str(plz))
    if streets is None:
        raise SourceArgumentNotFoundWithSuggestions("plz", plz, list(data))
    numbers = streets.get(strasse)
    if numbers is None:
        raise SourceArgumentNotFoundWithSuggestions("strasse", strasse, list(streets))
    number = str(hausnr) if hausnr else None
    if "*" in numbers:
        # The whole street shares one set of districts.
        entry = numbers["*"]
    elif not number:
        raise SourceArgumentRequiredWithSuggestions(
            "hausnr", "is required for this street", suggestions=list(numbers)
        )
    elif number not in numbers:
        raise SourceArgumentNotFoundWithSuggestions("hausnr", number, list(numbers))
    else:
        entry = numbers[number]
    # One code per waste stream; "city" and "district" are labels, not codes.
    return sorted({v for k, v in entry.items() if k not in ("city", "district")})


def _rows(responses, source=None) -> list[dict]:
    """One row per date of ``{district: {round: {timestamp: "YYYY-MM-DD"}}}``."""
    return [
        {"type": round_name, "date": date}
        for response in responses
        for rounds in response.json()["data"].values()
        for round_name, dates in rounds.items()
        for date in dates.values()
    ]


@final
class Source(BaseSource):
    TITLE = "Heilbronn Entsorgungsbetriebe"
    DESCRIPTION = "Source for city of Heilbronn, Germany."
    URL = "https://heilbronn.de"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.GARDEN_WASTE,
        wt.RECYCLABLES,
        wt.PAPER,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Rosenau": {"plz": 74072, "strasse": "Rosenau", "hausnr": 33},
        "Biberach": {"strasse": "Kehrhüttenstraße", "plz": 74078, "hausnr": "90"},
        "Rosenbergstraße 50": {
            "strasse": "Rosenbergstraße",
            "plz": "74074",
            "hausnr": "50",
        },
    }

    PARAMS = (
        postcode("plz"),
        street("strasse"),
        house_number("hausnr", optional=True),
    )

    HOWTO: ClassVar[dict] = {
        "de": (
            "Gib PLZ und Straße so an, wie sie im Abfallkalender der Stadt "
            "Heilbronn stehen. Die Hausnummer ist nur bei Straßen nötig, in "
            "denen sich die Abfuhrbezirke je Hausnummer unterscheiden."
        ),
        "en": (
            "Enter the postcode and street as they appear in the city of "
            "Heilbronn's waste calendar. The house number is only required for "
            "streets whose collection districts differ by house number."
        ),
    }

    # The address resolves to one collection district per waste stream; the
    # pickup dates are then fetched for each of those districts.
    retrieve = retrievers.FanOutRetriever(
        prepare=retrievers.Lookup(
            API,
            params={"method": "get", "datatype": "districts"},
            pick=_districts,
        ),
        targets=lambda source, districts: districts,
        fetch=retrievers.Request(
            API,
            params=lambda district, districts, **_: {
                "method": "get",
                "datatype": "pickupdates",
                "district": district,
            },
        ),
    )

    parse = staticmethod(_rows)

    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map=_TYPE_MAP,
        carry_raw_label=True,
    )
