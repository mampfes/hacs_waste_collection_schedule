from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "hausmüll.info"
DESCRIPTION = "Source for hausmüll.info."
URL = "https://hausmuell.info"
COUNTRY = "de"
TEST_CASES = {
    "Dietzhausen Am Rain 10 ebkds": {
        "ort": "Dietzhausen",
        "strasse": "Am Rain",
        "hausnummer": 10,
        "subdomain": "ebkds",
    },
    "Adam-Ries-Straße 5, Erfurt": {
        "subdomain": "erfurt",
        "strasse": "Adam-Ries-Straße",
        "hausnummer": "5",
    },
    "schmalkalden-meiningen, Obermaßfeld-Grimmenthal": {
        "subdomain": "schmalkalden-meiningen",
        "ort": "Obermaßfeld-Grimmenthal",
    },
    "schmalkalden-meiningen, Dillstädt": {
        "subdomain": "schmalkalden-meiningen",
        "ort": "Dillstädt",
    },
    "schmalkalden-meiningen Zella-Mehils Benshausen Albrechter Straße": {
        "subdomain": "schmalkalden-meiningen",
        "ort": "Zella-Mehlis",
        "ortsteil": "Benshausen",
        "strasse": "Albrechtser Straße",
    },
    "schmalkalden-meiningen Breitungen, Bußhof": {
        "subdomain": "schmalkalden-meiningen",
        "ort": "Breitungen",
        "ortsteil": "Bußhof",
    },
    "ew, Döringsdorf, Wanfrieder Str.": {
        "subdomain": "ew",
        "ort": "Döringsdorf",
        "strasse": "Wanfrieder Str.",
    },
    "ew, Bernterode (WBS), Hinter den Höfen": {
        "subdomain": "ew",
        "ort": "Bernterode (WBS)",
        "strasse": "Hinter den Höfen",
    },
    "azv, Berka vor dem Hainich": {
        "subdomain": "azv",
        "ort": "Berka vor dem Hainich",
    },
    "azv, Hörselberg-Hainich": {
        "subdomain": "azv",
        "ort": "Hörselberg-Hainich",
        "ortsteil": "Ettenhausen/Nesse",
    },
    "börde, Belsdorf (Altkreis BÖ), Alleringerslebener Straße 15a": {
        "subdomain": "boerde",
        "ort": "Belsdorf (Altkreis BÖ)",
        "strasse": "Alleringerslebener Straße",
        "hausnummer": "15a",
    },
    "chemnitz, Straße des Friedens/Wittgensdorf 2 a": {
        "subdomain": "asc",
        "strasse": "Straße des Friedens/Wittgensdorf",
        "hausnummer": "2 a",
    },
    "wesel Flüren, In der Flürener Heide": {
        "subdomain": "wesel",
        "ort": "Flüren",
        "strasse": "In der Flürener Heide",
    },
}


ICON_MAP = {
    "hausmüll": "mdi:trash-can",
    "restabfall": "mdi:trash-can",
    "restmüll": "mdi:trash-can",
    "glass": "mdi:bottle-soda",
    "biomüll": "mdi:leaf",
    "biomüll mit reinigung": "mdi:leaf",
    "bioabfall mit reinigung": "mdi:leaf",
    "bioabfall": "mdi:leaf",
    "papier": "mdi:package-variant",
    "papier, pappe, karton": "mdi:package-variant",
    "papier, pappe & kart.": "mdi:package-variant",
    "pappe, papier & kart.": "mdi:package-variant",
    "altpapier": "mdi:package-variant",
    "gelbe tonne": "mdi:recycle",
    "gelber sack": "mdi:recycle",
    "gelber sack / gelbe tonne": "mdi:recycle",
    "leichtverpackungen": "mdi:recycle",
    "leichtstoffverpackungen": "mdi:recycle",
    "grünschnitt": "mdi:tree",
    "schadstoffe": "mdi:biohazard",
    "schadstoffmobil": "mdi:biohazard",
    "problemmüll": "mdi:biohazard",
}

SUPPORTED_PROVIDERS = [
    {
        "subdomain": "ebkds",
        "title": "Eigenbetrieb Kommunalwirtschaftliche Dienstleistungen Suhl",
        "url": "https://www.ebkds.de/",
    },
    {
        "subdomain": "erfurt",
        "title": "Stadtwerke Erfurt, SWE",
        "url": "https://www.stadtwerke-erfurt.de/",
    },
    {
        "subdomain": "schmalkalden-meiningen",
        "title": "Kreiswerke Schmalkalden-Meiningen GmbH",
        "url": "https://www.kwsm.de/",
    },
    {
        "subdomain": "ew",
        "title": "Eichsfeldwerke GmbH",
        "url": "https://www.eichsfeldwerke.de/",
    },
    {
        "subdomain": "azv",
        "title": "Abfallwirtschaftszweckverband Wartburgkreis (AZV)",
        "url": "https://www.azv-wak-ea.de/",
    },
    {
        "subdomain": "boerde",
        "title": "Landkreis Börde AöR (KsB)",
        "url": "https://www.ks-boerde.de",
    },
    {
        "subdomain": "asc",
        "title": "Chemnitz (ASR)",
        "url": "https://www.asr-chemnitz.de/",
    },
    {"subdomain": "wesel", "title": "ASG Wesel", "url": "https://www.asg-wesel.de/"},
]

EXTRA_INFO = [
    {"title": p["title"], "url": p["url"], "country": "de"} for p in SUPPORTED_PROVIDERS
]


API_URL = "https://{}.hausmuell.info/"


def replace_special_chars(s: str) -> str:
    return (
        s.replace("ß", "s")
        .replace("ä", "a")
        .replace("ö", "o")
        .replace("ü", "u")
        .replace("Ä", "A")
        .replace("Ö", "O")
        .replace("Ü", "U")
    )


def replace_special_chars_with_underscore(s: str) -> str:
    return (
        s.replace("ß", "_")
        .replace("ä", "_")
        .replace("ö", "_")
        .replace("ü", "_")
        .replace("Ä", "_")
        .replace("Ö", "_")
        .replace("Ü", "_")
    )


def replace_special_chars_args(d: dict, replace_func=replace_special_chars) -> dict:
    to_return = {}
    for k, v in d.items():
        if isinstance(v, list):
            to_return[k] = [replace_func(i) for i in v]
        else:
            to_return[k] = replace_func(v)

    return to_return


class Source:
    def __init__(
        self,
        subdomain: str,
        ort: str | None = None,
        ortsteil: str | None = None,
        strasse: str | None = None,
        hausnummer: str | int | None = None,
    ):
        self._ort: str = ort if ort else ""
        self._strasse: str = strasse if strasse else ""
        self._hausnummer: str = str(hausnummer) if hausnummer else ""
        self._ortsteil: str = ortsteil if ortsteil else ""

        self._api_url: str = API_URL.format(subdomain)
        self._ics = ICS()

    def _get_elemts(self, response_text: str) -> list[str]:
        to_return: list[str] = []

        li = BeautifulSoup(response_text, "html.parser").find("li")

        if not li:
            return ["0"]
        onclick = li.get("onclick")
        if not onclick:
            return ["0"]

        ids = onclick.split(")")[0].split("(")[1].split(",")

        to_return = [i.strip() for i in ids if i.strip().isdigit()]
        return to_return

    def request_all(
        self, url: str, data: dict, params: dict, error_message: str
    ) -> requests.Response:
        """Request url with data if not successful retry with different kinds of replaced special chars.

        Args:
            url (str): url to request
            data (dict): data to send
            params (dict): params to send
            error_message (str): error message to raise if all requests fail

        Raises:
            Exception: if all requests fail

        Returns:
            requests.Response: the successful response
        """
        r = requests.post(url, data=data, params=params)
        if "kein Eintrag gefunden" not in r.text and not "<ul></ul>" == r.text.strip():
            return r
        r = requests.post(
            url,
            data=replace_special_chars_args(data),
            params=replace_special_chars_args(params),
        )
        if "kein Eintrag gefunden" not in r.text and not "<ul></ul>" == r.text.strip():
            return r
        r = requests.post(
            url,
            data=replace_special_chars_args(
                data, replace_special_chars_with_underscore
            ),
            params=replace_special_chars_args(params),
        )
        if "kein Eintrag gefunden" not in r.text and not "<ul></ul>" == r.text.strip():
            return r
        raise Exception(error_message)

    def fetch(self):
        args = {
            "hidden_kalenderart": "privat",
            "input_ort": self._ort,
            "input_ortsteil": self._ortsteil,
            "input_str": [self._strasse, self._strasse],
            "input_hnr": [self._hausnummer, self._hausnummer],
            "ort_id": "0",
            "ortteil_id": "0",
            "str_id": "0",
            "hidden_id_ort": "0",
            "hidden_id_ortsteil": "0",
            "hidden_id_str": "0",
            "hidden_id_hnr": "0",
            "hidden_id_egebiet": "0",
            "hidden_send_btn": "ics",
            "hiddenYear": str(datetime.now().year),
        }

        r = requests.get(self._api_url)
        if r.url != self._api_url:
            self._api_url = r.url
        self._search_url: str = self._api_url + "search/"
        self._ics_url: str = self._api_url + "ics/ics.php"

        soup = BeautifulSoup(r.text, "html.parser")
        for i in soup.find_all("input"):
            if i.get("name").startswith("showBins"):
                args[i.get("name")] = "on"

        if self._ort:
            args["input"] = self._ort
            r = self.request_all(
                self._search_url + "search_orte.php",
                args,
                {"input": self._ort, "ort_id": "0"},
                "Ort provided but not found in search results.",
            )

            ids = self._get_elemts(r.text)
            args["hidden_id_ort"] = args["ort_id"] = ids[0]
            if len(ids) > 1:
                args["hidden_id_egebiet"] = ids[1]

        if self._ortsteil:
            r = self.request_all(
                self._search_url + "search_ortsteile.php",
                args,
                {"input": self._ortsteil, "ort_id": args["ort_id"]},
                "Ortsteil provided but not found in search results.",
            )

            ids = self._get_elemts(r.text)

            args["ort_id"] = args["hidden_id_ortsteil"] = (
                args["hidden_id_ort"] if ids[0] == "0" else ids[0]
            )
            if len(ids) > 1:
                args["hidden_id_egebiet"] = ids[1]

        if self._strasse:
            r = self.request_all(
                self._search_url + "search_strassen.php",
                args,
                {"input": self._strasse, "str_id": "0", "ort_id": args["ort_id"]},
                "Strasse provided but not found in search results.",
            )
            ids = self._get_elemts(r.text)
            args["hidden_id_str"] = args["str_id"] = ids[0]
            if len(ids) > 1:
                args["hidden_id_egebiet"] = ids[1]

        if self._hausnummer:
            args["input"] = self._hausnummer
            r = self.request_all(
                self._search_url + "search_hnr.php",
                args,
                {"input": self._hausnummer, "hnr_id": "0", "str_id": args["str_id"]},
                "hausnummer provided but not found in search results.",
            )

            ids = self._get_elemts(r.text)
            args["hidden_id_hnr"] = args["hnr_id"] = ids[0]
            if len(ids) > 1:
                args["hidden_id_egebiet"] = ids[1]

        r = requests.post(self._search_url + "check_zusatz.php", data=args)
        id_string = BeautifulSoup(r.text, "html.parser").find("span")
        args["hidden_id_zusatz"] = (
            args["hidden_id_hnr"] if id_string is None else id_string.text.strip()
        )

        r = requests.post(self._ics_url, data=args)
        r.raise_for_status()

        if "Bitte geben Sie Ihre Daten korrekt an." in r.text:
            raise ValueError("No Valid response, please check your configuration.")

        r.encoding = "utf-8"
        dates = self._ics.convert(r.text)
        entries = []
        for d in dates:
            bin_type = d[1].replace("Ã¼", "ü").replace("Entsorgung:", "").strip()
            icon = ICON_MAP.get(
                bin_type.lower().replace("verschobene abholung:", "").strip()
            )
            entries.append(Collection(d[0], bin_type, icon))

        return entries
