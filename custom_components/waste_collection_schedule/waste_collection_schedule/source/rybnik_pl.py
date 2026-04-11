import logging
import re
import unicodedata
from datetime import date, datetime
from io import BytesIO

import requests
from pypdf import PdfReader
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequiredWithSuggestions,
)

_LOGGER = logging.getLogger(__name__)

TITLE = "Rybnik"
DESCRIPTION = (
    "Source for Rybnik (Poland) municipal waste collection schedules "
    "provided by EKO Sp. z o.o."
)
URL = "https://www.rybnik.eu"

_BASE_URL = (
    "https://www.rybnik.eu/fileadmin/user_files/mieszkaj/samorzad/"
    "odpady_komunalne/Harmonogramy_{year}/"
)

# Mapping from friendly district name to URL slug.
# Slugs use double-underscores for multi-part names and ASCII transliteration.
DISTRICT_MAP: dict[str, str] = {
    "Boguszowice Stare": "Boguszowice_Stare",
    "Chwalowice / Boguszowice Os. / Klokocin": "Chwalowice__Boguszowice_Os.__Klokocin",
    "Gotartowice": "Gotartowice",
    "Grabownia / Golejow / Ochojec": "Grabownia__Golejow__Ochojec",
    "Ligota": "Ligota",
    "Maroko-Nowiny": "Maroko-Nowiny",
    "Niedobczyce": "Niedobczyce",
    "Niewiadom": "Niewiadom",
    "Orzepowice / Stodoly / Chwalecice": "Orzepowice__Stodoly__Chwalecice",
    "Paruszowiec / Kamien": "Paruszowiec__Kamien",
    "Polnoc": "Polnoc",
    "Radziejow / Popielow": "Radziejow__Popielow",
    "Smolna / Zamyslow / Meksyk": "Smolna__Zamyslow__Meksyk",
    "Srodmiescie / Wielopole / Kuznia": "Srodmiescie__Wielopole__Kuznia",
    "Zebrzydowice": "Zebrzydowice",
}

PROPERTY_TYPES = ("residential", "commercial")

# Maps PDF waste-type token → (friendly English name, MDI icon)
WASTE_TYPE_MAP: dict[str, tuple[str, str]] = {
    "ZMIESZANE": ("Mixed waste", "mdi:trash-can"),
    "SEGREGOWANE": ("Recyclables", "mdi:recycle"),
    "BIODEGRADOWALNE": ("Bio / organic", "mdi:leaf"),
}

TEST_CASES = {
    "Paruszowiec-Piaski residential": {
        "district": "Paruszowiec / Kamien",
        "sub_district": "Paruszowiec-Piaski",
        "property_type": "residential",
    },
    "Boguszowice Stare residential (all sub-districts)": {
        "district": "Boguszowice Stare",
        "property_type": "residential",
    },
    "Niedobczyce commercial": {
        "district": "Niedobczyce",
        "property_type": "commercial",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Download the current schedule PDF for your district from the "
        "Rybnik city website: https://www.rybnik.eu/dla-mieszkancow/odpady-komunalne/ "
        "(navigate to the current year's schedules). "
        "Open page 2 of the PDF and note your Rejon (sub-district zone) name "
        "from the leftmost column of the schedule table."
    ),
}

PARAM_DESCRIPTIONS = {
    "en": {
        "district": (
            "The district / area group name (determines which PDF is downloaded). "
            f"Must be one of: {', '.join(DISTRICT_MAP.keys())}."
        ),
        "sub_district": (
            "The Rejon (zone) name as shown in the leftmost column of the PDF schedule table "
            "(e.g. 'Paruszowiec-Piaski', 'Kamień 1', 'Kamień 2'). "
            "Leave blank to return all zones in the district."
        ),
        "property_type": (
            "Type of property. One of: 'residential' (zamieszkałe, default), "
            "'commercial' (firmy/niezamieszkałe)."
        ),
    },
}

# Matches a waste-type row: keyword followed by exactly 12 month columns of digits/semicolons.
_ROW_RE = re.compile(r"(ZMIESZANE|SEGREGOWANE|BIODEGRADOWALNE)" r"((?:\s+[\d;]+){12})")

# Matches a street-name initial like "A.Szewczyka" or "H.Groborza".
_STREET_INITIAL_RE = re.compile(r"^[A-ZĄĆĘŁŃÓŚŹŻ]\.[A-Za-ząćęłńóśźż]")


def _normalize_rejon(name: str) -> str:
    """Normalize a Rejon name for fuzzy comparison.

    Strips whitespace, hyphens, and underscores, then casefolds.
    Handles pypdf occasionally omitting hyphens from merged cells
    (e.g. 'ParuszowiecPiaski' matches 'Paruszowiec-Piaski').
    """
    normalized = unicodedata.normalize("NFC", name)
    return re.sub(r"[\s\-_]+", "", normalized).casefold()


def _extract_rejon_order(reader: PdfReader) -> list[str]:
    """Extract the ordered list of Rejon names from the cover page.

    The cover page (first page containing 'Rejony') has a table like:

        Rejony         Nazwy ulic
        Paruszowiec-Piaski
        H.Groborza, Konopnickiej, ...
        Kamień 1   A.Szewczyka, Gminna, ...
        Kamień 2   A.Bożka, Falista, ...

    Rejon names appear either on their own line or at the start of a line
    before the first street initial (X.YYY pattern).
    The order here matches the top-to-bottom visual order of data blocks on page 2.
    """
    for page in reader.pages:
        text = page.extract_text() or ""
        if "Rejony" not in text:
            continue

        names: list[str] = []
        in_table = False

        for line in text.splitlines():
            line = line.strip()

            # Detect the start of the Rejon table
            if "Rejony" in line and "Nazwy" in line:
                in_table = True
                continue

            if not in_table or not line:
                continue

            # Stop at EKO footer
            if any(
                marker in line
                for marker in ("EKO Sp.", "ul. Kościuszki", "Internet:", "Facebook:")
            ):
                break

            # Skip street-initial lines (e.g. "H.Groborza, Konopnickiej,...")
            if _STREET_INITIAL_RE.match(line):
                continue

            # Skip street continuation lines (contain Polish range markers)
            if re.search(r"\bdo\s+\d+\b|\bnp\.\b|\bparz\.\b|\bZakątek\b", line):
                continue

            # Extract candidate name: everything before the first street initial
            parts = line.split()
            name_parts: list[str] = []
            for part in parts:
                if _STREET_INITIAL_RE.match(part):
                    break
                name_parts.append(part)

            candidate = " ".join(name_parts).rstrip(",").strip()

            if candidate and len(candidate) < 50:
                names.append(candidate)

        if names:
            _LOGGER.debug("Extracted Rejon order from cover page: %s", names)
            return names

    _LOGGER.warning("Could not extract Rejon order from cover page.")
    return []


def _find_schedule_text(reader: PdfReader) -> str:
    """Return text from the first page that contains 'ZMIESZANE'."""
    for page in reader.pages:
        text = page.extract_text() or ""
        if "ZMIESZANE" in text:
            return text
    raise ValueError(
        "Could not find the schedule table in the PDF "
        "(no page contains 'ZMIESZANE'). The PDF format may have changed."
    )


def _extract_blocks(text: str) -> list[list[tuple[str, list[str]]]]:
    """Extract data blocks (groups of 3 waste-type rows) from the schedule page text."""
    all_rows: list[tuple[str, list[str]]] = []

    for m in _ROW_RE.finditer(text):
        waste_key = m.group(1)
        month_tokens = m.group(2).split()
        if len(month_tokens) != 12:
            _LOGGER.warning(
                "Expected 12 month columns for %s, got %d — skipping row.",
                waste_key,
                len(month_tokens),
            )
            continue
        all_rows.append((waste_key, month_tokens))

    if not all_rows:
        raise ValueError(
            "No waste-type rows found in PDF text. The PDF format may have changed."
        )

    blocks: list[list[tuple[str, list[str]]]] = []
    i = 0
    while i < len(all_rows):
        if (
            i + 2 < len(all_rows)
            and all_rows[i][0] == "ZMIESZANE"
            and all_rows[i + 1][0] == "SEGREGOWANE"
            and all_rows[i + 2][0] == "BIODEGRADOWALNE"
        ):
            blocks.append(all_rows[i : i + 3])
            i += 3
        else:
            _LOGGER.warning(
                "Unexpected row order at index %d (%s) — skipping.",
                i,
                all_rows[i][0],
            )
            i += 1

    if not blocks:
        raise ValueError(
            "No complete schedule blocks found in PDF text. "
            "The PDF format may have changed."
        )

    return blocks


def _build_entries(
    blocks: list[list[tuple[str, list[str]]]],
    rejon_order: list[str],
    year: int,
    sub_district_filter: str,
) -> list[Collection]:
    """Build Collection entries, optionally filtered by sub_district."""
    entries: list[Collection] = []
    matched_filter = False

    for block_idx, block in enumerate(blocks):
        rejon_name = (
            rejon_order[block_idx]
            if block_idx < len(rejon_order)
            else f"Zone {block_idx + 1}"
        )

        if sub_district_filter:
            if _normalize_rejon(sub_district_filter) != _normalize_rejon(rejon_name):
                continue
            matched_filter = True

        for waste_key, month_tokens in block:
            friendly_name, icon = WASTE_TYPE_MAP[waste_key]
            for month_idx, token in enumerate(month_tokens):
                month_num = month_idx + 1
                for day_str in token.split(";"):
                    day_str = day_str.strip()
                    if not day_str.isdigit():
                        continue
                    try:
                        collection_date = date(year, month_num, int(day_str))
                    except ValueError:
                        _LOGGER.warning(
                            "Invalid date %d-%02d-%s — skipping.",
                            year,
                            month_num,
                            day_str,
                        )
                        continue
                    entries.append(
                        Collection(date=collection_date, t=friendly_name, icon=icon)
                    )

    if sub_district_filter and not matched_filter:
        raise SourceArgumentNotFoundWithSuggestions(
            "sub_district", sub_district_filter, rejon_order
        )

    if not entries:
        raise ValueError("No collection entries could be parsed from the PDF.")

    return entries


class Source:
    def __init__(
        self,
        district: str = "",
        sub_district: str = "",
        property_type: str = "residential",
    ):
        self._property_type = property_type.lower().strip()
        if self._property_type not in PROPERTY_TYPES:
            raise SourceArgumentNotFoundWithSuggestions(
                "property_type", property_type, list(PROPERTY_TYPES)
            )

        self._sub_district = sub_district.strip()

        district = district.strip()
        if not district:
            raise SourceArgumentRequiredWithSuggestions(
                "district",
                "district is required",
                list(DISTRICT_MAP.keys()),
            )
        if district not in DISTRICT_MAP:
            raise SourceArgumentNotFoundWithSuggestions(
                "district", district, list(DISTRICT_MAP.keys())
            )
        self._district = district
        self._slug = DISTRICT_MAP[district]

    def fetch(self) -> list[Collection]:
        year = datetime.now().year
        pdf_bytes, actual_year = self._fetch_pdf(year)

        reader = PdfReader(BytesIO(pdf_bytes))
        rejon_order = _extract_rejon_order(reader)
        schedule_text = _find_schedule_text(reader)
        blocks = _extract_blocks(schedule_text)

        _LOGGER.debug(
            "District '%s': %d blocks, %d Rejon names from cover: %s",
            self._district,
            len(blocks),
            len(rejon_order),
            rejon_order,
        )

        return _build_entries(blocks, rejon_order, actual_year, self._sub_district)

    def _build_url(self, year: int) -> str:
        base = _BASE_URL.format(year=year)
        if self._property_type == "commercial":
            return f"{base}Firmy{year}_{self._slug}_firmy_{year}.pdf"
        # residential (default)
        return f"{base}zamieszkale{year}_{self._slug}_{year}.pdf"

    def _fetch_pdf(self, year: int) -> tuple[bytes, int]:
        """Download the schedule PDF, trying current year then year-1 on HTTP 404.

        Returns (pdf_bytes, year_used).
        """
        for attempt_year in (year, year - 1):
            url = self._build_url(attempt_year)
            _LOGGER.debug("Fetching waste schedule PDF: %s", url)
            resp = requests.get(url, timeout=30)
            if resp.status_code == 404:
                if attempt_year == year:
                    _LOGGER.info(
                        "PDF for year %d not found (HTTP 404), trying %d.",
                        attempt_year,
                        attempt_year - 1,
                    )
                else:
                    _LOGGER.info(
                        "PDF for year %d not found (HTTP 404).",
                        attempt_year,
                    )
                continue
            resp.raise_for_status()
            return resp.content, attempt_year

        raise FileNotFoundError(
            f"Could not fetch Rybnik waste schedule PDF for {year} or {year - 1}. "
            f"Last URL tried: {self._build_url(year - 1)}"
        )
