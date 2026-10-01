from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city
from waste_collection_schedule.service.TribeEvents import TribeEventsRetriever
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Abfallwirtschaft Kyffhäuserkreis"
    DESCRIPTION = (
        "Source for Abfallwirtschaft Kyffhäuserkreis, covering waste collection "
        "schedules for towns and villages within the Kyffhäuserkreis district, "
        "Thuringia, Germany."
    )
    URL = "https://abfall-kyffhaeuser.de"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Ebeleben (single schedule)": {"city": "Ebeleben"},
        "Bad Frankenhausen - Tour 1": {"city": "Bad Frankenhausen - Tour 1"},
        "Sondershausen - Tour 3": {"city": "Sondershausen - Tour 3"},
    }

    PARAMS = (city(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Visit https://abfall-kyffhaeuser.de/kalender/, open the 'Ort' filter "
            "and use the exact place name shown there as the 'city' argument. Larger "
            "towns (Bad Frankenhausen, Sondershausen, Artern) are split into several "
            "collection tours ('Tour 1', 'Tour 2', ...) - check your bin / waste "
            "collection notice or ask the Kyffhäuserkreis waste department which "
            "tour serves your street. If you enter an unknown or ambiguous name, "
            "the resulting error message will list the valid place names."
        ),
        "de": (
            "Besuchen Sie https://abfall-kyffhaeuser.de/kalender/, öffnen Sie den "
            "Filter 'Ort' und verwenden Sie den dort angezeigten Namen exakt als "
            "'city'-Parameter. Größere Orte (Bad Frankenhausen, Sondershausen, "
            "Artern) sind in mehrere Abfuhrtouren ('Tour 1', 'Tour 2', ...) "
            "aufgeteilt - bitte prüfen Sie Ihren Abfuhrkalender/-bescheid oder "
            "fragen Sie bei der Abfallwirtschaft Kyffhäuserkreis nach, welche Tour "
            "für Ihre Straße zuständig ist. Bei unbekannten oder mehrdeutigen "
            "Namen listet die Fehlermeldung alle gültigen Ortsnamen auf."
        ),
    }

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    retrieve = TribeEventsRetriever(base_url="https://abfall-kyffhaeuser.de")
    parse = parsers.EachResponse(parsers.JsonParser("events"))
    transform = JsonTransformer(
        date_key="start_date",
        type_key="title",
        type_value_map={
            "Restabfall": wt.GENERAL_WASTE,
            "Biotonne": wt.ORGANIC,
            "Papiertonne": wt.PAPER,
            "Gelbe Tonne": wt.RECYCLABLES,
            "Gelber RC": wt.RECYCLABLES,
        },
    )
