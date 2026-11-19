from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "Landkreis Erlangen-Höchstadt"
DESCRIPTION = "Source for Landkreis Erlangen-Höchstadt"
URL = "https://www.erlangen-hoechstadt.de/"
TEST_CASES = {
    "Höchstadt": {"city": "Höchstadt", "street": "Böhmerwaldstraße"},
    "Brand": {"city": "Eckental", "street": "Eckenhaid, Amselweg"},
    "Ortsteile": {"city": "Wachenroth", "street": "Ort inkl. aller Ortsteile"},
}


PARAM_TRANSLATIONS = {
    "de": {
        "city": "Ort",
        "street": "Straße / Ortsteil",
    }
}


class Source:
    def __init__(self, city: str, street: str):
        self._city = city.strip()
        self._street = street.strip()
        self._ics = ICS(split_at=" / ")
        self._base_url = (
            "https://www.erlangen-hoechstadt.de/Aktuelles/Abfallkalender/index.php"
        )
        self._autocomplete_url = (
            "https://www.erlangen-hoechstadt.de/output/autocomplete.php"
        )

    def fetch(self):
        session = requests.Session()

        # -------------------------------------------------------------
        # 1. Find location (locid)
        # -------------------------------------------------------------
        resp = session.get(self._base_url, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        loc_select = soup.find("select", {"name": "locid"}) or soup.find(
            "select", attrs={"id": lambda i: i and "locid" in i.lower()}
        )
        if not loc_select:
            raise ValueError("Could not find selection field (locid).")

        loc_id = None
        for option in loc_select.find_all("option"):
            text = option.get_text(strip=True)
            if self._city.lower() in text.lower():
                loc_id = option.get("value")
                break

        if not loc_id:
            available_cities = [
                opt.get_text(strip=True)
                for opt in loc_select.find_all("option")
                if opt.get("value")
            ]
            raise ValueError(
                f"Location '{self._city}' not found. Available: {available_cities[:10]}..."
            )

        # -------------------------------------------------------------
        # 2. Straße (pois) über Autocomplete-Endpunkt ermitteln
        # -------------------------------------------------------------
        resp = session.get(
            self._autocomplete_url,
            params={
                "out": "json",
                "type": "abto",
                "mode": "",
                "select": "2",
                "refid": loc_id,
                "term": "%",
            },
            headers={
                "X-Requested-With": "XMLHttpRequest",
                "Referer": self._base_url,
            },
            timeout=30,
        )
        resp.raise_for_status()
        suggestions = resp.json()

        pois_id = None
        poiname = ""
        for value, label in suggestions:
            if self._street.lower() in label.lower():
                pois_id = value
                poiname = label
                break

        if not pois_id:
            raise ValueError(
                f"Street '{self._street}' not found in '{self._city}'."
                f" Available: {[label for _, label in suggestions[:10]]}..."
            )

        # -------------------------------------------------------------
        # 3. Get calendar with locid & pois and get ICS link
        # -------------------------------------------------------------
        cal_params = {
            "ModID": "48",
            "object": "",
            "La": "1",
            "NavID": "4237.507",
            "kuo": "2",
            "locid": loc_id,
            "pois": pois_id,
            "poir": "",
            "poiname": poiname,
            "typ": "jahr",
            "monat": "",
        }

        cal_resp = session.get(self._base_url, params=cal_params, timeout=30)
        cal_resp.raise_for_status()

        # Check if URL provides a direct download
        if "BEGIN:VCALENDAR" in cal_resp.text:
            ics_text = cal_resp.text
        else:
            soup = BeautifulSoup(cal_resp.text, "html.parser")
            # get i-cal download button (data-href)
            ics_btn = soup.find(class_="waste-ical-btn")

            if not ics_btn or not ics_btn.get("data-href"):
                raise ValueError(
                    "Download link could not extracted from ICS file."
                )

            download_url = urljoin(self._base_url, ics_btn["data-href"])
            ics_resp = session.get(download_url, timeout=30)
            ics_resp.raise_for_status()
            ics_resp.encoding = "utf-8"
            ics_text = ics_resp.text

        # -------------------------------------------------------------
        # 4. Fill collection objects
        # -------------------------------------------------------------
        dates = self._ics.convert(ics_text)
        return [Collection(d[0], d[1]) for d in dates]
