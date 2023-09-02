#!/usr/bin/env python3
import json
import random
import re
from datetime import date, datetime

import requests
from bs4 import BeautifulSoup

SUPPORTED_APPS = [
    "de.albagroup.app",
    "de.k4systems.abfallinfocw",
    "de.k4systems.abfallinfoapp",
]

SUPPORTED_SERVICES = {
    "de.albagroup.app": [
        "Berlin",
        "Braunschweig",
        "Havelland",
        "Oberhavel",
        "Ostprignitz-Ruppin",
        "Tübingen",
    ],
    "de.k4systems.abfallinfocw": [
        "Altensteig",
        "Althengstett",
        "Bad Herrenalb",
        "Bad Liebenzell",
        "Bad Teinach",
        "Bad Wildbad",
        "Calw",
        "Dobel",
        "Ebhausen",
        "Egenhausen",
        "Enzklösterle",
        "Gechingen",
        "Haiterbach",
        "Höfen",
        "Nagold",
        "Neubulach",
        "Neuweiler",
        "Oberreichenbach",
        "Ostelsheim",
        "Rohrdorf",
        "Schömberg",
        "Simmersfeld",
        "Simmozheim",
        "Unterreichenbach",
        "Wildberg",
    ],
    "de.k4systems.abfallinfoapp": [
        "Bad Münstereifel",
        "Dahlem",
        "Hellenthal",
        "Kall",
        "Mechernich",
        "Schleiden",
        "Weilerswist",
        "Zülpich",
    ],
}


def random_hex(length: int = 1) -> str:
    return "".join(random.choice("0123456789abcdef") for _ in range(length))


API_BASE = "https://app.abfallplus.de/{}"
API_ASSISTANT = API_BASE.format("assistent/{}")  # ignore: E501


def extract_onclicks(
    data: BeautifulSoup | str | requests.Response, hnr=False
) -> list[list]:
    if isinstance(data, requests.Response):
        data = data.text
    if isinstance(data, str):
        data = BeautifulSoup(data, features="html.parser")

    to_return = []
    for a in data.find_all("a"):
        onclick: str = a.attrs["onclick"].replace("('#f_ueberspringen').val('0')", "")
        start = onclick.find("(") + 1
        end = onclick.find(")")
        string = ("[" + onclick[start:end] + "]").replace("'", '"')
        to_return.append(json.loads(string))
        if hnr:
            res = re.search(r"\.val\([0-9]+\)", onclick)
            if res:
                to_return[-1].append(res.group()[5:-1])
    return to_return


def compare(a, b, remove_space=False):
    if remove_space:
        a = a.replace(" ", "")
        b = b.replace(" ", "")
    return a.lower().strip() == b.lower().strip()


class AppAbfallplusDe:
    def __init__(
        self,
        app_id,
        region,
        strasse,
        hnr,
        bundesland_id=None,
        landkreis_id=None,
        kommune_id=None,
        bezirk_id=0,
        strasse_id=None,
        hnr_id=None,
    ):
        self._client = (
            random_hex(8)
            + random_hex(4)
            + random_hex(4)
            + random_hex(4)
            + random_hex(12)
        )
        self._app_id = app_id
        self._session = requests.Session()
        self._region_search = region
        self._strasse_search = strasse
        self._hnr_search = hnr

        self._hnr = hnr_id
        self._bundesland_id = bundesland_id
        self._landkreis_id = landkreis_id
        self._kommune_id = kommune_id
        self._bezirk_id = bezirk_id
        self._strasse_id = strasse_id

    def init_connection(self):
        data = {
            "client": self._client,
            "app_id": self._app_id,
        }
        self._session.post(API_BASE.format("config.xml"), data=data).raise_for_status()
        r = self._session.post(API_BASE.format("login/"), data=data)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, features="html.parser")
        if not (inputs := soup.find_all("input")):
            return

        for input in inputs:
            if input.attrs["name"] == "f_id_bundesland":
                self._bundesland_id = input.attrs["value"]
            elif input.attrs["name"] == "f_id_landkreis":
                self._landkreis_id = input.attrs["value"]
            elif input.attrs["name"] == "f_id_kommune":
                self._kommune_id = input.attrs["value"]

    def get_regions(self, region_key_name="kommune") -> list:
        data = {}
        if self._bundesland_id:
            data["id_bundesland"] = self._bundesland_id
        if self._landkreis_id:
            data["id_landkreis"] = self._landkreis_id
        if self._kommune_id:
            data["id_kommune"] = self._kommune_id

        r = self._session.post(API_ASSISTANT.format(f"{region_key_name}/"), data=data)
        r.raise_for_status()
        regions = []
        for a in extract_onclicks(r):
            regions.append(
                {
                    "id": a[0],
                    "name": a[1],
                    "bundesland_id": a[5].get("set_id_bundesland"),
                    "landkreis_id": a[5].get("set_id_landkreis"),
                    "kommune_id": a[5].get("set_id_kommune"),
                }
            )
            # name = a.text.strip()
            # id = a.attrs()["onclick"].split("'")[1]
        if region_key_name == "kommune" and regions == []:
            return self.get_regions("region")
        return regions

    def select_region(self):
        regions = self.get_regions()
        for region in regions:
            if compare(region["name"], self._region_search):
                self._bundesland_id = region["bundesland_id"]
                self._landkreis_id = region["landkreis_id"]
                self._region_id = region["id"]
                self._kommune_id = region["kommune_id"]
                return

        raise Exception(f"Region {self._region_search} not found.")

    def get_streets(self):
        data = {
            "id_landkreis": self._landkreis_id,
            "id_bezirk": self._bezirk_id,
            "id_kommune": self._kommune_id,
            "id_kommune_qry": self._kommune_id,
            "strasse_qry": self._strasse_search,
        }
        r = self._session.post(
            API_ASSISTANT.format("strasse/"),
            data=data,
        )
        r.raise_for_status()
        streets = []
        for a in extract_onclicks(r):
            streets.append(
                {
                    "id": a[0],
                    "name": a[1],
                    "id_kommune": a[5]["set_id_kommune"],
                    "id_beirk": a[5]["set_id_bezirk"],
                }
            )
        return streets

    def select_street(self):
        for street in self.get_streets():
            if compare(street["name"], self._strasse_search):
                self._strasse_id = street["id"]
                self._kommune_id = street["id_kommune"]
                self._bezirk_id = street["id_beirk"]
                return
        raise Exception(f"Street {self._strasse_search} not found.")

    def get_hnrs(self):
        data = {
            "id_landkreis": self._landkreis_id,
            "id_kommune": self._kommune_id,
            "id_bezirk": self._bezirk_id if self._bezirk_id else "",
            "id_strasse": self._strasse_id,
            # "awk_href_back":"awk_assistent_step_2",
        }
        # data=urllib.parse.urlencode(data, safe="|ß", encoding="utf-8")
        # data = "&".join([f"{k}={v}" for k, v in data.items()])

        r = self._session.post(
            API_ASSISTANT.format("hnr/"),
            data=data,
            headers={
                "content-type": "application/x-www-form-urlencoded; charset=UTF-8"
            },
        )
        hnrs = []
        for a in extract_onclicks(r, hnr=True):
            hnrs.append({"id": a[0], "name": a[0], "f_id_strasse": a[6]})
        return hnrs

    def select_hnr(self):
        for hnr in self.get_hnrs():
            if compare(hnr["name"], self._hnr_search, remove_space=True):
                self._hnr = hnr["id"]
                self._f_id_strasse = hnr["f_id_strasse"]
                return
        raise Exception(f"HNR {self._hnr_search} not found.")

    def select_all_waste_types(self):
        data = {
            "f_id_region": self._region_id,
            "f_id_bundesland": self._bundesland_id,
            "f_id_landkreis": self._landkreis_id,
            "f_id_kommune": self._kommune_id,
            "f_id_bezirk": self._bezirk_id,
            "f_id_strasse": self._f_id_strasse,
            "f_hnr": self._hnr,
            "f_kdnr": "",
        }
        r = self._session.post(API_ASSISTANT.format("abfallarten/"), data=data)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, features="html.parser")
        self._f_id_abfallart = []
        for input in soup.find_all("input", {"name": "f_id_abfallart[]"}):
            self._f_id_abfallart.append(input.attrs["value"])

    def validate(self):
        data = {
            "f_id_region": self._region_id,
            "f_id_bundesland": self._bundesland_id,
            "f_id_landkreis": self._landkreis_id,
            "f_id_kommune": self._kommune_id,
            "f_id_bezirk": self._bezirk_id,
            "f_id_strasse": self._f_id_strasse,
            "f_hnr": self._hnr,
            "f_kdnr": "",
            "f_id_abfallart[]": self._f_id_abfallart,
            "f_uhrzeit_tag": "86400|0",
            "f_uhrzeit_stunden": 54000,
            "f_uhrzeit_minuten": 600,
            "f_anonym": 1,
            "f_ausgangspunkt": 1,
            "f_ueberspringen": 0,
        }

        r = self._session.post(API_ASSISTANT.format("ueberpruefen/"), data=data)
        r.raise_for_status()
        data["f_datenschutz"] = datetime.now().strftime("%Y%m%d%H%M%S")
        r = self._session.post(API_ASSISTANT.format("finish/"), data=data)

    def get_collections(self) -> list[dict[str, date | str]]:
        """Get collections for the selected address as a list of dicts.

        Returns:
            list[dict[str, date|str]]: all collection dates
        """
        r = self._session.post(
            API_BASE.format("struktur.xml.zip"),
            data={"client": self._client, "app_id": self._app_id},
        )
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "xml")
        categories = {}
        for category in (
            soup.find("key", text="categories")
            .find_next_sibling("array")
            .find_all("dict")
        ):
            id = category.find("key", text="id").find_next_sibling("string").text
            name = (
                category.find("key", text="name")
                .find_next_sibling("string")
                .text.replace("![CDATA[", "")
                .replace("]]", "")
                .strip()
            )
            categories[id] = name

        collections: list[dict] = []
        for collection in (
            soup.find("key", text="dates").find_next_sibling("array").find_all("dict")
        ):
            category = (
                collection.find("key", text="category_id")
                .find_next_sibling("string")
                .text
            )
            category_name = categories[category]
            pickup_date_str = (
                collection.find("key", text="pickup_date")
                .find_next_sibling("string")
                .text
            )
            pickup_date = datetime.strptime(
                pickup_date_str, "%Y-%m-%dT%H:%M:%S%z"
            ).date()

            collections.append({"category": category_name, "date": pickup_date})

        return collections

    def generate_calendar(self) -> list[dict[str, date | str]]:
        """Run all necessary function and return the output of get_collections.

        Returns:
            list[dict[str, date|str]]: all collection dates
        """
        self.init_connection()
        self.select_region()
        self.select_street()
        self.select_hnr()
        self.select_all_waste_types()
        self.validate()
        return self.get_collections()

    def test(self):
        # self.init_connection()
        # self.get_regions()
        print(self.generate_calendar())


def generate_supported_services():
    supported_services = {}
    for app_id in SUPPORTED_APPS:
        supported_services[app_id] = []
        app = AppAbfallplusDe(app_id, "", "", "")
        app.init_connection()
        for region in app.get_regions():
            print(region)
            supported_services[app_id].append(region["name"])

    print(json.dumps(supported_services, indent=4, ensure_ascii=False))


if __name__ == "__main__":
    generate_supported_services()
    # app = AppAbfallplusDe("de.k4systems.abfallinfoapp", "", "", "")
    # app.init_connection()
    # print(app.get_regions())
    # app = AppAbfallplusDe("de.albagroup.app", "Braunschweig", "Hauptstraße", "7A")
    # app.test()
