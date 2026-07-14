import re
from datetime import date
from difflib import get_close_matches
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequiredWithSuggestions,
)

TITLE = "Stadtwerke Singen"
DESCRIPTION = "Source for Stadtwerke Singen, Germany."
URL = "https://www.stadtwerke-singen.de"
COUNTRY = "de"
TEST_CASES = {
    "Im Twielfeld": {"street": "Im Twielfeld"},
    "Beuren (Ortsteil)": {"street": "Beuren"},
    "Alemannenstraße 10": {"street": "Alemannenstraße", "house_number": 10},
    "Alemannenstraße 60": {"street": "Alemannenstraße", "house_number": 60},
}

ICON_MAP = {
    "Biomüllabfuhr": Icons.ORGANIC,
    "Restmüllabfuhr (schwarzer Deckel)": Icons.GENERAL_WASTE,
    "Restmüll mit rotem Deckel": Icons.GENERAL_WASTE,
    "Altpapier": Icons.PAPER,
    "Gelbe Tonne": Icons.PLASTIC_PACKAGING,
    "Christbaumabfuhr": Icons.CHRISTMAS_TREE,
}

PARAM_TRANSLATIONS = {
    "en": {
        "street": "Street or district",
        "house_number": "House number",
    },
    "de": {
        "street": "Straße oder Ortsteil",
        "house_number": "Hausnummer",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "street": (
            "Street name as listed in the Stadtwerke Singen waste calendar "
            "street directory, or one of the outlying districts (Beuren, "
            "Bohlingen, Friedingen, Hausen, Schlatt, Überlingen)."
        ),
        "house_number": (
            "House number. Only required if the street is split into "
            "several address ranges with different collection days "
            "(e.g. 'Alemannenstraße')."
        ),
    },
    "de": {
        "street": (
            "Straßenname wie im Straßenverzeichnis des Abfallkalenders der "
            "Stadtwerke Singen, oder einer der Stadtteile (Beuren, "
            "Bohlingen, Friedingen, Hausen, Schlatt, Überlingen)."
        ),
        "house_number": (
            "Hausnummer. Nur erforderlich, wenn die Straße in mehrere "
            "Adressbereiche mit unterschiedlichen Abfuhrterminen aufgeteilt "
            "ist (z. B. 'Alemannenstraße')."
        ),
    },
}

_OVERVIEW_URL = "https://www.stadtwerke-singen.de/abfall/abfallkalender/"

_GERMAN_MONTHS = {
    "januar": 1,
    "februar": 2,
    "märz": 3,
    "april": 4,
    "mai": 5,
    "juni": 6,
    "juli": 7,
    "august": 8,
    "september": 9,
    "oktober": 10,
    "november": 11,
    "dezember": 12,
}


def _extract_abfuhr_id(href: str) -> int | None:
    values = parse_qs(urlparse(href).query).get("abfuhr")
    return int(values[0]) if values else None


def _parse_range(part: str) -> tuple[int, int | None] | None:
    match = re.match(r"(\d+)\s*-\s*(Ende|\d+)", part.strip())
    if not match:
        return None
    low = int(match.group(1))
    high = None if match.group(2) == "Ende" else int(match.group(2))
    return low, high


def _house_number_in_range(house_number: int, suffix: str | None) -> bool:
    if suffix is None:
        return True

    body = suffix
    if body.lower().startswith("nr."):
        body = body[3:].strip()

    parts = re.split(r"\s+u\.\s+", body)
    for part in parts:
        parsed = _parse_range(part)
        if parsed is None:
            continue
        low, high = parsed
        if house_number < low:
            continue
        if high is not None and house_number > high:
            continue
        if len(parts) > 1 and house_number % 2 != low % 2:
            continue
        return True
    return False


class Source:
    def __init__(self, street: str, house_number: int | None = None):
        self._street = street.strip()
        self._house_number = house_number
        self._year = 0

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        base_url = self._get_base_url(session)
        abfuhr_id = self._resolve_abfuhr_id(session, base_url)
        return self._parse_schedule(session, base_url, abfuhr_id)

    def _get_base_url(self, session: requests.Session) -> str:
        r = session.get(_OVERVIEW_URL)
        r.raise_for_status()

        match = re.search(
            r"https://www\.stadtwerke-singen\.de/abfall/abfallkalender-(\d{4})/",
            r.text,
        )
        if not match:
            raise SourceArgumentNotFoundWithSuggestions(
                "street",
                self._street,
                [],
            )

        self._year = int(match.group(1))
        return match.group(0)

    def _resolve_abfuhr_id(self, session: requests.Session, base_url: str) -> int:
        r = session.get(base_url)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # 1. Outlying districts are addressed directly, no house number needed.
        for a in soup.select("div.districtdirectory a"):
            if a.get_text(strip=True).casefold() == self._street.casefold():
                abfuhr_id = _extract_abfuhr_id(a["href"])
                if abfuhr_id is not None:
                    return abfuhr_id

        # 2. Otherwise look the street up in the alphabetical street directory.
        letter = self._street[0].casefold()
        r = session.get(base_url, params={"st": letter})
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        entries: list[tuple[str, str, str | None, int]] = []
        street_list = soup.find("ul", class_="streetlist")
        if street_list:
            for a in street_list.find_all("a"):
                text = a.get_text(strip=True)
                abfuhr_id = _extract_abfuhr_id(a["href"])
                if abfuhr_id is None:
                    continue
                match = re.match(r"^(.*?)\s*\((Nr\..*)\)\s*$", text)
                if match:
                    base_name, suffix = match.group(1).strip(), match.group(2).strip()
                else:
                    base_name, suffix = text, None
                entries.append((text, base_name, suffix, abfuhr_id))

        matches = [e for e in entries if e[1].casefold() == self._street.casefold()]

        if not matches:
            all_names = sorted({e[1] for e in entries})
            suggestions = get_close_matches(self._street, all_names, n=5, cutoff=0.5)
            raise SourceArgumentNotFoundWithSuggestions(
                "street", self._street, suggestions
            )

        if len(matches) == 1:
            return matches[0][3]

        if self._house_number is None:
            raise SourceArgumentRequiredWithSuggestions(
                "house_number",
                f"street '{self._street}' is split into several address ranges",
                [m[0] for m in matches],
            )

        for _display, _base_name, suffix, abfuhr_id in matches:
            if _house_number_in_range(self._house_number, suffix):
                return abfuhr_id

        raise SourceArgumentNotFoundWithSuggestions(
            "house_number", self._house_number, [m[0] for m in matches]
        )

    def _parse_schedule(
        self, session: requests.Session, base_url: str, abfuhr_id: int
    ) -> list[Collection]:
        r = session.get(base_url, params={"abfuhr": abfuhr_id})
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        entries: list[Collection] = []

        for div in soup.find_all("div", class_="muellresp"):
            h4 = div.find("h4")
            if not h4:
                continue
            waste_type = h4.get_text(strip=True)
            icon = ICON_MAP.get(waste_type)

            for wrapper in div.find_all("div", class_="collection-wrapper"):
                month_div = wrapper.find("div", class_="collection-month")
                date_div = wrapper.find("div", class_="collection-date")
                if not month_div or not date_div:
                    continue

                month_name = month_div.get_text(strip=True).rstrip(":").casefold()
                month = _GERMAN_MONTHS.get(month_name)
                if month is None:
                    continue

                for day_str in date_div.get_text(strip=True).split(","):
                    day_str = day_str.strip().rstrip(".")
                    if not day_str:
                        continue
                    day = int(day_str.split(".")[0])
                    entries.append(
                        Collection(date(self._year, month, day), waste_type, icon)
                    )

        # The christmas-tree collection is a single line of full dates
        # (DD.MM.YYYY) instead of the per-month breakdown used above.
        for h4 in soup.find_all("h4"):
            title = h4.get_text(strip=True)
            if title != "Christbaumabfuhr":
                continue
            parent = h4.parent
            text = parent.get_text(" ", strip=True).replace(title, "", 1).strip()
            for match in re.findall(r"\d{2}\.\d{2}\.\d{4}", text):
                day, month, year = (int(part) for part in match.split("."))
                entries.append(
                    Collection(date(year, month, day), title, ICON_MAP.get(title))
                )

        return entries
