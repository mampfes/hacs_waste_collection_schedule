"""Abfallwirtschaft Rendsburg (awr.de).

On the shared AWR/AWSH ``collection_dates`` API; see
``service/AwrCollectionDates.py`` for the three-lookup chain that resolves the
address and downloads the calendar.
"""

from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, street, waste_types
from waste_collection_schedule.parsers import IcsParser
from waste_collection_schedule.service.AwrCollectionDates import (
    TYPE_VALUE_MAP,
    CollectionDatesRetriever,
    clean_waste_type,
)
from waste_collection_schedule.transformers import ICSTransformer

BASE_URL = "https://www.awr.de"


@final
class Source(BaseSource):
    TITLE = "Abfallwirtschaft Rendsburg"
    DESCRIPTION = "Source for Abfallwirtschaft Rendsburg"
    URL = "https://www.awr.de"
    COUNTRY = "de"
    # Canonical types observed in the calendar feed; the cleaned German labels
    # resolve through the shared multilingual vocabulary.
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Rendsburg": {"city": "Rendsburg", "street": "Hindenburgstraße"},
    }

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter city and street exactly as on https://www.awr.de/service/abfuhrtermine/. A street "
            "lists every container variant the city collects (e.g. Restabfall "
            "2-weekly and 4-weekly). To get only your own bins, select them on "
            "the website and copy the ids from the calendar link, e.g. "
            ".../abfallarten/R02-B02-D04-P04/kalender.ics, into waste_types "
            "as R02,B02,D04,P04. Leave it empty to get every variant."
        ),
        "de": (
            "Ort und Straße genau wie auf https://www.awr.de/service/abfuhrtermine/ eingeben. Eine "
            "Straße liefert alle Behältervarianten des Ortes (z. B. Restabfall "
            "2- und 4-wöchentlich). Um nur die eigenen Tonnen zu erhalten, diese "
            "auf der Website auswählen und die Kennungen aus dem Kalender-Link, "
            "z. B. .../abfallarten/R02-B02-D04-P04/kalender.ics, als "
            "R02,B02,D04,P04 in waste_types eintragen. Leer lassen für alle "
            "Varianten."
        ),
    }

    PARAMS = (city(), street(), waste_types())
    RAISE_ON_EMPTY = True

    retrieve = CollectionDatesRetriever(base_url=BASE_URL)
    parse = IcsParser()
    transform = ICSTransformer(
        type_value_map=TYPE_VALUE_MAP, clean=clean_waste_type, carry_raw_label=True
    )
