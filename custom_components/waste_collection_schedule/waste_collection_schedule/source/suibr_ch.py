from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, preprocessors
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import dropdown, house_number, street
from waste_collection_schedule.service.Sammelkalender import (
    calendar_retriever,
    split_types,
)
from waste_collection_schedule.transformers import JsonTransformer

_MUNICIPALITIES = [
    "Beckenried",
    "Buochs",
    "Dallenwil",
    "Emmetten",
    "Ennetbürgen",
    "Ennetmoos",
    "Hergiswil",
    "Oberdorf",
    "Stans",
    "Stansstad",
    "Wolfenschiessen",
]

_TYPE_MAP = {
    "Kehricht": wt.GENERAL_WASTE,
    "Grüngut": wt.GARDEN_WASTE,
    "Häckseldienst": wt.GARDEN_WASTE,
    "Karton": wt.PAPER,
    "Papier": wt.PAPER,
    "Alteisen/Metall": wt.METAL,
    "Inertstoff": wt.BULKY_WASTE,
    "Christbaum": wt.OTHER,
    "Hol Bring Markt": wt.OTHER,
    "Repair Café": wt.OTHER,
    "Velobörse": wt.OTHER,
}


@final
class Source(BaseSource):
    TITLE = "SUIBR"
    DESCRIPTION = "Source for SUIBR (Nidwalden) waste collection."
    URL = "https://www.suibr.ch"
    COUNTRY = "ch"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@AlpenGlowNW"]
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.GARDEN_WASTE,
        wt.PAPER,
        wt.METAL,
        wt.BULKY_WASTE,
        wt.OTHER,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Beckenried": {"municipality": "Beckenried", "street": "Acheri", "hnr": 1},
        "Buochs": {"municipality": "Buochs", "street": "Aamättli", "hnr": 2},
        "Dallenwil": {
            "municipality": "Dallenwil",
            "street": "Aawasserstrasse",
            "hnr": 11,
        },
        "Emmetten": {"municipality": "Emmetten", "street": "Altberg", "hnr": 1},
        "Ennetbürgen": {
            "municipality": "Ennetbürgen",
            "street": "Abendweg",
            "hnr": 11,
        },
        "Ennetmoos": {"municipality": "Ennetmoos", "street": "Allweg", "hnr": 2},
        "Hergiswil": {"municipality": "Hergiswil", "street": "Aescheli", "hnr": 1},
        "Oberdorf": {
            "municipality": "Oberdorf",
            "street": "Aawasserstrasse",
            "hnr": 1,
        },
        "Stans": {"municipality": "Stans", "street": "Ächerli", "hnr": 1},
        "Stansstad": {"municipality": "Stansstad", "street": "Acheregg", "hnr": 1},
        "Wolfenschiessen": {
            "municipality": "Wolfenschiessen",
            "street": "Aegerten",
            "hnr": 1,
        },
    }

    PARAMS = (
        dropdown("municipality", _MUNICIPALITIES, label="Municipality"),
        street(optional=True),
        house_number("hnr", optional=True),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Choose your municipality and enter your street and house number as "
            "the calendar at https://www.kvvnw.sammelkalender.ch writes them. "
            "The error message lists the valid values."
        ),
        "de": (
            "Wähle deine Gemeinde und gib Straße und Hausnummer so an, wie der "
            "Kalender auf https://www.kvvnw.sammelkalender.ch sie schreibt. Die "
            "Fehlermeldung nennt die gültigen Werte."
        ),
    }

    retrieve = calendar_retriever(
        "https://www.kvvnw.sammelkalender.ch/kunden_WANN_auswahl_form.php",
        "https://www.kvvnw.sammelkalender.ch/kunden_sammlung_ausw_cont.php",
    )
    parse = parsers.EachResponse(
        parsers.JsonParser(),
        then=preprocessors.ExplodeList(split_types, into="type"),
    )
    transform = JsonTransformer(
        date_key="DATUM",
        type_key="type",
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        type_value_map=_TYPE_MAP,
    )
