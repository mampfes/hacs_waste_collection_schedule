"""GVA Baden (baden.umweltverbaende.at).

Demonstrates: a single district of a multi-district platform. The Baden site used to
list its municipalities on the ``?kat=32`` pages this source scraped; it now offers
one ICS calendar (or a few, per collection area) per municipality. This source keeps
its ``region`` parameter and serves it from the ``umweltverbaende_at`` platform
component, with the district fixed to ``baden``.
"""

from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import municipality, text_field
from waste_collection_schedule.service.Umweltverbaende import (
    UmweltverbaendeParser,
    UmweltverbaendeRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer


@final
class Source(BaseSource):
    TITLE = "GVA Baden"
    DESCRIPTION = "Source for waste collection services Association of Municipalities in the District of Baden"
    URL = "https://baden.umweltverbaende.at/"
    COUNTRY = "at"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"region": "Sooß"},
        "Test_002": {"region": "Mitterndorf"},
        "Test_003": {"region": "Schönau"},
        "Alland": {"region": "Alland", "calendar": "ICS Abfuhrbereich 1"},
    }

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your municipality (`region`) as it is listed at "
            "https://baden.umweltverbaende.at/. A municipality with several "
            "collection areas also needs `calendar`, the calendar's name as "
            "listed there (for example `ICS Abfuhrbereich 1`). The error message "
            "lists the valid values. The `umweltverbaende_at` source serves this "
            "district too."
        ),
        "de": (
            "Geben Sie Ihre Gemeinde (`region`) so an, wie sie auf "
            "https://baden.umweltverbaende.at/ aufgeführt ist. Hat die Gemeinde "
            "mehrere Abfuhrbereiche, ist zusätzlich `calendar` nötig, der Name "
            "des Kalenders wie dort aufgeführt (zum Beispiel `ICS Abfuhrbereich "
            "1`). Die Fehlermeldung nennt die gültigen Werte. Die Quelle "
            "`umweltverbaende_at` bedient diesen Verband ebenfalls."
        ),
    }

    PARAMS = (
        municipality("region"),
        text_field("calendar", optional=True),
    )

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.PAPER,
        wt.ORGANIC,
    ]

    retrieve = UmweltverbaendeRetriever(fixed_district="baden", municipal="region")
    parse = UmweltverbaendeParser()
    transform = ICSTransformer(
        type_value_map={
            "Abholung Restmuell": wt.GENERAL_WASTE,
            "Abholung Gelber Sack": wt.RECYCLABLES,
            "Abholung Altpapier": wt.PAPER,
            "Abholung Biotonne": wt.ORGANIC,
        }
    )
