"""PreZero Service Mitte waste collection schedule for Landkreis Helmstedt."""

from __future__ import annotations

import datetime
import re
from collections.abc import Iterable, Iterator
from typing import Any, ClassVar, final
from urllib.parse import urljoin

from waste_collection_schedule import parsers, recurrence
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import district, dropdown
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import PdfRow, PdfWord
from waste_collection_schedule.retrievers import TwoStepRetriever
from waste_collection_schedule.transformers import ICSTransformer

INDEX_URL = "https://prezero.com/de/landkreis-helmstedt"

MUNICIPALITY_PATTERNS: dict[str, str] = {
    "Gemeinde Lehre": r"(/de/asset/download/[^\"'<>]*Abfuhrkalender_Gem\._Lehre[^\"'<>]*\.pdf[^\"'<>]*)",
    "Samtgemeinden Grasleben und Velpke": r"(/de/asset/download/[^\"'<>]*Abfuhrkalender_Samtg\.[^\"'<>]*Grasleben_und_Velpke[^\"'<>]*\.pdf[^\"'<>]*)",
    "Königslutter Ortsteile und Samtgemeinde Nord-Elm": r"(/de/asset/download/[^\"'<>]*Abfuhrkalender_K[^\"'<>]*nigslutter_Otsteile_und_Nord-Elm[^\"'<>]*\.pdf[^\"'<>]*)",
    "Stadt Schöningen und Samtgemeinde Heeseberg": r"(/de/asset/download/[^\"'<>]*Abfuhrkalender_Sch[^\"'<>]*ningen_und_Samtg\._Heeseberg[^\"'<>]*\.pdf[^\"'<>]*)",
    "Stadt Helmstedt und Ortsteile": r"(/de/asset/download/[^\"'<>]*Abfuhrkalender_Stadt_Helmstedt_und_Ortsteile[^\"'<>]*\.pdf[^\"'<>]*)",
    "Stadt Königslutter am Elm": r"(/de/asset/download/[^\"'<>]*Abfuhrkalender_Stadt_K[^\"'<>]*nigslutter_am_Elm[^\"'<>]*\.pdf[^\"'<>]*)",
}

_YEAR_RE = re.compile(r"\b(20\d{2})\b")
_AREA_RE = re.compile(r"^(?:Gebiet|Bezirk)\s+(\d+)$", re.IGNORECASE)


def _extract_pdf_url(response: Any, source: BaseSource) -> str:
    municipality = source.params["municipality"]
    pattern = MUNICIPALITY_PATTERNS.get(municipality)
    if not pattern:
        raise SourceArgumentNotFoundWithSuggestions(
            "municipality", municipality, list(MUNICIPALITY_PATTERNS.keys())
        )
    m = re.search(pattern, response.text, re.IGNORECASE)
    if not m:
        raise ValueError(f"Could not find PDF link for {municipality} on {INDEX_URL}")
    return urljoin(INDEX_URL, m.group(1))


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip()).casefold()


def _extract_year(rows: list[PdfRow]) -> int:
    for row in rows:
        if row.page > 1:
            continue
        text = " ".join(w.text for w in row.words)
        m = _YEAR_RE.search(text)
        if m:
            return int(m.group(1))
    raise ValueError("Could not find calendar year in PreZero Helmstedt PDF")


def _parse_area_mapping(rows: list[PdfRow]) -> dict[str, str]:
    """Extract {Ort/Ortsteil/Straße: Gebiet/Bezirk-Nummer} from page index 2+."""
    mapping: dict[str, str] = {}
    for row in rows:
        if row.page < 2:
            continue
        words = sorted(row.words, key=lambda w: w.x0)
        for idx in range(1, len(words)):
            m = _AREA_RE.match(words[idx].text.strip())
            if not m:
                continue
            place = words[idx - 1].text.strip()
            if place and not _AREA_RE.match(place) and not place.lower().startswith("ort"):
                mapping[place] = m.group(1)
    return mapping


def _cluster_month_columns(rows: list[PdfRow], page: int) -> list[tuple[float, int]]:
    """Find month headers on a calendar page and return sorted (x_center, month_num)."""
    headers: list[tuple[float, int]] = []
    for row in rows:
        if row.page != page:
            continue
        for w in row.words:
            first_token = w.text.strip().split()[0].rstrip(".")
            if len(first_token) < 3:
                continue
            m = recurrence.month(first_token, locale="de")
            if m is not None:
                x_center = (w.x0 + w.x1) / 2.0
                if not any(
                    abs(x_center - existing_x) < 35 and m == existing_m
                    for existing_x, existing_m in headers
                ):
                    headers.append((x_center, m))
    headers.sort(key=lambda item: item[0])
    return headers


def _extract_dates_for_area(
    rows: list[PdfRow], year: int, target_area: str
) -> list[datetime.date]:
    """Parse collection dates for `target_area` from page indices 0 and 1."""
    dates: list[datetime.date] = []
    for page in (0, 1):
        month_cols = _cluster_month_columns(rows, page)
        if not month_cols:
            continue

        boundaries: list[tuple[float, float, int]] = []
        for idx, (x_center, month_num) in enumerate(month_cols):
            left = 0.0 if idx == 0 else (month_cols[idx - 1][0] + x_center) / 2.0
            right = (
                9999.0
                if idx == len(month_cols) - 1
                else (x_center + month_cols[idx + 1][0]) / 2.0
            )
            boundaries.append((left, right, month_num))

        for row in rows:
            if row.page != page:
                continue
            for left, right, month_num in boundaries:
                cell_words: list[PdfWord] = [
                    w for w in row.words if left <= ((w.x0 + w.x1) / 2.0) < right
                ]
                if len(cell_words) < 3:
                    continue
                day_num: int | None = None
                area_tokens: list[str] = []
                has_weekday = False
                for w in cell_words:
                    tok = w.text.strip()
                    if recurrence.weekday(tok, locale="de", abbreviated=True) is not None:
                        has_weekday = True
                    elif tok.isdigit() and day_num is None and 1 <= int(tok) <= 31:
                        day_num = int(tok)
                    elif day_num is not None:
                        area_tokens.extend(re.findall(r"🟡\s*(\d+)", tok))
                if has_weekday and day_num is not None and target_area in area_tokens:
                    try:
                        dates.append(datetime.date(year, month_num, day_num))
                    except ValueError:
                        continue
    return sorted(set(dates))


@final
class Source(BaseSource):
    TITLE = "PreZero Landkreis Helmstedt (Gelbe Tonne)"
    DESCRIPTION = (
        "Gelbe Tonne waste collection schedule for Landkreis Helmstedt (PreZero Service Mitte)."
    )
    URL = INDEX_URL
    COUNTRY = "de"
    RAISE_ON_EMPTY = True
    SOURCE_CODEOWNERS: ClassVar[list] = ["@Rince77"]

    TEST_CASES: ClassVar[dict] = {
        "Meinkot": {
            "municipality": "Samtgemeinden Grasleben und Velpke",
            "district": "Meinkot",
        },
        "Velpke": {
            "municipality": "Samtgemeinden Grasleben und Velpke",
            "district": "Velpke",
        },
        "Lehre": {
            "municipality": "Gemeinde Lehre",
            "district": "Lehre",
        },
        "Helmstedt Abteiweg": {
            "municipality": "Stadt Helmstedt und Ortsteile",
            "district": "Abteiweg",
        },
        "Koenigslutter Raebke": {
            "municipality": "Königslutter Ortsteile und Samtgemeinde Nord-Elm",
            "district": "Räbke",
        },
        "Schoeningen Abelnkarre": {
            "municipality": "Stadt Schöningen und Samtgemeinde Heeseberg",
            "district": "Abelnkarre",
        },
        "Koenigslutter Stadt Albrechtsburg": {
            "municipality": "Stadt Königslutter am Elm",
            "district": "Albrechtsburg",
        },
    }

    PARAMS = (
        dropdown(
            "municipality",
            options=list(MUNICIPALITY_PATTERNS.keys()),
            default="Samtgemeinden Grasleben und Velpke",
        ),
        district(),
    )

    WASTE_TYPES: ClassVar[list] = [wt.RECYCLABLES]

    HOWTO: ClassVar[dict] = {
        "de": (
            "Wählen Sie Ihren Abfuhrbezirk (Gemeinde/Samtgemeinde) aus dem PreZero-Abfuhrkalender "
            "für den Landkreis Helmstedt (https://prezero.com/de/landkreis-helmstedt) sowie Ihren "
            "Ort, Ortsteil bzw. Ihre Straße."
        ),
        "en": (
            "Select your collection district (municipality) from the PreZero Landkreis Helmstedt "
            "schedule (https://prezero.com/de/landkreis-helmstedt) and enter your village/district or street."
        ),
    }

    retrieve = TwoStepRetriever(
        lookup_url=INDEX_URL,
        extract=_extract_pdf_url,
        schedule_url=lambda key, **_: key,
    )

    parse = parsers.PdfTableParser(min_words=100)

    def preprocess(
        self, rows: Iterable[PdfRow], source: BaseSource | None = None
    ) -> Iterator[tuple[datetime.date, str]]:
        row_list = list(rows)
        year = _extract_year(row_list)
        area_map = _parse_area_mapping(row_list)
        if not area_map:
            raise ValueError(
                "Could not extract area assignment table from PreZero Helmstedt PDF"
            )

        wanted = _normalize(self.params["district"])
        target_area: str | None = None
        for place_name, area_num in area_map.items():
            if _normalize(place_name) == wanted:
                target_area = area_num
                break

        if target_area is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "district",
                self.params["district"],
                sorted(area_map.keys()),
            )

        for collection_date in _extract_dates_for_area(row_list, year, target_area):
            yield (collection_date, "Gelbe Tonne")

    transform = ICSTransformer(
        type_value_map={
            "Gelbe Tonne": wt.RECYCLABLES,
        }
    )
