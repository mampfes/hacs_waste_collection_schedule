"""IrisSaltenCalendar retrieval and parsing, using the pipeline HTTP session."""

import datetime
import urllib.parse
from typing import Any

from bs4 import BeautifulSoup

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc

MONTH_MAP = {
    "januar": 1,
    "februar": 2,
    "mars": 3,
    "april": 4,
    "mai": 5,
    "juni": 6,
    "juli": 7,
    "august": 8,
    "september": 9,
    "oktober": 10,
    "november": 11,
    "desember": 12,
}


class _CalendarClient:
    _session: Any

    def __init__(self, address: str, kommune: str = ""):
        self._address = address
        self._kommune = kommune

    def retrieve(self):
        s = self._session
        s.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36",
                "Accept": "application/json, text/javascript, */*; q=0.01",
            }
        )
        safe_adresse = urllib.parse.quote(self._address)
        search_url = f"https://iris-salten.no/wp-content/themes/iris/data/location-search.php?query={safe_adresse}"
        r_search = s.get(search_url, timeout=30)
        r_search.raise_for_status()
        try:
            results = r_search.json()
        except ValueError as exc:
            raise ValueError(
                "Failed to read JSON data from Iris Salten address search."
            ) from exc
        uuid = None
        for result in results:
            if result.get("adresse", "").lower() == self._address.lower():
                if self._kommune:
                    if self._kommune.lower() in result.get("kommune", "").lower():
                        uuid = result.get("id")
                        break
                else:
                    uuid = result.get("id")
                    break
        if not uuid:
            raise ValueError(
                f"Found no valid ID for the address: {self._address}. Check your spelling."
            )
        safe_address_param = urllib.parse.quote_plus(self._address)
        safe_kommune_param = urllib.parse.quote_plus(self._kommune)
        schedule_url = f"https://iris-salten.no/privat/tommeplan/?lookup={uuid}&address={safe_address_param}&municipality={safe_kommune_param}"
        r_schedule = s.get(schedule_url, timeout=30)
        r_schedule.raise_for_status()
        return r_schedule

    def parse(self, r_schedule):
        soup = BeautifulSoup(r_schedule.text, "html.parser")
        calendar_list = soup.select("ul.calendar__list li")
        entries = []
        for item in calendar_list:
            text = item.get_text(" ", strip=True)
            parts = text.split()
            if len(parts) < 4:
                continue
            try:
                day_str = parts[1].replace(".", "")
                month_str = parts[2].lower()
                waste_original = " ".join(parts[3:])
                waste_lower = waste_original.lower()
                day = int(day_str)
                month = MONTH_MAP.get(month_str)
                if not month:
                    continue
                now = datetime.date.today()
                year = now.year
                if month < now.month and now.month - month > 6:
                    year += 1
                elif month > now.month and month - now.month > 6:
                    year -= 1
                date_obj = datetime.date(year, month, day)
                found_any = False
                if "restavfall" in waste_lower:
                    entries.append({"date": date_obj, "type": "Restavfall"})
                    found_any = True
                if "matavfall" in waste_lower:
                    name = (
                        "Matavfall uten hageavfall"
                        if "uten hageavfall" in waste_lower
                        else "Matavfall"
                    )
                    entries.append({"date": date_obj, "type": name})
                    found_any = True
                if "papir" in waste_lower:
                    name = "Papir og papp" if "og papp" in waste_lower else "Papir"
                    entries.append({"date": date_obj, "type": name})
                    found_any = True
                if "plast" in waste_lower:
                    name = "Plastemballasje" if "emballasje" in waste_lower else "Plast"
                    entries.append({"date": date_obj, "type": name})
                    found_any = True
                if "glass" in waste_lower or "metall" in waste_lower:
                    name = (
                        "Glass- og metallemballasje"
                        if "metallemballasje" in waste_lower
                        else "Glass og metall"
                    )
                    entries.append({"date": date_obj, "type": name})
                    found_any = True
                if not found_any:
                    entries.append({"date": date_obj, "type": waste_original})
            except (ValueError, IndexError):
                continue
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
