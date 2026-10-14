"""Resolve Québec addresses to their published HTML calendar."""

from typing import Any

from bs4 import BeautifulSoup

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFound,
)
from waste_collection_schedule.retrievers import RetrieverFunc, form_inputs

PROVIDER_URL = "https://www.ville.quebec.qc.ca/services/info-collecte/"


def _form_state(soup: BeautifulSoup) -> dict[str, str]:
    keys = ("__VIEWSTATE", "__VIEWSTATEGENERATOR", "__EVENTVALIDATION")
    fields = form_inputs(soup, hidden_only=True, required=keys)
    return {key: fields[key] for key in keys}


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
        form_data = {
            **_form_state(soup),
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
                        **_form_state(result_soup),
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
        if not result_soup.select("table.calendrier"):
            raise SourceArgumentNotFound(
                "street_number_and_name",
                self._street_number_and_name,
                "No collection schedule available",
            )
        return search_response


class CalendarRetriever(RetrieverFunc):
    def __call__(self, source: BaseSource) -> Any:
        client = _CalendarClient(**source.params)
        client._session = source.session
        return client.retrieve()
