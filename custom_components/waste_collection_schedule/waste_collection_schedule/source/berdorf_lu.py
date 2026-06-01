import re
from datetime import date
from io import BytesIO

from bs4 import BeautifulSoup
from curl_cffi import requests
from pypdf import PdfReader
from waste_collection_schedule import Collection, Icons

TITLE = "Gemeng Bäertref"
DESCRIPTION = "Source for Berdorf commune (Gemeng Bäertref) waste collection schedule, Luxembourg."
URL = "https://www.berdorf.lu"
COUNTRY = "lu"

_DATA_URL = "https://www.berdorf.lu/service-citoyens/dechets"

TEST_CASES = {
    "Berdorf": {},
}

ICON_MAP = {
    "Hausmüll": Icons.GENERAL_WASTE,
    "Biotonne": Icons.ORGANIC,
    "Glas": Icons.GLASS,
    "Papier": Icons.PAPER,
    "PMC": Icons.PLASTIC_PACKAGING,
    "Organische und inerte Abfälle": Icons.GARDEN,
    "Sperrmüll": Icons.BULKY,
    "SuperDrecksKëscht": Icons.HAZARDOUS,
    "Altkleidersammlung": Icons.TEXTILE,
}

# German weekday abbreviations used in the PDF
_WEEKDAYS = {"MO", "DI", "MI", "DO", "FR", "SA", "SO"}
# Matches lines like "2FR H.müll / D.men.  Bio" or "25MI Sperrmüll / D.encombrants"
_LINE_RE = re.compile(r"^(\d{1,2})([A-Za-z]{2,3})\s*(.*)")
_PDF_RE = re.compile(r"offallkalenner-(\d{4})\.pdf", re.IGNORECASE)
# Full date pattern used in the info text (e.g. "17.02.2026")
_DATE_RE = re.compile(r"(\d{2})\.(\d{2})\.(\d{4})")


def _parse_waste_types(content: str) -> list[str]:
    types: list[str] = []
    if "H.müll" in content or "D.men." in content:
        types.append("Hausmüll")
    if re.search(r"\bBio\b", content):
        types.append("Biotonne")
    if "Glas" in content or "verre" in content:
        types.append("Glas")
    if re.search(r"[Pp]apier", content):
        types.append("Papier")
    if "PMC" in content:
        types.append("PMC")
    if "Org.&inert" in content or "D.org.&inertes" in content:
        types.append("Organische und inerte Abfälle")
    if "Sperrmüll" in content or "D.encombrants" in content:
        types.append("Sperrmüll")
    if "SuperDrecksKëscht" in content or re.search(r"\bSDK\b", content):
        types.append("SuperDrecksKëscht")
    if "Kleiders" in content:
        types.append("Altkleidersammlung")
    return types


def _extract_sdk_dates(full_text: str) -> list[date]:
    """Extract SuperDrecksKëscht collection dates from the info-text section.

    The PDF calendar grid can miss entries when the SDK colour block overlaps
    a regular collection cell (e.g. Aug 18 with Glas/Papier+SDK). The info
    section always lists all four SDK dates explicitly.
    """
    m = re.search(
        r"SuperDrecksK[eë]scht.*?Termine:?\s*([\d.,\s]+)",
        full_text,
        re.DOTALL,
    )
    if not m:
        return []
    dates: list[date] = []
    for dm in _DATE_RE.finditer(m.group(1)):
        try:
            dates.append(date(int(dm.group(3)), int(dm.group(2)), int(dm.group(1))))
        except ValueError:
            pass
    return dates


def _parse_pdf_page(page_text: str, start_month: int, year: int) -> list[Collection]:
    """Parse one page of the Offallkalenner PDF.

    The PDF is a 2-page document: page 1 covers Jan–Jun, page 2 covers Jul–Dec.
    Months transition when the day number resets from a higher value back to 1.
    """
    entries: list[Collection] = []
    month = start_month
    prev_day = 0

    for line in page_text.split("\n"):
        m = _LINE_RE.match(line.strip())
        if not m:
            continue
        day = int(m.group(1))
        wd = m.group(2).upper()
        if wd not in _WEEKDAYS:
            continue
        content = m.group(3).strip()
        if day < prev_day:
            month += 1
        prev_day = day

        for wt in _parse_waste_types(content):
            try:
                entries.append(
                    Collection(date=date(year, month, day), t=wt, icon=ICON_MAP.get(wt))
                )
            except ValueError:
                pass

    return entries


class Source:
    def __init__(self):
        pass

    def fetch(self) -> list[Collection]:
        session = requests.Session(impersonate="chrome")

        response = session.get(_DATA_URL, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        current_year = date.today().year
        best_url: str | None = None
        best_year = 0

        for a_tag in soup.find_all("a", href=True):
            href = str(a_tag["href"])
            m = _PDF_RE.search(href)
            if m:
                pdf_year = int(m.group(1))
                if pdf_year >= current_year and pdf_year > best_year:
                    best_year = pdf_year
                    best_url = href

        if not best_url:
            return []

        if best_url.startswith("/"):
            best_url = "https://www.berdorf.lu" + best_url

        pdf_response = session.get(best_url, timeout=30)
        pdf_response.raise_for_status()

        reader = PdfReader(BytesIO(pdf_response.content))
        page_texts = [page.extract_text() for page in reader.pages]
        full_text = "\n".join(page_texts)

        entries: list[Collection] = []
        for page_num, page_text in enumerate(page_texts):
            # Page 1 (index 0) covers Jan–Jun, page 2 (index 1) covers Jul–Dec
            start_month = 7 if page_num == 1 else 1
            entries.extend(_parse_pdf_page(page_text, start_month, best_year))

        # Supplement from the info-text section: some SDK entries are missed by
        # the grid parser when the coloured SDK block overlaps another cell.
        sdk_icon = ICON_MAP.get("SuperDrecksKëscht")
        seen_sdk: set[date] = {e.date for e in entries if e.type == "SuperDrecksKëscht"}
        for d in _extract_sdk_dates(full_text):
            if d not in seen_sdk:
                entries.append(Collection(date=d, t="SuperDrecksKëscht", icon=sdk_icon))

        return entries
