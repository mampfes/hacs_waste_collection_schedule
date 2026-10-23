from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import integer, street
from waste_collection_schedule.service.SingenCalendar import (
    CalendarParser,
    CalendarRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Stadtwerke Singen"
    DESCRIPTION = "Source for Stadtwerke Singen, Germany."
    URL = "https://www.stadtwerke-singen.de"
    COUNTRY = "de"
    TEST_CASES: ClassVar[dict] = {
        "Im Twielfeld": {"street": "Im Twielfeld"},
        "Beuren (Ortsteil)": {"street": "Beuren"},
        "Alemannenstraße 10": {"street": "Alemannenstraße", "house_number": 10},
        "Alemannenstraße 60": {"street": "Alemannenstraße", "house_number": 60},
    }
    HOWTO: ClassVar[dict[str, str]] = {
        "en": "Street name as listed in the Stadtwerke Singen waste calendar street directory, or one of the outlying districts (Beuren, Bohlingen, Friedingen, Hausen, Schlatt, Überlingen). House number. Only required if the street is split into several address ranges with different collection days (e.g. 'Alemannenstraße').",
        "de": "Straßenname wie im Straßenverzeichnis des Abfallkalenders der Stadtwerke Singen, oder einer der Stadtteile (Beuren, Bohlingen, Friedingen, Hausen, Schlatt, Überlingen). Hausnummer. Nur erforderlich, wenn die Straße in mehrere Adressbereiche mit unterschiedlichen Abfuhrterminen aufgeteilt ist (z. B. 'Alemannenstraße').",
    }
    PARAMS = (
        street(),
        integer("house_number", "House number"),
    )

    retrieve = CalendarRetriever()
    parse = CalendarParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={
            "Biomüllabfuhr": wt.ORGANIC,
            "Restmüllabfuhr (schwarzer Deckel)": wt.GENERAL_WASTE,
            "Restmüll mit rotem Deckel": wt.GENERAL_WASTE,
            "Altpapier": wt.PAPER,
            "Gelbe Tonne": wt.RECYCLABLES,
            "Christbaumabfuhr": wt.GARDEN_WASTE,
        },
        carry_raw_label=True,
    )
