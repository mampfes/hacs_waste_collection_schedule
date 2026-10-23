from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.retrievers import Request
from waste_collection_schedule.service.GminaZgierz import ZgierzParser
from waste_collection_schedule.transformers import ICSTransformer


@final
class Source(BaseSource):
    TITLE = "Gmina Zgierz"
    DESCRIPTION = "Source for Gmina Zgierz garbage collection"
    URL = "https://gminazgierz.pl"
    COUNTRY = "pl"
    RAISE_ON_EMPTY = True

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter the name of your village (location_name) as listed in the "
            "yearly schedule on https://bip.gminazgierz.pl, for example `Grotniki`. "
            "The schedule groups the villages into the regions Rejon I to IV."
        ),
    }

    WASTE_TYPES: ClassVar[list] = [
        wt.BULKY_WASTE,
        wt.GENERAL_WASTE,
        wt.ORGANIC,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Grotniki": {"location_name": "Grotniki"},
        "Biała": {"location_name": "Biała"},
        "Kębliny": {"location_name": "Kębliny"},
        "Rosanów": {"location_name": "Rosanów"},
    }

    PARAMS = (text_field("location_name", "Location name"),)

    retrieve = Request("https://bip.gminazgierz.pl/api/articles/59717")
    parse = ZgierzParser()
    transform = ICSTransformer(
        type_value_map={
            "Segregowane i zmieszane": wt.GENERAL_WASTE,
            "BIO": wt.ORGANIC,
            "Gabaryty": wt.BULKY_WASTE,
        },
    )
