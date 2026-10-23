"""Nemenčinės komunalininkas (nemenkom.lt) XLSX schedule retrieval and parsing."""

import datetime as dt
import io
import re
import zipfile
from typing import Any
from urllib.parse import urljoin

import lxml.etree as ET

from waste_collection_schedule import recurrence
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc

PAGE_URL = "https://www.nemenkom.lt/buitiniu-ir-pakuociu-atlieku-surinkimo-grafikas/"
HEADERS = {"user-agent": "Mozilla/5.0"}
MAX_FILE_BYTES = 5 * 1024 * 1024
NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
XML_PARSER = ET.XMLParser(resolve_entities=False, no_network=True)
GENERAL_WASTE = "Buitinės atliekos"


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().casefold()


def _discover_xlsx_url(html: str) -> str:
    hrefs = re.findall(r"href=[\"']([^\"']+\.xlsx)[\"']", html, flags=re.IGNORECASE)
    if not hrefs:
        raise ValueError("No XLSX schedule link found on the nemenkom.lt page")
    return urljoin(PAGE_URL, hrefs[0])


def _col_index(ref: str) -> tuple[int, int]:
    m = re.match(r"^([A-Z]+)(\d+)$", ref)
    if not m:
        raise ValueError(f"Invalid cell ref: {ref}")
    col = 0
    for ch in m.group(1):
        col = col * 26 + ord(ch) - 64
    return int(m.group(2)), col - 1


def _read_rows(content: bytes) -> tuple[str, list[list[str]]]:
    with zipfile.ZipFile(io.BytesIO(content)) as zf:
        try:
            sst = ET.fromstring(zf.read("xl/sharedStrings.xml"), parser=XML_PARSER)
            strings = [
                "".join(t.text or "" for t in si.findall(".//s:t", NS))
                for si in sst.findall("s:si", NS)
            ]
        except KeyError:
            strings = []
        wb = ET.fromstring(zf.read("xl/workbook.xml"), parser=XML_PARSER)
        sheet_el = wb.find(".//s:sheet", NS)
        title = sheet_el.attrib.get("name", "") if sheet_el is not None else ""
        sheet = ET.fromstring(zf.read("xl/worksheets/sheet1.xml"), parser=XML_PARSER)
    cells: dict[int, dict[int, str]] = {}
    for c in sheet.findall(".//s:c", NS):
        ref = c.attrib.get("r")
        if not ref:
            continue
        row, col = _col_index(ref)
        if c.attrib.get("t") == "s":
            v = c.find("s:v", NS)
            text = strings[int(v.text)] if v is not None and v.text else ""
        elif c.attrib.get("t") == "inlineStr":
            text = "".join(t.text or "" for t in c.findall(".//s:t", NS))
        else:
            v = c.find("s:v", NS)
            text = v.text if v is not None and v.text else ""
        if text.strip():
            cells.setdefault(row, {})[col] = text.strip()
    rows = []
    for r in sorted(cells):
        width = max(cells[r]) + 1
        rows.append([cells[r].get(i, "") for i in range(width)])
    return title, rows


def _village_matches(cell: str, village: str, street: str | None) -> bool:
    name, _, rest = cell.partition("(")
    if _norm(name) != _norm(village):
        return False
    if not street:
        return True
    return _norm(street) in _norm(rest)


def parse_schedule(
    content: bytes, village: str, street: str | None = None
) -> list[dict[str, Any]]:
    title, rows = _read_rows(content)
    year_match = re.search(r"\b(20\d{2})\b", title)
    if not year_match:
        raise ValueError("Year not found in XLSX sheet name")
    year = int(year_match.group(1))
    header_idx = next(
        (i for i, r in enumerate(rows) if any(_norm(c) == "kaimai" for c in r)), None
    )
    if header_idx is None:
        raise ValueError(
            "Header row not found in XLSX; the file format may have changed"
        )
    header = rows[header_idx]
    # The header cells are merged inconsistently; the village/street name is
    # always the column directly left of the weekday column.
    weekday_col = next(
        (i for i, c in enumerate(header) if _norm(c).startswith("savaitės")), None
    )
    if not weekday_col:
        raise ValueError("Weekday column not found in XLSX header")
    village_col = weekday_col - 1
    month_cols = {
        i: month for i, c in enumerate(header) if (month := recurrence.month(c))
    }
    entries: list[dict[str, Any]] = []
    known: list[str] = []
    for row in rows[header_idx + 1 :]:
        if len(row) <= village_col or not row[village_col]:
            continue
        known.append(row[village_col].partition("(")[0].strip())
        if not _village_matches(row[village_col], village, street):
            continue
        for col, month in month_cols.items():
            if col >= len(row):
                continue
            for day in re.findall(r"(\d{1,2})\s*d", row[col]):
                entries.append(
                    {"date": dt.date(year, month, int(day)), "type": GENERAL_WASTE}
                )
        if entries:
            break
    if not entries:
        raise SourceArgumentNotFoundWithSuggestions(
            "village", village, sorted(set(known))
        )
    return entries


class NemenkomRetriever(RetrieverFunc):
    def __call__(self, source: BaseSource) -> Any:
        session = source.session
        page = session.get(PAGE_URL, timeout=30, headers=HEADERS)
        page.raise_for_status()
        r = session.get(_discover_xlsx_url(page.text), timeout=30, headers=HEADERS)
        r.raise_for_status()
        if len(r.content) > MAX_FILE_BYTES:
            raise ValueError("XLSX file is too large")
        return r.content


class NemenkomParser(Parser[list[dict[str, Any]]]):
    def __call__(
        self, response: Any, source: BaseSource | None = None
    ) -> list[dict[str, Any]]:
        if source is None:
            raise ValueError("Nemenkom parser requires a source")
        return parse_schedule(
            response, source.params["village"], source.params.get("street")
        )
