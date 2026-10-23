from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street, text_field
from waste_collection_schedule.service.AmbergCalendar import (
    CalendarParser,
    CalendarRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Amberg"
    DESCRIPTION = "Source for the city of Amberg (Bavaria), Germany."
    URL = "https://www.amberg.de"
    COUNTRY = "de"
    TEST_CASES: ClassVar[dict] = {
        "Street: Adalbert-Stifter-Str. (zone A1)": {"street": "Adalbert-Stifter-Str."},
        "Zone: C4 direct": {"zone": "C4"},
        "Street: Barbarastr. (zone B2)": {"street": "Barbarastr."},
    }
    HOWTO: ClassVar[dict[str, str]] = {
        "en": "Visit https://amberg.de/abfallberatung/abfuhrkalender-2026, look up your street in the table, and note the zone code (e.g. A1). You can then use either the street name or the zone code directly.",
        "de": "Besuchen Sie https://amberg.de/abfallberatung/abfuhrkalender-2026, suchen Sie Ihre Straße in der Tabelle, und notieren Sie das Abfuhrgebiet (z. B. A1). Sie können dann entweder den Straßennamen oder das Abfuhrgebiet direkt verwenden.",
    }
    PARAMS = (
        street(optional=True),
        text_field("zone", "Collection zone", optional=True),
    )

    retrieve = CalendarRetriever()
    parse = CalendarParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={
            # One combined round collects both streams on the same date.
            "Rest- und Biomüll": [wt.GENERAL_WASTE, wt.ORGANIC],
            "Papiertonne": wt.PAPER,
            "Gelber Sack": wt.RECYCLABLES,
            "Sperrmüll": wt.BULKY_WASTE,
            "Häckselgut": wt.GARDEN_WASTE,
            "Problemmüll": wt.HAZARDOUS,
        },
    )
