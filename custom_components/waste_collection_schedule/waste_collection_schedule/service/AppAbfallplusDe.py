#!/usr/bin/env python3
import json
import re
import time
import uuid
from collections import OrderedDict
from datetime import date, datetime

import requests
from bs4 import BeautifulSoup, Tag

SUPPORTED_APPS = [
    "de.albagroup.app",
    "de.k4systems.abfallinfocw",
    "de.k4systems.abfallinfoapp",
    "de.k4systems.abfallappes",
    "de.k4systems.egst",
    "de.idcontor.abfallwbd",
    "de.ucom.abfallavr",
    "de.k4systems.abfallapprv",
    "de.k4systems.avlserviceplus",
    "de.k4systems.muellalarm",
    "de.k4systems.abfallapploe",
    # "de.k4systems.abfallappart",
    "de.k4systems.abfallapp",
    "de.k4systems.abfallappvorue",
    "de.k4systems.abfallappfds",
    "de.k4systems.abfallscout",
    "de.k4systems.avea",
    "de.k4systems.neustadtaisch",
    "de.k4systems.abfalllkswp",
    "de.k4systems.awbemsland",
    "de.k4systems.abfallappclp",
    "de.k4systems.abfallappnf",
    "de.k4systems.abfallappog",
    "de.k4systems.abfallappmol",
    "de.k4systems.kufiapp",
    "de.k4systems.abfalllkbz",
    "de.k4systems.abfallappbb",
    "de.k4systems.abfallappla",
    "de.k4systems.abfallappwug",
    "de.k4systems.abfallappik",
    "de.k4systems.leipziglk",
    "de.k4systems.abfallappbk",
    "de.cmcitymedia.hokwaste",
    "de.abfallwecker",
    "de.k4systems.abfallappka",
    "de.k4systems.lkgoettingen",
    "de.k4systems.abfallappcux",
    "de.k4systems.abfallslk",
    "de.k4systems.abfallappzak",
    "de.zawsr",
    "de.k4systems.teamorange",
    "de.k4systems.abfallappvivo",
    "de.k4systems.lkgr",
    "de.k4systems.zawdw",
    "de.k4systems.abfallappgib",
    "de.k4systems.wuerzburg",
    "de.k4systems.abfallappgap",
    "de.k4systems.bonnorange",
    "de.gimik.apps.muellwecker_neuwied",
    "abfallH.ucom.de",
    "de.k4systems.abfallappts",
    "de.k4systems.awa",
    "de.k4systems.abfallappfuerth",
    "de.k4systems.abfallwelt",
    "de.k4systems.lkemmendingen",
    "de.k4systems.abfallkreisrt",
    "de.k4systems.abfallappmetz",
    "de.k4systems.abfallappmyk",
    "de.k4systems.abfallappoal",
    "de.k4systems.regioentsorgung",
    "de.k4systems.abfalllkbt",
    "de.k4systems.awvapp",
    "de.k4systems.aevapp",
    "de.k4systems.awbgp",
    "de.k4systems.abfallhr",
    "de.k4systems.abfallappbh",
    "de.k4systems.awgbassum",
    "de.data_at_work.aws",
    "de.k4systems.hebhagen",
    "de.k4systems.meinawblm",
    "de.k4systems.abfallmsp",
    "de.k4systems.asoapp",
    "de.k4systems.awistasta",
    "de.ucom.abfallebe",
    "de.k4systems.abfallinfocw",
    "de.k4systems.bawnapp",
    "de.k4systems.abfallappol",
    "de.k4systems.awbrastatt",
    "de.k4systems.abfallappmil",
    "de.k4systems.abfallsbk",
    "de.k4systems.wabapp",
    "abfallMA.ucom.de",
    "de.k4systems.llabfallapp",
    "de.k4systems.lkruelzen",
    "de.k4systems.abfallzak",
    "de.k4systems.abfallappno",
    "de.k4systems.udb",
    "de.k4systems.abfallappsig",
    "de.k4systems.asf",
    "de.drekopf.abfallplaner",
    "de.k4systems.unterallgaeu",
    "de.k4systems.landshutlk",
    "de.k4systems.zakb",
    "de.k4systems.abfallinfoapp",
    "de.k4systems.awrplus",
    "de.k4systems.lkmabfallplus",
    "de.k4systems.athosmobil",
    "de.k4systems.willkommen",
    "de.idcontor.abfalllu",
    "de.ahrweiler.meinawb",
    "de.edg.abfallapp",
    "de.biberach.abfallapp",
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
    "de.k4systems.abfallinfocw": ["Kreis Calw"],
    "de.k4systems.abfallinfoapp": ["Mechernich und Kommunen"],
    "de.k4systems.abfallappes": ["Landkreis Esslingen"],
    "de.k4systems.egst": ["Kreis Steinfurt"],
    "de.idcontor.abfallwbd": ["Duisburg"],
    "de.ucom.abfallavr": ["Rhein-Neckar-Kreis"],
    "de.k4systems.abfallapprv": ["Kreis Ravensburg"],
    "de.k4systems.avlserviceplus": ["Kreis Ludwigsburg"],
    "de.k4systems.muellalarm": ["Schönmackers"],
    "de.k4systems.abfallapploe": ["Kreis Lörrach"],
    "de.k4systems.abfallapp": ["Kreis Augsburg"],
    "de.k4systems.abfallappvorue": ["Kreis Vorpommern-Rügen"],
    "de.k4systems.abfallappfds": ["Kreis Freudenstadt"],
    "de.k4systems.abfallscout": ["Kreis Bad Kissingen"],
    "de.k4systems.avea": ["Leverkusen"],
    "de.k4systems.neustadtaisch": ["Kreis Neustadt/Aisch-Bad Windsheim"],
    "de.k4systems.abfalllkswp": ["Kreis Südwestpfalz"],
    "de.k4systems.awbemsland": ["Kreis Emsland"],
    "de.k4systems.abfallappclp": ["Kreis Cloppenburg"],
    "de.k4systems.abfallappnf": ["Kreis Nordfriesland"],
    "de.k4systems.abfallappog": ["Ortenaukreis"],
    "de.k4systems.abfallappmol": ["Kreis Märkisch-Oderland"],
    "de.k4systems.kufiapp": ["Landkreis Wunsiedel im Fichtelgebirge"],
    "de.k4systems.abfalllkbz": ["Kreis Bautzen"],
    "de.k4systems.abfallappbb": ["Landkreis Böblingen"],
    "de.k4systems.abfallappla": ["Landshut"],
    "de.k4systems.abfallappwug": ["Kreis Weißenburg-Gunzenhausen"],
    "de.k4systems.abfallappik": ["Ilm-Kreis"],
    "de.k4systems.leipziglk": ["Landkreis Leipzig"],
    "de.k4systems.abfallappbk": ["Bad Kissingen"],
    "de.cmcitymedia.hokwaste": ["Hohenlohekreis"],
    "de.abfallwecker": [
        "Rottweil",
        "Tuttlingen",
        "Waldshut",
        "Prignitz",
        "Nordsachsen",
    ],
    "de.k4systems.abfallappka": ["Kreis Karlsruhe"],
    "de.k4systems.lkgoettingen": [
        "Abfallwirtschaft Altkreis Göttingen",
        "Abfallwirtschaft Altkreis Osterode am Harz",
    ],
    "de.k4systems.abfallappcux": ["Kreis Cuxhaven"],
    "de.k4systems.abfallslk": ["Salzlandkreis"],
    "de.k4systems.abfallappzak": ["ZAK Kempten"],
    "de.zawsr": ["ZAW-SR"],
    "de.k4systems.teamorange": ["Kreis Würzburg"],
    "de.k4systems.abfallappvivo": ["Kreis Miesbach"],
    "de.k4systems.lkgr": ["Landkreis Görlitz"],
    "de.k4systems.zawdw": ["AWG Donau-Wald"],
    "de.k4systems.abfallappgib": ["Kreis Wesermarsch"],
    "de.k4systems.wuerzburg": ["Würzburg"],
    "de.k4systems.abfallappgap": ["Kreis Garmisch-Partenkirchen"],
    "de.k4systems.bonnorange": ["Bonn"],
    "de.gimik.apps.muellwecker_neuwied": ["Kreis Neuwied"],
    "abfallH.ucom.de": ["Kreis Heilbronn"],
    "de.k4systems.abfallappts": ["Kreis Traunstein"],
    "de.k4systems.awa": ["Augsburg"],
    "de.k4systems.abfallappfuerth": ["Kreis Fürth"],
    "de.k4systems.abfallwelt": ["Kreis Kitzingen"],
    "de.k4systems.lkemmendingen": ["Kreis Emmendingen"],
    "de.k4systems.abfallkreisrt": ["Kreis Reutlingen"],
    "de.k4systems.abfallappmetz": ["Metzingen"],
    "de.k4systems.abfallappmyk": ["Kreis Mayen-Koblenz"],
    "de.k4systems.abfallappoal": ["Kreis Ostallgäu"],
    "de.k4systems.regioentsorgung": ["RegioEntsorgung AöR"],
    "de.k4systems.abfalllkbt": ["Kreis Bayreuth"],
    "de.k4systems.awvapp": ["Kreis Vechta"],
    "de.k4systems.aevapp": ["Schwarze Elster"],
    "de.k4systems.awbgp": ["Kreis Göppingen"],
    "de.k4systems.abfallhr": ["ALF Lahn-Fulda"],
    "de.k4systems.abfallappbh": ["Kreis Breisgau-Hochschwarzwald"],
    "de.k4systems.awgbassum": ["Kreis Diepholz"],
    "de.data_at_work.aws": ["Kreis Schaumburg"],
    "de.k4systems.hebhagen": ["Hagen"],
    "de.k4systems.meinawblm": ["Kreis Limburg-Weilburg"],
    "de.k4systems.abfallmsp": ["Landkreis Main-Spessart"],
    "de.k4systems.asoapp": ["Kreis Osterholz"],
    "de.k4systems.awistasta": ["Kreis Starnberg"],
    "de.ucom.abfallebe": ["Essen"],
    "de.k4systems.bawnapp": ["Kreis Nienburg / Weser"],
    "de.k4systems.abfallappol": ["Oldenburg"],
    "de.k4systems.awbrastatt": ["Kreis Rastatt"],
    "de.k4systems.abfallappmil": ["Kreis Miltenberg"],
    "de.k4systems.abfallsbk": ["Schwarzwald-Baar-Kreis"],
    "de.k4systems.wabapp": ["Westerwaldkreis"],
    "abfallMA.ucom.de": ["Mannheim"],
    "de.k4systems.llabfallapp": ["Kreis Landsberg am Lech"],
    "de.k4systems.lkruelzen": ["Kreis Uelzen"],
    "de.k4systems.abfallzak": ["Zollernalbkreis"],
    "de.k4systems.abfallappno": ["Neckar-Odenwald-Kreis"],
    "de.k4systems.udb": ["Burgenland (Landkreis)"],
    "de.k4systems.abfallappsig": ["Kreis Sigmaringen"],
    "de.k4systems.asf": ["Freiburg im Breisgau"],
    "de.drekopf.abfallplaner": ["Drekopf"],
    "de.k4systems.unterallgaeu": [
        "Rottweil",
        "Tuttlingen",
        "Waldshut",
        "Frankfurt (Oder)",
        "Prignitz",
    ],
    "de.k4systems.landshutlk": ["Kreis Landshut"],
    "de.k4systems.zakb": ["Kreis Bergstraße"],
    "de.k4systems.awrplus": ["Kreis Rotenburg (Wümme)"],
    "de.k4systems.lkmabfallplus": ["München Landkreis"],
    "de.k4systems.athosmobil": ["ATHOS GmbH"],
    "de.k4systems.willkommen": [
        "Rottweil",
        "Tuttlingen",
        "Waldshut",
        "Frankfurt (Oder)",
        "Prignitz",
    ],
    "de.idcontor.abfalllu": ["Ludwigshafen"],
    "de.ahrweiler.meinawb": ["Kreis Ahrweiler"],
    "de.edg.abfallapp": ["Entsorgung Dortmund GmbH (EDG)"],
    "de.biberach.abfallapp": ["Kreis Biberach"],
}

MAP_APP_USERAGENTS = {
    "abfallH.ucom.de": "Landkreis HN",
    "abfallMA.ucom.de": "Abfall-Ma",
    "de.ahrweiler.meinawb": "Abfall App",
    "de.abfallwecker": "ABFALL+",
    "de.albagroup.app": "Abfuhrtermine",
    "de.biberach.abfallapp": "Abfall App",
    "de.cmcitymedia.hokwaste": "Abfallinfo HOK",
    "de.data_at_work.aws": "aws Schaumburg",
    "de.drekopf.abfallplaner": "Abfallplaner",
    "de.edg.abfallapp": "Abfall App",
    "de.gimik.apps.muellwecker_neuwied": "Müllwecker",
    "de.idcontor.abfalllu": "Abfall LU",
    "de.idcontor.abfallwbd": "WBD App",
    "de.k4systems.abfallappart": "ART App",
    "de.k4systems.abfallappbb": "Abfall-App",
    "de.k4systems.abfallappbh": "Abfall App",
    "de.k4systems.abfallappbk": "AbfallApp BK",
    "de.k4systems.abfallappclp": "Abfall App CLP",
    "de.k4systems.abfallappcux": "Abfall LK Cux",
    "de.k4systems.abfallappes": "Abfall-App",
    "de.k4systems.abfallappfds": "Abfall App FDS",
    "de.k4systems.abfallappfuerth": "Abfall-App",
    "de.k4systems.abfallappgap": "Abfall App",
    "de.k4systems.abfallappgib": "Abfall App",
    "de.k4systems.abfallappik": "AbfallApp IK",
    "de.k4systems.abfallappka": "Abfall App KA",
    "de.k4systems.abfallappla": "Abfall App",
    "de.k4systems.abfallapploe": "Abfall-App",
    "de.k4systems.abfallappmetz": "Abfall App",
    "de.k4systems.abfallappmil": "AbfallApp MIL",
    "de.k4systems.abfallappmol": "AbfallApp MOL",
    "de.k4systems.abfallappmyk": "AbfallApp Myk",
    "de.k4systems.abfallappnf": "Abfall-AppNF",
    "de.k4systems.abfallappno": "Abfall-App",
    "de.k4systems.abfallappoal": "Ostallgäu",
    "de.k4systems.abfallappog": "Ortenaukreis",
    "de.k4systems.abfallappol": "Abfall App OL",
    "de.k4systems.abfallapp": "AbfallApp",
    "de.k4systems.abfallapprv": "Abfall App RV",
    "de.k4systems.abfallappsig": "AbfallSIG",
    "de.k4systems.abfallappts": "AbfallApp TS",
    "de.k4systems.abfallappvivo": "Abfall App",
    "de.k4systems.abfallappvorue": "Abfall App",
    "de.k4systems.abfallappwug": "AbfallApp WUG",
    "de.k4systems.abfallappzak": "Abfall App",
    "de.k4systems.abfallhr": "Abfall HR",
    "de.k4systems.abfallinfoapp": "Abfallinfoapp",
    "de.k4systems.abfallinfocw": "AbfallinfoCW",
    "de.k4systems.abfallkreisrt": "AbfallKreisRT",
    "de.k4systems.abfalllkbt": "Abfall LK BT",
    "de.k4systems.abfalllkbz": "Abfall LK BZ",
    "de.k4systems.abfalllkswp": "Abfall LKSWP",
    "de.k4systems.abfallmsp": "Abfall MSP",
    "de.k4systems.abfallsbk": "Abfall SBK",
    "de.k4systems.abfallscout": "Abfall-Scout",
    "de.k4systems.abfallslk": "Abfall SLK",
    "de.k4systems.abfallwelt": "abfallwelt",
    "de.k4systems.abfallzak": "Abfall ZAK",
    "de.k4systems.aevapp": "AEV-App",
    "de.k4systems.asf": "ASF",
    "de.k4systems.asoapp": "ASO-App",
    "de.k4systems.athosmobil": "ATHOS mobil",
    "de.k4systems.avea": "AVEA-App",
    "de.k4systems.avlserviceplus": "AVL Service+",
    "de.k4systems.awa": "Abfallplaner",
    "de.k4systems.awbemsland": "AWB Emsland",
    "de.k4systems.awbgp": "AWB-GP",
    "de.k4systems.awbrastatt": "AWB Rastatt",
    "de.k4systems.awgbassum": "AWG Bassum",
    "de.k4systems.awistasta": "Awista-STA",
    "de.k4systems.awrplus": "AWR+",
    "de.k4systems.awvapp": "AWV App",
    "de.k4systems.bawnapp": "BAWNapp",
    "de.k4systems.bonnorange": "Abfallplaner",
    "de.k4systems.egst": "EGST",
    "de.k4systems.hebhagen": "HEB Hagen",
    "de.k4systems.kufiapp": "KUFI App",
    "de.k4systems.landshutlk": "Abfall App",
    "de.k4systems.leipziglk": "LK Leipzig",
    "de.k4systems.lkemmendingen": "LK Emmendingen",
    "de.k4systems.lkgoettingen": "LK Göttingen",
    "de.k4systems.lkgr": "LK GR",
    "de.k4systems.lkruelzen": "Abfall App",
    "de.k4systems.lkmabfallplus": "Abfall App",
    "de.k4systems.llabfallapp": "LL Abfall App",
    "de.k4systems.meinawblm": "Mein AWB LM",
    "de.k4systems.muellalarm": "MüllALARM",
    "de.k4systems.neustadtaisch": "Abfall-App",
    "de.k4systems.regioentsorgung": "RE-entsorgt",
    "de.k4systems.teamorange": "team orange",
    "de.k4systems.udb": "Müllabfuhr",
    "de.k4systems.unterallgaeu": "Unterallgäu",
    "de.k4systems.wabapp": "WAB-App",
    "de.k4systems.willkommen": "Will Kommen",
    "de.k4systems.wuerzburg": "Stadtreiniger",
    "de.k4systems.zakb": "zakb",
    "de.k4systems.zawdw": "ZAW DW",
    "de.ucom.abfallavr": "AVR Abfall",
    "de.ucom.abfallebe": "Wir räumen ab!",
    "de.zawsr": "ZAW-SR",
}


def get_extra_info():
    for app, services in SUPPORTED_SERVICES.items():
        for service in services:
            app_name = app.split(".")[-1]
            if app_name == "abfallapp" or app_name == "app":
                app_name = app.split(".")[-2]
            if app_name == "abfallapp" or app_name == "app":
                app_name = ""
            yield {
                "title": service,
                "url": "Abfall+ App" + (": " + app.split(".")[-1]) if app_name else "",
                "country": "de",
                "default_params": {"app_id": app},
            }


API_BASE = "https://app.abfallplus.de/{}"
API_ASSISTANT = API_BASE.format("assistent/{}")  # ignore: E501
USER_AGENT = "Android / {} 8.1.1 (1915081010) / DM=unknown;DT=vbox86p;SN=Google;SV=8.1.0 (27);MF=unknown"
USER_AGENT_ASSISTANT = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Abfallwecker"
ABFALLARTEN_H2_SKIP = ["Sondermüll"]
VERIFY_SSL = True


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
        end = onclick.find("})") + 1
        if end == 0:
            end = onclick.find(')"')

        string = ("[" + onclick[start:end] + "]").replace('"', '\\"').replace("'", '"')
        try:
            to_return.append(json.loads(string))
        except json.decoder.JSONDecodeError:
            raise Exception(f"Failed to parse '{string}', onclick: '{onclick}'")
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
        strasse=None,
        hnr=None,
        bezirk=None,
        kommune=None,
        bundesland=None,
        landkreis=None,
        bundesland_id=None,
        landkreis_id=None,
        kommune_id=None,
        bezirk_id="",
        strasse_id=None,
        hnr_id=None,
    ):
        self._client = str(uuid.uuid4())

        self._app_id = app_id
        self._session = requests.Session()
        self._bundesland_search = bundesland
        self._landkreis_search = landkreis
        self._region_search = kommune
        self._strasse_search = strasse
        self._hnr_search = hnr
        self._bezirk_search = bezirk

        self._hnr = hnr_id
        self._bundesland_id = bundesland_id
        self._landkreis_id = landkreis_id
        self._kommune_id = kommune_id
        self._bezirk_id = bezirk_id
        self._strasse_id = strasse_id

        self._needs_subtitle: list[str] = []

    def _request(
        self,
        url_ending,
        base=API_ASSISTANT,
        data=None,
        params=None,
        method="post",
        headers=None,
    ):
        if headers is None:
            headers = OrderedDict({})

        if base == API_ASSISTANT:
            headers["User-Agent"] = USER_AGENT_ASSISTANT
            headers["Accept"] = "*/*"
            headers["Origin"] = "https://app.abfallplus.de"
            headers["X-Requested-With"] = "XMLHttpRequest"
            headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
            headers["Referer"] = "https://app.abfallplus.de/login/"
            headers["Accept-Encoding"] = "gzip, deflate, br"
            headers["Accept-Language"] = "de-DE,de;q=0.9"

        else:
            headers["User-Agent"] = USER_AGENT.format(
                MAP_APP_USERAGENTS.get(self._app_id, "%")
            )

        if "config.xml" in url_ending:
            headers["Accept-Encoding"] = "gzip, deflate, br"
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        else:
            time.sleep(1)

        if method not in ("get", "post"):
            raise Exception(f"Method {method} not supported.")
        if method == "get":
            r = self._session.get(
                base.format(url_ending),
                params=params,
                headers=headers,
                verify=VERIFY_SSL,
            )
        elif method == "post":
            req = requests.Request(
                method="POST",
                url=base.format(url_ending),
                data=data,
                params=params,
                headers=headers,
                cookies=self._session.cookies,
            )
            prepped = req.prepare()

            r = self._session.send(
                prepped,
                verify=VERIFY_SSL,
            )
        return r

    def get_kom_or_lk_name(self) -> str | bool:
        """Get the landkreis or kommune name if the app is designed for a specific one."""
        if self._kommune_id and "|" in self._kommune_id:
            if self._kommune_id.split("|")[0] != "0":
                return self._kommune_id.split("|")[-1]

        if self._landkreis_id and "|" in self._landkreis_id:
            if self._landkreis_id and "|" in self._landkreis_id:
                if self._landkreis_id.split("|")[0] != "0":
                    return self._landkreis_id.split("|")[-1]
        return False

    def init_connection(self):
        data = {
            "client": self._client,
            "app_id": self._app_id,
        }
        self._request("config.xml", base=API_BASE, data=data).raise_for_status()
        r = self._request("login/", base=API_BASE, data=data)
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
        to_request = [
            a["href"].split("#awk_assistent_step_standort_")[1]
            for a in soup.find_all(
                "a", href=re.compile(r"#awk_assistent_step_standort_[a-z]*")
            )
        ]
        self._bezirk_needed = False

        if "bezirk" in to_request:
            self._bezirk_needed = True
        return to_request

    def get_bundeslaender(self):
        r = self._request("bundesland/", method="get")
        r.raise_for_status()
        bundeslaender = []
        for a in extract_onclicks(r):
            bundeslaender.append(
                {
                    "id": a[0],
                    "name": a[1],
                }
            )
        return bundeslaender

    def select_bundesland(self, bundesland=None):
        if bundesland:
            self._bundesland_search = bundesland
        for bundesland in self.get_bundeslaender():
            if compare(bundesland["name"], self._bundesland_search):
                self._bundesland_id = bundesland["id"]
                return

    def get_landkreise(self, region_key_name="landkreis"):
        data = {}
        if self._bundesland_id:
            data["id_bundesland"] = self._bundesland_id
        r = self._request(f"{region_key_name}/", data=data)
        r.raise_for_status()
        landkreise = []
        for a in extract_onclicks(r):
            landkreise.append(
                {
                    "id": a[0],
                    "name": a[1],
                }
            )
            for element in a:
                if isinstance(element, dict):
                    if "set_id_bundesland" in a[5]:
                        self._bundesland_id = a[5]["set_id_bundesland"]
                    if "set_id_landkreis" in a[5]:
                        self._landkreis_id = a[5]["set_id_landkreis"]

        if region_key_name == "landkreis" and landkreise == []:
            return self.get_landkreise(region_key_name="region")
        return landkreise

    def select_landkreis(self, landkreis=None):
        if landkreis:
            self._landkreis_search = landkreis
        for landkreis in self.get_landkreise():
            if compare(landkreis["name"], self._landkreis_search):
                self._landkreis_id = landkreis["id"]
                return

    def get_kommunen(self, region_key_name="kommune") -> list:
        data = {}
        if self._bundesland_id:
            data["id_bundesland"] = self._bundesland_id
        if self._landkreis_id:
            data["id_landkreis"] = self._landkreis_id
        # if self._kommune_id:
        #     data["id_kommune"] = self._kommune_id
        r = self._request(region_key_name + "/", data=data)
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
            return self.get_kommunen("region")
        return regions

    def select_kommune(self, kommune=None):
        if kommune:
            self._region_search = kommune

        regions = self.get_kommunen()
        for region in regions:
            if compare(region["name"], self._region_search):
                if region["bundesland_id"] is not None:
                    self._bundesland_id = region["bundesland_id"]
                if region["landkreis_id"] is not None:
                    self._landkreis_id = region["landkreis_id"]
                self._region_id = region["id"]
                self._kommune_id = (
                    region["kommune_id"]
                    if region["kommune_id"] is not None
                    else region["id"]
                )
                return

        raise Exception(f"Region {self._region_search} not found.")

    def get_bezirke(self):
        data = {}
        if self._bundesland_id:
            data["id_bundesland"] = self._bundesland_id
        if self._landkreis_id:
            data["id_landkreis"] = self._landkreis_id
        if self._kommune_id:
            data["id_kommune"] = self._kommune_id
        r = self._request("bezirk/", data=data)
        r.raise_for_status()
        bezirke = []
        for a in extract_onclicks(r):
            bez = {
                "id": a[0],
                "name": a[1],
                "bundesland_id": a[5].get("set_id_bundesland"),
                "landkreis_id": a[5].get("set_id_landkreis"),
                "kommune_id": a[5].get("set_id_kommune"),
                "finished": False,
            }
            if (
                "step_follow_data" in a[5]
                and "step_akt" in a[5]["step_follow_data"]
                and a[5]["step_follow_data"]["step_akt"] == "strasse"
            ):
                bez["finished"] = True
                bez["street_id"] = a[5]["step_follow_data"]["id"]
            bezirke.append(bez)
        return bezirke

    def select_bezirk(self, bezirk=None) -> bool:
        if bezirk:
            self._bezirk_search = bezirk

        bezirke = self.get_bezirke()
        for bezirk in bezirke:
            if compare(bezirk["name"], self._bezirk_search):
                if bezirk["bundesland_id"] is not None:
                    self._bundesland_id = bezirk["bundesland_id"]
                if bezirk["landkreis_id"] is not None:
                    self._landkreis_id = bezirk["landkreis_id"]
                if bezirk["kommune_id"] is not None:
                    self._kommune_id = bezirk["kommune_id"]
                self._bezirk_id = bezirk["id"]
                if bezirk["finished"] or "street_id" in bezirk:
                    self._f_id_strasse = self._strasse_id = (
                        bezirk["street_id"]
                        if bezirk.get("street_id") is not None
                        else bezirk["id"]
                    )
                return bezirk["finished"]

        raise Exception(f"Bezirk {self._bezirk_search} not found.")

    def get_streets(self, search=None):
        if search:
            self._strasse_search = search

        data = {
            "id_landkreis": self._landkreis_id,
            "id_bezirk": self._bezirk_id,
            "id_kommune": self._kommune_id,
            "id_kommune_qry": self._kommune_id,
            "strasse_qry": self._strasse_search,
        }

        r = self._request("strasse/", data=data)
        r.raise_for_status()
        streets = []
        for a in extract_onclicks(r):
            streets.append(
                {
                    "id": a[0],
                    "name": a[1],
                    "id_kommune": (
                        a[5]["set_id_kommune"] if "set_id_kommune" in a[5] else None
                    ),
                    "id_beirk": (
                        a[5]["set_id_bezirk"] if "set_id_bezirk" in a[5] else None
                    ),
                    "hrns": a[3] != "fertig",
                }
            )
        return streets

    def select_street(self, street=None):
        if street:
            self._strasse_search = street
        streets = self.get_streets()
        if self._strasse_search is None and len(streets) == 1:
            self._strasse_search = streets[0]["name"]
        if self._strasse_search is None and len(streets) == 0:
            return
        elif self._strasse_search is None:
            raise Exception(
                f"Street expected, available: {[s['name'] for s in streets]}"
            )

        for street in streets:
            if compare(street["name"], self._strasse_search):
                self._f_id_strasse = self._strasse_id = street["id"]
                if street["id_kommune"] is not None:
                    self._kommune_id = street["id_kommune"]
                if street["id_beirk"] is not None:
                    self._bezirk_id = street["id_beirk"]
                self._hnrs = street["hrns"]
                return
        street_names = [s["name"] for s in streets]
        raise Exception(
            f"Street '{self._strasse_search}' not found. available: {street_names}"
        )

    def get_hrn_needed(self) -> bool:
        return self._hnrs

    def get_hnrs(self):
        data = {
            "id_landkreis": self._landkreis_id,
            "id_kommune": self._kommune_id,
            "id_bezirk": self._bezirk_id if self._bezirk_id else "",
            "id_strasse": self._strasse_id,
        }

        r = self._request(
            "hnr/",
            data=data,
        )
        hnrs = []
        for a in extract_onclicks(r, hnr=True):
            hnrs.append(
                {
                    "id": a[0],
                    "name": a[0].split("|")[0],
                    "f_id_strasse": a[6] if len(a) > 6 else None,
                }
            )
        return hnrs

    def select_hnr(self, hnr=None):
        if hnr:
            self._hnr_search = hnr
        hnrs = self.get_hnrs()
        if self._hnr_search is None and len(hnrs) == 1:
            self._hnr_search = hnrs[0]["name"]
        elif self._hnr_search is None and len(hnrs) == 0:
            return
        elif self._hnr_search is None:
            raise Exception(f"hnr expected, available: {[hnr['name'] for hnr in hnrs]}")
        for hnr in hnrs:
            if compare(hnr["name"], self._hnr_search, remove_space=True):
                self._hnr = hnr["id"]
                if hnr["f_id_strasse"] is not None:
                    self._f_id_strasse = hnr["f_id_strasse"]
                return
        raise Exception(f"HNR {self._hnr_search} not found.")

    def select_all_waste_types(self):
        data = {
            "f_id_region": self._region_id if hasattr(self, "_region_id") else "",
            "f_id_bundesland": self._bundesland_id,
            "f_id_landkreis": self._landkreis_id,
            "f_id_kommune": self._kommune_id,
            "f_id_bezirk": "",  # self._bezirk_id,
            "f_id_strasse": self._f_id_strasse,
            "f_hnr": self._hnr,
            "f_kdnr": "",
        }
        r = self._request("abfallarten/", data=data)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, features="html.parser")
        self._f_id_abfallart = []
        for to_skip in ABFALLARTEN_H2_SKIP:
            to_skip_element = soup.find("h2", text=to_skip)
            div_to_skip = (
                to_skip_element.find_parent("div") if to_skip_element else None
            )
            if div_to_skip:
                for input in to_skip_element.find_parent("div").find_all(
                    "input", {"name": "f_id_abfallart[]"}
                ):
                    if compare(input.text, self._region_search, remove_space=True):
                        id = input.attrs["id"].split("_")[-1]
                        self._f_id_abfallart.append(input.attrs["value"])
                        self._needs_subtitle.append(id)
                        if id.isdigit():
                            self._needs_subtitle.append(str(int(id) - 1))
                        break
                # remove sondermuell h2 from soup
                div_to_skip.decompose()

        for input in soup.find_all("input", {"name": "f_id_abfallart[]"}):
            if input.attrs["value"] == "0":
                if "id" not in input.attrs:
                    continue
                id = input.attrs["id"].split("_")[-1]
                self._f_id_abfallart.append(id)
                self._needs_subtitle.append(id)
                if id.isdigit():
                    self._needs_subtitle.append(str(int(id) - 1))
                continue

            self._f_id_abfallart.append(input.attrs["value"])
        self._f_id_abfallart = list(set(self._f_id_abfallart))
        self._needs_subtitle = list(set(self._needs_subtitle))

    def validate(self):
        data = {
            # "f_id_region": self._region_id if hasattr(self, "_region_id") else "",
            "f_id_bundesland": self._bundesland_id,
            "f_id_landkreis": self._landkreis_id,
            "f_id_kommune": self._kommune_id,
            "f_id_bezirk": "",  # self._bezirk_id,
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

        r = self._request("ueberpruefen/", data=data)
        r.raise_for_status()
        data["f_datenschutz"] = datetime.now().strftime("%Y%m%d%H%M%S")
        r = self._request("finish/", data=data)
        r.raise_for_status()

    def get_collections(self) -> list[dict[str, date | str]]:
        """Get collections for the selected address as a list of dicts.

        Returns:
            list[dict[str, date|str]]: all collection dates
        """
        r = self._request(
            "version.xml",
            base=API_BASE,
            data={"client": self._client, "app_id": self._app_id},
        )
        r = self._request(
            "version.xml",
            params={"renew": 1},
            base=API_BASE,
            data={"client": self._client, "app_id": self._app_id},
        )
        r = self._request(
            "struktur.xml.zip",
            base=API_BASE,
            data={"client": self._client, "app_id": self._app_id},
        )
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "xml")
        soup_categories = soup.find("key", text="categories")
        if not soup_categories:
            raise Exception("No categories found.")
        soup_array = soup_categories.find_next_sibling("array")
        if not soup_array or not isinstance(soup_array, Tag):
            raise Exception("No array found.")

        categories = {}

        for category in soup_array.find_all("dict"):
            id = category.find("key", text="id").find_next_sibling("string").text
            name = (
                category.find("key", text="name")
                .find_next_sibling("string")
                .text.replace("![CDATA[", "")
                .replace("]]", "")
                .strip()
            )
            if any(s_id in id for s_id in self._needs_subtitle):
                subtitle = (
                    category.find("key", text="subtitle")
                    .find_next_sibling("string")
                    .text.replace("![CDATA[", "")
                    .replace("]]", "")
                    .strip()
                )
                name += " - " + subtitle
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
        if self._bundesland_search:
            self.select_bundesland()
        if self._landkreis_search:
            self.select_landkreis()
        if self._region_search:
            self.select_kommune()
        finished = False
        if self._bezirk_search:
            finished = self.select_bezirk()
        if not finished:
            self.select_street()
            if self._hnrs:
                self.select_hnr()
        self.select_all_waste_types()
        self.validate()
        return self.get_collections()

    def test(self):
        print(self.generate_calendar())

    def get_suppoted_by_bl(self):
        supported = []
        for i in range(1, 17):
            r = self._request("landkreis/", data={"id_bundesland": i})
            r.raise_for_status()
            soup = BeautifulSoup(r.text, features="html.parser")

            for a in soup.find_all("a"):
                if "gibt es bereits eine eigene App" in str(a):
                    continue
                if "Dieser Landkreis wird aktuell nicht unterstützt" in str(a):
                    continue
                if "in Kürze unterstützt." in str(a):
                    continue
                supported.append(a.text.strip())
        return supported

    def clear(self, above):
        if above >= 4:
            self._bundesland_id = None
        if above >= 3:
            self._landkreis_id = None
        if above >= 2:
            self._kommune_id = None
        if above >= 1:
            self._bezirk_id = None
            self._strasse_id = None
        if above >= 0:
            self._hnr = None
            self._hnr_id = None

    def debug(self):
        r = "AppAbfallplusDe("
        r += f"""app_id={self._app_id},
        hnr={self._hnr},
        bundesland_id={self._bundesland_id},
        landkreis_id={self._landkreis_id},
        kommune_id={self._kommune_id},
        bezirk_id={self._bezirk_id},
        strasse_id={self._strasse_id}
        -- SEARCH --
        (
            bundesland_search={self._bundesland_search},
            landkreis_search={self._landkreis_search},
            region_search={self._region_search},
            strasse_search={self._strasse_search},
            hnr_search={self._hnr_search},
        )
        """
        return r + ")"


def generate_supported_services(suppoted_apps=SUPPORTED_APPS):
    supported_services = {}
    for index, app_id in enumerate(suppoted_apps):
        print(f"starting {index + 1}/{len(suppoted_apps)}: {app_id}")
        supported_services[app_id] = []
        app = AppAbfallplusDe(app_id, "", "", "")
        app.init_connection()
        if name := app.get_kom_or_lk_name():
            supported_services[app_id].append(name)
            continue
        print(json.dumps(supported_services, indent=4, ensure_ascii=False))

        for region in app.get_kommunen():
            supported_services[app_id].append(region["name"])

        if supported_services[app_id] == []:
            supported_services[app_id].extend(app.get_suppoted_by_bl())

        print(json.dumps(supported_services, indent=4, ensure_ascii=False))
    print("\n\n\nFINAL:" + json.dumps(supported_services, indent=4, ensure_ascii=False))


def get_newly_supported_apps():
    """Parse the Play Store page to get the app IDs of the newly supported apps."""
    # DO NOT MOVE THIS IMPORT TO THE TOP IT MAY BREAK THE SCRIPT IF SELENIUM IS NOT INSTALLED
    import time

    from selenium import webdriver
    from selenium.webdriver.firefox.options import Options
    from selenium.webdriver.firefox.service import Service as FirefoxService
    from webdriver_manager.firefox import GeckoDriverManager

    base_url = "https://play.google.com/store/apps/developer?id=Abfall%2B"

    # Setup Firefox options
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # Initialize the Firefox driver
    driver = webdriver.Firefox(
        service=FirefoxService(GeckoDriverManager().install()), options=options
    )
    driver.get(base_url)

    app_ids = set()
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        # Scroll down to the bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)  # Wait to load the page

        # Extract app IDs
        soup = BeautifulSoup(driver.page_source, "html.parser")
        for link in soup.find_all("a"):
            href = link.get("href")
            if link and "/store/apps/details?id=" in href:
                app_id = href.split("=")[-1]
                app_ids.add(app_id)

        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    driver.quit()
    # print changes
    print(f"Added: {app_ids - set(SUPPORTED_APPS)}")


if __name__ == "__main__":
    # get_newly_supported_apps()
    generate_supported_services()

    # Check if the app is supported and works with user agent
    # app = AppAbfallplusDe("de.biberach.abfallapp", "", "", "")
    # app.init_connection()
    # print(app.get_kom_or_lk_name())
    # print(app.get_kommunen())
