import waste_collection_schedule.service.AppAbfallplusDe as AppAbfallplusDe
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

SUPPORTED_SERVICES = AppAbfallplusDe.SUPPORTED_SERVICES
EXTRA_INFO = AppAbfallplusDe.get_extra_info
EXTRA_INFO_LANG = "de"
TITLE = "Apps by Abfall+"
TITLE_LANG = "de"
DESCRIPTION = "Source for Apps by Abfall+."
DESCRIPTION_LANG = "de"
URL = "https://www.abfallplus.de/"
TEST_CASES = {
    "de.k4systems.abfallappnf Ahrenviöl alle Straßen": {
        "app_id": "de.k4systems.abfallappnf",
        "city": "Ahrenviöl",
        "street": "Alle Straßen",
    },
    "de.albagroup.app Braunschweig Hauptstraße 7A  ": {
        "app_id": "de.albagroup.app",
        "city": "Braunschweig",
        "street": "Hauptstraße",
        "house_number": "7A",
    },
    "de.k4systems.bonnorange Auf dem Hügel": {
        "app_id": "de.k4systems.bonnorange",
        "city": "A",  # First letter of street required
        "street": "Auf dem Hügel",
        "house_number": 6,
    },
    "de.ucom.abfallavr Brühl Habichtstr. 4A": {
        "app_id": "de.ucom.abfallavr",
        "street": "Habichtstr.",
        "house_number": "4A",
        "city": "Brühl",
    },
    "de.k4systems.abfallappwug Bergen hauptstr. 1": {
        "app_id": "de.k4systems.abfallappwug",
        "street": "Alle Straßen",
        "city": "Bergen",
    },
    "de.k4systems.abfallappcux Wurster Nordseeküste Aakweg Alle Hausnummern": {
        "app_id": "de.k4systems.abfallappcux",
        "street": "Aakweg",
        "house_number": "Alle Hausnummern",
        "city": "Wurster Nordseeküste",
    },
    "de.abfallwecker Mutzschen, Am Lindigt 1": {
        "app_id": "de.abfallwecker",
        "city": "Dahlen",
        "street": "Hauptstraße",
        "house_number": 2,
        "bundesland": "Sachsen",
        "landkreis": "Landkreis Nordsachsen",
    },
    "de.k4systems.leipziglk Brandis Brandis": {
        "app_id": "de.k4systems.leipziglk",
        "city": "Brandis",
        "district": "Brandis",
    },
    "de.k4systems.leipziglk Machern Machern": {
        "app_id": "de.k4systems.leipziglk",
        "city": "Machern",
        "district": "Machern",
        "street": "alle Straßen",
    },
    "de.k4systems.lkgoettingen, Abfallwirtschaft Altkreis Göttingen,  Adelebsen, Alle Straßen": {
        "app_id": "de.k4systems.lkgoettingen",
        "landkreis": "Abfallwirtschaft Altkreis Göttingen",
        "city": "Adelebsen",
        "street": "Alle Straßen",
        "district": "Adelebsen",
    },
    # MORE TEST CASES UNCOMMENT IF NEEDED FOR DEBUGGING
    # "de.k4systems.zakb Fürth Ahornweg 3": {
    #     "app_id": "de.k4systems.zakb",
    #     "street": "Ahornweg",
    #     "house_number": "3",
    #     "city": "Fürth",
    # },
    # "de.albagroup.app Kreis Oberhavel, Region Marwitz, Oberkrämer, Dreihügelweg  ": {
    #     "app_id": "de.albagroup.app",
    #     "district": "Marwitz",
    #     "city": "Oberkrämer",
    #     "street": "Dreihügelweg",
    #     "landkreis": "Oberhavel",
    # },
    # "de.k4systems.avea Leverkusen Haberstr.": {
    #     "app_id": "de.k4systems.avea",
    #     "street": "Haberstr.",
    #     "city": "Leverkusen",
    # },
    # "de.k4systems.abfallappog Bad Peterstal-Griesbach alle Straßen": {
    #     "app_id": "de.k4systems.abfallappog",
    #     "street": "Alle Straßen",
    #     "city": "Bad Peterstal-Griesbach",
    # },
    # "de.k4systems.abfallappfuerth Großhabersdorf Am Dürren Grund 1 a": {
    #     "app_id": "de.k4systems.abfallappfuerth",
    #     "street": "Am Dürren Grund",
    #     "house_number": "1",
    #     "city": "Großhabersdorf",
    # },
    # "de.k4systems.awbgp Bad Boll Ahornstraße Alle Hausnummern": {
    #     "app_id": "de.k4systems.awbgp",
    #     "street": "Ahornstraße",
    #     "house_number": "Alle Hausnummern",
    #     "city": "Bad Boll",
    # },
    # "de.k4systems.abfalllkbz Hoyerswerda district: WK VIII": {
    #     "app_id": "de.k4systems.abfalllkbz",
    #     "district": "WK VIII",
    #     "city": "Hoyerswerda",
    # },
    # "de.idcontor.abfallwbd Duisburg, Rahm Am Junkersknappen 6": {
    #     "app_id": "de.idcontor.abfallwbd",
    #     "street": "Am Junkersknappen",
    #     "district": "Rahm",
    #     "house_number": "6",
    #     "city": "Duisburg",
    # },
    # "de.k4systems.awbrastatt Muggensturm Adlergasse": {
    #     "app_id": "de.k4systems.awbrastatt",
    #     "street": "Adlergasse",
    #     "city": "Muggensturm",
    # },
    # # This test case will probably fail in 2025, due to harmonization of waste collection services
    # # https://www.landkreisgoettingen.de/themen-leistungen/abfall-entsorgung/harmonisierung-der-abfallwirtschaften
    # "de.k4systems.lkgoettingen Altkreis Osterode": {
    #     "app_id": "de.k4systems.lkgoettingen",
    #     "landkreis": "Abfallwirtschaft Altkreis Osterode am Harz",
    #     "city": "Osterode am Harz",
    #     "street": "Kornmarkt",
    #     "district": "Osterode am Harz"
    # }
    # "de.k4systems.abfallscout Hammelburg Morlesau": {
    #     "app_id": "de.k4systems.abfallscout",
    #     "city": "Hammelburg",
    #     "district": "Morlesau",
    #     # "street": "Alle Straßen", # OPTIONAL
    #     # "house_number": "Alle Hausnummern" # OPTIONAL
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
        street: str | None = None,
        house_number: str | int | None = None,
        district: str | None = None,
        city: str | None = None,
        bundesland: str | None = None,
        landkreis: str | None = None,
    ):
        self._app = AppAbfallplusDe.AppAbfallplusDe(
            app_id=app_id,
            kommune=city,
            street=street,
            house_number=(
                str(house_number) if isinstance(house_number, int) else house_number
            ),
            bundesland=bundesland,
            landkreis=landkreis,
            district=district,
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
