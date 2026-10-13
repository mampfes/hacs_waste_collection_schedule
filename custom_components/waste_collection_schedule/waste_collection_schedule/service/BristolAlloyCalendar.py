"""BristolAlloyCalendar retrieval and parsing through the shared, verified HTTP session."""

# Adapted from UKBinCollectionData by robbrad:
# https://github.com/robbrad/UKBinCollectionData

from datetime import datetime
from typing import Any

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc

HEADERS = {
    "Accept": "*/*",
    "Accept-Language": "en-GB,en;q=0.9",
    "Connection": "keep-alive",
    "Ocp-Apim-Subscription-Key": "47ffd667d69c4a858f92fc38dc24b150",
    "Ocp-Apim-Trace": "true",
    "Origin": "https://bristolcouncil.powerappsportals.com",
    "Referer": "https://bristolcouncil.powerappsportals.com/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "cross-site",
    "Sec-GPC": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36",
}


class _CalendarClient:
    _session: Any

    def __init__(self, uprn):
        self._uprn = str(uprn).zfill(12)

    def retrieve(self):
        s = self._session
        payload = {"servicetypeid": "7dce896c-b3ba-ea11-a812-000d3a7f1cdc"}
        response = s.get(
            "https://bristolcouncil.powerappsportals.com/completedynamicformunauth/",
            headers=HEADERS,
            params=payload,
        )
        payload = {"Uprn": "UPRN" + self._uprn}
        response = s.post(
            "https://bcprdapidyna002.azure-api.net/bcprdfundyna001-llpg/DetailedLLPG",
            headers=HEADERS,
            json=payload,
        )
        payload = {"uprn": self._uprn}
        response = s.post(
            "https://bcprdapidyna002.azure-api.net/bcprdfundyna001-alloy/NextCollectionDates",
            headers=HEADERS,
            json=payload,
        )
        return response

    def parse(self, response):
        data = response.json()["data"]
        entries = []
        for item in data:
            for collection in item["collection"]:
                for collection_date_key in ["nextCollectionDate", "lastCollectionDate"]:
                    date_string = collection[collection_date_key].split("T")[0]
                    entries.append(
                        {
                            "date": datetime.strptime(date_string, "%Y-%m-%d").date(),
                            "type": item["containerName"],
                        }
                    )
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
