from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.transformers import JsonTransformer

STREETS_URL = "https://www.monheim.de/?type=1106181"
DATES_URL = "https://www.monheim.de/?type=1106182"

GARBAGE_TYPE_MAP = {
    "0": "Spülung und Leerung der Restmülltonnen",
    "1": "Wertstoffhof",
    "2": "Schadstoff Mobil",
    "3": "Grünabfälle",
    "4": "Spülung und Leerung der Biotonnen",
    "5": "Gelber Sack",
    "6": "Restmüll",
    "7": "Braune Tonne",
    "8": "Blaue Tonne",
    "9": "zusätzliche Grünabgabe",
}

_REST_CLEANING = wt.preserved(GARBAGE_TYPE_MAP["0"])
_RECYCLING_CENTRE = wt.preserved(GARBAGE_TYPE_MAP["1"])
_BIO_CLEANING = wt.preserved(GARBAGE_TYPE_MAP["4"])


def _datasets(responses, source):
    return [parsers.JsonParser()(response, source) for response in responses]


def _events(datasets, source):
    """Join the street index and calendar, retaining events for all districts."""
    streets = datasets[0].get("streets", [])
    name = source.params["street"]
    match = next(
        (item for item in streets if item["streetname"].lower() == name.lower()),
        None,
    )
    if match is None:
        raise SourceArgumentNotFoundWithSuggestions(
            "street", name, [item["streetname"] for item in streets]
        )
    district = str(match["district"])
    records = datasets[1].get("collectiondates", [])
    return [
        record
        for record in records
        if not (
            districts := [
                part.strip()
                for part in record.get("districts", "").split(",")
                if part.strip()
            ]
        )
        or district in districts
    ]


def _type_label(record):
    type_id = str(record.get("garbageTypes", ""))
    return GARBAGE_TYPE_MAP.get(type_id, type_id)


@final
class Source(BaseSource):
    TITLE = "Monheim am Rhein"
    DESCRIPTION = (
        "Source for Monheim am Rhein waste collection (Stadt Monheim am Rhein, NRW)."
    )
    URL = "https://www.monheim.de"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Marderstraße": {"street": "Marderstraße"},
        "Ackerweg": {"street": "Ackerweg"},
        "Rheinpromenade": {"street": "Rheinpromenade"},
    }
    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unknown street": {"street": "__unknown_street__"},
    }
    PARAMS = (street("street"),)
    HOWTO: ClassVar[dict[str, str]] = {
        "en": "Open https://www.monheim.de/leben-in-monheim/abfall-stadtreinigung/abfallkalender and pick your street; use the exact spelling shown there.",
        "de": "Öffnen Sie https://www.monheim.de/leben-in-monheim/abfall-stadtreinigung/abfallkalender und wählen Sie Ihre Straße; verwenden Sie die genaue Schreibweise.",
    }
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
        wt.HAZARDOUS,
        _REST_CLEANING,
        _RECYCLING_CENTRE,
        _BIO_CLEANING,
    ]

    retrieve = retrievers.FanOutRetriever(
        targets=lambda source, context: (STREETS_URL, DATES_URL),
        fetch=retrievers.Request(lambda target, context, **_: target),
    )
    parse = staticmethod(_datasets)
    preprocess = staticmethod(_events)
    transform = JsonTransformer(
        date_key="dateOfCollection",
        type_key=_type_label,
        type_value_map={
            GARBAGE_TYPE_MAP["0"]: _REST_CLEANING,
            GARBAGE_TYPE_MAP["1"]: _RECYCLING_CENTRE,
            GARBAGE_TYPE_MAP["2"]: wt.HAZARDOUS,
            GARBAGE_TYPE_MAP["3"]: wt.GARDEN_WASTE,
            GARBAGE_TYPE_MAP["4"]: _BIO_CLEANING,
            GARBAGE_TYPE_MAP["5"]: wt.RECYCLABLES,
            GARBAGE_TYPE_MAP["6"]: wt.GENERAL_WASTE,
            GARBAGE_TYPE_MAP["7"]: wt.ORGANIC,
            GARBAGE_TYPE_MAP["8"]: wt.PAPER,
            GARBAGE_TYPE_MAP["9"]: wt.GARDEN_WASTE,
        },
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        skip_unparseable_dates=True,
        carry_raw_label=True,
    )
