import re

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "Abfallwirtschaftsbetrieb LK Mainz-Bingen"
DESCRIPTION = "Source for Abfallwirtschaftsbetrieb LK Mainz-Bingen."
URL = "https://www.awb-mainz-bingen.de/"
TEST_CASES = {
    "Stadt Ingelheim Ingelheim Süd Albert-Schweitzer-Straße": {
        "bezirk": "Stadt Ingelheim",
        "ort": "Ingelheim Süd",
        "strasse": "Albert-Schweitzer-Straße",
    },
    "Verbandsgemeinde Rhein-Selz, Mommenheim": {
        "bezirk": "Verbandsgemeinde Rhein-Selz",
        "ort": "mOmMenHeiM",
    },
    "Stadt Bingen, Bingen-Stadt, Martinstraße (Haus-Nr.: 5 - 11, 10 - 18)": {
        "bezirk": "Stadt Bingen",
        "ort": "Bingen-Stadt",
        "strasse": "Martinstraße (Haus-Nr.: 5 - 11, 10 - 18)",
    },
}


ICON_MAP = {
    "Restmüll": "mdi:trash-can",
    "Glass": "mdi:bottle-soda",
    "Biomüll": "mdi:leaf",
    "Papier": "mdi:package-variant",
    "Gelbe/r Tonne / Sack": "mdi:recycle",
    "Problemmüll": "mdi:toxic",
}


API_URL = "https://abfallkalender.awb-mainz-bingen.de/"


class Source:
    def __init__(self, bezirk: str, ort: str, strasse: str | None = None):
        self._bezirk: str = bezirk
        self._ort: str = ort
        self._strasse: str | None = strasse
        self._ics = ICS()

    def fetch(self):
        session = requests.Session()

        # Get bezirk id from main page
        r = session.get(API_URL)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        bezirk = soup.find("select", {"id": "Abfuhrbezirk"}).find(
            "option", text=re.compile(re.escape(self._bezirk), re.IGNORECASE)
        )

        if not bezirk:
            found = [i.text for i in soup.find_all("option")][1:]
            raise Exception(
                f"No matching bezirk found search for: {self._bezirk} found: {str(found)}"
            )

        bezirk_id = bezirk.get("value")

        # set arguments to imitate xajax call
        xjxargs_string = "<xjxobj>"
        for key, value in {
            "Abfuhrbezirk": "{bezirk_id}",
            "Ortschaft": "{ort_id}",
            "Strasse": "{strasse_id}",
        }.items():
            xjxargs_string += "<e><k>" + key + "</k><v>S" + value + "</v></e>"
        xjxargs_string += "</xjxobj>"

        args = {
            "xjxfun": "show_ortsteil_dropdown",
            "xjxargs[]": xjxargs_string.format(
                bezirk_id=bezirk_id, ort_id=0, strasse_id=0
            ),
        }

        # send request to get dropdown with for ort id
        r = session.post(API_URL, data=args)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "xml")
        teilorte_div = soup.find("cmd", {"id": "divTeilort"})

        if not teilorte_div:
            raise Exception("invalid response from server", soup)

        teilorte = BeautifulSoup(
            teilorte_div.text.replace("<![CDATA[", "").replace("]]>", ""), "html.parser"
        )

        ort = teilorte.find(
            "option", text=re.compile(re.escape(self._ort), re.IGNORECASE)
        )
        if not ort:
            raise Exception(
                f"No matching ort found. Searched for: {self._ort}. Found {str([i.text for i in teilorte.find_all('option')][1:])})"
            )

        ort_id = ort.get("value")

        args = {
            "xjxfun": "show_strasse_dropdown_or_abfuhrtermine",
            "xjxargs[]": xjxargs_string.format(
                bezirk_id=bezirk_id, ort_id=ort_id, strasse_id=0
            ),
        }

        r = session.post(API_URL, data=args)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "xml")
        div_strasse = soup.find("cmd", {"id": "divStrasse"})

        if not div_strasse:
            raise Exception("invalid response from server")

        strassen_soup = BeautifulSoup(
            div_strasse.text.replace("<![CDATA[", "").replace("]]>", ""), "html.parser"
        )

        # If strasse is needed
        if strassen_soup.find("option"):
            if not self._strasse:
                raise Exception("Street needed but not provided")

            # get strasse id
            strasse_id = strassen_soup.find(
                "option", text=re.compile(re.escape(self._strasse), re.IGNORECASE)
            )
            if not strasse_id:
                found = [i.text for i in strassen_soup.find_all("option")][1:]
                raise Exception(
                    f"Street wanted but no matching street found. Searched for: {self._strasse}. Found {str(found)})"
                )

            strasse_id = strasse_id.get("value")
            xjxargs = {
                "bezirk_id": bezirk_id,
                "ort_id": ort_id,
                "strasse_id": strasse_id,
            }
            args = {
                "xjxfun": "show_abfuhrtermine",
                "xjxargs[]": xjxargs_string.format(**xjxargs),
            }

            # get main calendar
            r = session.post(API_URL, data=args)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "xml")

        cal_wrapper = soup.find("cmd", {"id": "divKalenderWrapper"})

        if not cal_wrapper:
            raise Exception("No calendar found", r.text)
        cal_soup = BeautifulSoup(
            cal_wrapper.text.replace("<![CDATA[", "").replace("]]>", ""), "html.parser"
        )

        entries = []
        # get ical file url
        for ical_path in cal_soup.findAll("a", {"href": re.compile("ical")}):
            ical_path = ical_path.get("href")
            # get ical file
            r = requests.get(API_URL + ical_path)
            r.raise_for_status()
            r.encoding = "utf-8"

            # remove DURATION because the returned icalendar has invalid DURATION syntax
            ical_string = re.sub(r"^DURATION.*\n?", "", r.text, flags=re.MULTILINE)

            dates = self._ics.convert(ical_string)
            for d in dates:
                bin_type = d[1].split(" am ")[0].replace("Abfuhrtermin", "").strip()
                entries.append(Collection(d[0], bin_type, ICON_MAP.get(bin_type)))

        return entries
