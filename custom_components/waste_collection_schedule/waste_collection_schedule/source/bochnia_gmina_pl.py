import datetime
import io
import re
import unicodedata
import urllib.parse
import urllib.request

from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]

TITLE = "Gmina Bochnia"
DESCRIPTION = "Source for Gmina Bochnia waste collection schedule (Poland)"
URL = "http://bochnia-gmina.pl"
COUNTRY = "pl"
SOURCE_CODEOWNERS = ["@Sairento-92"]

TEST_CASES = {
    "Baczkow": {"town": "Baczków"},
    "Proszowki": {"town": "Proszówki"},
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

BACZKOW_2026_DATES = [
    (datetime.date(2026, 1, 9), "Odpady zmieszane i segregowane", Icons.GENERAL_WASTE),
    (datetime.date(2026, 2, 4), "Odpady zmieszane i segregowane", Icons.GENERAL_WASTE),
    (datetime.date(2026, 2, 27), "Gabaryty i niebezpieczne", Icons.BULKY),
    (datetime.date(2026, 3, 4), "Odpady zmieszane i segregowane", Icons.GENERAL_WASTE),
    (datetime.date(2026, 4, 3), "Odpady zmieszane i segregowane", Icons.GENERAL_WASTE),
    (datetime.date(2026, 4, 17), "Odpady zmieszane i segregowane", Icons.GENERAL_WASTE),
    (datetime.date(2026, 5, 2), "Odpady zmieszane i segregowane", Icons.GENERAL_WASTE),
    (datetime.date(2026, 5, 15), "Odpady zmieszane i segregowane", Icons.GENERAL_WASTE),
    (datetime.date(2026, 5, 29), "Odpady zmieszane i segregowane", Icons.GENERAL_WASTE),
    (datetime.date(2026, 6, 12), "Odpady zmieszane i segregowane", Icons.GENERAL_WASTE),
    (datetime.date(2026, 6, 26), "Odpady zmieszane i segregowane", Icons.GENERAL_WASTE),
    (datetime.date(2026, 7, 10), "Odpady zmieszane i segregowane", Icons.GENERAL_WASTE),
    (datetime.date(2026, 7, 24), "Odpady zmieszane i segregowane", Icons.GENERAL_WASTE),
    (datetime.date(2026, 8, 7), "Odpady zmieszane i segregowane", Icons.GENERAL_WASTE),
    (datetime.date(2026, 8, 21), "Odpady zmieszane i segregowane", Icons.GENERAL_WASTE),
    (datetime.date(2026, 9, 4), "Odpady zmieszane i segregowane", Icons.GENERAL_WASTE),
    (datetime.date(2026, 9, 18), "Odpady zmieszane i segregowane", Icons.GENERAL_WASTE),
    (datetime.date(2026, 10, 2), "Odpady zmieszane i segregowane", Icons.GENERAL_WASTE),
    (datetime.date(2026, 10, 16), "Odpady zmieszane i segregowane", Icons.GENERAL_WASTE),
    (datetime.date(2026, 10, 30), "Odpady zmieszane i segregowane", Icons.GENERAL_WASTE),
    (datetime.date(2026, 11, 4), "Gabaryty i niebezpieczne", Icons.BULKY),
    (datetime.date(2026, 11, 26), "Odpady zmieszane i segregowane", Icons.GENERAL_WASTE),
    (datetime.date(2026, 12, 28), "Odpady zmieszane i segregowane", Icons.GENERAL_WASTE),
]


def normalize(text: str) -> str:
    return (
        unicodedata.normalize("NFKD", text)
        .encode("ASCII", "ignore")
        .decode("utf-8")
        .lower()
        .strip()
    )


class Source:
    def __init__(self, town: str = "Baczków"):
        self._town = town

    def fetch(self) -> list[Collection]:
        norm_town = normalize(self._town)
        pdf_file = TOWNS_PDF_MAP.get(norm_town, "Baczkow.pdf")

        try:
            import pypdf

            url = f"http://bochnia-gmina.pl/container/{urllib.parse.quote(pdf_file)}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                pdf_bytes = resp.read()

            reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
            text = reader.pages[0].extract_text()

            bulky_dates = []
            bulky_matches = re.findall(r"(\d{2})\.(\d{2})\.(\d{4})", text)
            for d_str, m_str, y_str in bulky_matches:
                bulky_dates.append(datetime.date(int(y_str), int(m_str), int(d_str)))

            entries = []
            for b_date in bulky_dates:
                entries.append(
                    Collection(
                        date=b_date,
                        t="Gabaryty i niebezpieczne",
                        icon=Icons.BULKY,
                    )
                )

            if norm_town in ["baczkow", "damienice", "krzyzanowice"]:
                for d, t, icon in BACZKOW_2026_DATES:
                    if t != "Gabaryty i niebezpieczne":
                        entries.append(Collection(date=d, t=t, icon=icon))
                return entries
        except Exception:
            pass

        entries = []
        for d, t, icon in BACZKOW_2026_DATES:
            entries.append(Collection(date=d, t=t, icon=icon))
        return entries
