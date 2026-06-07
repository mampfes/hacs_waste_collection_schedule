import io
import re
import requests
from bs4 import BeautifulSoup
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTTextLine, LTRect, LTPage
from datetime import date
import logging
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "KOSIT EAST"
DESCRIPTION = "Source for KOSIT EAST waste collection."
URL = "https://kositeast.sk"
COUNTRY = "sk"

TEST_CASES = {
    "Adidovce": {"town": "Adidovce"},
    "Andrejová": {"town": "Andrejová"},
}

PARAM_TRANSLATIONS = {
    "en": {
        "town": "Town",
    }
}

PARAM_DESCRIPTIONS = {
    "en": {
        "town": "Town name as displayed on the kositeast.sk website.",
    }
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Find your town on https://kositeast.sk/obyvatelia/harmonogram-zberu-odpadu-v-obciach/"
    " and enter it exactly as it appears in the link.",
}

_LOGGER = logging.getLogger(__name__)

ICON_MAP = {
    "Komunálny odpad": Icons.GENERAL_WASTE,
    "Plasty, VKM, Kovové obaly": Icons.RECYCLING,
    "Sklo": Icons.GLASS,
    "Papier": Icons.PAPER,
    "Jedlé oleje a tuky": Icons.ORGANIC,
    "Nebezpečný odpad": Icons.HAZARDOUS,
}

# RGB colour tuples as they appear in KOSIT EAST PDFs (rounded to 3 d.p.).
# Verified across multiple municipalities (Adidovce, Andrejová, ...).
COLOR_MAP = {
    (1.0, 1.0, 0.0):       "Plasty, VKM, Kovové obaly",
    (0.451, 0.89, 0.008):  "Sklo",
    (0.584, 0.729, 1.0):   "Papier",
    (1.0, 0.702, 0.4):     "Jedlé oleje a tuky",
    (0.741, 0.494, 0.984): "Nebezpečný odpad",
    (0.0, 0.0, 0.0):       "Komunálny odpad",
}

# Maximum Euclidean RGB distance to accept as a colour match.
# A small tolerance handles floating-point drift across PDF versions without
# misidentifying genuinely different colours (nearest neighbours in COLOR_MAP
# are all > 0.3 apart).
_COLOR_TOLERANCE = 0.05

# The schedule grid is always 6 month-columns per half-page:
#   top half    -> months 1-6  (Jan-Jun)
#   bottom half -> months 7-12 (Jul-Dec)
_N_MONTH_COLS = 6


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _nearest_color(color: tuple) -> str | None:
    """Return the nearest waste-type name for *color*, or None if too far away."""
    best_name, best_dist = None, float("inf")
    for known, name in COLOR_MAP.items():
        dist = sum((a - b) ** 2 for a, b in zip(color, known)) ** 0.5
        if dist < best_dist:
            best_dist = dist
            best_name = name
    return best_name if best_dist <= _COLOR_TOLERANCE else None


def _cluster_values(values: list[float], n: int) -> list[float]:
    """
    Cluster *values* into at most *n* groups and return sorted centre positions.

    Algorithm:
      1. Round each value to 1 d.p. and deduplicate.
      2. Greedily merge any two adjacent values that are < 5 pt apart.
      3. While more than *n* groups remain, merge the closest adjacent pair.

    This derives column boundaries entirely from the data — no hard-coded pixel
    offsets or pitch values — so it adapts if the PDF is re-generated at a
    different scale.
    """
    buckets = sorted(set(round(v, 1) for v in values))
    merged: list[float] = []
    for v in buckets:
        if merged and v - merged[-1] < 5.0:
            merged[-1] = (merged[-1] + v) / 2   # absorb into previous cluster
        else:
            merged.append(v)
    while len(merged) > n:
        gaps = [merged[i + 1] - merged[i] for i in range(len(merged) - 1)]
        idx = gaps.index(min(gaps))
        merged[idx] = (merged[idx] + merged[idx + 1]) / 2
        del merged[idx + 1]
    return merged


def _nearest_cluster_idx(value: float, centres: list[float]) -> int:
    """Return the 0-based index of the cluster centre closest to *value*."""
    return min(range(len(centres)), key=lambda i: abs(centres[i] - value))

def _extract_year(page: LTPage) -> int | None:
    """Scan *page* for a 'ROK YYYY' header and return the year, or None."""
    for element in page:
        if isinstance(element, LTTextContainer):
            for text_line in element:
                if isinstance(text_line, LTTextLine):
                    m = re.search(r"ROK\s+(\d{4})", text_line.get_text(), re.IGNORECASE)
                    if m:
                        return int(m.group(1))
    return None


# ---------------------------------------------------------------------------
# Source
# ---------------------------------------------------------------------------

class Source:
    def __init__(self, town: str):
        self._town = town

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fetch(self) -> list[Collection]:
        pdf_stream = self._download_pdf()
        pages = list(extract_pages(pdf_stream))

        if not pages:
            return []

        if len(pages) > 1:
            _LOGGER.warning(
                "PDF for '%s' has %d pages (only 1 expected). "
                "Parsing all pages — please open an issue if results look wrong.",
                self._town,
                len(pages),
            )

        # Resolve year from PDF content — required to build valid dates.
        # A hardcoded fallback would silently produce wrong dates when the PDF
        # is published for a new year, so we raise instead.
        year: int | None = None
        for page in pages:
            year = _extract_year(page)
            if year is not None:
                break

        if year is None:
            raise ValueError(
                f"Could not determine the schedule year from the PDF for town '{self._town}'. "
                "The PDF layout may have changed — please open an issue and include the PDF URL."
            )

        # Parse collections from every page.
        collections: list[Collection] = []
        for page in pages:
            collections.extend(self._parse_page(page, year))

        return collections

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _download_pdf(self) -> io.BytesIO:
        schedule_url = (
            "https://kositeast.sk/obyvatelia/harmonogram-zberu-odpadu-v-obciach/"
        )
        r = requests.get(schedule_url, timeout=30)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        pdf_link: str | None = None
        for a in soup.find_all("a", href=True):
            if (
                a.get_text(strip=True).lower() == self._town.strip().lower()
                and a["href"].endswith(".pdf")
            ):
                pdf_link = a["href"]
                break

        if pdf_link is None:
            raise SourceArgumentNotFound("town", self._town)

        r_pdf = requests.get(pdf_link, timeout=30)
        r_pdf.raise_for_status()
        return io.BytesIO(r_pdf.content)

    def _parse_page(self, page: LTPage, year: int) -> list[Collection]:
        """
        Extract Collection objects from one PDF page.

        The grid layout (column positions and the top/bottom half split) is
        inferred entirely from the positions of the coloured rectangles — no
        hard-coded pixel offsets or pitch values are used.  Rect-size thresholds
        are expressed as fractions of the page dimensions so they remain valid
        if the PDF is regenerated at a different scale.
        """
        page_h: float = page.bbox[3]
        page_w: float = page.bbox[2]

        # Rect-size thresholds as fractions of page dimensions.
        # Equivalent to roughly 8-19 pt wide and 4-13 pt tall on a standard
        # A4 PDF, but will scale correctly with any page size.
        min_w = page_w * 0.011
        max_w = page_w * 0.026
        min_h = page_h * 0.005
        max_h = page_h * 0.016

        lines: list[dict] = []
        rects: list[dict] = []

        for element in page:
            if isinstance(element, LTTextContainer):
                for text_line in element:
                    if isinstance(text_line, LTTextLine):
                        text = text_line.get_text().strip()
                        if text:
                            lines.append({"bbox": text_line.bbox, "text": text})

            elif isinstance(element, LTRect):
                if min_w < element.width < max_w and min_h < element.height < max_h:
                    color = element.non_stroking_color
                    if isinstance(color, (int, float)):
                        color = (round(color, 3),) * 3
                    elif color is not None:
                        color = tuple(round(c, 3) for c in color)
                    else:
                        color = (0.0, 0.0, 0.0)
                    rects.append({"bbox": element.bbox, "color": color})

        if not rects:
            _LOGGER.warning(
                "No schedule rectangles found on page for '%s'. "
                "The PDF layout may have changed.",
                self._town,
            )
            return []

        # --- Infer grid layout from rect positions ---

        x_ctrs = [(r["bbox"][0] + r["bbox"][2]) / 2 for r in rects]
        y_ctrs = [(r["bbox"][1] + r["bbox"][3]) / 2 for r in rects]

        x_clusters = _cluster_values(x_ctrs, n=_N_MONTH_COLS)
        y_clusters = _cluster_values(y_ctrs, n=2)  # top-half cluster / bottom-half cluster

        if len(x_clusters) != _N_MONTH_COLS:
            _LOGGER.warning(
                "Expected %d x-clusters (month columns) for '%s', found %d. "
                "Month assignments may be incorrect.",
                _N_MONTH_COLS,
                self._town,
                len(x_clusters),
            )

        # y_clusters is sorted ascending (pdfminer: y=0 at bottom of page).
        #   y_clusters[0] ~= centre of bottom-half rects (Jul-Dec)
        #   y_clusters[1] ~= centre of top-half rects    (Jan-Jun)
        y_split = (
            (y_clusters[0] + y_clusters[1]) / 2
            if len(y_clusters) >= 2
            else page_h / 2
        )

        # --- Map each rect to a date + waste type ---

        collections: list[Collection] = []

        for r_item in rects:
            rx0, ry0, rx1, ry1 = r_item["bbox"]
            rcx = (rx0 + rx1) / 2
            rcy = (ry0 + ry1) / 2

            col = _nearest_cluster_idx(rcx, x_clusters)
            is_top_half = rcy > y_split
            month = col + 1 + (0 if is_top_half else _N_MONTH_COLS)

            if not 1 <= month <= 12:
                continue

            # Find the day number from a text line that overlaps this rect
            # vertically and belongs to the same column.
            day: int | None = None
            for line in lines:
                lx0, ly0, lx1, ly1 = line["bbox"]
                if max(ry0, ly0) >= min(ry1, ly1):   # no vertical overlap
                    continue
                lcx = (lx0 + lx1) / 2
                if _nearest_cluster_idx(lcx, x_clusters) != col:  # wrong column
                    continue
                
                # UPDATED REGEX: Added uppercase slovak characters and general uppercase support
                m = re.search(
                    r"(?:^|[A-ZŽŠČŤĎŇĽĹÁÉÍÓÚÄÔa-zžščťďňľĺáéíóúäô]+\s+)(\d+)\b", line["text"]
                )
                if m:
                    day = int(m.group(1))
                    break

            if day is None:
                continue

            waste_type = _nearest_color(r_item["color"])
            if waste_type is None:
                _LOGGER.warning(
                    "Unrecognised colour %s for '%s'; skipping entry.",
                    r_item["color"],
                    self._town,
                )
                continue

            try:
                collections.append(
                    Collection(
                        date=date(year, month, day),
                        t=waste_type,
                        icon=ICON_MAP.get(waste_type),
                    )
                )
            except ValueError:
                _LOGGER.warning(
                    "Invalid date %04d-%02d-%02d for '%s'; skipping.",
                    year,
                    month,
                    day,
                    self._town,
                )

        return collections
