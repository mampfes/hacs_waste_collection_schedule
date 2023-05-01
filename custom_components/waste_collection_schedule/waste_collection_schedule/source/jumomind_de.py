import datetime
import logging

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Jumomind"
DESCRIPTION = "Source for Jumomind.de waste collection."
URL = "https://www.jumomind.de"
TEST_CASES = {
    # DEPRICATED
    "ZAW": {"service_id": "zaw", "city_id": 106, "area_id": 94},
    "Bad Homburg, Bahnhofstrasse": {"service_id": "hom", "city_id": 1, "area_id": 411},
    "Bad Buchau via MyMuell": {
       "service_id": "mymuell",
       "city_id": 3031,
       "area_id": 3031,
    },
    # END DEPRICATED
    "Darmstaadt ": {
       "service_id": "mymuell",
       "ort": "Darmstadt",
       "strasse": "Achatweg"
    },
    "zaw Alsbach-Hähnlein Hähnleiner Str.": {
       "service_id": "zaw",
       "ort": "Alsbach-Hähnlein",
       "strasse": "Hähnleiner Str."
    },
    "ingolstadt": {
       "service_id": "ingol",
       "ort": "Ingolstadt",
       "strasse": "Hauffstr.",
       "house_number": "9 1/2",
    },
    "mymuell only city": {
        "service_id": "mymuell",
        "ort": "Kipfenberg OT Arnsberg, Biberg, Dunsdorf, Schelldorf, Schambach, Mühlen im Schambachtal und Schambacher Leite, Järgerweg, Böllermühlstraße, Attenzell, Krut, Böhming, Regelmannsbrunn, Hirnstetten und Pfahldorf",
    },
}


ICON_MAP = {
    "Restmüll": "mdi:trash-can",
    "Glass": "mdi:bottle-soda",
    "Biomüll": "mdi:leaf",
    "Papier": "mdi:package-variant",
    "Gelber": "mdi:recycle",
    "Schadstoffmobil": "mdi:truck-alert",
}

SERVICE_MAP = {
    "zaw": {
        "url": "https://www.zaw-online.de",
        "list":["Darmstadt-Dieburg (ZAW)"],
    },
    "ingol": {
        "list": ["Ingolstadt"],
        "url": "https://www.in-kb.de",  
    },
    "mymuell": 
        {
            "comment": "MyMuell App",
            "url": "https://www.mymuell.de/",
            "list": [
                "Abens",
                "Abickhafe",
                "Achstetten",
                "Adelschlag",
                "Alleshausen",
                "Allmannsweiler",
                "Altenbeken-Altenbeken",
                "Altenbeken-Buke",
                "Altenbeken-Schwaney",
                "Altfunnixsiel",
                "Altharlingersiel",
                "Altheim",
                "Altmannstein",
                "Alzenau",
                "Angelsburg",
                "Ardorf",
                "Aschaffenburg",
                "Asel",
                "Attenweiler",
                "Bad Arolsen",
                "Bad Buchau",
                "Bad Lippspringe",
                "Bad Schussenried",
                "Bad Wünnenberg",
                "Beilngries",
                "Bensersiel",
                "Bentstreek",
                "Berdum",
                "Berkheim",
                "Bessenbach",
                "Betzenweiler",
                "Beverungen",
                "Biberach",
                "Biberach",
                "Blankenbach",
                "Blersum",
                "Blomberg",
                "Bockhorn",
                "Böhmfeld",
                "Borchen",
                "Borkum",
                "Bunde",
                "Büren",
                "Burgrieden",
                "Burhafe",
                "Buttforde",
                "Buxheim",
                "Carolinensiel",
                "Dammbach",
                "Darmstadt",
                "Delbrück",
                "Denkendorf",
                "Dettingen",
                "Dollnstein",
                "Dose",
                "Dunum",
                "Dürmentingen",
                "Dürnau",
                "Eberhardzell",
                "Eggelingen",
                "Egweil",
                "Eichstätt",
                "Eitensheim",
                "Erkrath",
                "Erlenmoos",
                "Erolzheim",
                "Ertingen",
                "Esens",
                "Etzel",
                "Eversmeer",
                "Flensburg",
                "Friedeburg",
                "Fulkum",
                "Funnix",
                "Gaimersheim",
                "Geiselbach",
                "Glattbach",
                "Goldbach",
                "Großkrotzenburg",
                "Großmehring",
                "Großostheim",
                "Gutenzell-Hürbel",
                "Haan",
                "Haibach",
                "Hainburg",
                "Heigenbrücken",
                "Heiligenhaus",
                "Heimbuchenthal",
                "Heinrichsthal",
                "Hepberg",
                "Hesel",
                "Hilden",
                "Hitzhofen",
                "Hochdorf",
                "Hoheesche",
                "Holtgast",
                "Horsten",
                "Hösbach",
                "Hovel",
                "Hövelhof",
                "Ingoldingen",
                "Jemgum",
                "Jever",
                "Johannesberg",
                "Jümme",
                "Kahl",
                "Kamp-Lintfort",
                "Kanzach",
                "Karlstein",
                "Kinding",
                "Kipfenberg",
                "Kirchberg",
                "Kirchdorf",
                "Kleinkahl",
                "Kleinostheim",
                "Kösching",
                "Krombach",
                "Langenenslingen",
                "Langenfeld",
                "Laufach",
                "Laupheim",
                "Leer",
                "Leerhafe",
                "Lenting",
                "Lichtenau",
                "Mainaschaff",
                "Marx",
                "Maselheim",
                "Mespelbrunn",
                "Mettmann",
                "Mietingen",
                "Mindelstetten",
                "Mittelbiberach",
                "Mömbris",
                "Moormerland",
                "Moorweg",
                "Moosburg",
                "Mörnsheim",
                "Mühlheim am Main",
                "Musterstadt",
                "Nassenfels",
                "Nenndorf",
                "Neuharlingersiel",
                "Neumünster",
                "Neuschoo",
                "Oberdolling",
                "Ochsenhausen",
                "Ochtersum",
                "Oggelshausen",
                "Ostrhauderfehn",
                "Paderborn",
                "Pförring",
                "Pollenfeld",
                "Ratingen",
                "Reepsholt",
                "Rhauderfehn",
                "Riedlingen",
                "Rot an der Rot",
                "Rothenbuch",
                "Sailauf",
                "Salzgitter",
                "Salzkotten",
                "Sande",
                "Schemmerhofen",
                "Schernfeld",
                "Schmitten im Taunus",
                "Schöllkrippen",
                "Schöneck",
                "Schortens",
                "Schweindorf",
                "Schwendi",
                "Seekirch",
                "Seligenstadt",
                "Sommerkahl",
                "Sommerkahl",
                "Stammham",
                "Stedesdorf",
                "Steinhausen an der Rottum",
                "Stockstadt am Main",
                "Tannheim",
                "Tiefenbach",
                "Titting",
                "Ulm",
                "Ummendorf",
                "Unlingen",
                "Uplengen",
                "Usingen",
                "Utarp",
                "Uttel",
                "Uttenweiler",
                "Varel",
                "Vöhringen",
                "Volkmarsen",
                "Wain",
                "Waldaschaff",
                "Walting",
                "Wangerland",
                "Wangerooge",
                "Warthausen",
                "Weener",
                "Wegberg",
                "Weibersbrunn",
                "Wellheim",
                "Werdum",
                "Westerholt",
                "Westerngrund",
                "Westoverledingen",
                "Wettstetten",
                "Wiesede",
                "Wiesedermeer",
                "Wiesen",
                "Wilhelmshaven",
                "Willen",
                "Willmsfeld",
                "Wittmund",
                "Wülfrath",
                "Zetel"
            ]
        },
}

def EXTRA_INFO():
    extra_info = []
    for provider, entries in SERVICE_MAP.items():
        url = entries["url"]
        comment = ""
        if "comment" in entries:
            comment = f" ({entries['comment']})"
        
        for area in entries["list"]:
            title = area + comment
            
            extra_info.append({"title": title, "url": url})
    return extra_info

        
API_SEARCH_URL = "https://{provider}.jumomind.com/mmapp/api.php"
API_DATES_URL = "https://{provider}.jumomind.com/webservice.php"

LOGGER = logging.getLogger(__name__)

class Source:
    def __init__(self, service_id: str, ort: str = None, strasse: str = None, city_id=None, area_id=None, house_number=None):
        self._search_url: str = API_SEARCH_URL.format(provider=service_id)
        self._dates_url: str = API_DATES_URL.format(provider=service_id)
        self._ort: str = ort.lower().strip() if ort else None
        self._strasse: str = strasse.lower().strip() if strasse else None
        self._house_number: str = str(
            house_number).lower().strip() if house_number else None

        self._service_id = service_id
        self._city_id = city_id if city_id else None
        self._area_id = area_id if area_id else None

    def fetch(self):
        session = requests.Session()

        city_id = self._city_id
        area_id = self._area_id

        if city_id is None and self._ort is None:
            raise Exception("City or city id is required")
        if city_id is not None and self._ort is not None:
            raise Exception("City or city id is required. Do not use both")

        r = session.get(self._search_url, params={"r": "cities_web"})
        r.raise_for_status()

        cities = r.json()

        if not city_id is None:
            if area_id is None:
                raise Exception(
                    "no area id but needed when city id is given. Remove city id when using city (and street) name")
        else:
            has_streets = True
            for city in cities:
                if city["name"].lower().strip() == self._ort or city["_name"].lower().strip() == self._ort:
                    city_id = city["id"]
                    area_id = city["area_id"]
                    has_streets = city["has_streets"]
                    break

            if city_id is None:
                raise Exception("City not found")

            if has_streets:
                r = session.get(self._search_url, params={
                                "r": "streets", "city_id": city_id})
                r.raise_for_status()
                streets = r.json()

                street_found = False
                for street in streets:
                    if street["name"].lower().strip() == self._strasse or street["_name"].lower().strip() == self._strasse:
                        street_found = True
                        area_id = street["area_id"]
                        if "houseNumbers" in street:
                            for house_number in street["houseNumbers"]:
                                if house_number[0].lower().strip() == self._house_number:
                                    area_id = house_number[1]
                                    break
                        break
                if not street_found:
                    raise Exception("Street not found")
            else:
                if self._strasse is not None:
                    LOGGER.warning("City does not need street name please remove it, continuing anyway")

        # get names for bins
        bin_name_map = {}
        r = session.get(self._search_url, params={
                        "r": "trash", "city_id": city_id, "area_id": area_id})
        r.raise_for_status()

        for bin_type in r.json():
            bin_name_map[bin_type["name"]] = bin_type["title"]
            if not bin_type["_name"] in bin_name_map:
                bin_name_map[bin_type["_name"]] = bin_type["title"]

        r = session.get(self._dates_url, params={
                        "idx": "termins", "city_id": city_id, "area_id": area_id, "ws": 3})
        r.raise_for_status()

        entries = []
        for event in r.json()[0]["_data"]:
            bin_type = bin_name_map[event["cal_garbage_type"]]
            date = datetime.datetime.strptime(
                event["cal_date"], "%Y-%m-%d").date()
            icon = ICON_MAP.get(bin_type.split(" ")[0])  # Collection icon
            entries.append(Collection(date=date, t=bin_type, icon=icon))

        return entries
