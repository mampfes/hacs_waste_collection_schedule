"""HeidekreisCalendar retrieval and parsing through the shared, verified HTTP session."""

from datetime import date, timedelta
from typing import Any

from curl_cffi import requests

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc

API_BASE = "https://ahkwebapi.heidekreis.de/api"
HEADERS = {
    "accept": "application/json, text/plain, */*",
    "content-type": "application/json",
    "referer": "https://ahkweb.heidekreis.de/",
    "origin": "https://ahkweb.heidekreis.de",
}


def _normalize(value: str) -> str:
    return (value or "").strip().lower()


class _CalendarClient:
    _session: Any

    def __init__(self, city: str, postcode: str, street: str, house_number: str):
        self._city = str(city)
        self._postcode = str(postcode)
        self._street = str(street)
        self._house_number = str(house_number)

    def retrieve(self):
        session = self._session
        session.headers.update(HEADERS)
        ar_strasse = self._resolve_street_id(session)
        id_objekt = self._resolve_object_id(session, ar_strasse)
        today = date.today()
        date_from = today.strftime("%m/%d/%Y")
        date_to = (today + timedelta(days=365)).strftime("%m/%d/%Y")
        type_names = self._get_disposal_type_names(session)
        icon_descriptions = self._get_icon_descriptions(
            session, id_objekt, date_from, date_to
        )
        response = self._get_entries(
            session, id_objekt, date_from, date_to, icon_descriptions, type_names
        )
        return response, icon_descriptions, type_names

    def parse(self, raw):
        response, icon_descriptions, type_names = raw
        return self._parse_entries(response, icon_descriptions, type_names)

    def _resolve_street_id(self, session: requests.Session) -> int:
        r = session.get(
            f"{API_BASE}/QMasterData/QStreetByPartialName",
            params={"PartialName": self._street},
        )
        r.raise_for_status()
        streets = r.json()
        target_street = _normalize(self._street)
        target_postcode = self._postcode.strip()
        target_city_parts = [
            _normalize(part) for part in self._city.replace(",", "/").split("/")
        ]
        matches = [
            s
            for s in streets
            if _normalize(s.get("strassenname")) == target_street
            and str(s.get("plz", "")).strip() == target_postcode
            and (
                _normalize(s.get("ort")) in target_city_parts
                or _normalize(s.get("ortOrtsteil")) in target_city_parts
                or any(
                    part in _normalize(s.get("ortOrtsteil", ""))
                    for part in target_city_parts
                )
            )
        ]
        if not matches:
            matches = [
                s
                for s in streets
                if _normalize(s.get("strassenname")) == target_street
                and str(s.get("plz", "")).strip() == target_postcode
            ]
        if not matches:
            raise ValueError(
                f"No street found for street='{self._street}', postcode='{self._postcode}', city='{self._city}'. Check spelling against the address lookup on https://www.ahk-heidekreis.de/fuer-privatkunden/abfuhrzeiten.html"
            )
        return matches[0]["arStrasse"]

    def _resolve_object_id(self, session: requests.Session, ar_strasse: int) -> int:
        r = session.post(f"{API_BASE}/QMasterData/QHouseNrEkal", json=[ar_strasse])
        r.raise_for_status()
        house_numbers = r.json()
        target_house_number = _normalize(self._house_number)
        matches = [
            h
            for h in house_numbers
            if _normalize(h.get("hausNrHausNrZ")) == target_house_number
        ]
        if not matches:
            available = ", ".join(
                sorted({h.get("hausNrHausNrZ", "") for h in house_numbers})
            )
            raise ValueError(
                f"House number '{self._house_number}' not found for this street. Available house numbers: {available}"
            )
        return matches[0]["arObjekt"]

    def _get_disposal_type_names(self, session: requests.Session) -> dict:
        r = session.get(f"{API_BASE}/QDisposalCalendar/QDisposalTypes")
        r.raise_for_status()
        return {t["id"]: t["name"] for t in r.json()}

    def _get_icon_descriptions(
        self, session: requests.Session, id_objekt: int, date_from: str, date_to: str
    ) -> dict:
        r = session.get(
            f"{API_BASE}/QDisposalCalendar/QDisposalDayIcons",
            params={"idObject": id_objekt, "from": date_from, "to": date_to},
        )
        r.raise_for_status()
        return {
            entry["id"]: entry["description"].strip()
            for entry in r.json()
            if entry.get("description")
        }

    def _get_entries(
        self,
        session: requests.Session,
        id_objekt: int,
        date_from: str,
        date_to: str,
        icon_descriptions: dict,
        type_names: dict,
    ):
        r = session.get(
            f"{API_BASE}/QDisposalCalendar/QDisposaldays",
            params={"idObject": id_objekt, "from": date_from, "to": date_to},
        )
        r.raise_for_status()
        return r

    def _parse_entries(self, r, icon_descriptions, type_names):
        days = r.json()
        entries = []
        for d in days:
            entry_date = date.fromisoformat(d["date"][:10])
            waste_type = icon_descriptions.get(d.get("idIcon")) or type_names.get(
                d.get("idDisposalType"), f"Typ {d.get('idDisposalType')}"
            )
            entries.append({"date": entry_date, "type": waste_type})
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
        return client.parse(response)
