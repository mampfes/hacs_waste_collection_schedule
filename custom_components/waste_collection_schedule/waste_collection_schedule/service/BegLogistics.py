"""BegLogistics calendar retrieval and record parsing.

HTTP uses the pipeline session; parsers emit dated records for a transformer.
"""

from datetime import datetime
from typing import Any

from bs4 import BeautifulSoup

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc

API_URL = "https://kalender.beg-logistics.de/schedules/public"
API_URL2 = "https://kalender.beg-logistics.de/sessions"
STREETS_SEARCH_URL = "https://kalender.beg-logistics.de/auto_complete/streets.json"
STREET_UPDATE_URL = "https://kalender.beg-logistics.de/auto_complete/update_street.js"


def _fetch_street(source: BaseSource, s: Any, term: str | None = None) -> str:
    args = {"term": term if term is not None else source.params["street"]}
    r = s.get(STREETS_SEARCH_URL, params=args)
    r.raise_for_status()
    streets = r.json()
    for street in streets:
        if (
            street.lower().replace(",", "").replace(".", "").casefold()
            == source.params["street"]
            .lower()
            .replace(",", "")
            .replace(".", "")
            .casefold()
        ):
            return street
    if term is None and "," in source.params["street"]:
        return _fetch_street(source, s, source.params["street"].split(",")[0])
    raise SourceArgumentNotFoundWithSuggestions(
        "street", source.params["street"], streets
    )


def _retrieve(source: BaseSource) -> Any:
    s = source.session
    street = _fetch_street(source, s)
    r = s.get(API_URL)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    form = soup.select_one("form#new_session")
    if not form:
        raise ValueError("No form found on " + API_URL)
    args = {}
    for input in form.select("input"):
        if "name" in input.attrs and "value" in input.attrs:
            args[input["name"]] = input["value"]
    args["session[street]"] = street
    args["session[number]"] = source.params["hnr"]
    args["session[two_weeks]"] = ["0", "1" if source.params["two_weeks"] else "0"]
    r = s.post(API_URL2, data=args, timeout=30)
    r.raise_for_status()
    return r


def _parse(source: BaseSource, r) -> list[dict[str, Any]]:
    soup = BeautifulSoup(r.text, "html.parser")
    entries = []
    for li in soup.select("ul.list li.day"):
        date_str = li.get_text(strip=True).split(" ")[-1]
        date = datetime.strptime(date_str, "%d.%m.%Y").date()
        imgs = li.select("img")
        for img in imgs:
            type = img["alt"]
            entries.append({"date": date, "type": type})
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
