from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, district, street, text_field
from waste_collection_schedule.service.MyWasteWatcherCalendar import (
    CalendarParser,
    CalendarRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer, label_cleaner


@final
class Source(BaseSource):
    TITLE = "myWasteWatcher (WasteWatcher.NET)"
    DESCRIPTION = (
        "Source for mywastewatcher.de (WasteWatcher.NET) waste collection schedules."
    )
    URL = "https://www.mywastewatcher.de"
    COUNTRY = "de"
    TEST_CASES: ClassVar[dict] = {
        "Hamminkeln, Molkereistraße (default oguid/app_path)": {
            "ort": "Hamminkeln",
            "strasse": "Molkereistraße",
        },
        "Hamminkeln, Ackerstraße Mehrhoog": {
            "oguid": "B3E02353-2090-4EFA-B3C7-AEC81FBC1E6F",
            "app_path": "abfallkalenderdk",
            "ort": "Hamminkeln",
            "strasse": "Ackerstraße",
            "ortsteil": "Mehrhoog",
        },
        "Hamminkeln, Marktstraße": {
            "oguid": "B3E02353-2090-4EFA-B3C7-AEC81FBC1E6F",
            "app_path": "abfallkalenderdk",
            "ort": "Hamminkeln",
            "strasse": "Marktstraße",
        },
        "Hamminkeln, dropdown label": {"strasse": "Ackerstraße (Mehrhoog)"},
    }
    HOWTO: ClassVar[dict] = {
        "en": "The pre-filled oguid and app_path select Hamminkeln — then just enter city and street exactly as shown on the website. For another municipality, open its calendar page on https://www.mywastewatcher.de (e.g. via the link from your local waste authority): the first path segment of the URL is the app_path (e.g. 'abfallkalenderdk'), and the oguid is the value of the 'oguid' parameter in the URL.",
        "de": "Die vorausgefüllten Werte für oguid und app_path wählen Hamminkeln aus — dann nur noch Ort und Straße genau wie auf der Webseite angezeigt eingeben. Für eine andere Kommune deren Abfallkalender-Seite auf https://www.mywastewatcher.de öffnen (z.B. über den Link des Entsorgungsbetriebs): Das erste Pfad-Segment der URL ist der App-Pfad (z.B. 'abfallkalenderdk'), die OGUID ist der Wert des URL-Parameters 'oguid'.",
    }
    SOURCE_CODEOWNERS: ClassVar[list[str]] = ["@ItsMly"]
    PARAMS = (
        text_field(
            "oguid",
            "Organisation identifier",
            default="B3E02353-2090-4EFA-B3C7-AEC81FBC1E6F",
        ),
        text_field("app_path", "Calendar application", default="abfallkalenderdk"),
        city("ort", optional=True),
        street("strasse", optional=True),
        district("ortsteil", optional=True),
        text_field("bemerkung", "Street qualifier", optional=True),
    )

    retrieve = CalendarRetriever()
    parse = CalendarParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        description_key="description",
        clean=label_cleaner(strip_suffixes=(" HAM02", " HAM03")),
        type_value_map={
            "RM": wt.GENERAL_WASTE,
            "RA": wt.GENERAL_WASTE,
            "PA": wt.PAPER,
            "SC": wt.HAZARDOUS,
            "LP": wt.RECYCLABLES,
            "PP": wt.PAPER,
            "BIO": wt.ORGANIC,
            "Schadstoffmobil": wt.HAZARDOUS,
        },
    )
