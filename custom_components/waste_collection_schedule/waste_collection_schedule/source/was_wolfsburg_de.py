from typing import ClassVar, final

from waste_collection_schedule import parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, street
from waste_collection_schedule.preprocessors import Compose, RequireRecords
from waste_collection_schedule.transformers import JsonTransformer

API_URL = "https://abfuhrtermine.waswob.de/php/abfuhr_api.php"

_TYPE_MAP = {
    "Wertstofftonne": wt.RECYCLABLES,
    "Bioabfall": wt.ORGANIC,
    "Restabfall": wt.GENERAL_WASTE,
    "Altpapier": wt.PAPER,
}


def _rows(answer, source) -> list[dict]:
    """Flatten ``{address: {"behaelter": {size: {type: {date: note}}}}}`` to one row per date.

    An unknown address is answered with ``{"success": false, "error": ...}``,
    which carries no ``behaelter`` and so flattens to nothing.
    """
    rows: list[dict] = []
    if not isinstance(answer, dict) or answer.get("success") is False:
        return rows
    entry = next(iter(answer.values()), None)
    if not isinstance(entry, dict):
        return rows
    for container in (entry.get("behaelter") or {}).values():
        for name in _TYPE_MAP:
            for date in container.get(name) or {}:
                rows.append({"date": date, "type": name})
    return rows


def _street_names(response, **_) -> list[str]:
    streets = response.json()
    if not isinstance(streets, dict):
        return []
    return sorted(str(s.get("strName", "")) for s in streets.values())


@final
class Source(BaseSource):
    TITLE = "Wolfsburger Abfallwirtschaft und Straßenreinigung"
    DESCRIPTION = "Source for waste collections for WAS-Wolfsburg, Germany."
    URL = "https://was-wolfsburg.de"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Barnstorf": {"street": "Bahnhofspassage", "number": 1},
        "Sülfeld": {"street": "Bärheide", "number": 1},
    }

    PARAMS = (street("street"), house_number("number"))

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter the street name and house number exactly as listed on "
            "https://abfuhrtermine.waswob.de/."
        ),
        "de": (
            "Straßenname und Hausnummer wie auf "
            "https://abfuhrtermine.waswob.de/ angegeben."
        ),
    }

    # The API answers an unknown address with HTTP 502 and a JSON error body.
    retrieve = retrievers.Request(
        API_URL,
        params=lambda street, number, **_: {
            "action": "termine",
            "strasse": street,
            "hausnummer": number,
        },
        raise_for_status=False,
    )

    parse = parsers.JsonParser()

    preprocess = Compose(
        _rows,
        RequireRecords(
            argument="street",
            suggestions=retrievers.Suggestions(
                API_URL, params={"action": "strassen"}, pick=_street_names
            ),
            hint="use the street and house number as listed on abfuhrtermine.waswob.de",
        ),
    )

    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map=_TYPE_MAP,
    )
