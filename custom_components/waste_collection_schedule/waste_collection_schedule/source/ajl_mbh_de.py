import re
from datetime import date

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "AJL - Abfallwirtschaftsgesellschaft Jerichower Land mbH"
DESCRIPTION = (
    "Source for AJL - Abfallwirtschaftsgesellschaft Jerichower Land mbH, Germany."
)
URL = "https://www.ajl-mbh.de"
COUNTRY = "de"

TEST_CASES = {
    "Biederitz (no street)": {"town": "Biederitz"},
    "Burg, Fliederweg": {"town": "Burg", "street": "Fliederweg"},
    "Biederitz by ID": {"town": 98},
    "Burg by ID with street ID": {"town": 154, "street": 313},
}

ICON_MAP = {
    "Gelbe Tonne": Icons.PLASTIC_PACKAGING,
    "Papier": Icons.PAPER,
    "Biomüll": Icons.ORGANIC,
    "Restmüll": Icons.GENERAL_WASTE,
    "Sperrmüll": Icons.BULKY,
    "Schadstoffmobil": Icons.HAZARDOUS,
    "Weihnachtsbaum": Icons.CHRISTMAS_TREE,
}

PARAM_TRANSLATIONS = {
    "en": {
        "town": "Town",
        "street": "Street (only needed for towns with multiple collection zones)",
    },
    "de": {
        "town": "Ort",
        "street": "Straße (nur bei Orten mit mehreren Abholbereichen nötig)",
    },
}

BASE_URL = "https://www.ajl-mbh.de/abfallkalender/entsorgungstermine"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def _fetch_towns() -> dict[str, int]:
    """Return a mapping of town name → town ID from the base page."""
    r = requests.get(BASE_URL, headers=HEADERS, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    towns: dict[str, int] = {}
    for a in soup.find_all("a", class_="stadtbutton"):
        href = a.get("href", "")
        m = re.search(r"town=(\d+)", href)
        name = a.get("name", "").strip()
        if m and name:
            towns[name] = int(m.group(1))
    return towns


def _fetch_streets(town_id: int, year: int) -> dict[str, int]:
    """Return a mapping of street name → street ID for the given town."""
    r = requests.get(
        BASE_URL,
        params={"year": year, "town": town_id},
        headers=HEADERS,
        timeout=30,
    )
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    streets: dict[str, int] = {}
    select = soup.find("select", id="street")
    if select:
        for option in select.find_all("option"):
            val = option.get("value", "")
            label = option.get_text(strip=True)
            if val and val != "-1" and label:
                try:
                    streets[label] = int(val)
                except ValueError:
                    pass
    return streets


class Source:
    def __init__(
        self,
        town: str | int,
        street: str | int | None = None,
    ):
        self._town = town
        self._street = street

    def fetch(self) -> list[Collection]:
        today = date.today()
        year = today.year

        # Resolve town ID
        if isinstance(self._town, int):
            town_id = self._town
        else:
            towns = _fetch_towns()
            # Case-insensitive fallback
            match = towns.get(self._town)
            if match is None:
                # Try case-insensitive
                lower_map = {k.lower(): v for k, v in towns.items()}
                match = lower_map.get(self._town.lower())
            if match is None:
                raise SourceArgumentNotFoundWithSuggestions(
                    "town",
                    self._town,
                    list(towns.keys()),
                )
            town_id = match

        # Resolve street ID (if provided)
        street_id: int | None = None
        if self._street is not None:
            if isinstance(self._street, int):
                street_id = self._street
            else:
                streets = _fetch_streets(town_id, year)
                match_s = streets.get(self._street)
                if match_s is None:
                    lower_map_s = {k.lower(): v for k, v in streets.items()}
                    match_s = lower_map_s.get(self._street.lower())
                if match_s is None:
                    raise SourceArgumentNotFoundWithSuggestions(
                        "street",
                        self._street,
                        list(streets.keys()),
                    )
                street_id = match_s

        # Fetch calendar page
        params: dict[str, int | str] = {"year": year, "town": town_id}
        if street_id is not None:
            params["street"] = street_id

        r = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=30)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # Extract year from heading (e.g. "Abholtermine 2026 für …")
        cal_year = year
        heading = soup.find("h2", class_="ajl-green")
        if heading:
            m = re.search(r"(\d{4})", heading.get_text())
            if m:
                cal_year = int(m.group(1))

        # Find the calenderview div
        cal_div = soup.find("div", id="calenderview")
        if cal_div is None:
            # Town requires a street selection — no data available at town level
            streets = _fetch_streets(town_id, year)
            raise SourceArgumentNotFoundWithSuggestions(
                "street",
                str(self._street),
                list(streets.keys()),
            )

        entries: list[Collection] = []
        for cat_div in cal_div.find_all("div", class_="cat"):
            # The inner div has a class like cat-gelb, cat-papier, etc.
            inner = cat_div.find("div", class_=re.compile(r"^cat-"))
            if inner is None:
                continue
            h3 = inner.find("h3")
            if h3 is None:
                continue
            waste_type = h3.get_text(strip=True)
            icon = ICON_MAP.get(waste_type)

            for day_div in inner.find_all("div", class_="dayprint"):
                text = day_div.get_text(strip=True)
                # Format: "Mo 19.01." → day=19, month=01
                dm = re.search(r"(\d{1,2})\.(\d{2})\.", text)
                if dm:
                    try:
                        d = date(cal_year, int(dm.group(2)), int(dm.group(1)))
                        entries.append(Collection(d, waste_type, icon=icon))
                    except ValueError:
                        pass

        return entries
