from dataclasses import dataclass
import datetime, requests, logging, re
from typing import Optional
import unicodedata
from io import BytesIO
from bs4 import BeautifulSoup

from waste_collection_schedule.exceptions import SourceArgAmbiguousWithSuggestions, SourceArgumentNotFound
from waste_collection_schedule.collection import Collection
from waste_collection_schedule.icons import Icons
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextLine, LTTextContainer, LAParams


###############################################################################
##########           Integration's configuration constants           ##########
###############################################################################

TITLE = "S.E.S.A."
DESCRIPTION = "Source script for sesaeste.it"
SOURCE_CODEOWNERS = ['@AlexSartori']
BASE_URL = "https://sesaeste.it"
URL = BASE_URL
API_URL = BASE_URL + "/proc_cerca_comune/"

TEST_CASES = {
    "Legnaro": {"user_municipality": "Legnaro"},
    "Solesino": {"user_municipality": "Solesino"},
    "Polverara": {"user_municipality": "Polverara"}
}

ICON_MAP = {
    "PLASTICA E LATTINE": Icons.PLASTIC_PACKAGING, # TODO: add an mdi icon for plastic+metal? Probably useful for other sources too.
    "UMIDO": Icons.BIO_KITCHEN,
    "SECCO": Icons.GENERAL_WASTE,
    "CARTA": Icons.PAPER,
    "VETRO": Icons.GLASS,
    "VERDE": Icons.GARDEN,
}

PARAM_DESCRIPTIONS = {
    "en": {
        "user_municipality": "Municipality",
    },
    "it": {
        "user_municipality": "Comune",
    },
}


###############################################################################
##########           Parsing configuration and parameters            ##########
###############################################################################

CATEGORIES = ["PLASTICA E LATTINE", "UMIDO", "SECCO", "CARTA", "VETRO", "VERDE"]
CATEGORY_RE = "|".join(c.replace(" ", r"\s+") for c in CATEGORIES)
SHIFT_RE = re.compile(
    rf"RACCOLTA\s+((?:{CATEGORY_RE})(?:\s+(?:{CATEGORY_RE}))*)"
    rf"\s+(ANTICIPATA|POSTICIPATA)\s+AL\s+(\d{{1,2}}/\d{{1,2}})"
)

# The text flow in these PDFs is extremely garbled and messy. Pypdf or pdfplumber will
# cluster characters one-by-one but this will lead to overlapped words impossible to parse.
# Using pdfminer's higher-level API (e.g., LTTextLine) will preserve the original text stream,
# but we need coordinate-based heuristics to disciminate the type of text being read.

# NOTE: it is possible that, if in future years parsing will break, one only needs to tune these params.

DAY_X0_MIN, DAY_X0_MAX = 25.0, 66.0
CATEGORY_X0_MAX = 300.0
TITLE_TOP_MAX = 100.0
DAY_MARKER_RE = re.compile(r"^[a-dA-D]?\s*(\d{1,2})$")
ROW_MARGIN = 6.0 # Shift notices can be rendered some pts above the day row. We need some margin.

MONTHS_IT = {
    "gennaio": 1, "febbraio": 2, "marzo": 3, "aprile": 4,
    "maggio": 5, "giugno": 6, "luglio": 7, "agosto": 8,
    "settembre": 9, "ottobre": 10, "novembre": 11, "dicembre": 12,
}

logger = logging.getLogger(__name__)


###############################################################################
##########                       PDF download                        ##########
###############################################################################

def fetch_municipality_id(municipality_name) -> str:
    html_cercacomune = BeautifulSoup(requests.get(API_URL).text)
    select = html_cercacomune.find(id="RifComune")
    candidates: list[tuple[str, str]] = []

    if select is None:
        raise ValueError(f"The S.E.S.A. landing webpage has an unexpected format and the list of municipalities could not be found.")

    for opt in select.find_all('option'):
        if opt.string.lower() == municipality_name.lower():
            candidates = [(opt.get('value'), opt.string)]
            break
        if municipality_name.lower() in opt.string.lower():
            candidates.append((opt.get('value'), opt.string))
    
    if len(candidates) == 0:
        raise SourceArgumentNotFound("user_municipality", municipality_name)
    if len(candidates) > 1:
        raise SourceArgAmbiguousWithSuggestions("user_municipality", municipality_name, [m for _, m in candidates])
    
    return candidates[0][0]


def fetch_pdf_calendar(municipality_id):
    mun_id = fetch_municipality_id(municipality_id)

    html_calendar = BeautifulSoup(
        requests.post(API_URL, {
            'RifComune': mun_id,
            'showheader': False
        }).text
    )
    
    a = html_calendar.find('a', title='Scarica il calendario')
    if a is None:
        raise ValueError(f"The S.E.S.A. municipality webpage has an unexpected format and the PDF schedule link could not be found.")
    
    pdf_url = BASE_URL + a.get('href')
    req = requests.get(pdf_url, stream=True)
    req.raise_for_status()
    pdf_data = BytesIO(req.content)

    return pdf_data


###############################################################################
##########                      Parsing logic                        ##########
###############################################################################

@dataclass
class ScheduleShift:
    category: str
    direction: str          # "anticipata" | "posticipata"
    shifted_to: str         # gg/mm

def _strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))

def parse_pdf(file_data: BytesIO) -> list[Collection]:
    results: list[Collection] = []
    current_month_year: Optional[tuple[int, int]] = None
    pages_since_title = 99

    for page in extract_pages(file_data, laparams=LAParams()):
        lines = _page_lines(page)
        month_year = _detect_month_year(lines)

        if month_year is not None:
            current_month_year = month_year
            pages_since_title = 0
        else:
            pages_since_title += 1

        # Each month uses 2 pages (days 1-16 and 17-31). After the second page since the
        # title we're reading garbage (lol) from glossaries and such.
        if current_month_year is None or pages_since_title >= 2:
            continue

        month, year = current_month_year
        badge_lines = [l for l in lines if DAY_X0_MAX < l["x0"] < CATEGORY_X0_MAX]
        y_cutoff = _get_footer_y0(badge_lines)
        day_markers = _find_day_markers(lines) # {day, top}

        for i, marker in enumerate(day_markers):
            top_start = marker["top"] - ROW_MARGIN
            top_end = (
                day_markers[i + 1]["top"] - ROW_MARGIN
                if i + 1 < len(day_markers)
                else y_cutoff
            )
            block = [l for l in badge_lines if top_start <= l["top"] < top_end]

            try:
                d = datetime.date(year, month, marker["day"])
            except ValueError:
                continue

            categories, shifts = _parse_day_block(block)
            results.append(
                Collection(
                    date=d,
                    t=categories[0], # TODO create more objects for more cats in the same day
                    icon = ICON_MAP.get(categories[0])
                )
            )

    results.sort(key=lambda e: e.date)
    return results


def _page_lines(page) -> list[dict]:
    """Extract LTTextLines from a page with their coordinated"""
    lines: list[dict] = []

    def walk(obj):
        if isinstance(obj, LTTextLine):
            if text := obj.get_text().strip():
                lines.append({"text": text, "x0": obj.x0, "top": page.height - obj.y1})
        elif isinstance(obj, LTTextContainer):
            for child in obj:
                walk(child)

    for obj in page:
        walk(obj)
        
    return sorted(lines, key=lambda l: (l["top"], l["x0"]))

def _detect_month_year(lines: list[dict]) -> Optional[tuple[int, int]]:
    """Look for 'MESE AAAA' in the tiel section."""
    for l in lines:
        if l["top"] >= TITLE_TOP_MAX:
            continue
        candidate = _strip_accents(l["text"]).lower().replace("0", "o") # Yep...
        for name, num in MONTHS_IT.items():
            if name in candidate:
                if y := re.search(r"(20\d{2})", l["text"]):
                    return num, int(y.group(1))
    return None

def _get_footer_y0(badge_lines: list[dict]) -> float:
    tops = [l["top"] for l in badge_lines if l["text"].upper().startswith("ECOCENTRO")]
    return (min(tops) - 2.0) if tops else float("inf")

def _find_day_markers(lines: list[dict]) -> list[dict]:
    '''Extract day numbers with y coordinate and return them sorted from top to bottom.'''
    markers = []
    for l in lines:
        if not (DAY_X0_MIN <= l["x0"] <= DAY_X0_MAX):
            continue

        m = DAY_MARKER_RE.match(l["text"])
        if m and 1 <= int(m.group(1)) <= 31:
            markers.append({"day": int(m.group(1)), "top": l["top"]})

    return sorted(markers, key=lambda l: l["top"])

def _parse_day_block(block: list[dict]) -> tuple[list[str], list[ScheduleShift]]:
    """Analizza le righe-badge di un giorno: riquadri "RACCOLTA ... AL
    gg/mm" (badge + riga di completamento allineata a sinistra) e badge
    semplici rimanenti, segnalando come `warnings` eventuali sovrapposizioni
    di testo reali nel PDF sorgente (stessa posizione, testi diversi)."""
    block_sorted = sorted(block, key=lambda l: l["top"])
    shifts: list[ScheduleShift] = []
    consumed: set[int] = set()

    # Look for a 2-line shift notice ("raccolta X [\n] anticipata/posticipata al Y")
    for j, l in enumerate(block_sorted):
        if not l["text"].upper().startswith("RACCOLTA"):
            continue
        nxt = next(
            (l2 for l2 in block_sorted[j + 1:] if abs(l2["x0"] - l["x0"]) < 3),
            None,
        )
        combined = (l["text"] + (" " + nxt["text"] if nxt else "")).upper()
        if m := SHIFT_RE.search(combined):
            cats_txt, direction, shifted_to = m.groups()
            for cat in re.findall(CATEGORY_RE, cats_txt):
                shifts.append(
                    ScheduleShift(re.sub(r"\s+", " ", cat).upper(), direction.lower(), shifted_to)
                )
        consumed.add(id(l))
        if nxt:
            consumed.add(id(nxt))

    remaining = [l for l in block_sorted if id(l) not in consumed]
    cat_re = re.compile(rf"^(?:{CATEGORY_RE})$")
    category_badges = [l for l in remaining if cat_re.match(l["text"].upper())]

    # Due badge disegnati esattamente sovrapposti restano righe separate ma
    # nella STESSA posizione: si raggruppano per prossimità (non un secco
    # arrotondamento) per riconoscerli come un'unica ambiguità da segnalare.
    position_clusters: list[dict] = [] # {top, x0, texts}
    for l in category_badges:
        cluster = next(
            (c for c in position_clusters if abs(l["top"] - c["top"]) <= 2 and abs(l["x0"] - c["x0"]) <= 5),
            None,
        )
        if cluster is None:
            position_clusters.append({"top": l["top"], "x0": l["x0"], "texts": [l["text"].upper()]})
        else:
            cluster["texts"].append(l["text"].upper())

    categories: list[str] = []
    for cluster in position_clusters:
        texts = cluster["texts"]
        if len(set(texts)) == 1:
            categories.append(texts[0])
        else:
            logger.warning(f"Category badges appear to be overlaping: {texts}")

    return list(dict.fromkeys(categories)), shifts


###############################################################################
##########                      Integration API                      ##########
###############################################################################

class Source:
    def __init__(self, user_municipality: str):
        self.user_municipality = user_municipality

    def fetch(self) -> list[Collection]:
        pdf_data = fetch_pdf_calendar(self.user_municipality)
        logger.info(f"Downloaded PDF calendar")

        entries = parse_pdf(pdf_data)
        logger.info(f"Parsed PDF calendar")

        return entries