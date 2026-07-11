"""AWM München, Germany.

Demonstrates: a large, genuinely branching TYPO3 form wizard. Posting the
address may return the ICS download link directly, or the site may first
need a location id per waste-stream (when an address has more than one
container location) and/or a collection-cycle string per waste-stream (when a
stream can be emptied on more than one schedule) -- each a separate POST only
required when the previous response's HTML contains that stream's <select>.
None of this branching, nor the "one response can carry several
`a.downloadics` links to fetch and merge", fits a configured retriever, so it
stays a source-defined ``retrieve``/``parse`` pair.
"""

import re
import urllib.parse
from typing import ClassVar, final

from bs4 import BeautifulSoup, Tag
from waste_collection_schedule import parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, street, text_field
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequiredWithSuggestions,
)
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GENERAL_WASTE,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_DOMAIN = "https://www.awm-muenchen.de"
_HEADERS = {"Origin": _DOMAIN}  # the backend checks Origin on every POST.

_FORM_NAME = "abfuhrkalender"
_FIELD = "tx_awmabfuhrkalender_abfuhrkalender"

_LOCATION_ID_RE = r"\d+"
_CYCLE_STRING_RE = r"(?:\d{3}|\d\/\d);[A-Z]"

# (location-id param, stellplatz key, cycle-string param, leerungszyklus key)
_STREAMS = (
    ("r_location_id", "restmuell", "r_collection_cycle_string", "R"),
    ("b_location_id", "bio", "b_collection_cycle_string", "B"),
    ("p_location_id", "papier", "p_collection_cycle_string", "P"),
)


def _clean_label(label: str) -> str:
    return label.split(",")[0].replace("Achtung:", "").strip()


def _form_info(html_text: str, form_name: str) -> "tuple[str, dict]":
    """Return the form's action URL and its hidden input fields."""
    soup = BeautifulSoup(html_text, "html.parser")
    form = soup.find("form", id=form_name)
    if not isinstance(form, Tag):
        raise SourceArgumentNotFoundWithSuggestions("street", form_name, [])
    action = form.get("action")
    action_url = f"{_DOMAIN}{urllib.parse.unquote(str(action))}"
    hidden = {}
    for tag in form.find_all("input"):
        if isinstance(tag, Tag) and str(tag.get("type", "")).lower() == "hidden":
            hidden[tag.get("name")] = tag.get("value", "")
    return action_url, hidden


def _options(soup: BeautifulSoup, attr_name: str, attr_value: str) -> list:
    select = soup.find("select", {attr_name: attr_value})
    return select.find_all("option") if isinstance(select, Tag) else []


@final
class Source(BaseSource):
    TITLE = "AWM München"
    DESCRIPTION = "Source for AWM München."
    URL = _DOMAIN
    COUNTRY = "de"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Waltenbergerstr. 1": {
            "street": "Waltenbergerstr.",
            "house_number": "1",
        },
        "Geretsrieder Str. 10a": {
            "street": "Geretsrieder Str.",
            "house_number": "10a",
        },
        "Bellinzonastraße 19": {
            "street": "Bellinzonastr.",
            "house_number": "19",
            "r_location_id": "70050134",
            "b_location_id": "70050134",
            "p_location_id": "70050134",
        },
        "Marienplatz 1": {
            "street": "Marienplatz",
            "house_number": "1",
            "r_collection_cycle_string": "001;U",
            "p_collection_cycle_string": "002;U",
        },
    }

    PARAMS = (
        street(field="street"),
        house_number(field="house_number"),
        text_field("r_location_id", "Residual waste location ID", optional=True),
        text_field("b_location_id", "Organic waste location ID", optional=True),
        text_field("p_location_id", "Paper location ID", optional=True),
        text_field(
            "r_collection_cycle_string",
            "Residual waste emptying cycle",
            optional=True,
        ),
        text_field(
            "b_collection_cycle_string", "Organic waste emptying cycle", optional=True
        ),
        text_field("p_collection_cycle_string", "Paper emptying cycle", optional=True),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Fill in the street and house number, then submit. If the address "
            "has more than one container location or emptying cycle per "
            "waste stream, the fetch error lists the valid values to enter "
            "for the corresponding *_location_id / *_collection_cycle_string "
            "argument."
        ),
        "de": (
            "Straße und Hausnummer ausfüllen, dann abschicken. Falls die "
            "Adresse mehrere Standorte oder Leerungszyklen pro Abfallart "
            "hat, listet die Fehlermeldung die gültigen Werte für das "
            "jeweilige Argument *_location_id / *_collection_cycle_string auf."
        ),
        "it": (
            "Compilare la via e il numero civico, quindi inviare. Se "
            "l'indirizzo ha più posizioni del contenitore o cicli di "
            "svuotamento per flusso di rifiuti, l'errore elenca i valori "
            "validi per l'argomento *_location_id / *_collection_cycle_string."
        ),
        "fr": (
            "Remplir la rue et le numéro, puis envoyer. Si l'adresse a "
            "plusieurs emplacements de conteneur ou cycles de vidage par "
            "flux de déchets, l'erreur liste les valeurs valides pour "
            "l'argument *_location_id / *_collection_cycle_string concerné."
        ),
    }

    transform = ICSTransformer(
        clean=_clean_label,
        type_value_map={
            "Restmülltonne": GENERAL_WASTE,
            "Biotonne": ORGANIC,
            "Papiertonne": PAPER,
            "Wertstofftonne": RECYCLABLES,
        },
    )

    def __init__(
        self,
        street: str,
        house_number: str,
        r_location_id: str = "",
        b_location_id: str = "",
        p_location_id: str = "",
        r_collection_cycle_string: str = "",
        b_collection_cycle_string: str = "",
        p_collection_cycle_string: str = "",
    ):
        super().__init__(
            street=street,
            house_number=house_number,
            r_location_id=r_location_id,
            b_location_id=b_location_id,
            p_location_id=p_location_id,
            r_collection_cycle_string=r_collection_cycle_string,
            b_collection_cycle_string=b_collection_cycle_string,
            p_collection_cycle_string=p_collection_cycle_string,
        )

    def _fetch_links(self, session, links: list) -> list:
        responses = []
        for link in links:
            href = link.get("href")
            r = session.get(f"{_DOMAIN}{urllib.parse.unquote(href)}", headers=_HEADERS)
            r.raise_for_status()
            responses.append(r)
        return responses

    def _apply_choice(
        self,
        args: dict,
        field: str,
        value: str,
        options: list,
        param_name: str,
        pattern: str,
    ) -> None:
        if not value:
            if options:
                raise SourceArgumentRequiredWithSuggestions(
                    param_name,
                    "multiple choices returned from AWM service.",
                    [f"'{o.get('value')}' for {o.text}" for o in options],
                )
            return
        match = re.findall(pattern, value)
        if match:
            args[field] = match[0]

    def retrieve(self, source):
        session = self.session
        p = self.params

        r = session.get(f"{_DOMAIN}/entsorgen/abfuhrkalender", headers=_HEADERS)
        r.raise_for_status()
        r.encoding = "utf-8"

        action_url, args = _form_info(r.text, _FORM_NAME)
        args[f"{_FIELD}[strasse]"] = p["street"]
        args[f"{_FIELD}[hausnummer]"] = p["house_number"]
        args[f"{_FIELD}[section]"] = "address"
        args[f"{_FIELD}[submitAbfuhrkalender]"] = "true"

        r = session.post(action_url, data=args, headers=_HEADERS)
        r.raise_for_status()
        page_soup = BeautifulSoup(r.text, "html.parser")

        links = page_soup.find_all("a", {"class": "downloadics"})
        if links:
            return self._fetch_links(session, links)

        action_url, args = _form_info(r.text, _FORM_NAME)

        location_options = {
            key: _options(page_soup, "id", f"{_FIELD}[stellplatz][{key}]")
            for _loc, key, _cyc, _leer in _STREAMS
        }
        if any(location_options.values()):
            for loc_param, key, _cyc, _leer in _STREAMS:
                self._apply_choice(
                    args,
                    f"{_FIELD}[stellplatz][{key}]",
                    p[loc_param],
                    location_options[key],
                    loc_param,
                    _LOCATION_ID_RE,
                )

            r = session.post(action_url, data=args, headers=_HEADERS)
            r.raise_for_status()
            page_soup = BeautifulSoup(r.text, "html.parser")

            links = page_soup.find_all("a", {"class": "downloadics"})
            if links:
                return self._fetch_links(session, links)

            action_url, args = _form_info(r.text, _FORM_NAME)

        cycle_options = {
            leer: _options(page_soup, "name", f"{_FIELD}[leerungszyklus][{leer}]")
            for _loc, _key, _cyc, leer in _STREAMS
        }
        if any(cycle_options.values()):
            for _loc, _key, cyc_param, leer in _STREAMS:
                self._apply_choice(
                    args,
                    f"{_FIELD}[leerungszyklus][{leer}]",
                    p[cyc_param],
                    cycle_options[leer],
                    cyc_param,
                    _CYCLE_STRING_RE,
                )

            r = session.post(action_url, data=args, headers=_HEADERS)
            r.raise_for_status()
            page_soup = BeautifulSoup(r.text, "html.parser")

            links = page_soup.find_all("a", {"class": "downloadics"})
            if links:
                return self._fetch_links(session, links)

        raise SourceArgumentNotFoundWithSuggestions(
            "house_number", f"{p['street']} {p['house_number']}", []
        )

    def parse(self, raw, source=None):
        ics_parser = parsers.IcsParser()
        entries: list = []
        for response in raw:
            entries.extend(ics_parser(response, source))
        return entries
