"""GrandBesancon calendar retrieval and record parsing.

HTTP uses the pipeline session; parsers emit dated records for a transformer.
"""

from datetime import date, timedelta
from typing import Any

import lxml.etree as ET

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc

WASTE_TYPE_MAP = {"incinerable": "Ordures ménagères", "recyclable": "Tri sélectif"}
DAY_MAP = {
    "lundi": 0,
    "mardi": 1,
    "mercredi": 2,
    "jeudi": 3,
    "vendredi": 4,
    "samedi": 5,
    "dimanche": 6,
}
STREETS_URL = "https://datasets.grandbesancon.fr/besanconfr.php"
COLLECTION_URL = "https://datasets.grandbesancon.fr/dechets.php"


def _resolve_street_code(source: BaseSource) -> str:
    params = {
        "method": "getRuesCommuneAction",
        "output": "json",
        "insee": source.params["insee_code"],
    }
    r = source.session.get(STREETS_URL, params=params, timeout=30)
    r.raise_for_status()
    streets = r.json()
    if not streets:
        raise SourceArgumentNotFound("insee_code", source.params["insee_code"])
    for s in streets:
        if s["librueweb"].lower() == source.params["street"].lower():
            return s["cdrue"]
    suggestions = [s["librueweb"] for s in streets]
    raise SourceArgumentNotFoundWithSuggestions(
        "street", source.params["street"], suggestions
    )


def _fetch_collection_xml(source: BaseSource) -> Any:
    params = {
        "method": "getJourDeCollecteDechetsParAdresseAction",
        "insee": source.params["insee_code"],
    }
    if source.params["house_number"]:
        params["numrue"] = source.params["house_number"]
    r = source.session.get(COLLECTION_URL, params=params, timeout=30)
    r.raise_for_status()
    return r


def _retrieve(source: BaseSource) -> Any:
    cdrue = _resolve_street_code(source)
    return (_fetch_collection_xml(source), cdrue)


def _parse(source: BaseSource, raw) -> list[dict[str, Any]]:
    response, cdrue = raw
    root = ET.fromstring(
        response.content, parser=ET.XMLParser(resolve_entities=False, no_network=True)
    )
    target_addr = None
    for addr in root.findall(".//adresse"):
        rue = addr.find("rue")
        if rue is not None and rue.get("id") == cdrue.lstrip("0"):
            num = addr.find("numero")
            if source.params["house_number"] and num is not None:
                if num.text != source.params["house_number"]:
                    continue
            target_addr = addr
            break
    if target_addr is None:
        raise SourceArgumentNotFound("street", source.params["street"])
    infos = target_addr.find("infosCollecte")
    if infos is None:
        return []
    today = date.today()
    end_date = today + timedelta(days=365)
    entries: list[dict] = []
    for jour in infos.findall("jourDeCollecte"):
        waste_api_type = jour.get("type", "")
        semaine = jour.get("semaine")
        day_name = jour.text
        if not day_name:
            continue
        weekday = DAY_MAP.get(day_name.lower().strip())
        if weekday is None:
            continue
        waste_type = WASTE_TYPE_MAP.get(waste_api_type, waste_api_type)
        d = today
        days_ahead = weekday - d.weekday()
        if days_ahead < 0:
            days_ahead += 7
        d = d + timedelta(days=days_ahead)
        while d <= end_date:
            iso_week = d.isocalendar()[1]
            include = True
            if (semaine == "impaires" and iso_week % 2 == 0) or (
                semaine == "paires" and iso_week % 2 == 1
            ):
                include = False
            if include:
                entries.append({"date": d, "type": waste_type})
            d += timedelta(weeks=1)
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
