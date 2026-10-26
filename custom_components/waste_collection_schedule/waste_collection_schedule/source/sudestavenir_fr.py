from typing import ClassVar, final

from waste_collection_schedule import parsers, preprocessors, regions
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, municipality, street
from waste_collection_schedule.service.GeoSoftware import CalendarRetriever, schedules
from waste_collection_schedule.transformers import RowTransformer


@final
class Source(BaseSource):
    TITLE = "Grand Paris Sud Est Avenir (GPSEA)"
    DESCRIPTION = "Source script for sudestavenir.fr, waste collection schedules for the Grand Paris Sud Est Avenir (GPSEA) intercommunal territory"
    URL = "https://sudestavenir.fr/"
    COUNTRY = "fr"
    TEST_CASES: ClassVar[dict] = {
        "1 Place du Grand Pavois, Creteil": {
            "commune": "Creteil",
            "street": "Place du Grand Pavois",
            "house_number": "1",
        }
    }
    TEST_CASES = {
        **TEST_CASES,
        "Provider abbreviated street": {
            "commune": "Creteil",
            "street": "PL DU GRAND PAVOIS",
            "house_number": "1",
        },
    }
    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unknown street": {
            "commune": "Creteil",
            "street": "zzzznotreal",
            "house_number": "1",
        }
    }
    REGIONS: ClassVar[list] = [
        regions.region(
            "Alfortville", url="https://sudestavenir.fr/", commune="Alfortville"
        ),
        regions.region(
            "Boissy-Saint-Léger",
            url="https://sudestavenir.fr/",
            commune="Boissy-Saint-Léger",
        ),
        regions.region(
            "Bonneuil-sur-Marne",
            url="https://sudestavenir.fr/",
            commune="Bonneuil-sur-Marne",
        ),
        regions.region(
            "Chennevières-sur-Marne",
            url="https://sudestavenir.fr/",
            commune="Chennevières-sur-Marne",
        ),
        regions.region("Créteil", url="https://sudestavenir.fr/", commune="Créteil"),
        regions.region(
            "Limeil-Brévannes",
            url="https://sudestavenir.fr/",
            commune="Limeil-Brévannes",
        ),
        regions.region("Noiseau", url="https://sudestavenir.fr/", commune="Noiseau"),
        regions.region(
            "Ormesson-sur-Marne",
            url="https://sudestavenir.fr/",
            commune="Ormesson-sur-Marne",
        ),
        regions.region(
            "Le Plessis-Trévise",
            url="https://sudestavenir.fr/",
            commune="Le Plessis-Trévise",
        ),
        regions.region(
            "La Queue-en-Brie",
            url="https://sudestavenir.fr/",
            commune="La Queue-en-Brie",
        ),
        regions.region(
            "Sucy-en-Brie", url="https://sudestavenir.fr/", commune="Sucy-en-Brie"
        ),
    ]
    PARAMS = (municipality("commune"), street(), house_number())
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GLASS,
        wt.BULKY_WASTE,
        wt.GARDEN_WASTE,
    ]
    HOWTO: ClassVar[dict] = {
        "en": "Enter your GPSEA commune, street and house number. French street types such as Place/PL and Avenue/AV are accepted. The infosheet supplies recurring weekdays, date lists, seasons and morning/afternoon details. Dated precision belongs to the year of its published calendar link. Since the v3 pipeline migration, waste types use canonical, localised names; update filters, automations and customisations using the old labels."
    }
    retrieve = CalendarRetriever(
        "https://geo.gpsea.fr/adws/app/3394f2c6-49bc-11ea-90a1-114edab0a319",
        source_id="ecce3c92-5194-11ea-9e88-250d8464572d",
        filters=(
            "79029f6a-f185-11e9-9256-e1c42467b095",
            "a09256bf-f185-11e9-9256-e1c42467b095",
            "e3fd1e85-5188-11ea-9e88-250d8464572d",
            "af552d94-f185-11e9-9256-e1c42467b095",
        ),
        info_sheet="2215b34d-11f1-11eb-8a48-9979b5aed361",
    )
    parse = parsers.JsonParser("properties")
    preprocess = preprocessors.Compose(
        preprocessors.DefaultPreprocessor(),
        preprocessors.RecurrenceExpander(schedules),
        preprocessors.Deduplicate(),
        preprocessors.SortRows(),
    )
    transform = RowTransformer(
        clean=lambda key: key.split("|")[0],
        description_key=lambda row: {"AM": "Matin", "PM": "Après-midi"}.get(
            row[1].split("|")[1]
        ),
        type_value_map={
            "om": wt.GENERAL_WASTE,
            "em": wt.RECYCLABLES,
            "ve": wt.GLASS,
            "ec": wt.BULKY_WASTE,
            "dv": wt.GARDEN_WASTE,
        },
    )
