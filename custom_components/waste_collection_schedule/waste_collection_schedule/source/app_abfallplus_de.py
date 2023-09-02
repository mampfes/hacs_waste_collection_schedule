from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.AppAbfallplusDe import (AppAbfallplusDe,
                                                               get_extra_info)

EXTRA_INFO = get_extra_info
TITLE = "Apps by Abfall+"
DESCRIPTION = "Source for Apps by Abfall+."
URL = "https://www.abfallplus.de/"
TEST_CASES = {
    "de.albagroup.app Braunschweig Hauptstraße 7A  ": {
        "app_id": "de.albagroup.app",
        "city": "Braunschweig",
        "strasse": "Hauptstraße",
        "hnr": "7A",
        "bundesland": "",
        "landkreis": "",
    }
}


ICON_MAP = {
    "restmüll": "mdi:trash-can",
    "schwarz": "mdi:trash-can",
    "grau": "mdi:trash-can",
    "glass": "mdi:bottle-soda",
    "bio": "mdi:leaf",
    "braun": "mdi:leaf",
    "pappier": "mdi:package-variant",
    "blaue tonne": "mdi:package-variant",
    "plastik": "mdi:recycle",
    "wertstoff": "mdi:recycle",
    "gelber sack": "mdi:recycle",
}


API_URL = ""


class Source:
    def __init__(
        self,
        app_id: str,
        city: str,
        strasse: str,
        hnr: str | int,
        bundesland: str,
        landkreis: str,
    ):
        self._app = AppAbfallplusDe(app_id, city, strasse, hnr, bundesland, landkreis)

    def fetch(self):
        entries = []
        for d in self._app.generate_calendar():
            bin_type = d["category"]
            icon = None
            for name, icon_str in ICON_MAP.items():
                if name in bin_type.lower():
                    icon = icon_str
                    break

            # Collection icon
            entries.append(Collection(date=d["date"], t=bin_type, icon=icon))

        return entries
