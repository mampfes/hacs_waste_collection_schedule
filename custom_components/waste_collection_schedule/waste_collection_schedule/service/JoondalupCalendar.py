"""JoondalupCalendar: provider retrieval and parsing using the shared verified HTTP session."""

import json
from datetime import date, datetime, timedelta
from typing import Any

from curl_cffi import requests
from dateutil.rrule import FR, MO, SA, SU, TH, TU, WE, WEEKLY, rrule
from requests.utils import requote_uri

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc

HEADERS: dict = {
    "user-agent": "Mozilla/5.0",
    "accept": "application/json, text/plain, */*",
}
DAYS: dict = {
    "MONDAY": MO,
    "TUESDAY": TU,
    "WEDNESDAY": WE,
    "THURSDAY": TH,
    "FRIDAY": FR,
    "SATURDAY": SA,
    "SUNDAY": SU,
}
STREET_TYPES = {
    "AV": "Avenue",
    "AVE": "Avenue",
    "BVD": "Boulevard",
    "BLVD": "Boulevard",
    "CCT": "Circuit",
    "CH": "Chase",
    "CL": "Close",
    "CR": "Crescent",
    "CRES": "Crescent",
    "CT": "Court",
    "DR": "Drive",
    "DRV": "Drive",
    "ESP": "Esplanade",
    "GDNS": "Gardens",
    "GR": "Grove",
    "GRV": "Grove",
    "HWY": "Highway",
    "LN": "Lane",
    "LP": "Loop",
    "PDE": "Parade",
    "PKWY": "Parkway",
    "PL": "Place",
    "RD": "Road",
    "RSE": "Rise",
    "SQ": "Square",
    "ST": "Street",
    "TCE": "Terrace",
    "WY": "Way",
}


class _CalendarClient:
    _session: Any

    def __init__(self, number=None, street=None, suburb=None, mapkey=None):
        if mapkey is None:
            self._number = str(number)
            self._street = str(street)
            self._suburb = str(suburb).upper()
            self._mapkey = None
        else:
            self._number = None
            self._street = None
            self._suburb = None
            self._mapkey = str(mapkey)

    def _lookup_street(self, session: requests.Session, street: str) -> list:
        search_term = requote_uri(f"{street} {self._suburb}")
        r = session.get(
            f"https://www.joondalup.wa.gov.au/aapi/coj/propertylookup/{search_term}",
            headers=HEADERS,
        )
        r.raise_for_status()
        return json.loads(r.content) or []

    def _find_mapkey(self, session: requests.Session) -> str:
        """Resolve number + street + suburb to the council's mapkey.

        Previously a street or number the council did not recognise left the
        mapkey unset, and the schedule request went on to ask for
        ``bindatelookup/None`` -- which answered with an empty list and failed
        as "list index out of range", telling the visitor nothing.
        """
        if self._street is None:
            raise SourceArgumentNotFound("street", "")
        properties = self._lookup_street(session, self._street)
        if not properties:
            words = self._street.split()
            if words:
                expanded = STREET_TYPES.get(words[-1].upper().rstrip("."))
                if expanded:
                    properties = self._lookup_street(
                        session, " ".join([*words[:-1], expanded])
                    )
        if not properties:
            raise SourceArgumentNotFound(
                "street",
                self._street,
                f"Joondalup does not list a street called '{self._street}' in '{self._suburb}'. Check the street name and suburb, and write the street type out in full (Drive, not Dr).",
            )
        for property in properties:
            if str(property["house_no"]) == self._number:
                return str(property["mapkey"])
        raise SourceArgumentNotFoundWithSuggestions(
            "number",
            self._number,
            sorted(
                {
                    str(property["house_no"])
                    for property in properties
                    if property.get("house_no") is not None
                },
                key=lambda n: (len(n), n),
            ),
        )

    def format_date(self, s: str) -> date:
        dt = datetime.strptime(s, "%A %d/%m/%Y").date()
        return dt

    def generate_general_waste_date(self, s: datetime, d: int) -> date:
        rr = rrule(WEEKLY, dtstart=s, byweekday=d)
        dt = rr.after(s)
        assert dt is not None
        return dt.date()

    def generate_recycle_dates(self, s: str) -> tuple:
        d: date = self.format_date(s)
        dt1: date = d + timedelta(days=-7)
        dt2: date = d + timedelta(days=7)
        return (dt1, dt2)

    def retrieve(self) -> Any:
        s = self._session
        if self._mapkey is None:
            self._mapkey = self._find_mapkey(s)
        r = s.get(
            f"https://www.joondalup.wa.gov.au/aapi/coj/bindatelookup/{self._mapkey}",
            headers=HEADERS,
        )
        return r, self._mapkey

    def parse(self, raw):
        r, self._mapkey = raw
        start_date = datetime.now() + timedelta(days=-1)
        results = json.loads(r.content)
        if not results:
            raise SourceArgumentNotFound(
                "mapkey",
                self._mapkey,
                "Joondalup holds no collection schedule for this property.",
            )
        pickups = results[0]
        general = self.generate_general_waste_date(
            start_date, DAYS[pickups["Rubbish_Day"].upper().strip()]
        )
        recycle1, recycle2 = self.generate_recycle_dates(pickups["Next_Recycling_Date"])
        schedule: dict = {
            "Recycling": self.format_date(pickups["Next_Recycling_Date"]),
            "Bulk Put Out": self.format_date(pickups["Bulk_Rubbish_Put_Out"]),
            "Bulk Pick Up": self.format_date(pickups["Bulk_Rubbish_Pick_Up"]),
            "General Waste": general,
            "Green Waste": recycle1,
            "Green Waste ": recycle2,
        }
        entries = []
        for item in schedule:
            entries.append({"date": schedule[item], "type": item.strip()})
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
