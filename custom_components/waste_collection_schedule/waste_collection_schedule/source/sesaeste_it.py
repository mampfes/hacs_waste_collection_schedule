from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import municipality
from waste_collection_schedule.preprocessors import ExplodeList
from waste_collection_schedule.service.SesaCalendar import (
    CalendarRetriever,
    waste_labels,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "S.E.S.A."
    DESCRIPTION = "Source script for sesaeste.it"
    URL = "https://sesaeste.it"
    COUNTRY = "it"
    SOURCE_CODEOWNERS: ClassVar[list[str]] = ["@AlexSartori"]
    TEST_CASES: ClassVar[dict] = {
        "Legnaro": {"user_municipality": "Legnaro"},
        "Solesino": {"user_municipality": "Solesino"},
        "Polverara": {"user_municipality": "Polverara"},
    }
    HOWTO: ClassVar[dict] = {
        "en": "Use the name of your municipality exactly as it appears in the municipality list of the S.E.S.A. app, for example `Legnaro`.",
        "it": "Usa il nome del tuo comune esattamente come appare nell'elenco dei comuni dell'app S.E.S.A., ad esempio `Legnaro`.",
    }
    PARAMS = (municipality("user_municipality"),)

    retrieve = CalendarRetriever()
    parse = parsers.JsonParser()
    preprocess = ExplodeList(waste_labels, into="waste_type")
    transform = JsonTransformer(
        date_key="Giorno",
        type_key="waste_type",
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        clean=str.capitalize,
        type_value_map={
            "PLASTICA LATTINE": [wt.PLASTIC, wt.METAL],
            "UMIDO": wt.ORGANIC,
            "SECCO": wt.GENERAL_WASTE,
            "CARTA": wt.PAPER,
            "VETRO": wt.GLASS,
            "VERDE": wt.GARDEN_WASTE,
        },
    )
