from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import district, integer, street
from waste_collection_schedule.service import PotsdamAbfallkalender
from waste_collection_schedule.transformers import ICSTransformer


@final
class Source(BaseSource):
    TITLE = "Potsdam"
    DESCRIPTION = "Source for Potsdam."
    URL = "https://www.potsdam.de"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.RECYCLABLES,
        wt.PAPER,
        wt.GARDEN_WASTE,
        wt.OTHER,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Golm Akazienweg mixed": {
            "ortsteil": "Golm",
            "strasse": "Akazienweg",
            "rest_rhythm": 4,
            "papier_rhythm": 2,
            "bio_rhythm": 3,
        },
        "Teltower Vorstadt Kurze Str.": {
            "ortsteil": "Teltower Vorstadt",
            "strasse": "Kurze Str.",
            "rest_rhythm": 1,
            "papier_rhythm": 3,
            "bio_rhythm": 5,
        },
        "Uetz-Paaren Kanalweg": {
            "ortsteil": "Uetz-Paaren",
            "strasse": "Kanalweg",
            "rest_rhythm": 4,
            "papier_rhythm": 4,
            "bio_rhythm": 2,
        },
    }

    PARAMS = (
        district("ortsteil"),
        street("strasse"),
        integer("rest_rhythm", "General waste rhythm", default=0),
        integer("papier_rhythm", "Paper rhythm", default=0),
        integer("bio_rhythm", "Organics rhythm", default=0),
        integer("gelb_rhythm", "Recycling rhythm", default=3),
    )

    HOWTO: ClassVar[dict] = {
        "de": (
            "Ortsteil und Straße wie im Abfallkalender der Stadt Potsdam. "
            "Die Rhythmen entsprechen der Auswahl im Kalender: Restabfall, "
            "Bioabfall und Altpapier je 1 = 2x pro Woche, 2 = wöchentlich, "
            "3 = 14-tägig, 4 = 4-wöchentlich; Bioabfall zusätzlich 5 = "
            "Kombileerung."
        ),
        "en": (
            "District and street as in the Potsdam waste calendar. The "
            "rhythms match the choice in the calendar for general waste, "
            "organic waste and paper: 1 = twice a week, 2 = weekly, "
            "3 = every two weeks, 4 = every four weeks; organic waste also "
            "5 = combined emptying."
        ),
    }

    retrieve = PotsdamAbfallkalender.retriever
    parse = parsers.EachResponse(PotsdamAbfallkalender.PotsdamParser())

    transform = ICSTransformer(
        type_value_map={
            "Restabfall": wt.GENERAL_WASTE,
            "Bioabfall": wt.ORGANIC,
            "Leichtverpackungen": wt.RECYCLABLES,
            "Altpapier": wt.PAPER,
            "Biotonnenreinigung": wt.OTHER,
            "Weihnachtsbaumabholung": wt.GARDEN_WASTE,
            "Grünabfallsammlung": wt.GARDEN_WASTE,
        }
    )
