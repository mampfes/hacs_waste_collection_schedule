"""BohdanecXlsxCalendar retrieval and parsing, using the pipeline HTTP session."""

import datetime as dt
import re
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

from curl_cffi import requests

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.parsers import Parser, XlsxParser
from waste_collection_schedule.retrievers import RetrieverFunc

OFFICIAL_PAGE_URL = "https://lazne.bohdanec.cz/svozovy%2Dkalendar/ms-2523"

HEADERS = {"user-agent": "Mozilla/5.0"}
MAX_FILE_BYTES = 1 * 1024 * 1024
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


def _collect_rows(grid: list[list[Any]]) -> dict[int, dict[int, str]]:
    """Non-empty, stripped cell texts by row and zero-based column (A = 0)."""
    rows: dict[int, dict[int, str]] = {}
    for row_idx, row in enumerate(grid, start=1):
        for col_idx, value in enumerate(row):
            if value is None:
                continue
            text = str(value).strip()
            if text:
                rows.setdefault(row_idx, {})[col_idx] = text
    return rows


def _collect_month_rows(rows: dict[int, dict[int, str]]) -> list[tuple[int, int]]:
    month_rows: list[tuple[int, int]] = []
    for row_idx, row in rows.items():
        text = row.get(0)
        if text in MONTHS:
            month_rows.append((row_idx, MONTHS[text]))
    return month_rows


def _extract_year(rows: dict[int, dict[int, str]]) -> int:
    for row in rows.values():
        for text in row.values():
            m = re.search("\\b(20\\d{2})\\b", text)
            if m:
                return int(m.group(1))
    raise ValueError("Year not found in XLSX.")


def _download_xlsx(url: str, session: requests.Session) -> bytes:
    r = session.get(url, timeout=30, headers=HEADERS)
    r.raise_for_status()
    content_length = r.headers.get("Content-Length")
    if content_length and int(content_length) > MAX_FILE_BYTES:
        raise ValueError(f"XLSX file is too large (> {MAX_FILE_BYTES} bytes): {url}")
    if len(r.content) > MAX_FILE_BYTES:
        raise ValueError(f"XLSX file is too large (> {MAX_FILE_BYTES} bytes): {url}")
    return r.content


def _discover_xlsx_url(page_url: str, session: requests.Session) -> str:
    r = session.get(page_url, timeout=30, headers=HEADERS)
    r.raise_for_status()
    html = r.text
    anchors = re.findall(
        "<a[^>]+href=[\"\\']([^\"\\']+)[\"\\'][^>]*>(.*?)</a>",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )

    def score_link(href: str, text: str) -> int:
        h = href.lower()
        t = re.sub("\\s+", " ", text).strip().lower()
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
    hrefs = re.findall("href=[\"\\']([^\"\\']+)[\"\\']", html, flags=re.IGNORECASE)
    candidates = [h for h in hrefs if ".xlsx" in h.lower() or "file.ashx" in h.lower()]
    if not candidates:
        raise ValueError("No XLSX link found on the page")
    return urljoin(page_url, candidates[0])


class _CalendarClient:
    _session: Any

    def __init__(self, url: str | None = None, file: str | None = None):
        self._url = url
        self._file = file
        self._official_url = OFFICIAL_PAGE_URL

    def retrieve(self) -> bytes:
        session = self._session
        try:
            if self._url:
                return _download_xlsx(self._url, session)
            if self._file:
                path = Path(self._file)
                if not path.exists():
                    raise FileNotFoundError(f"File '{path.resolve()}' not found")
                if path.stat().st_size > MAX_FILE_BYTES:
                    raise ValueError(
                        f"XLSX file is too large (> {MAX_FILE_BYTES} bytes): {path.resolve()}"
                    )
                return path.read_bytes()
            url = _discover_xlsx_url(self._official_url, session)
            return _download_xlsx(url, session)
        except requests.RequestsError as exc:
            raise ValueError(
                "Failed to download XLSX. Please check if the city webpage or XLSX link is still available."
            ) from exc

    def parse(self, content: bytes, source: BaseSource | None = None):
        # Raw numbers (dates=False): the day cells are text such as "2. PLAST".
        grid = XlsxParser(dates=False, max_bytes=MAX_FILE_BYTES).read(content, source)
        rows = _collect_rows(grid.rows)
        year = _extract_year(rows)
        month_rows = _collect_month_rows(rows)
        if not month_rows:
            raise ValueError(
                "No month rows found in XLSX. The file format may have changed."
            )
        entries: list[dict] = []
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
            text_e = row.get(4)
            text_f = row.get(5)
            if not text_e and (not text_f):
                continue
            day = None
            if text_e:
                m = re.match("^\\s*(\\d{1,2})\\.", text_e)
                if m:
                    day = int(m.group(1))
            if day is None:
                continue
            kinds = []
            if text_e:
                kinds.extend(re.findall("\\b(KO|PLAST|PAP[ÍI]R)\\b", text_e))
            if text_f:
                kinds.extend(re.findall("\\b(KO|PLAST|PAP[ÍI]R)\\b", text_f))
            if not kinds:
                continue
            collection_date = dt.date(year, last_month, day)
            for kind in kinds:
                if kind == "KO":
                    entries.append({"date": collection_date, "type": "Komunální odpad"})
                elif kind == "PLAST":
                    entries.append({"date": collection_date, "type": "Plast"})
                elif kind in ("PAPÍR", "PAPIR"):
                    entries.append({"date": collection_date, "type": "Papír"})
        return entries


class CalendarRetriever(RetrieverFunc):
    def __call__(self, source: BaseSource) -> Any:
        client = _CalendarClient(**source.params)
        client._session = source.session
        return client.retrieve()


class CalendarParser(Parser[list[dict[str, Any]]]):
    def __call__(
        self, response: Any, source: BaseSource | None = None
    ) -> list[dict[str, Any]]:
        if source is None:
            raise ValueError("Calendar parser requires a source")
        client = _CalendarClient(**source.params)
        client._session = source.session
        return client.parse(response, source)
