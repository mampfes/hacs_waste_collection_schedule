"""QuebecCityCalendar: provider retrieval and parsing using the shared verified HTTP session."""

import datetime
import re
from typing import Any

from bs4 import BeautifulSoup

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFound,
)
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc

TYPE_MAP = {
    "Ordures et résidus alimentaires": "Garbage and Food Waste",
    "Recyclage": "Recycling",
    "Feuilles": "Leaves",
}
PROVIDER_URL = "https://www.ville.quebec.qc.ca/services/info-collecte/"
MONTH_NAMES = {
    "janvier": 1,
    "février": 2,
    "mars": 3,
    "avril": 4,
    "mai": 5,
    "juin": 6,
    "juillet": 7,
    "août": 8,
    "septembre": 9,
    "octobre": 10,
    "novembre": 11,
    "décembre": 12,
}


def _form_value(soup: BeautifulSoup, field_id: str) -> str:
    field = soup.find("input", {"id": field_id})
    if field is None:
        raise ValueError(f"Missing address form field: {field_id}")
    value = field.get("value")
    if not isinstance(value, str):
        raise ValueError(f"Invalid address form field: {field_id}")
    return value


class _CalendarClient:
    _session: Any

    def __init__(self, street_number_and_name: str, unique_id: str | None = None):
        self._street_number_and_name = street_number_and_name
        self._unique_id = unique_id

    def retrieve(self) -> Any:
        session = self._session
        response = session.get(PROVIDER_URL)
        if response.status_code != 200:
            raise ValueError(
                f"Failed to access {PROVIDER_URL}, status code: {response.status_code}"
            )
        soup = BeautifulSoup(response.text, "html.parser")
        viewstate = _form_value(soup, "__VIEWSTATE")
        eventvalidation = _form_value(soup, "__EVENTVALIDATION")
        viewstategenerator = _form_value(soup, "__VIEWSTATEGENERATOR")
        form_data = {
            "__VIEWSTATE": viewstate,
            "__VIEWSTATEGENERATOR": viewstategenerator,
            "__EVENTVALIDATION": eventvalidation,
            "ctl00$ctl00$contenu$texte_page$ucInfoCollecteRechercheAdresse$RechercheAdresse$txtNomRue": self._street_number_and_name,
            "ctl00$ctl00$contenu$texte_page$ucInfoCollecteRechercheAdresse$RechercheAdresse$BtnRue": "Rechercher",
        }
        search_response = session.post(PROVIDER_URL, data=form_data)
        if search_response.status_code != 200:
            raise ValueError(
                f"Failed to submit search request, status code: {search_response.status_code}"
            )
        result_soup = BeautifulSoup(search_response.text, "html.parser")
        error_msg = result_soup.find(
            "span",
            {
                "id": "ctl00_ctl00_contenu_texte_page_ucInfoCollecteRechercheAdresse_lblErr"
            },
        )
        if error_msg and error_msg.text.strip():
            raise SourceArgumentNotFound(
                argument="street_number_and_name",
                value=self._street_number_and_name,
                message_addition=f"Error searching for address: {error_msg.text.strip()}",
            )
        multiple_results_div = result_soup.find(
            "div",
            {
                "id": "ctl00_ctl00_contenu_texte_page_ucInfoCollecteRechercheAdresse_RechercheAdresse_divPlusieursResultats"
            },
        )
        if multiple_results_div:
            address_select = result_soup.find(
                "select",
                {
                    "id": "ctl00_ctl00_contenu_texte_page_ucInfoCollecteRechercheAdresse_RechercheAdresse_ddChoix"
                },
            )
            if address_select:
                options = address_select.find_all("option")
                formatted_addresses = []
                option_values = {}
                for option in options:
                    address_text = option.text.strip()
                    option_value = option["value"]
                    formatted_address = f"{address_text}. Use unique_id: {option_value}"
                    formatted_addresses.append(formatted_address)
                    option_values[option_value] = address_text
                if self._unique_id and self._unique_id in option_values:
                    form_data = {
                        "__VIEWSTATE": _form_value(result_soup, "__VIEWSTATE"),
                        "__VIEWSTATEGENERATOR": _form_value(
                            result_soup, "__VIEWSTATEGENERATOR"
                        ),
                        "__EVENTVALIDATION": _form_value(
                            result_soup, "__EVENTVALIDATION"
                        ),
                        "ctl00$ctl00$contenu$texte_page$ucInfoCollecteRechercheAdresse$RechercheAdresse$ddChoix": self._unique_id,
                        "ctl00$ctl00$contenu$texte_page$ucInfoCollecteRechercheAdresse$RechercheAdresse$btnChoix": "Poursuivre",
                    }
                    search_response = session.post(PROVIDER_URL, data=form_data)
                    if search_response.status_code != 200:
                        raise ValueError(
                            f"Failed to submit address selection, status code: {search_response.status_code}"
                        )
                    result_soup = BeautifulSoup(search_response.text, "html.parser")
                else:
                    raise SourceArgAmbiguousWithSuggestions(
                        argument="unique_id",
                        value=self._unique_id or "",
                        suggestions=formatted_addresses,
                    )
        return search_response

    def parse(self, search_response):
        result_soup = BeautifulSoup(search_response.text, "html.parser")
        entries = []
        calendar_tables = result_soup.find_all("table", {"class": "calendrier"})
        if not calendar_tables:
            raise SourceArgumentNotFound(
                argument="street_number_and_name",
                value=self._street_number_and_name,
                message_addition="No collection schedule available",
            )
        for table in calendar_tables:
            entries.extend(self._parse_calendar_table(table))
        return entries

    def _parse_calendar_table(self, table):
        """Parse a single calendar table and return Collection entries."""
        caption = table.find("caption")
        if not caption:
            return []
        match = re.search("([A-Za-zÀ-ÿ]+)\\s+(\\d{4})", caption.text.strip())
        if not match:
            return []
        month = MONTH_NAMES.get(match.group(1).lower())
        if not month:
            return []
        year = int(match.group(2))
        entries = []
        for row in table.find_all("tr")[1:]:
            for cell in row.find_all("td"):
                date_element = cell.find("p", {"class": "date"})
                if not date_element or not date_element.text.strip().isdigit():
                    continue
                day = int(date_element.text.strip())
                img_container = cell.find("p", {"class": "img"})
                if not img_container:
                    continue
                for img in img_container.find_all("img"):
                    french_type = img.get("title", img.get("alt", "")).strip()
                    if not french_type:
                        continue
                    try:
                        collection_date = datetime.date(year, month, day)
                    except ValueError:
                        continue
                    entries.append(
                        {
                            "date": collection_date,
                            "type": TYPE_MAP.get(french_type, french_type),
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
