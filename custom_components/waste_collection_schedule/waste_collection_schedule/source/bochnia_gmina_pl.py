import datetime
import io
import re
import urllib.parse

import pypdf
import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Gmina Bochnia"
DESCRIPTION = "Source for Gmina Bochnia waste collection schedule (Poland)"
URL = "http://bochnia-gmina.pl"
COUNTRY = "pl"
SOURCE_CODEOWNERS = ["@Sairento-92"]

TEST_CASES = {
    "Baczkow": {"town": "Baczków"},
    "Proszowki": {"town": "Proszówki"},
    "Lapczyca": {"town": "Łapczyca"},
}

ICON_MAP = {
    "Odpady zmieszane i segregowane": Icons.GENERAL_WASTE,
    "Gabaryty i niebezpieczne": Icons.BULKY,
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Enter the name of the town in Gmina Bochnia (e.g. Baczków, Damienice, Proszówki, Łapczyca, etc.).",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "town": "Name of the village/town in Gmina Bochnia",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "town": "Town / Village",
    },
}

PL_TRANS = str.maketrans("ąćęłńóśźżĄĆĘŁŃÓŚŹŻ", "acelnoszzACELNOSZZ")

TOWNS_PDF_MAP = {
    "Baczków": "Baczkow.pdf",
    "Bessów": "Bessow.pdf",
    "Bogucice": "Bogucice.pdf",
    "Brzeźnica": "Brzeznica.pdf",
    "Buczyna": "Buczyna.pdf",
    "Cerekiew": "Cerekiew.pdf",
    "Chełm": "Chelm.pdf",
    "Cikowice": "Cikowice.pdf",
    "Damienice": "Damienice.pdf",
    "Dąbrowica": "Dabrowica.pdf",
    "Gawłów": "Gawlow.pdf",
    "Gierczyce": "Gierczyce.pdf",
    "Gorzków": "Gorzkow.pdf",
    "Grabina": "Grabina.pdf",
    "Krzyżanowice": "Krzyzanowice.pdf",
    "Łapczyca": "Lapczyca.pdf",
    "Majkowice": "Majkowice.pdf",
    "Moszczenica": "Moszczenica.pdf",
    "Nieprześnia": "Nieprzesnia.pdf",
    "Nieszkowice Małe": "Nieszkowice male.pdf",
    "Nieszkowice Wielkie": "Nieszkowice wielkie.pdf",
    "Ostrów Szlachecki": "Ostrow szlachecki.pdf",
    "Pogwizdów": "Pogwizdow.pdf",
    "Proszówki": "Proszowki.pdf",
    "Siedlec": "Siedlec.pdf",
    "Słomka": "Slomka.pdf",
    "Stanisławice": "Stanislawice.pdf",
    "Stradomka": "Stradomka.pdf",
    "Wola Nieszkowska": "Wola nieszkowska.pdf",
    "Zatoka": "Zatoka.pdf",
    "Zawada": "Zawada.pdf",
}

MIXED_WASTE = "Odpady zmieszane i segregowane"
BULKY_WASTE = "Gabaryty i niebezpieczne"

# heading that introduces the bulky / hazardous waste dates in the PDF
BULKY_HEADING = "Odpady wielkogabarytowe"


def normalize(text: str) -> str:
    return text.translate(PL_TRANS).lower().strip()


TOWNS_BY_NORMALIZED_NAME = {normalize(name): name for name in TOWNS_PDF_MAP}


class Source:
    def __init__(self, town: str = "Baczków"):
        self._town = town

    def fetch(self) -> list[Collection]:
        town = TOWNS_BY_NORMALIZED_NAME.get(normalize(self._town))
        if town is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "town", self._town, sorted(TOWNS_PDF_MAP.keys())
            )

        pdf_file = TOWNS_PDF_MAP[town]
        url = f"http://bochnia-gmina.pl/container/{urllib.parse.quote(pdf_file)}"
        r = requests.get(url, timeout=30)
        r.raise_for_status()

        reader = pypdf.PdfReader(io.BytesIO(r.content))
        text = reader.pages[0].extract_text() or ""
        if not text.strip():
            raise ValueError(
                f"No text could be extracted from PDF for town '{self._town}'."
            )

        # 1. Year of the schedule
        year_match = re.search(r"\b(20\d{2})\b", text)
        year = int(year_match.group(1)) if year_match else datetime.date.today().year

        entries: list[Collection] = []

        # 2. Bulky / hazardous dates (e.g. "LUTY (27.02.2026)"), listed below the
        #    bulky waste heading.
        heading_pos = text.find(BULKY_HEADING)
        bulky_text = text[heading_pos:] if heading_pos != -1 else text
        for d_str, m_str, y_str in re.findall(
            r"(\d{1,2})\.(\d{1,2})\.(\d{4})", bulky_text
        ):
            try:
                date = datetime.date(int(y_str), int(m_str), int(d_str))
            except ValueError:
                continue
            entries.append(Collection(date=date, t=BULKY_WASTE, icon=Icons.BULKY))

        # 3. Monthly collection dates table
        table_match = re.search(
            r"zmieszane\s+(?:20\d{2})?\s*(.*?)\s*" + re.escape(BULKY_HEADING),
            text,
            re.DOTALL | re.IGNORECASE,
        )
        table_text = table_match.group(1) if table_match else text

        zmieszane_part = table_text.split("Worek:")[0].strip().replace("\n", " ")
        raw_tokens = [t.strip() for t in zmieszane_part.split() if t.strip()]

        month_days: list[list[int]] = []
        cur_month: list[int] = []

        for tok in raw_tokens:
            nums = [
                int(n) for n in re.findall(r"\b(\d{1,2})\b", tok) if 1 <= int(n) <= 31
            ]
            if not nums:
                continue

            cur_month.extend(nums)
            if tok.endswith(","):
                continue
            month_days.append(cur_month)
            cur_month = []
            if len(month_days) == 12:
                break

        if cur_month and len(month_days) < 12:
            month_days.append(cur_month)

        for m_idx, days in enumerate(month_days):
            month = m_idx + 1
            for d in days:
                try:
                    date = datetime.date(year, month, d)
                except ValueError:
                    continue
                entries.append(
                    Collection(date=date, t=MIXED_WASTE, icon=Icons.GENERAL_WASTE)
                )

        return entries
