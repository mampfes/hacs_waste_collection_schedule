"""KawMainzBingen calendar retrieval and record parsing.

HTTP uses the pipeline session; parsers emit dated records for a transformer.
"""

from __future__ import annotations

import datetime
from typing import Any

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc

API_URL = "https://abfallkalender-api-lk.kaw-mainz-bingen.de/public/frontend"
RECORDS_PER_PAGE = 999999
DATE_FORMAT = "%Y-%m-%d"


def _normalize(value: str) -> str:
    return " ".join(value.casefold().split())


def _active_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        item for item in items if item.get("Id", 0) > 0 and item.get("RecordState") == 1
    ]


def _find_by_name(items: list[dict[str, Any]], name: str) -> dict[str, Any] | None:
    normalized_name = _normalize(name)
    return next(
        (item for item in items if _normalize(item.get("Name", "")) == normalized_name),
        None,
    )


def _names(items: list[dict[str, Any]]) -> list[str]:
    return [item["Name"] for item in items]


def _retrieve(source: BaseSource) -> Any:
    session = source.session
    settings = _get_settings(source, session)
    bezirk = _find_bezirk(source, settings)
    ort = _find_ort(source, settings, bezirk["Id"])
    today = datetime.date.today()
    date_to = datetime.date(today.year + 1, 12, 31)
    params = {
        "Filter.SearchTerm": "",
        "Filter.DistrictId": bezirk["Id"],
        "Filter.CityId": ort["Id"],
        "Filter.StreetId": 0,
        "Filter.DateFrom": today.strftime(DATE_FORMAT),
        "Filter.DateTo": date_to.strftime(DATE_FORMAT),
        "Filter.WasteTypeIds": ",".join(
            str(waste_type["Id"])
            for waste_type in _active_items(settings["WasteTypes"])
        ),
        "Filter.ShowGroupedResults": "false",
        "Filter.RecordsPerPage": RECORDS_PER_PAGE,
        "Filter.CurrentPage": 1,
        "Filter.SortColumn": "Date",
    }
    r = session.get(f"{API_URL}/collectiondates", params=params, timeout=30)
    r.raise_for_status()
    return r


def _parse(source: BaseSource, r) -> list[dict[str, Any]]:
    data = r.json()
    _raise_for_api_error(data)
    entries: list[dict] = []
    for item in data.get("DataList", []):
        date = datetime.datetime.strptime(item["Date"], "%d.%m.%Y").date()
        bin_type = item["WasteTypeName"]
        entries.append(
            {
                "date": date,
                "type": bin_type,
                "location": item.get("Location"),
                "description": item.get("AdditionalDescription"),
            }
        )
    return entries


def _get_settings(source: BaseSource, session: Any) -> dict[str, Any]:
    r = session.get(
        f"{API_URL}/settings",
        params={"Filter.IncludeStaticObjects": "true"},
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    _raise_for_api_error(data)
    return data["Data"]


def _find_bezirk(source: BaseSource, settings: dict[str, Any]) -> dict[str, Any]:
    districts = _active_items(settings["Districts"])
    district = _find_by_name(districts, source.params["bezirk"])
    if district is None:
        raise SourceArgumentNotFoundWithSuggestions(
            "bezirk", source.params["bezirk"], _names(districts)
        )
    return district


def _find_ort(
    source: BaseSource, settings: dict[str, Any], bezirk_id: int
) -> dict[str, Any]:
    cities = [
        city
        for city in _active_items(settings["Cities"])
        if city["DistrictId"] == bezirk_id
    ]
    city = _find_by_name(cities, source.params["ort"])
    if city is None:
        raise SourceArgumentNotFoundWithSuggestions(
            "ort", source.params["ort"], _names(cities)
        )
    return city


def _raise_for_api_error(data: dict[str, Any]) -> None:
    if data.get("ReturnCode") not in (0, 990):
        raise ValueError(
            data.get("ErrorMessage")
            or data.get("Message")
            or "Invalid response from server"
        )


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
