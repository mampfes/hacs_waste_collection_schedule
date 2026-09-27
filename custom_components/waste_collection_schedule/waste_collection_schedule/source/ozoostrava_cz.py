from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.preprocessors import FlattenGroups
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import RowTransformer


@final
class Source(BaseSource):
    TITLE = "OZO Ostrava"
    DESCRIPTION = "Waste collection schedules for Ostrava and nearby municipalities"
    URL = "https://ozoostrava.cz"
    COUNTRY = "cz"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.GLASS,
        wt.RECYCLABLES,
        wt.PAPER,
        wt.ORGANIC,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Ostrava Poruba": {
            "obec": "Ostrava",
            "obvod": "Poruba",
            "ulice": "Hlavní třída",
            "cislo": "583",
        },
        "Hladké Životice": {
            "obec": "Hladké Životice",
            "obvod": "Hladké Životice",
            "ulice": "Hlavní",
            "cislo": "12",
        },
    }

    PARAMS = (
        text_field("obec", "Obec (municipality)"),
        text_field("obvod", "Obvod (district)"),
        text_field("ulice", "Ulice (street)"),
        text_field("cislo", "Číslo popisné (house number)"),
    )

    retrieve = HttpGetRetriever(
        url="https://ozoostrava.cz/svoz2.php",
        params=lambda obec, obvod, ulice, cislo, **_: {
            "obec": obec,
            "obvod": obvod,
            "ulice": ulice,
            "cisp": cislo,
            "druh": -1,
        },
    )
    # {"2026-09-01": {"směsný odpad": ..., "sklo": ...}, ...}: each date names
    # the rounds collected on it.
    parse = parsers.JsonParser()
    preprocess = FlattenGroups(with_key=True)
    transform = RowTransformer(
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        type_value_map={
            "směsný odpad": wt.GENERAL_WASTE,
            "sklo": wt.GLASS,
            "plasty": wt.RECYCLABLES,
            "papír": wt.PAPER,
            "bioodpad": wt.ORGANIC,
            "singlestream": wt.RECYCLABLES,
            # Holiday notices, not collections.
            "velikonoce": None,
            "vánoce": None,
        },
    )
