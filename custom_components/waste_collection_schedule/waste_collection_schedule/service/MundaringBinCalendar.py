"""MundaringBinCalendar retrieval and parsing through the shared, verified HTTP session."""

from datetime import datetime
from typing import Any

from bs4 import BeautifulSoup
from dateutil.rrule import FR, MO, SA, SU, TH, TU, WE, WEEKLY, rrule

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc

HEADERS = {"user-agent": "Mozilla/5.0"}
DAYS = {
    "Monday": MO,
    "Tuesday": TU,
    "Wednesday": WE,
    "Thursday": TH,
    "Friday": FR,
    "Saturday": SA,
    "Sunday": SU,
}


class _CalendarClient:
    _session: Any

    def __init__(self, parcel_number: str | int, suburb: str):
        self._parcel_number = str(parcel_number)
        self._suburb = str(suburb).upper()

    def tidytext(self, lst: list) -> list:
        temp_list = [
            txt.replace("\r\n            ", "").replace("\r\n", "").strip()
            for txt in lst
        ]
        return temp_list

    def retrieve(self):
        s = self._session
        params = {"parcelNumber": self._parcel_number, "suburb": self._suburb}
        r = s.get(
            "https://my.mundaring.wa.gov.au/BinLocationInfo/Info?",
            headers=HEADERS,
            params=params,
        )
        r.raise_for_status()
        return r

    def parse(self, r):
        soup = BeautifulSoup(r.content.decode("utf-8"), "html.parser")
        pickups = soup.find_all("div", {"class": "form-group mb-3"})
        today = datetime.now()
        entries = []
        for pickup in pickups[1:]:
            details: list = self.tidytext(pickup.text.split(":"))
            for _detail in details:
                if "FOGO" in details[0]:
                    dt = next(
                        iter(
                            rrule(
                                WEEKLY,
                                byweekday=DAYS[details[1]],
                                dtstart=today,
                                count=1,
                            )
                        )
                    )
                    waste = "FOGO Bin"
                elif "Bulk" in details[0]:
                    dt = datetime.strptime(details[1], "%d %B %Y")
                    waste = "Bulk Verge Collection"
                else:
                    dt = datetime.strptime(details[1], "%d/%m/%Y")
                    if "Recycle" in details[0]:
                        waste = "Recycle Bin"
                    else:
                        waste = "General Waste"
            entries.append({"date": dt.date(), "type": waste})
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
