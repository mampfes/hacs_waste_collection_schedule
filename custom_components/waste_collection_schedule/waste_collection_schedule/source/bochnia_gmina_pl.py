import datetime
import re
import urllib.parse
from collections.abc import Iterator
from typing import ClassVar, final

from waste_collection_schedule import config_params, lookups
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.parsers import PdfTextParser
from waste_collection_schedule.regions import region
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import ICSTransformer

MIXED_WASTE = "Odpady zmieszane i segregowane"
BULKY_WASTE = "Gabaryty i niebezpieczne"

# Heading that introduces the bulky / hazardous waste dates in the PDF.
_BULKY_HEADING = "Odpady wielkogabarytowe"

_UPLOADS_URL = "https://bochnia-gmina.pl/wp-content/uploads/"

# Several villages share one PDF; each village is listed under the file the
# municipality publishes it in.
_TOWNS_PDF_MAP = {
    "Baczków": "Baczkow.pdf",
    "Bessów": "Bessow.pdf",
    "Bogucice": "Bessow.pdf",
    "Brzeźnica": "Brzeznica.pdf",
    "Buczyna": "Buczyna.pdf",
    "Cerekiew": "Cerekiew.pdf",
    "Chełm": "Chelm.pdf",
    "Cikowice": "Cikowice.pdf",
    "Damienice": "Damienice.pdf",
    "Dąbrowica": "Dabrowica.pdf",
    "Gawłów": "Slomka.pdf",
    "Gierczyce": "Gierczyce.pdf",
    "Gorzków": "Gorzkow.pdf",
    "Grabina": "Grabina.pdf",
    "Krzyżanowice": "Krzyzanowice.pdf",
    "Łapczyca": "Lapczyca.pdf",
    "Majkowice": "Majkowice.pdf",
    "Moszczenica": "Moszczenica.pdf",
    "Nieprześnia": "Nieprzesnia.pdf",
    "Nieszkowice Małe": "Chelm.pdf",
    "Nieszkowice Wielkie": "Pogwizdow.pdf",
    "Ostrów Szlachecki": "Slomka.pdf",
    "Pogwizdów": "Pogwizdow.pdf",
    "Proszówki": "Proszowki.pdf",
    "Siedlec": "Siedlec.pdf",
    "Słomka": "Slomka.pdf",
    "Stanisławice": "Stanislawice.pdf",
    "Stradomka": "Stradomka.pdf",
    "Wola Nieszkowska": "Pogwizdow.pdf",
    "Zatoka": "Zatoka.pdf",
    "Zawada": "Zawada.pdf",
}

_PL_TRANS = str.maketrans("ąćęłńóśźżĄĆĘŁŃÓŚŹŻ", "acelnoszzACELNOSZZ")


def _fold(value: object) -> str:
    """Match a village regardless of case, whitespace and Polish diacritics."""
    return lookups.normalize_text(str(value).translate(_PL_TRANS))


def _pdf_url(town: str, **_) -> str:
    pdf_file = lookups.resolve(_TOWNS_PDF_MAP, town, argument="town", normalize=_fold)
    return _UPLOADS_URL + urllib.parse.quote(pdf_file)


def _month_days(table: str) -> list[list[int]]:
    """Day numbers per month from the "zmieszane" row.

    A month's days wrap over several extracted lines; a trailing comma means the
    month continues with the next token, anything else closes it.
    """
    row = table.split("Worek:")[0].replace("\n", " ")
    months: list[list[int]] = []
    current: list[int] = []
    for token in row.split():
        days = [
            int(n) for n in re.findall(r"\b(\d{1,2})\b", token) if 1 <= int(n) <= 31
        ]
        if not days:
            continue
        current.extend(days)
        if token.endswith(","):
            continue
        months.append(current)
        current = []
        if len(months) == 12:
            break
    if current and len(months) < 12:
        months.append(current)
    return months


def _rows(text: str, source: object = None) -> Iterator[tuple[datetime.date, str]]:
    year_match = re.search(r"\b(20\d{2})\b", text)
    year = int(year_match.group(1)) if year_match else datetime.date.today().year

    # Bulky / hazardous dates ("LUTY (27.02.2026)") follow the bulky heading.
    heading = text.find(_BULKY_HEADING)
    bulky_text = text[heading:] if heading != -1 else text
    for day, month, bulky_year in re.findall(
        r"(\d{1,2})\.(\d{1,2})\.(\d{4})", bulky_text
    ):
        try:
            yield datetime.date(int(bulky_year), int(month), int(day)), BULKY_WASTE
        except ValueError:
            continue

    # Monthly collection table: one run of day numbers per month.
    table = re.search(
        r"zmieszane\s+(?:20\d{2})?\s*(.*?)\s*" + re.escape(_BULKY_HEADING),
        text,
        re.DOTALL | re.IGNORECASE,
    )
    for month, days in enumerate(_month_days(table.group(1) if table else text), 1):
        for day in days:
            try:
                yield datetime.date(year, month, day), MIXED_WASTE
            except ValueError:
                continue


@final
class Source(BaseSource):
    TITLE = "Gmina Bochnia"
    DESCRIPTION = "Source for Gmina Bochnia waste collection schedule (Poland)"
    URL = "https://bochnia-gmina.pl"
    COUNTRY = "pl"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@Sairento-92"]
    RAISE_ON_EMPTY = True

    REGIONS = tuple(region(town, town=town) for town in _TOWNS_PDF_MAP)

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.BULKY_WASTE]

    TEST_CASES: ClassVar[dict] = {
        "Baczkow": {"town": "Baczków"},
        "Proszowki": {"town": "Proszówki"},
        "Lapczyca": {"town": "Łapczyca"},
    }

    PARAMS = (config_params.city(field="town"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter the name of the town in Gmina Bochnia "
            "(e.g. Baczków, Damienice, Proszówki, Łapczyca, etc.)."
        ),
    }

    retrieve = HttpGetRetriever(url=_pdf_url)
    parse = PdfTextParser(min_chars=100)
    preprocess = staticmethod(_rows)
    transform = ICSTransformer(
        type_value_map={
            MIXED_WASTE: wt.GENERAL_WASTE,
            BULKY_WASTE: wt.BULKY_WASTE,
        }
    )
