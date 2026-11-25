from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFoundWithSuggestions,
)
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

        city_options = [
            (option.get("value"), option.get_text(strip=True))
            for option in loc_select.find_all("option")
            if option.get("value")
        ]
        exact_cities = [
            (value, label)
            for value, label in city_options
            if self._city.casefold() == label.casefold()
        ]
        city_matches = exact_cities or [
            (value, label)
            for value, label in city_options
            if self._city.casefold() in label.casefold()
        ]
        if len(city_matches) > 1:
            raise SourceArgAmbiguousWithSuggestions(
                "city", self._city, [label for _, label in city_matches]
            )
        if not city_matches:
            raise SourceArgumentNotFoundWithSuggestions(
                "city", self._city, [label for _, label in city_options]
            )
        loc_id, _ = city_matches[0]

        # -------------------------------------------------------------
        # 2. Determine street(pois) via autocomplete endpoint
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

        exact_streets = [
            (value, label)
            for value, label in suggestions
            if self._street.casefold() == label.casefold()
        ]
        street_matches = exact_streets or [
            (value, label)
            for value, label in suggestions
            if self._street.casefold() in label.casefold()
        ]
        if len(street_matches) > 1:
            raise SourceArgAmbiguousWithSuggestions(
                "street", self._street, [label for _, label in street_matches]
            )
        if not street_matches:
            raise SourceArgumentNotFoundWithSuggestions(
                "street", self._street, [label for _, label in suggestions]
            )
        pois_id, poiname = street_matches[0]

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
                raise ValueError("Download link could not extracted from ICS file.")

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
