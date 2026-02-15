import datetime as dt
import io
import logging
import re
import zipfile
from pathlib import Path
from urllib.parse import urljoin
import xml.etree.ElementTree as ET

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

_LOGGER = logging.getLogger(__name__)

TITLE = "Lázně Bohdaneč"
DESCRIPTION = "Source of city waste collection calendar (paper/plastic/mixed) of Lázně Bohdaneč."
URL = "https://lazne.bohdanec.cz/svozovy%2Dkalendar/ms-2523"
OFFICIAL_PAGE_URL = URL
TEST_CASES = {"Lázně Bohdaneč": {"file": "tests/data/laznebohdanec.xlsx"}}
HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "By default no arguments are required. The integration will automatically\n"
        "retrieve the current XLSX link from the official city page (Lázně Bohdaneč\n"
        "website, sections \"Odpady\" -> \"Svozový kalendář\").\n"
        "* If you want to pin the exact URL, open that page, click the XLSX download link,\n"
        "  copy the direct XLSX URL, and use it as `url`.\n"
        "* As a fallback you can download the file and use a local `file` path. Beware you need to manually upload file to HA.\n"
        "* If you enable dedicated calendars per waste type, set colors per calendar in the HA calendar UI."
    ),
}

PARAM_DESCRIPTIONS = {
    "en": {
        "url": "Direct URL to the XLSX file with dates",
        "file": "Path to a local XLSX file with dates (needs to be uploaded manually into HA)",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "url": "Direct XLSX URL",
        "file": "Local XLSX file",
    },
}

ICON_MAP = {
    "PAPIR": "mdi:newspaper-variant",
    "PLAST": "mdi:recycle",
    "KO": "mdi:trash-can",
}

HEADERS = {"user-agent": "Mozilla/5.0"}
MAX_FILE_BYTES = 1 * 1024 * 1024
NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}

MONTHS = {
    "Leden": 1,
    "Únor": 2,
    "Březen": 3,
    "Duben": 4,
    "Květen": 5,
    "Červen": 6,
    "Červenec": 7,
    "Srpen": 8,
    "Září": 9,
    "Říjen": 10,
    "Listopad": 11,
    "Prosinec": 12,
}


class Source:
    def __init__(
        self,
        url: str | None = None,
        file: str | None = None,
    ):
        self._url = url
        self._file = file
        self._official_url = OFFICIAL_PAGE_URL

    def fetch(self):
        zf = None
        session = requests.Session()
        try:
            if self._url:
                zf = _open_zip_from_url(self._url, session)
            elif self._file:
                path = Path(self._file)
                if not path.exists():
                    raise FileNotFoundError(f"File '{path.resolve()}' not found")
                if path.stat().st_size > MAX_FILE_BYTES:
                    raise ValueError(
                        f"XLSX file is too large (> {MAX_FILE_BYTES} bytes): {path.resolve()}"
                    )
                try:
                    zf = zipfile.ZipFile(path)
                except zipfile.BadZipFile as exc:
                    raise ValueError(
                        f"File is not a valid XLSX file: {path.resolve()}"
                    ) from exc
            else:
                url = _discover_xlsx_url(self._official_url, session)
                zf = _open_zip_from_url(url, session)
        except requests.RequestException as exc:
            raise ValueError(
                "Failed to download XLSX. Please check if the city webpage or XLSX link is still available."
            ) from exc

        with zf:
            strings = _read_shared_strings(zf)
            sheet_xml = zf.read("xl/worksheets/sheet1.xml")

        year = _extract_year(strings)
        sheet = ET.fromstring(sheet_xml)
        rows = _collect_rows(sheet, strings)

        month_rows = _collect_month_rows(rows)
        if not month_rows:
            raise ValueError(
                "No month rows found in XLSX. The file format may have changed."
            )

        entries: list[Collection] = []
        last_month = None
        month_index = 0
        sorted_month_rows = sorted(month_rows)

        for row_idx in sorted(rows.keys()):
            while (
                month_index < len(sorted_month_rows)
                and sorted_month_rows[month_index][0] <= row_idx
            ):
                last_month = sorted_month_rows[month_index][1]
                month_index += 1
            if not last_month:
                continue
            row = rows[row_idx]
            text_e = row.get("E")
            text_f = row.get("F")
            if not text_e and not text_f:
                continue
            day = None
            if text_e:
                m = re.match(r"^\s*(\d{1,2})\.", text_e)
                if m:
                    day = int(m.group(1))

            if day is None:
                continue
            kinds = []
            if text_e:
                kinds.extend(re.findall(r"\b(KO|PLAST|PAP[ÍI]R)\b", text_e))
            if text_f:
                kinds.extend(re.findall(r"\b(KO|PLAST|PAP[ÍI]R)\b", text_f))
            if not kinds:
                continue
            collection_date = dt.date(year, last_month, day)
            for kind in kinds:
                if kind == "KO":
                    entries.append(
                        Collection(
                            collection_date, "Komunální odpad", icon=ICON_MAP["KO"]
                        )
                    )
                elif kind == "PLAST":
                    entries.append(
                        Collection(collection_date, "Plast", icon=ICON_MAP["PLAST"])
                    )
                elif kind in ("PAPÍR", "PAPIR"):
                    entries.append(
                        Collection(collection_date, "Papír", icon=ICON_MAP["PAPIR"])
                    )
        return entries


def _read_shared_strings(zf: zipfile.ZipFile) -> list[str]:
    try:
        sst_xml = zf.read("xl/sharedStrings.xml")
    except KeyError:
        # Some XLSX files use inline strings only and do not include sharedStrings.xml
        return []
    sst = ET.fromstring(sst_xml)
    strings: list[str] = []
    for si in sst.findall("s:si", NS):
        parts = []
        for t in si.findall(".//s:t", NS):
            parts.append(t.text or "")
        strings.append("".join(parts))
    return strings


def _collect_rows(sheet: ET.Element, strings: list[str]) -> dict[int, dict[str, str]]:
    rows: dict[int, dict[str, str]] = {}
    for c in sheet.findall(".//s:c", NS):
        ref = c.attrib.get("r")
        if not ref:
            continue
        col, row = _split_cell_ref(ref)
        text = None
        cell_type = c.attrib.get("t")
        if cell_type == "s":
            v = c.find("s:v", NS)
            if v is not None and v.text is not None:
                try:
                    text = strings[int(v.text)]
                except (IndexError, ValueError):
                    _LOGGER.warning(
                        "Invalid sharedStrings index '%s' at cell %s",
                        v.text,
                        ref,
                    )
                    text = None
        elif cell_type == "inlineStr":
            t = c.find(".//s:t", NS)
            if t is not None:
                text = t.text
        else:
            v = c.find("s:v", NS)
            if v is not None:
                text = v.text
        if text is None:
            continue
        text = text.strip()
        if not text:
            continue
        rows.setdefault(row, {})[col] = text
    return rows


def _collect_month_rows(rows: dict[int, dict[str, str]]) -> list[tuple[int, int]]:
    month_rows: list[tuple[int, int]] = []
    for row_idx, row in rows.items():
        text = row.get("A")
        if text in MONTHS:
            month_rows.append((row_idx, MONTHS[text]))
    return month_rows


def _extract_year(strings: list[str]) -> int:
    for s in strings:
        m = re.search(r"\b(20\d{2})\b", s)
        if m:
            return int(m.group(1))
    raise ValueError("Year not found in XLSX shared strings.")


def _split_cell_ref(ref: str) -> tuple[str, int]:
    m = re.match(r"^([A-Z]+)(\d+)$", ref)
    if not m:
        raise ValueError(f"Invalid cell ref: {ref}")
    return m.group(1), int(m.group(2))


def _open_zip_from_url(url: str, session: requests.Session) -> zipfile.ZipFile:
    r = session.get(url, timeout=30, headers=HEADERS)
    r.raise_for_status()
    content_length = r.headers.get("Content-Length")
    if content_length and int(content_length) > MAX_FILE_BYTES:
        raise ValueError(f"XLSX file is too large (> {MAX_FILE_BYTES} bytes): {url}")
    if len(r.content) > MAX_FILE_BYTES:
        raise ValueError(f"XLSX file is too large (> {MAX_FILE_BYTES} bytes): {url}")
    try:
        return zipfile.ZipFile(io.BytesIO(r.content))
    except zipfile.BadZipFile as exc:
        raise ValueError(f"URL does not point to a valid XLSX file: {url}") from exc


def _discover_xlsx_url(page_url: str, session: requests.Session) -> str:
    r = session.get(page_url, timeout=30, headers=HEADERS)
    r.raise_for_status()
    html = r.text

    anchors = re.findall(
        r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )

    def score_link(href: str, text: str) -> int:
        h = href.lower()
        t = re.sub(r"\s+", " ", text).strip().lower()
        score = 0
        if ".xlsx" in h:
            score += 10
        if "file.ashx" in h:
            score += 3
        if "xlsx" in t:
            score += 5
        if "svoz" in t:
            score += 3
        if "kalend" in t:
            score += 3
        return score

    ranked: list[tuple[int, str]] = []
    for href, text in anchors:
        h = href.lower()
        if ".xlsx" in h or "file.ashx" in h:
            ranked.append((score_link(href, text), href))

    if ranked:
        ranked.sort(reverse=True, key=lambda x: x[0])
        return urljoin(page_url, ranked[0][1])

    # Fallback: try any href mentioning XLSX, even outside <a> tags
    hrefs = re.findall(r'href=["\']([^"\']+)["\']', html, flags=re.IGNORECASE)
    candidates = [
        h
        for h in hrefs
        if ".xlsx" in h.lower() or "file.ashx" in h.lower()
    ]
    if not candidates:
        raise ValueError("No XLSX link found on the page")

    return urljoin(page_url, candidates[0])
