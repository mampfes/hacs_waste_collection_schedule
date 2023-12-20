import waste_collection_schedule.service.AppAbfallplusDe as AppAbfallplusDe
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

SUPPORTED_SERVICES = AppAbfallplusDe.SUPPORTED_SERVICES
EXTRA_INFO = AppAbfallplusDe.get_extra_info
TITLE = "Apps by Abfall+"
DESCRIPTION = "Source for Apps by Abfall+."
URL = "https://www.abfallplus.de/"
TEST_CASES = {
    "de.albagroup.app Braunschweig Hauptstraße 7A  ": {
        "app_id": "de.albagroup.app",
        "city": "Braunschweig",
        "strasse": "Hauptstraße",
        "hnr": "7A",
    },
    "de.k4systems.bonnorange Auf dem Hügel": {
        "app_id": "de.k4systems.bonnorange",
        "strasse": "Auf dem Hügel",
        "hnr": 6,
    },
    "de.ucom.abfallavr Brühl Habichtstr. 4A": {
        "app_id": "de.ucom.abfallavr",
        "strasse": "Habichtstr.",
        "hnr": "4A",
        "city": "Brühl",
    },
    "de.k4systems.abfallappwug Bergen hauptstr. 1": {
        "app_id": "de.k4systems.abfallappwug",
        "strasse": "Alle Straßen",
        "city": "Bergen",
    },
    "de.k4systems.abfallappcux Wurster Nordseeküste Aakweg Alle Hausnummern": {
        "app_id": "de.k4systems.abfallappcux",
        "strasse": "Aakweg",
        "hnr": "Alle Hausnummern",
        "city": "Wurster Nordseeküste",
    },
    "de.abfallwecker Mutzschen, Am Lindigt 1": {
        "app_id": "de.abfallwecker",
        "city": "Dahlen",
        "strasse": "Hauptstraße",
        "hnr": 2,
        "bundesland": "Sachsen",
        "landkreis": "Landkreis Nordsachsen",
    },
    "de.k4systems.leipziglk Brandis Brandis": {
        "app_id": "de.k4systems.leipziglk",
        "city": "Brandis",
        "bezirk": "Brandis",
    },
    # MORE TEST CASES UNCOMMENT IF NEEDED FOR DEBUGGING
    # "de.k4systems.zakb Fürth Ahornweg 3 A": {
    #     "app_id": "de.k4systems.zakb",
    #     "strasse": "Ahornweg",
    #     "hnr": "3 A",
    #     "city": "Fürth",
    # },
    # "de.k4systems.avea Leverkusen Haberstr.": {
    #     "app_id": "de.k4systems.avea",
    #     "strasse": "Haberstr.",
    #     "city": "Leverkusen",
    # },
    # "de.k4systems.abfallappog Bad Peterstal-Griesbach alle Straßen": {
    #     "app_id": "de.k4systems.abfallappog",
    #     "strasse": "Alle Straßen",
    #     "city": "Bad Peterstal-Griesbach",
    # },
    # "de.k4systems.abfallappfuerth Großhabersdorf Am Dürren Grund 1 a": {
    #     "app_id": "de.k4systems.abfallappfuerth",
    #     "strasse": "Am Dürren Grund",
    #     "hnr": "1 a",
    #     "city": "Großhabersdorf",
    # },
    # "de.k4systems.awbgp Bad Boll Ahornstraße Alle Hausnummern": {
    #     "app_id": "de.k4systems.awbgp",
    #     "strasse": "Ahornstraße",
    #     "hnr": "Alle Hausnummern",
    #     "city": "Bad Boll",
    # },
    # # This test case will probably fail in 2025, due to harmonization of waste collection services
    # # https://www.landkreisgoettingen.de/themen-leistungen/abfall-entsorgung/harmonisierung-der-abfallwirtschaften 
    # "de.k4systems.lkgoettingen Altkreis Osterode": {
    #     "app_id": "de.k4systems.lkgoettingen",
    #     "landkreis": "Abfallwirtschaft Altkreis Osterode am Harz",
    #     "city": "Osterode am Harz",
    #     "strasse": "Kornmarkt",
    #     "bezirk": "Osterode am Harz"
    # }
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
        strasse: str | None = None,
        hnr: str | int | None = None,
        bezirk: str | None = None,
        city: str | None = None,
        bundesland: str | None = None,
        landkreis: str | None = None,
    ):
        self._app = AppAbfallplusDe.AppAbfallplusDe(
            app_id=app_id,
            kommune=city,
            strasse=strasse,
            hnr=str(hnr) if isinstance(hnr, int) else hnr,
            bundesland=bundesland,
            landkreis=landkreis,
            bezirk=bezirk,
        )

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
