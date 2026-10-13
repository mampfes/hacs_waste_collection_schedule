"""AmmerlandApp calendar retrieval and record parsing.

HTTP uses the pipeline session; parsers emit dated records for a transformer.
"""

import datetime
import json
from typing import Any

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc

API_URL = "https://firebasestorage.googleapis.com/v0/b/abfall-ammerland.appspot.com/o/and%2F7%2Fawbapp.json?alt=media"
_MART_RES = 1
_MART_BIO = 2
_MART_WER = 4
_MART_PAP = 8
_MART_AST = 16
_MART_PRO = 32
_CITY_MAP = {
    "Apen": 1,
    "Bad Zwischenahn": 2,
    "Edewecht": 3,
    "Rastede": 4,
    "Westerstede": 5,
    "Wiefelstede": 6,
}


def _emit_collections(entries: list[dict], date: datetime.date, mart: int) -> None:
    """Append one Collection entry per waste type in the bitmask."""
    if mart & _MART_RES:
        entries.append({"date": date, "type": "Restabfall"})
    if mart & _MART_BIO:
        entries.append({"date": date, "type": "Bioabfall"})
    if mart & _MART_WER:
        entries.append({"date": date, "type": "Gelber Sack"})
    if mart & _MART_PAP:
        entries.append({"date": date, "type": "Papier"})


def _retrieve(source: BaseSource) -> Any:
    response = source.session.get(API_URL, timeout=30)
    response.raise_for_status()
    return response


def _parse(source: BaseSource, response) -> list[dict[str, Any]]:
    # The app feed concatenates JSON tables with ## rather than returning a
    # single JSON document. Table positions follow the Android app's schema.
    blocks = response.text.split("##")
    parts = [json.loads(b) for b in blocks if b.strip()]
    streets = parts[0]
    strgr = parts[1]  # Street sections.
    strdat = parts[3]  # Annual collection rhythm per street/section.
    astdat = parts[4]  # Street/section to garden-waste area mapping.
    kal1 = parts[5]  # Daily parity and paper-round reference.
    kal2 = parts[6]  # Garden-waste dates per area.
    kal3 = parts[7]  # Hazardous-waste dates per municipality.
    fkal = parts[8]  # Holiday shifts from original to replacement date.
    ortid = _CITY_MAP.get(source.params["city"])
    if ortid is None:
        raise SourceArgumentNotFoundWithSuggestions(
            "city", source.params["city"], list(_CITY_MAP.keys())
        )
    city_streets = [s for s in streets if s["ortid"] == ortid]
    street_map = {s["bez"]: s["id"] for s in city_streets}
    if source.params["street"] not in street_map:
        raise SourceArgumentNotFoundWithSuggestions(
            "street", source.params["street"], sorted(street_map.keys())
        )
    street_id = street_map[source.params["street"]]
    sections = [s for s in strgr if s["strid"] == street_id]
    strgrid = 0
    if sections:
        if source.params["street_section"] is None:
            section_names = [s["grenze"] for s in sections]
            raise SourceArgumentNotFoundWithSuggestions(
                "street_section", "", section_names
            )
        section_map = {s["grenze"]: s["id"] for s in sections}
        if source.params["street_section"] not in section_map:
            raise SourceArgumentNotFoundWithSuggestions(
                "street_section",
                source.params["street_section"],
                sorted(section_map.keys()),
            )
        strgrid = section_map[source.params["street_section"]]
    # Prefer this year's rhythm, retaining the app's fallback to older years.
    current_year = datetime.date.today().year
    sd = None
    for year_offset in range(current_year - 2017):
        year = current_year - year_offset
        jahr = year - 2000
        candidates = [
            e
            for e in strdat
            if e["strid"] == street_id
            and e["strgrid"] == strgrid
            and (e["jahr"] == jahr)
        ]
        if candidates:
            sd = candidates[0]
            break
    if sd is None:
        candidates = [
            e for e in strdat if e["strid"] == street_id and e["strgrid"] == strgrid
        ]
        if not candidates:
            raise ValueError(
                f"No schedule found for street '{source.params['street']}'"
                + (
                    f" section '{source.params['street_section']}'"
                    if source.params["street_section"]
                    else ""
                )
            )
        sd = max(candidates, key=lambda e: e["jahr"])
    ast_entry = next(
        (e for e in astdat if e["strid"] == street_id and e["astgrid"] == strgrid), None
    )
    # A street-level garden-waste round may apply to all its sections.
    if ast_entry is None and strgrid != 0:
        ast_entry = next(
            (e for e in astdat if e["strid"] == street_id and e["astgrid"] == 0), None
        )
    ast = ast_entry["ast"] if ast_entry else None
    holiday_shift: dict[str, str] = {e["datum"]: e["fdatum"] for e in fkal}
    entries: list[dict] = []
    for entry in kal1:
        date_str: str = entry["datum"]
        gu: bool = entry["gu"]
        vier: bool = entry["vier"]
        papier: int = entry["papier"]
        d = datetime.date.fromisoformat(date_str)
        dow = d.isoweekday() % 7  # Java Calendar: Sunday=0, Monday=1, ...
        mart = 0
        if dow == sd["resttag"] and gu == sd["restgu"]:
            if not source.params["four_weekly_rest"] or vier == sd["vier"]:
                mart |= _MART_RES
        if dow == sd["biotag"] and gu == sd["biogu"]:
            mart |= _MART_BIO
        if dow == sd["werttag"] and gu == sd["wertgu"]:
            mart |= _MART_WER
        if papier != 0 and papier == sd["papier"]:
            mart |= _MART_PAP
        if mart == 0:
            continue
        actual_date_str = holiday_shift.get(date_str, date_str)
        actual_date = datetime.date.fromisoformat(actual_date_str)
        _emit_collections(entries, actual_date, mart)
    if ast is not None:
        for entry in kal2:
            if entry["ortid"] == ortid and entry["ast"] == ast:
                date_str = entry["datum"]
                actual_date_str = holiday_shift.get(date_str, date_str)
                actual_date = datetime.date.fromisoformat(actual_date_str)
                entries.append({"date": actual_date, "type": "Ast- und Strauchwerk"})
    for entry in kal3:
        if entry["ortid"] == ortid:
            date_str = entry["datum"]
            actual_date_str = holiday_shift.get(date_str, date_str)
            actual_date = datetime.date.fromisoformat(actual_date_str)
            entries.append({"date": actual_date, "type": "Problemstoffe"})
    return entries


class CalendarRetriever(RetrieverFunc):
    """Retrieve the calendar and context needed to interpret it."""

    def __call__(self, source: BaseSource) -> Any:
        return _retrieve(source)


class CalendarParser(Parser[list[dict[str, Any]]]):
    """Read provider records without classifying their waste types."""

    def __call__(
        self, response: Any, source: BaseSource | None = None
    ) -> list[dict[str, Any]]:
        if source is None:
            raise ValueError("Calendar parser requires a source")
        return _parse(source, response)
