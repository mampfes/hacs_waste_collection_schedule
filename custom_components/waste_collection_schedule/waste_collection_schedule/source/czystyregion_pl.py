import json
import re
from datetime import datetime

from curl_cffi import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Czysty Region"
DESCRIPTION = "Source for Związek Międzygminny Czysty Region waste collection (Opole/Silesia region, Poland)."
URL = "https://www.czystyregion.pl"
COUNTRY = "pl"

HARMONOGRAMY_URL = f"{URL}/Harmonogramy"

RODZAJ_CHOICES = {"wielorodzinna", "jednorodzinna", "firma"}

TEST_CASES = {
    "Cisek (jednorodzinna)": {
        "gmina": "Cisek",
        "miejscowosc": "Cisek",
        "rodzaj": "jednorodzinna",
    },
    "Cisek (firma)": {
        "gmina": "Cisek",
        "miejscowosc": "Cisek",
        "rodzaj": "firma",
    },
    "Kędzierzyn-Koźle, ul. Piastów (wielorodzinna)": {
        "gmina": "Kędzierzyn-Koźle",
        "miejscowosc": "Kędzierzyn-Koźle",
        "rodzaj": "wielorodzinna",
        "ulica": "Piastów",
    },
    "Polska Cerekiew, ul. Kozielska (jednorodzinna)": {
        "gmina": "Polska Cerekiew",
        "miejscowosc": "Polska Cerekiew",
        "rodzaj": "jednorodzinna",
        "ulica": "Kozielska",
    },
}

ICON_MAP = {
    "Odpady zmieszane": Icons.GENERAL_WASTE,
    "Tworzywa sztuczne/ Metale": Icons.RECYCLING,
    "Papier": Icons.PAPER,
    "Szkło": Icons.GLASS,
    "Odpady BIO": Icons.ORGANIC,
    "Popiół": Icons.GENERAL_WASTE,
    "Zbiórka Akcyjna": Icons.BULKY,
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Open https://www.czystyregion.pl/Harmonogramy and step through the "
        "dropdowns (Wybierz gminę -> Wybierz rodzaj -> Wybierz miejscowość) "
        "to find the exact spelling of your commune (gmina) and town/village "
        "(miejscowość). If the result table lists more than one row for your "
        "town (e.g. large towns split into several 'Rejon' street groups), "
        "also note a distinctive street name from the 'Rejon' description "
        "shown for your area and pass it as 'ulica'."
    ),
}

PARAM_TRANSLATIONS = {
    "en": {
        "gmina": "Commune (gmina)",
        "miejscowosc": "Town/village (miejscowość)",
        "rodzaj": "Property type (rodzaj)",
        "ulica": "Street (for disambiguation)",
    },
    "de": {
        "gmina": "Gemeinde (gmina)",
        "miejscowosc": "Ort (miejscowość)",
        "rodzaj": "Immobilientyp (rodzaj)",
        "ulica": "Straße (zur Unterscheidung)",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "gmina": "Name of the commune (gmina) as listed on czystyregion.pl.",
        "miejscowosc": "Name of the town/village as listed on czystyregion.pl.",
        "rodzaj": "One of: wielorodzinna (multi-family), jednorodzinna (single-family), firma (business).",
        "ulica": "Optional street name used to pick the right area when your town has several separate schedules (only needed if the source reports an ambiguous result).",
    },
    "de": {
        "gmina": "Name der Gemeinde (gmina), wie auf czystyregion.pl gelistet.",
        "miejscowosc": "Name des Ortes, wie auf czystyregion.pl gelistet.",
        "rodzaj": "Einer von: wielorodzinna (Mehrfamilienhaus), jednorodzinna (Einfamilienhaus), firma (Gewerbe).",
        "ulica": "Optionaler Straßenname zur Auswahl des richtigen Bereichs, falls der Ort mehrere separate Pläne hat (nur bei mehrdeutigem Ergebnis nötig).",
    },
}


def _strip_tags(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", text).strip()


class Source:
    def __init__(
        self, gmina: str, miejscowosc: str, rodzaj: str, ulica: str = ""
    ) -> None:
        self._gmina = str(gmina).strip()
        self._miejscowosc = str(miejscowosc).strip()
        self._rodzaj = str(rodzaj).strip()
        self._ulica = str(ulica).strip()
        if self._rodzaj not in RODZAJ_CHOICES:
            raise SourceArgumentNotFoundWithSuggestions(
                "rodzaj", rodzaj, sorted(RODZAJ_CHOICES)
            )

    def fetch(self) -> list[Collection]:
        session = requests.Session(impersonate="chrome")

        r = session.get(HARMONOGRAMY_URL, timeout=30)
        r.raise_for_status()
        html = r.text

        token_match = re.search(r'name="_token" value="([^"]*)"', html)
        if not token_match:
            raise SourceArgumentNotFoundWithSuggestions("gmina", self._gmina, [])
        token = token_match.group(1)

        gminy_block_match = re.search(r'id="gminy"[^>]*>(.*?)</select>', html, re.S)
        gminy = {
            name.strip(): gid
            for gid, name in re.findall(
                r'<option value="(\d*)">([^<]*)</option>',
                gminy_block_match.group(1) if gminy_block_match else "",
            )
            if gid
        }
        gmina_id = next(
            (
                gid
                for name, gid in gminy.items()
                if name.casefold() == self._gmina.casefold()
            ),
            None,
        )
        if gmina_id is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "gmina", self._gmina, sorted(gminy)
            )

        regiony_match = re.search(r"var regiony = (\[.*?\]);", html, re.S)
        regiony = json.loads(regiony_match.group(1)) if regiony_match else []
        candidate_region_ids = [
            str(region["id"])
            for region in regiony
            if str(region.get("gmina_id")) == gmina_id
            and str(region.get("name", "")).strip().casefold()
            == self._miejscowosc.casefold()
        ]
        if not candidate_region_ids:
            names_for_gmina = sorted(
                {
                    str(region.get("name"))
                    for region in regiony
                    if str(region.get("gmina_id")) == gmina_id
                }
            )
            raise SourceArgumentNotFoundWithSuggestions(
                "miejscowosc", self._miejscowosc, names_for_gmina
            )

        rows: list[tuple[str, str]] = []
        for region_id in candidate_region_ids:
            resp = session.post(
                HARMONOGRAMY_URL,
                data={
                    "_token": token,
                    "gminy": gmina_id,
                    "rodzaj": self._rodzaj,
                    "regiony": region_id,
                },
                timeout=30,
            )
            resp.raise_for_status()
            tbody_match = re.search(
                r'<table id="harmonogramy".*?<tbody>(.*?)</tbody>', resp.text, re.S
            )
            if not tbody_match:
                continue
            for cell, harmonogram_id in re.findall(
                r"<tr>\s*<td>(.*?)</td>\s*<td>.*?</td>\s*<td>.*?</td>\s*"
                r'<td>.*?/Harmonogramy/(\d+)".*?</tr>',
                tbody_match.group(1),
                re.S,
            ):
                rows.append((harmonogram_id, _strip_tags(cell)))

        if not rows:
            raise SourceArgumentNotFoundWithSuggestions(
                "rodzaj", self._rodzaj, sorted(RODZAJ_CHOICES)
            )

        if len(rows) > 1 and self._ulica:
            filtered_rows = [
                (harmonogram_id, description)
                for harmonogram_id, description in rows
                if self._ulica.casefold() in description.casefold()
            ]
            if filtered_rows:
                rows = filtered_rows

        if len(rows) > 1:
            raise SourceArgAmbiguousWithSuggestions(
                "ulica",
                self._ulica,
                [description for _, description in rows],
            )

        harmonogram_id = rows[0][0]

        detail = session.get(f"{HARMONOGRAMY_URL}/{harmonogram_id}", timeout=30)
        detail.raise_for_status()

        events_match = re.search(r"events:\s*JSON\.parse\(`(.*?)`\)", detail.text, re.S)
        if not events_match:
            raise SourceArgumentNotFoundWithSuggestions(
                "miejscowosc", self._miejscowosc, []
            )
        events = json.loads(events_match.group(1))

        entries = []
        for event in events:
            try:
                date = datetime.strptime(event["start"], "%Y-%m-%d").date()
            except (KeyError, ValueError):
                continue
            waste_type = event.get("title", "")
            entries.append(Collection(date, waste_type, icon=ICON_MAP.get(waste_type)))
        return entries
