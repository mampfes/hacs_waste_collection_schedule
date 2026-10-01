from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, house_number, street
from waste_collection_schedule.service.junker_app import TYPE_VALUE_MAP, JunkerParser
from waste_collection_schedule.service.junker_street import JunkerStreetRetriever
from waste_collection_schedule.transformers import RowTransformer

TITLE = "CIDIU S.p.A."
DESCRIPTION = (
    "Source for CIDIU waste collection services for the north-west Turin province"
)
URL = "https://cidiu.it/"
COUNTRY = "it"

# CIDIU retired its own calendar (cidiu-processer.php) and now publishes the
# schedules through the Junker app, one Junker "municipality" per town, with one
# zone per street or range of street numbers.
TEST_CASES = {
    "Collegno": {
        "city": "COLLEGNO",
        "street": "VIA CONDOVE",
        "street_number": "107",
    },
    "Grugliasco": {
        "city": "GRUGLIASCO",
        "street": "VIALE GRAMSCI",
        "street_number": "18",
    },
    "Rivoli": {
        "city": "RIVOLI",
        "street": "CORSO SUSA",
        "street_number": 124,
    },
}

HOWTO = {
    "en": (
        "Enter the town served by CIDIU (e.g. Collegno), the street name "
        "without the number, and the street number."
    ),
    "it": (
        "Inserisci il comune servito da CIDIU (ad esempio Collegno), il nome "
        "della via senza il numero civico e il numero civico."
    ),
}


@final
class Source(BaseSource):
    TITLE = TITLE
    DESCRIPTION = DESCRIPTION
    URL = URL
    COUNTRY = COUNTRY
    TEST_CASES = TEST_CASES
    HOWTO = HOWTO
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.GLASS,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    PARAMS = (
        city("city"),
        street("street"),
        house_number("street_number"),
    )

    retrieve = JunkerStreetRetriever()
    parse = JunkerParser()
    transform = RowTransformer(type_value_map=TYPE_VALUE_MAP)
