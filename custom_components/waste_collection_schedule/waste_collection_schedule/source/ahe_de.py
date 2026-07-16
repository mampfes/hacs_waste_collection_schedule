import waste_collection_schedule.service.AppAbfallplusDe as AppAbfallplusDe
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]

TITLE = "AHE Ennepe-Ruhr-Kreis"
DESCRIPTION = "Source for AHE Ennepe-Ruhr-Kreis."
URL = "https://ahe.de"
COUNTRY = "de"
TEST_CASES = {
    "Wetter Ahornstraße 1": {
        "city": "Wetter",
        "strasse": "Ahornstraße",
        "hnr": "1",
    },
    "Herdecke Alte Straße 1": {
        "city": "Herdecke",
        "strasse": "Alte Straße",
        "hnr": "1",
    },
}

ICON_MAP = {
    "restabfall": Icons.GENERAL_WASTE,
    "restmüll": Icons.GENERAL_WASTE,
    "bioabfall": Icons.BIO_KITCHEN,
    "bio": Icons.ORGANIC,
    "papier": Icons.PAPER,
    "gelber sack": Icons.PLASTIC_PACKAGING,
    "wertstoff": Icons.RECYCLING,
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Visit [https://ahe.de/abfallkalender/](https://ahe.de/abfallkalender/) and select your city and street. Use the exact city name as the `city` parameter (e.g. `Wetter`, `Herdecke`, `Gevelsberg`)."
}

APP_ID = "de.abfallplus.ahe"


class Source:
    def __init__(
        self,
        city: str,
        strasse: str,
        hnr: str | int | None = None,
        bezirk: str | None = None,
    ):
        self._app = AppAbfallplusDe.AppAbfallplusDe(
            app_id=APP_ID,
            kommune=city,
            strasse=strasse,
            hnr=str(hnr) if isinstance(hnr, int) else hnr,
            bezirk=bezirk,
        )

    def fetch(self) -> list[Collection]:
        entries = []
        for d in self._app.generate_calendar():
            bin_type = d["category"]
            icon = None
            for name, icon_value in ICON_MAP.items():
                if name in bin_type.lower():
                    icon = icon_value
                    break
            entries.append(Collection(date=d["date"], t=bin_type, icon=icon))
        return entries
