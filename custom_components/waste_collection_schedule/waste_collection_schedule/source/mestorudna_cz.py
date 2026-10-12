from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, preprocessors, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import dropdown
from waste_collection_schedule.transformers import JsonTransformer

# Demonstrates: a header-less open-data CSV (id;date;code) read with
# CsvParser(columns=...), one city-wide calendar narrowed to the household's
# service area by a RowFilter. The even/odd-week codes are the only ones that
# differ between the areas; every other code applies to the whole town.

_EVEN_ONLY = {"SKOS", "D2DPLASTS", "BIOSU"}
_ODD_ONLY = {"SKOL", "D2DPLASTL", "BIOL"}


def _keep_service_area(row, source):
    """Drop the rows of the other week parity than the chosen service area."""
    area = str(source.params.get("city_part", "")).lower()
    if area == "liché týdny":
        return row["code"] not in _EVEN_ONLY
    if area == "sudé týdny":
        return row["code"] not in _ODD_ONLY
    return True


@final
class Source(BaseSource):
    TITLE = "Rudna u Prahy"
    DESCRIPTION = "Source for Rudna u Prahy waste collection"
    URL = "https://www.rudnamesto.cz/"
    COUNTRY = "cz"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Even weeks": {"city_part": "Sudé týdny"},
        "Odd weeks": {"city_part": "Liché týdny"},
        "ALL": {"city_part": "Vše"},
    }

    PARAMS = (
        dropdown(
            "city_part",
            ["Sudé týdny", "Liché týdny", "Vše"],
            label="Service area",
        ),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Choose your service area from the published map "
            "https://www.rudnamesto.cz/odpadovy-kalendar/d-193572. Select whether "
            "waste is collected on even or odd weeks."
        ),
    }

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.PLASTIC,
        wt.METAL,
        wt.CARTONS,
    ]

    retrieve = retrievers.HttpGetRetriever(
        url="https://www.mesto-rudna.cz/odpadovy-kalendar/permanent/data_calendar.csv"
    )

    parse = parsers.CsvParser(delimiter=";", columns=["id", "date", "code"])

    preprocess = preprocessors.RowFilter(_keep_service_area)

    transform = JsonTransformer(
        date_key="date",
        type_key="code",
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        type_value_map={
            "SKOL": wt.GENERAL_WASTE,
            "SKOS": wt.GENERAL_WASTE,
            "TKOJ": wt.GENERAL_WASTE,
            "TKOS": wt.GENERAL_WASTE,
            "B": wt.ORGANIC,
            "BIOJ": wt.ORGANIC,
            "BIOS": wt.ORGANIC,
            "BIOL": wt.ORGANIC,
            "BIOSU": wt.ORGANIC,
            "BS": wt.GARDEN_WASTE,
            "D2DPLAST": [wt.PLASTIC, wt.METAL, wt.CARTONS],
            "D2DPLASTL": [wt.PLASTIC, wt.METAL, wt.CARTONS],
            "D2DPLASTS": [wt.PLASTIC, wt.METAL, wt.CARTONS],
            "D2DPAPIR": wt.PAPER,
            "SHPA": wt.PAPER,
            "SHPL": wt.PLASTIC,
            "SHS": wt.GLASS,  # codespell:ignore shs
            "SHK": wt.METAL,
            "NO": wt.HAZARDOUS,
            "PET": wt.PLASTIC,
        },
    )
