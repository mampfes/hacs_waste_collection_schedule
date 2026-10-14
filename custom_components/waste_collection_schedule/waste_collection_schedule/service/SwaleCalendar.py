"""SwaleCalendar: provider retrieval and parsing using the shared verified HTTP session."""

import logging
import re
from datetime import date, datetime, timedelta
from time import sleep
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc

_LOGGER = logging.getLogger(__name__)
API_URL = (
    "https://swale.gov.uk/bins-littering-and-the-environment/bins/check-your-bin-day"
)


class _CalendarClient:
    _session: Any

    def __init__(self, uprn: int | str, postcode: str):
        self._uprn: str = str(uprn)
        self._postcode: str = postcode

    def append_year(self, d: str) -> date:
        today: date = datetime.now().date()
        year: int = today.year
        dt: date = datetime.strptime(f"{d} {year!s}", "%d %B %Y").date()
        if dt - today < timedelta(days=-31):
            dt = dt.replace(year=dt.year + 1)
        return dt

    @staticmethod
    def _lookup_form(soup: BeautifulSoup):
        """Return the council lookup form without depending on its numeric ID."""
        for form in soup.find_all("form"):
            if form.find("input", {"name": re.compile("^SQ_FORM_\\d+_PAGE$")}):
                return form
        return None

    @staticmethod
    def _field_name(form, label_text: str, fallback_tag: str | None = None) -> str:
        label = next(
            (
                item
                for item in form.find_all("label")
                if label_text in item.get_text(" ", strip=True).lower()
            ),
            None,
        )
        if label and (field_id := label.get("for")):
            field = form.find(id=field_id)
            if field and field.get("name"):
                return field["name"]
        if fallback_tag:
            for field in form.find_all(fallback_tag, {"name": True}):
                if field.get("type") not in {"hidden", "submit"}:
                    return field["name"]
        raise ValueError(f"Swale lookup form is missing its {label_text} control.")

    @staticmethod
    def _submit_control(form) -> tuple[str, str]:
        control = form.find("input", {"type": "submit", "name": True, "value": True})
        if not control:
            raise ValueError("Swale lookup form is missing its submit control.")
        return (control["name"], control["value"])

    @staticmethod
    def _hidden_data(soup: BeautifulSoup) -> dict[str, str]:
        data = {}
        for field in soup.select('input[type="hidden"][name]'):
            name = field.get("name")
            value = field.get("value") or ""
            if not isinstance(name, str) or not isinstance(value, str):
                raise ValueError("Swale lookup has an invalid hidden form field.")
            data[name] = value
        return data

    @staticmethod
    def _raise_for_unexpected_page(soup: BeautifulSoup, stage: str) -> None:
        title = soup.title.get_text(" ", strip=True).lower() if soup.title else ""
        content = soup.get_text(" ", strip=True).lower()
        if "just a moment" in title or "challenges.cloudflare.com" in content:
            raise ValueError("Swale lookup was blocked by a Cloudflare challenge.")
        errors = [
            error
            for error in soup.select(
                ".sq-form-error, .sq-form-error-message, .validation-error, .alert-danger, [role='alert']"
            )
            if error.get_text(" ", strip=True)
        ]
        if errors:
            raise ValueError(f"Swale {stage} submission returned a validation error.")

    @staticmethod
    def _submit(session, response, form, payload: dict[str, str]):
        method = form.get("method", "get").lower()
        request = getattr(session, method, None)
        if request is None:
            raise ValueError(f"Swale lookup form uses unsupported method {method!r}.")
        action = urljoin(response.url, form.get("action") or response.url)
        if method == "get":
            return request(action, params=payload)
        return request(action, data=payload)

    def retrieve(self) -> Any:
        s = self._session
        r = s.get(API_URL)
        r.raise_for_status()
        soup: BeautifulSoup = BeautifulSoup(r.content, "html.parser")
        self._raise_for_unexpected_page(soup, "initial")
        form = self._lookup_form(soup)
        if not form:
            raise ValueError("Swale lookup page did not contain an input form.")
        payload = self._hidden_data(soup)
        payload[self._field_name(form, "postcode", "input")] = self._postcode
        submit_name, submit_value = self._submit_control(form)
        payload[submit_name] = submit_value
        r = self._submit(s, r, form, payload)
        r.raise_for_status()
        sleep(5)
        soup = BeautifulSoup(r.content, "html.parser")
        self._raise_for_unexpected_page(soup, "postcode")
        form = self._lookup_form(soup)
        if not form:
            raise ValueError(
                "Swale postcode submission did not return an address form."
            )
        payload = self._hidden_data(soup)
        payload[self._field_name(form, "address", "select")] = self._uprn
        submit_name, submit_value = self._submit_control(form)
        payload[submit_name] = submit_value
        r = self._submit(s, r, form, payload)
        r.raise_for_status()
        soup = BeautifulSoup(r.content, "html.parser")
        self._raise_for_unexpected_page(soup, "UPRN")
        if self._lookup_form(soup):
            raise ValueError(
                "Swale UPRN submission returned an input form instead of results."
            )
        return r

    def parse(self, r):
        soup = BeautifulSoup(r.content, "html.parser")
        temp_list: list = []
        next_date = soup.find("strong", {"id": "SBC-YBD-collectionDate"})
        if not next_date:
            raise ValueError(
                "Could not find next collection date — the page may have changed or returned an error."
            )
        waste_list = soup.find("div", {"id": "SBCFirstBins"})
        if not waste_list:
            raise ValueError(
                "Could not find waste list — the page may have changed or returned an error."
            )
        waste_items = waste_list.find_all("li")
        raw_date = next_date.text.lower()
        if "today" in raw_date:
            dt = datetime.today().strftime("%d %B %Y")
        elif "tomorrow" in raw_date:
            dt = (datetime.today() + timedelta(days=1)).strftime("%d %B %Y")
        else:
            try:
                dt = raw_date.split("y, ")[-1].strip()
            except IndexError:
                dt = "Unknown"
        for item in waste_items:
            temp_list.append([dt, item.text.strip()])
        future_collection = soup.find("div", {"id": "FutureCollections"})
        if not future_collection:
            raise ValueError(
                "Could not find future collections — the page may have changed or returned an error."
            )
        future_date = future_collection.find("p")
        if not future_date:
            raise ValueError(
                "Could not find future collection date — the page may have changed or returned an error."
            )
        future_list = soup.find("ul", {"id": "FirstFutureBins"})
        if not future_list:
            raise ValueError(
                "Could not find future bins list — the page may have changed or returned an error."
            )
        future_items = future_list.find_all("li")
        for item in future_items:
            dt = future_date.text.split("y, ")[-1]
            temp_list.append([dt, item.text.strip()])
        remap_wastes: dict = {
            "blue bin": "Recycling",
            "food waste": "Food",
            "green bin": "Refuse",
            "garden waste": "Garden",
        }
        entries: list = []
        for pickup in temp_list:
            waste_date: date = self.append_year(pickup[0])
            raw = pickup[1].strip().lower()
            waste_type = remap_wastes.get(raw)
            if waste_type is None:
                _LOGGER.warning("Unknown waste type '%s' — skipping", raw)
                continue
            entries.append({"date": waste_date, "type": waste_type})
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
