"""Siókom Nonprofit Kft. (Hungary) waste collection source.

Calendars are annual PowerPoint-exported PDFs linked from
https://www.siokom.hu/jaratterv/. There are no street selectors: each link is a
settlement or a named district (e.g. "Siófok Cs-v", "Zamárdi Kőhegy").
"""

from __future__ import annotations

import logging
import re
import unicodedata
from datetime import date, timedelta
from io import BytesIO
from urllib.parse import quote, unquote, urljoin

import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFoundWithSuggestions,
)

_LOGGER = logging.getLogger(__name__)

TITLE = "Siókom Nonprofit Kft."
DESCRIPTION = (
    "Source for Siókom Nonprofit Kft. waste calendars "
    "(Siófok and surrounding settlements, Hungary)."
)
URL = "https://www.siokom.hu"
COUNTRY = "hu"
TEST_CASES = {
    "Balatonvilágos": {"area": "Balatonvilágos"},
    "Ádánd": {"area": "Ádánd"},
    "Siófok Cs-v": {"area": "Siófok Cs-v"},
    "Zamárdi vasúttól délre": {"area": "Zamárdi vasúttól délre"},
    "Kötcse": {"area": "Kötcse"},
    "Enying": {"area": "Enying"},
}

SOURCE_CODEOWNERS = ["@tothi"]

CALENDAR_URL = "https://www.siokom.hu/jaratterv/"

ICON_MAP = {
    "Communal": Icons.GENERAL_WASTE,
    "Selective": Icons.RECYCLING,
    "Green": Icons.GARDEN,
    "Bulky": Icons.BULKY,
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Open https://www.siokom.hu/jaratterv/ and copy the settlement or "
        "district name exactly as listed (e.g. 'Balatonvilágos', "
        "'Siófok Cs-v', 'Zamárdi Kőhegy'). Use the short name, not the "
        "neighbourhood description under Siófok rows. There is no street selector."
    ),
}

PARAM_DESCRIPTIONS = {
    "en": {
        "area": (
            "Settlement or district name as shown on siokom.hu/jaratterv/ "
            "(e.g. Balatonvilágos, Siófok Cs-v)."
        ),
        "ssl_verify": "Verify the HTTPS certificate.",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "area": "Settlement / district",
        "ssl_verify": "Verify SSL certificate",
    },
}

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "hu-HU,hu;q=0.9,en;q=0.8",
}

_MONTHS = {
    "január": 1,
    "február": 2,
    "március": 3,
    "április": 4,
    "május": 5,
    "június": 6,
    "július": 7,
    "augusztus": 8,
    "szeptember": 9,
    "október": 10,
    "november": 11,
    "december": 12,
}

_WEEKDAYS = {
    "hétfő": 0,
    "kedd": 1,
    "szerda": 2,
    "csütörtök": 3,
    "péntek": 4,
    "szombat": 5,
    "vasárnap": 6,
}

_TYPE_MAP = {
    "szelektív": "Selective",
    "zöldhulladék": "Green",
}

_TYPE_RE = re.compile(r"\b(szelektív|zöldhulladék)\b", re.IGNORECASE)
_SKIP_ROW_RE = re.compile(
    r"gyűjtés:|gyűjtésbe|gyűjtést|anyagok|például|tájékoztató",
    re.IGNORECASE,
)
_YEAR_RE = re.compile(r"(20\d{2})\.\s*évi\s+hulladéknaptár", re.IGNORECASE)
_CELL_RE = re.compile(r"-|\d{1,2}(?:[.,]\s*\d{1,2}){1,6}\.?|\d{1,2}\.?")
_DAY_RE = re.compile(r"\d{1,2}")
_RANGE_NC = r"\d{1,2}\.\d{1,2}\s*-\s*\d{1,2}\.\d{1,2}"
_WD_NC = "|".join(_WEEKDAYS)
_RANGED_RULE_RE = re.compile(
    rf"((?:{_RANGE_NC}(?:\s+és\s+{_RANGE_NC})*)\s+között)\s+"
    rf"(({_WD_NC})(?:\s+és\s+(?:{_WD_NC}))*)",
    re.IGNORECASE,
)
_RANGE_RE = re.compile(r"(\d{1,2})\.(\d{1,2})\s*-\s*(\d{1,2})\.(\d{1,2})")
_LOM_ISO_RE = re.compile(
    r"Lomtalanítás\s*:?\s*(20\d{2})\.(\d{1,2})\.(\d{1,2})",
    re.IGNORECASE,
)
_LOM_HU_RE = re.compile(
    r"(20\d{2})\.\s*(" + "|".join(_MONTHS) + r")\s+(\d{1,2})",
    re.IGNORECASE,
)


def _norm(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value)
    stripped = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    collapsed = re.sub(r"\s+", " ", stripped).strip().casefold()
    return re.sub(r"\s*-\s*", "-", collapsed)


def _is_calendar_href(href: str) -> bool:
    href_l = _norm(unquote(href))
    return "hulladeknaptar" in href_l or "jaratnaptarak" in href_l


def _anchor_label(anchor) -> str:
    text = re.sub(
        r"menetrend pdf letöltés",
        "",
        anchor.get_text(" ", strip=True),
        flags=re.IGNORECASE,
    )
    return re.sub(r"\s+", " ", text).strip()


def _match_area(needle: str, options: list[tuple[str, str]]) -> tuple[str, str]:
    """Return (label, url) for the area matching ``needle``."""
    labels = [label for label, _ in options]
    wanted = _norm(needle)
    exact = [(label, url) for label, url in options if _norm(label) == wanted]
    if len(exact) == 1:
        return exact[0]
    if len(exact) > 1:
        raise SourceArgAmbiguousWithSuggestions(
            "area", needle, [label for label, _ in exact]
        )
    partial = [
        (label, url)
        for label, url in options
        if wanted in _norm(label) or _norm(label).startswith(wanted)
    ]
    if len(partial) == 1:
        return partial[0]
    if len(partial) > 1:
        raise SourceArgAmbiguousWithSuggestions(
            "area", needle, [label for label, _ in partial]
        )
    raise SourceArgumentNotFoundWithSuggestions("area", needle, labels)


def _absolute_url(href: str) -> str:
    joined = urljoin(URL + "/", href)
    return quote(unquote(joined), safe=":/?#[]@!$&'()*+,;=")


def _scrape_calendars(html: str) -> list[tuple[str, str]]:
    """Collect (area label, calendar URL) pairs from the járatterv page.

    Drupal often splits the download icon and the settlement name into sibling
    anchors in the same table cell; the PDF href may sit on either one.
    """
    soup = BeautifulSoup(html, "html.parser")
    found: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()

    def add(label: str, href: str) -> None:
        label = re.sub(r"\s+", " ", label).strip()
        if not label or not href or not _is_calendar_href(href):
            return
        url = _absolute_url(href)
        key = (_norm(label), url)
        if key in seen:
            return
        seen.add(key)
        found.append((label, url))

    for row in soup.select("table tr"):
        hrefs = [
            a.get("href") or ""
            for a in row.find_all("a")
            if _is_calendar_href(a.get("href") or "")
        ]
        if not hrefs:
            continue
        labels = [
            lab
            for a in row.find_all("a")
            if (lab := _anchor_label(a)) and len(lab) <= 80
        ]
        if labels:
            # Prefer the short settlement/district name over any leftover caption.
            label = min(labels, key=len)
        else:
            raw = re.sub(
                r"menetrend pdf letöltés",
                "",
                row.get_text(" ", strip=True),
                flags=re.IGNORECASE,
            )
            label = re.split(r"[;\n]", raw, maxsplit=1)[0].strip()
        href = next(
            (item for item in hrefs if unquote(item).lower().endswith(".pdf")),
            hrefs[0],
        )
        add(label, href)

    if found:
        return found

    for anchor in soup.find_all("a"):
        add(_anchor_label(anchor), anchor.get("href") or "")
    return found


def _month_columns(line: str) -> list[tuple[int, int]] | None:
    low = line.lower()
    if "január" not in low or "december" not in low:
        return None
    cols: list[tuple[int, int]] = []
    for name, number in _MONTHS.items():
        pos = low.find(name)
        if pos >= 0:
            cols.append((pos, number))
    cols.sort()
    return cols if len(cols) == 12 else None


def _parse_type_row(
    line: str, year: int, month_cols: list[tuple[int, int]]
) -> list[tuple[date, str]]:
    if _SKIP_ROW_RE.search(line) or len(line) > 220:
        return []
    match = _TYPE_RE.search(line)
    if not match:
        return []
    after = line[match.end() :]
    if not re.search(r"\d|-", after):
        return []
    waste_type = _TYPE_MAP[match.group(1).lower()]
    entries: list[tuple[date, str]] = []
    for cell in _CELL_RE.finditer(after):
        token = cell.group()
        if token in ("-", "–", "—") or not _DAY_RE.search(token):
            continue
        month = min(
            month_cols, key=lambda col: abs(col[0] - (match.end() + cell.start()))
        )[1]
        for day in (int(item) for item in _DAY_RE.findall(token)):
            if not 1 <= day <= 31:
                continue
            try:
                entries.append((date(year, month, day), waste_type))
            except ValueError:
                _LOGGER.debug("Ignoring invalid date %s-%s-%s", year, month, day)
    return entries


def _weekdays_in(text: str) -> list[int]:
    found = [
        wd
        for name, wd in _WEEKDAYS.items()
        if re.search(rf"\b{name}\b", text, re.IGNORECASE)
    ]
    return sorted(set(found))


def _dates_in_range(start: date, end: date, weekdays: list[int]) -> list[date]:
    cursor = start
    result: list[date] = []
    while cursor <= end:
        if cursor.weekday() in weekdays:
            result.append(cursor)
        cursor += timedelta(days=1)
    return result


def _parse_communal(plain: str, year: int) -> list[date]:
    match = re.search(
        r"Vegyes\s+hulladékgyűjtési\s+nap\s*:(.*)", plain, re.IGNORECASE | re.DOTALL
    )
    if not match:
        return []
    rest = re.split(
        r"Szolgáltató|Lomtalanítás|Kérjük|Hulladékudvar",
        match.group(1),
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]
    rest = re.sub(r"\s+", " ", rest).strip()
    dated: list[date] = []
    if _RANGE_RE.search(rest):
        for rule in _RANGED_RULE_RE.finditer(rest):
            weekdays = _weekdays_in(rule.group(2))
            if not weekdays:
                continue
            for start_m, start_d, end_m, end_d in _RANGE_RE.findall(rule.group(1)):
                try:
                    start = date(year, int(start_m), int(start_d))
                    end = date(year, int(end_m), int(end_d))
                except ValueError:
                    continue
                dated.extend(_dates_in_range(start, end, weekdays))
    else:
        weekdays = _weekdays_in(rest)
        if weekdays:
            dated.extend(
                _dates_in_range(date(year, 1, 1), date(year, 12, 31), weekdays)
            )
    return sorted(set(dated))


def _parse_bulky(plain: str) -> list[date]:
    dates: list[date] = []
    for match in _LOM_ISO_RE.finditer(plain):
        try:
            dates.append(
                date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
            )
        except ValueError:
            continue
    if re.search(r"Lomtalanítási\s+időpontok", plain, re.IGNORECASE):
        for match in _LOM_HU_RE.finditer(plain):
            month = _MONTHS.get(match.group(2).lower())
            if month is None:
                continue
            try:
                dates.append(date(int(match.group(1)), month, int(match.group(3))))
            except ValueError:
                continue
    return sorted(set(dates))


def parse_calendar_pdf(content: bytes) -> list[Collection]:
    """Parse a Siókom hulladéknaptár PDF into collection events."""
    reader = PdfReader(BytesIO(content))
    if not reader.pages:
        raise Exception("The Siókom calendar PDF has no pages.")

    first_layout = reader.pages[0].extract_text(extraction_mode="layout") or ""
    plains = [page.extract_text() or "" for page in reader.pages]
    combined = "\n".join([first_layout, *plains])

    year_match = _YEAR_RE.search(combined)
    if not year_match:
        raise Exception("Could not read the calendar year from the Siókom PDF.")
    year = int(year_match.group(1))

    month_cols = None
    for line in first_layout.splitlines():
        month_cols = _month_columns(line)
        if month_cols:
            break
    if not month_cols:
        raise Exception("Could not find the month table in the Siókom PDF.")

    dated: list[tuple[date, str]] = []
    for line in first_layout.splitlines():
        dated.extend(_parse_type_row(line, year, month_cols))

    for when in _parse_communal(plains[0], year):
        dated.append((when, "Communal"))
    for when in _parse_bulky(combined):
        dated.append((when, "Bulky"))

    if not dated:
        raise Exception("No collection dates could be extracted from the Siókom PDF.")

    dated.sort(key=lambda item: (item[0], item[1]))
    return [
        Collection(when, waste_type, icon=ICON_MAP.get(waste_type))
        for when, waste_type in dated
    ]


class Source:
    def __init__(self, area: str, ssl_verify: bool = True) -> None:
        self._area = area
        self._ssl_verify = ssl_verify

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        session.headers.update(_HEADERS)
        response = session.get(CALENDAR_URL, timeout=30, verify=self._ssl_verify)
        response.raise_for_status()

        calendars = _scrape_calendars(response.text)
        if not calendars:
            raise Exception(
                "Could not find any calendar links on siokom.hu/jaratterv/."
            )

        _label, pdf_url = _match_area(self._area, calendars)
        if not pdf_url.lower().endswith(".pdf"):
            raise Exception(
                f"Siókom published a non-PDF calendar for '{self._area}' "
                f"({pdf_url}). A PDF is required."
            )

        pdf = session.get(
            pdf_url,
            timeout=60,
            verify=self._ssl_verify,
            headers={**_HEADERS, "Referer": CALENDAR_URL},
        )
        pdf.raise_for_status()
        if b"%PDF" not in pdf.content[:16]:
            raise Exception(f"Siókom calendar download was not a PDF: {pdf_url}")

        return parse_calendar_pdf(pdf.content)
