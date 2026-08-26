import datetime
import io
import re
import urllib.parse
import urllib.request

import pypdf
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]

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
    "baczkow": "Baczkow.pdf",
    "bessow": "Bessow.pdf",
    "bogucice": "Bogucice.pdf",
    "brzeznica": "Brzeznica.pdf",
    "buczyna": "Buczyna.pdf",
    "cerekiew": "Cerekiew.pdf",
    "chelm": "Chelm.pdf",
    "cikowice": "Cikowice.pdf",
    "damienice": "Damienice.pdf",
    "dabrowica": "Dabrowica.pdf",
    "gawlow": "Gawlow.pdf",
    "gierczyce": "Gierczyce.pdf",
    "gorzkow": "Gorzkow.pdf",
    "grabina": "Grabina.pdf",
    "krzyzanowice": "Krzyzanowice.pdf",
    "lapczyca": "Lapczyca.pdf",
    "majkowice": "Majkowice.pdf",
    "moszczenica": "Moszczenica.pdf",
    "nieprzesnia": "Nieprzesnia.pdf",
    "nieszkowice male": "Nieszkowice male.pdf",
    "nieszkowice wielkie": "Nieszkowice wielkie.pdf",
    "ostrow szlachecki": "Ostrow szlachecki.pdf",
    "pogwizdow": "Pogwizdow.pdf",
    "proszowki": "Proszowki.pdf",
    "siedlec": "Siedlec.pdf",
    "slomka": "Slomka.pdf",
    "stanislawice": "Stanislawice.pdf",
    "stradomka": "Stradomka.pdf",
    "wola nieszkowska": "Wola nieszkowska.pdf",
    "zatoka": "Zatoka.pdf",
    "zawada": "Zawada.pdf",
}


def normalize(text: str) -> str:
    return text.translate(PL_TRANS).lower().strip()


class Source:
    def __init__(self, town: str = "Baczków"):
        self._town = town

    def fetch(self) -> list[Collection]:
        from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

        norm_town = normalize(self._town)
        pdf_file = TOWNS_PDF_MAP.get(norm_town)
        if not pdf_file:
            raise SourceArgumentNotFoundWithSuggestions("town", self._town, sorted(TOWNS_PDF_MAP))
        url = f"http://bochnia-gmina.pl/container/{urllib.parse.quote(pdf_file)}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            pdf_bytes = resp.read()

        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        text = reader.pages[0].extract_text()

        # 1. Year
        year_match = re.search(r"\b(202\d)\b", text)
        year = int(year_match.group(1)) if year_match else datetime.date.today().year

        entries: list[Collection] = []

        # 2. Bulky / hazardous dates (e.g. (27.02.2026))
        for d_str, m_str, y_str in re.findall(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", text):
            entries.append(
                Collection(
                    date=datetime.date(int(y_str), int(m_str), int(d_str)),
                    t="Gabaryty i niebezpieczne",
                    icon=Icons.BULKY,
                )
            )

        # 3. Monthly collection dates table
        table_match = re.search(
            r"zmieszane\s+(?:202\d)?\s*(.*?)\s*Odpady wielkogabarytowe",
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
                    entries.append(
                        Collection(
                            date=datetime.date(year, month, d),
                            t="Odpady zmieszane i segregowane",
                            icon=Icons.GENERAL_WASTE,
                        )
                    )
                except ValueError:
                    pass

        return entries
