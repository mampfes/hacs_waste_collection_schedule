from typing import ClassVar, final

from waste_collection_schedule import date_parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import district, municipality, street
from waste_collection_schedule.service import DataPublicLu
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Luxembourg"
    DESCRIPTION = "Source for Luxembourg waste collection using data.public.lu"
    URL = "https://data.public.lu"
    COUNTRY = "lu"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.ORGANIC,
        wt.PAPER,
        wt.GLASS,
        wt.BULKY_WASTE,
        wt.GARDEN_WASTE,
        wt.ELECTRONICS,
        wt.HAZARDOUS,
        wt.METAL,
        wt.TEXTILES,
        wt.OTHER,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Beaufort": {"commune": "Beaufort"},
        "Reisdorf": {"commune": "Reisdorf"},
        "Bech - specific street": {
            "commune": "Bech",
            "localite": "Bech",
            "rue": "Am Biirk",
        },
        "Pétange - Rodange": {
            "commune": "Pétange",
            "localite": "Rodange",
            "rue": "Rue Willy Huberty",
        },
    }

    PARAMS = (
        municipality("commune"),
        district("localite", optional=True),
        street("rue", optional=True),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your commune as listed in the open data set on data.public.lu "
            "(the 'Commune' column, with accents). Communes that split their "
            "schedule also need the locality ('Localité') and, for some "
            "localities, the street ('Rue'). A missing or wrong value lists the "
            "valid ones."
        ),
    }

    retrieve = retrievers.Request(DataPublicLu.CSV_URL, timeout=60)
    parse = DataPublicLu.CalendarParser()

    transform = JsonTransformer(
        date_key="Date",
        type_key="Type de collecte",
        parse_date=date_parsers.for_format("%d/%m/%Y"),
        type_value_map={
            "Biodéchets": wt.ORGANIC,
            "Conteneur pour déchets ménagers": wt.GENERAL_WASTE,
            "Déchets ménagers en mélange": wt.GENERAL_WASTE,
            "Déchets de verdure": wt.GARDEN_WASTE,
            "Arbres de Noël": wt.GARDEN_WASTE,
            "Déchets d'équipements électriques et électroniques": wt.ELECTRONICS,
            "Déchets d’équipements électriques et électroniques": wt.ELECTRONICS,
            "Déchets encombrants": wt.BULKY_WASTE,
            "Déchets encombrants en vrac": wt.BULKY_WASTE,
            "Déchets recyclables": wt.RECYCLABLES,
            "Valorlux": wt.RECYCLABLES,
            "Ferraille": wt.METAL,
            "Papier/Carton": wt.PAPER,
            "Papier/Carton (commerces)": wt.PAPER,
            "Papier/Carton – 40L": wt.PAPER,
            "SuperDrecksKëscht": wt.HAZARDOUS,
            "Verre": wt.GLASS,
            "Verre (commerces)": wt.GLASS,
            "Verre – 40L": wt.GLASS,
            "Vieux bois": wt.OTHER,
            "Vieux vêtements": wt.TEXTILES,
        },
    )
