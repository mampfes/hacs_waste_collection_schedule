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
        "city": "Darmstadt",
        "street": "Achatweg"
    },
    "zaw Alsbach-Hähnlein Hähnleiner Str.": {
        "service_id": "zaw",
        "city": "Alsbach-Hähnlein",
        "street": "Hähnleiner Str."
    },
    "ingolstadt": {
        "service_id": "ingol",
        "city": "Ingolstadt",
        "street": "Hauffstr.",
        "house_number": "9 1/2",
    },
    "mymuell only city": {
        "service_id": "mymuell",
        "city": "Kipfenberg OT Arnsberg, Biberg, Dunsdorf, Schelldorf, Schambach, Mühlen im Schambachtal und Schambacher Leite, Järgerweg, Böllermühlstraße, Attenzell, Krut, Böhming, Regelmannsbrunn, Hirnstetten und Pfahldorf",
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
        "list": ["Darmstadt-Dieburg (ZAW)"],
    },
    "ingol": {
        "list": ["Ingolstadt"],
        "url": "https://www.in-kb.de",
    },

    "aoe": {
        "url": "https://www.lra-aoe.de",
        "list": ["Altötting (LK)"],
    },

    "lka": {
        "url": "https://mkw-grossefehn.de",
        "list": ["Aurich (MKW)"],
    },
    "hom": {
        "url": "https://www.bad-homburg.de",
        "list": ["Bad Homburg vdH"],
    },
    "bdg": {
        "url": "https://www.kreiswerke-barnim.de/",
        "list": ["Barnim"],
    },
    "hat": {
        "url": "https://www.hattersheim.de",
        "list": ["Hattersheim am Main"],
    },
    "ingol": {
        "url": "https://www.in-kb.de",
        "list": ["Ingolstadt"],
    },
    "lue": {
        "comment": "Jumomind", #has its own service
        "url": "https://www.luebbecke.de",
        "list": ["Lübbecke"],
    },
    "sbm": {
        "url": "https://www.minden.de/",
        "list": ["Minden"],
    },
    "ksr": {
        "url": "https://www.zbh-ksr.de",
        "list": ["Recklinghausen"],
    },
    "rhe": {
        "comment": "Jumomind", #has its own service
        "url": "https://www.rh-entsorgung.de/",
        "list": ["Rhein-Hunsrück"],
    },
    "udg": {
        "url": "https://www.udg-uckermark.de/",
        "list": ["Uckermark"],
    },
    "mymuell": {
            "comment": "MyMuell App",
            "url": "https://www.mymuell.de/",
            "list": ['Aschaffenburg', 'Bad Arolsen', 'Beverungen', 'Darmstadt', 'Esens', 'Flensburg', 'Großkrotzenburg', 'Hainburg', 'Holtgast', 'Kamp-Lintfort', 'Kirchdorf', 'Landkreis Aschaffenburg', 'Landkreis Biberach', 'Landkreis Eichstätt', 'Landkreis Friesland', 'Landkreis Leer', 'Landkreis Mettmann', 'Landkreis Paderborn', 'Landkreis Wittmund', 'Landkreis Wittmund', 'Main-Kinzig-Kreis', 'Mühlheim am Main', 'Nenndorf', 'Neumünster', 'Salzgitter', 'Schmitten im Taunus', 'Schöneck', 'Seligenstadt', 'Ulm', 'Usingen', 'Volkmarsen', 'Vöhringen', 'Wegberg', 'Westerholt', 'Wilhelmshaven']
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
    def __init__(self, service_id: str, city: str = None, street: str = None, city_id=None, area_id=None, house_number=None):
        self._search_url: str = API_SEARCH_URL.format(provider=service_id)
        self._dates_url: str = API_DATES_URL.format(provider=service_id)
        self._city: str = city.lower().strip() if city else None
        self._street: str = street.lower().strip() if street else None
        self._house_number: str = str(
            house_number).lower().strip() if house_number else None

        self._service_id = service_id
        self._city_id = city_id if city_id else None
        self._area_id = area_id if area_id else None

    def fetch(self):
        session = requests.Session()

        city_id = self._city_id
        area_id = self._area_id

        if city_id is None and self._city is None:
            raise Exception("City or city id is required")
        if city_id is not None and self._city is not None:
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
                if city["name"].lower().strip() == self._city or city["_name"].lower().strip() == self._city:
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
                    if street["name"].lower().strip() == self._street or street["_name"].lower().strip() == self._street:
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
                if self._street is not None:
                    LOGGER.warning(
                        "City does not need street name please remove it, continuing anyway")

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




def print_md_table():
    table = "|service_id|cities|\n|---|---|\n"
    
    for service, data in SERVICE_MAP.items():
        
        args = {"r": "cities"}
        r = requests.get(
            f"https://{service}.jumomind.com/mmapp/api.php", params=args
        )
        r.raise_for_status()
        table += f"|{service}|"
        
        for city in r.json():
            table += f"`{city['name']}`,"
            
        table += "|\n"
    print(table)


if __name__ == "__main__":
    print_md_table()
