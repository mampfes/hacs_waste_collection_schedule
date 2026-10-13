"""MundaringBinCalendar retrieval and parsing through the shared, verified HTTP session."""

from typing import Any

from bs4 import BeautifulSoup

from waste_collection_schedule import date_parsers, recurrence
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import Request

HEADERS = {"user-agent": "Mozilla/5.0"}


class _CalendarClient:
    def __init__(self, parcel_number: str | int, suburb: str):
        self._parcel_number = str(parcel_number)
        self._suburb = str(suburb).upper()

    def tidytext(self, lst: list) -> list:
        temp_list = [
            txt.replace("\r\n            ", "").replace("\r\n", "").strip()
            for txt in lst
        ]
        return temp_list

    def parse(self, r):
        soup = BeautifulSoup(r.content.decode("utf-8"), "html.parser")
        pickups = soup.find_all("div", {"class": "form-group mb-3"})
        entries = []
        for pickup in pickups[1:]:
            details = self.tidytext(pickup.text.split(":"))
            if "FOGO" in details[0]:
                day = recurrence.weekday(details[1])
                if day is None:
                    raise ValueError(f"Unknown collection weekday: {details[1]}")
                collection_date = recurrence.next_weekday(day)
                waste = "FOGO Bin"
            elif "Bulk" in details[0]:
                collection_date = date_parsers.for_format("%d %B %Y")(details[1])
                waste = "Bulk Verge Collection"
            else:
                collection_date = date_parsers.for_format("%d/%m/%Y")(details[1])
                waste = "Recycle Bin" if "Recycle" in details[0] else "General Waste"
            entries.append({"date": collection_date, "type": waste})
        return entries


class CalendarParser(Parser[list[dict[str, Any]]]):
    def __call__(
        self, response: Any, source: BaseSource | None = None
    ) -> list[dict[str, Any]]:
        if source is None:
            raise ValueError("Calendar parser requires a source")
        client = _CalendarClient(**source.params)
        return client.parse(response)


calendar_retriever = Request(
    "https://my.mundaring.wa.gov.au/BinLocationInfo/Info?",
    headers=HEADERS,
    params=lambda parcel_number, suburb, **_: {
        "parcelNumber": str(parcel_number),
        "suburb": str(suburb).upper(),
    },
)
