from typing import ClassVar, final

from waste_collection_schedule import date_parsers, regions
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    city,
    house_number,
    street,
    text_field,
)
from waste_collection_schedule.field_terms import SERVICE_ID
from waste_collection_schedule.retrievers import LookupChainRetriever
from waste_collection_schedule.service import Awido
from waste_collection_schedule.transformers import JsonTransformer

# AWIDO (Cubefour) is one web service for dozens of German districts and towns,
# one ``customer`` id each. The address walk (place, street, house number) and
# the calendar document are the platform's, in ``service/Awido.py``; this source
# declares them and the clients live in ``doc/regions/awido_de.yaml``.


@final
class Source(BaseSource):
    TITLE = "AWIDO Online"
    DESCRIPTION = "Source for AWIDO waste collection."
    URL = "https://www.awido-online.de/"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.BULKY_WASTE,
        wt.GARDEN_WASTE,
        wt.GENERAL_WASTE,
        wt.HAZARDOUS,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Giffhorn, Hankensbüttel, Allersehl": {
            "customer": "gifhorn",
            "city": "Hankensbüttel",
            "street": "Allersehl",
        },
        "Altenburg, Langenleuba-Niederhain": {
            "customer": "awb-altenburg",
            "city": "Langenleuba-Niederhain",
        },
        "coburg rödental krötenleite 4": {
            "customer": "coburg",
            "city": "rödental",
            "street": "krötenleite",
            "housenumber": 4,
        },
        "Schorndorf, Miedelsbacher Straße 30 /1": {
            "customer": "rmk",
            "city": "Schorndorf",
            "street": "Miedelsbacher Straße",
            "housenumber": "30 /1",
        },
        "Altomünster, Maisbrunn": {
            "customer": "lra-dah",
            "city": "Altomünster",
            "street": "Maisbrunn",
        },
        "SOK-Alsmannsdorf": {"customer": "zaso", "city": "SOK-Alsmannsdorf"},
        "Kaufbeuren, Rehgrund": {
            "customer": "kaufbeuren",
            "city": "Kaufbeuren",
            "street": "Rehgrund",
        },
        "Tübingen, Dettenhausen": {"customer": "tuebingen", "city": "Dettenhausen"},
        "Berchtesgadener Land": {
            "customer": "bgl",
            "city": "Laufen",
            "street": "Ahornweg",
            "housenumber": 1,
        },
        "Daaden-Herdorf": {"customer": "awb-ak", "city": "VG Daaden-Herdorf"},
        "Mühldorf": {"customer": "lra-mue", "city": "Ampfing", "street": "Marktplatz"},
        "Roth": {"customer": "roth", "city": "Spalt", "street": "Pflugsmühler Weg"},
        "Kissing Karwendelweg": {
            "customer": "aic-fdb",
            "city": "Kissing",
            "street": "Karwendelweg",
        },
        "Gießen": {"customer": "lkgi", "city": "Langgöns", "street": "Hauptstraße"},
        "Gotha, Ahornweg": {"customer": "gotha", "city": "Gotha", "street": "Ahornweg"},
        "Gotha, Drei Gleichen OT Günthersleben, Mittelstr": {
            "customer": "gotha",
            "city": "Drei Gleichen OT Günthersleben",
            "street": "Mittelstr",
        },
        "Ulm, Bahnhofplatz": {
            "customer": "ebu",
            "city": "Ulm",
            "street": "Bahnhofplatz",
        },
    }

    REGIONS = regions.from_yaml("awido_de", customer="customer", city="city")

    PARAMS = (
        text_field("customer", term=SERVICE_ID),
        city(),
        street(optional=True),
        house_number(field="housenumber", optional=True),
    )

    retrieve = LookupChainRetriever(
        steps=Awido.steps(),
        url=Awido.data_url,
        params=Awido.data_params,
    )
    parse = Awido.AwidoParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        description_key="description",
        parse_date=date_parsers.for_format("%Y%m%d"),
    )
