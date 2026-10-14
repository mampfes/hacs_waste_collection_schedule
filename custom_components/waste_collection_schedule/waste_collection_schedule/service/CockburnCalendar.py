"""CockburnCalendar: provider retrieval and parsing using the shared verified HTTP session."""

import re
from datetime import date, datetime, timedelta
from typing import Any, TypedDict

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFound,
)
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc

API_URL = "https://gis1.cockburn.wa.gov.au/webapiv2/PropertyInfoSearch/PropertyNo"
HEADERS = {
    "User-Agent": "Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0",
    "Accept": "application/xhtml+xml,text/json,application/xml",
}


class Collections(TypedDict):
    type: str
    dates: list[date]


class _CalendarClient:
    _session: Any

    def __init__(
        self, address: str | None = None, property_no: str | int | None = None
    ):
        self.address: str | None = None
        self.property_no: str | None = None
        if not address and (not property_no):
            raise ValueError("Either address or property_no must be provided")
        if address:
            address = address.strip()
            address = re.sub(" +", " ", address)
            address = re.sub(",", "", address)
            address = re.sub(" st ", " street ", address, flags=re.IGNORECASE)
            address = re.sub(" hwy ", " highway ", address, flags=re.IGNORECASE)
            address = re.sub(" ave ", " avenue ", address, flags=re.IGNORECASE)
            address = re.sub(" rd ", " road ", address, flags=re.IGNORECASE)
            address = re.sub(" ch ", " chase ", address, flags=re.IGNORECASE)
            address = re.sub(" lp ", " loop ", address, flags=re.IGNORECASE)
            address = re.sub(" dr ", " drive ", address, flags=re.IGNORECASE)
            address = re.sub(
                "western australia (\\d{4})", "WA \\1", address, flags=re.IGNORECASE
            )
            address = re.sub(" wa (\\d{4})", "  WA  \\1", address, flags=re.IGNORECASE)
            if not re.search("\\bwa\\b", address, flags=re.IGNORECASE):
                address = re.sub("\\s+(\\d{4})\\s*$", "  WA  \\1", address)
            self.address = address
            self.search_method = "address"
        if property_no:
            self.property_no = str(property_no)
            self.search_method = "property_no"

    def collect_dates(self, start_date, weeks):
        dates = []
        dates.append(start_date)
        for _ in range(1, 4 // weeks):
            start_date = start_date + timedelta(days=weeks * 7)
            dates.append(start_date)
        return dates

    def _search(self, query: str, search_method: str) -> list[dict]:
        search_value = re.sub("\\s+", "+", query.strip())
        r = self._session.get(
            f"{API_URL}?q={search_value}&search_method={search_method}", headers=HEADERS
        )
        r.raise_for_status()
        payload = r.json()
        return payload if isinstance(payload, list) else []

    def _search_address(self) -> list[dict]:
        """Find the property, retrying without the state and postcode.

        The search is stricter about what follows the street than about the
        street itself, and resolves fine without a state and postcode, so a
        trailing "WA 6164" is better dropped than sent when it matches nothing.
        """
        address = self.address or ""
        attempts = [address]
        without_state = re.sub(
            "\\s+wa\\s+\\d{4}\\s*$", "", address, flags=re.IGNORECASE
        ).strip()
        if without_state and without_state != address:
            attempts.append(without_state)
        for attempt in attempts:
            results = self._search(attempt, "address")
            if results:
                return results
        raise SourceArgumentNotFound(
            "address",
            address,
            "Cockburn did not recognise that address. Check the street number and name, and write the street type out in full (Street, not St).",
        )

    def extract_date(self, text: str) -> datetime | None:
        pattern = "\\d{1,2}-\\w{3}-\\d{4}"
        match = re.search(pattern, text)
        if match:
            original_date = match.group()
            formatted_date = datetime.strptime(original_date, "%d-%b-%Y")
            return formatted_date
        return None

    def retrieve(self) -> Any:
        if self.property_no:
            results = self._search(self.property_no, "property_no")
            if not results:
                raise SourceArgumentNotFound("property_no", self.property_no)
            data = results[0]
        else:
            results = self._search_address()
            if len(results) > 1:
                suggestions = [
                    match["Address"] for match in results if match.get("Address")
                ]
                raise SourceArgAmbiguousWithSuggestions(
                    "address", self.address, suggestions[:10]
                )
            data = results[0]
        return data

    def parse(self, data):
        entries: list[dict] = []
        if data:
            date_rubbish = datetime.today()
            while date_rubbish.strftime("%A") != data["BinDay"]:
                date_rubbish += timedelta(days=1)
            bin_dates = [date_rubbish.date()]
            grn_bin_datetime = self.extract_date(data["GardenWaste"])
            grn_bin_dates = [grn_bin_datetime.date()] if grn_bin_datetime else []
            jnk_dates = [
                datetime.strptime(data["JunkWhite1"], "%d-%b-%Y").date(),
                datetime.strptime(data["JunkWhite2"], "%d-%b-%Y").date(),
            ]
            grn_waste_dates = [
                datetime.strptime(data["GreenWaste1"], "%d-%b-%Y").date(),
                datetime.strptime(data["GreenWaste2"], "%d-%b-%Y").date(),
            ]
            collections: list[Collections] = []
            collections.append({"type": "Rubbish", "dates": bin_dates})
            collections.append({"type": "Recycling", "dates": bin_dates})
            collections.append({"type": "Junk Waste", "dates": jnk_dates})
            collections.append({"type": "Green Waste", "dates": grn_waste_dates})
            collections.append({"type": "Green Bin", "dates": grn_bin_dates})
            for collection in collections:
                for d in collection["dates"]:
                    entries.append({"date": d, "type": collection["type"]})
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
