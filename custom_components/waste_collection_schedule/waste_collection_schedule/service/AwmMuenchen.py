"""AWM München's branching TYPO3 form wizard (DE).

Abfallwirtschaftsbetrieb München publishes its calendar behind a form that
answers differently depending on the address. Posting the street and house
number may hand back the ICS download links straight away, or the form may
first want more:

* a **location id** per waste stream, when an address has more than one
  container location (a block of flats with several bin stores); and/or
* a **collection cycle** per waste stream, when a stream can be emptied on more
  than one schedule.

Each is a separate POST, and each is only required when the previous response's
HTML actually carries that stream's ``<select>``. So the wizard is not a fixed
number of steps: it is "submit, and if the download links are not there yet,
answer whatever the page is now asking and submit again".

:class:`CollectionCalendarRetriever` is that loop. One response can carry
several ``a.downloadics`` links (one per stream), so it returns a list and pairs
with :class:`~waste_collection_schedule.parsers.EachResponse`.

Only AWM runs this form, so this module is one provider's flow rather than a
platform. It lives here, and not in the source, so the source stays a
declarative composition and the next person to meet a staged TYPO3 form has a
worked example to read.
"""

import re
import urllib.parse
from typing import TYPE_CHECKING, Any

from bs4 import BeautifulSoup, Tag

from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequiredWithSuggestions,
)
from waste_collection_schedule.retrievers import Response, RetrieverFunc

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource

DOMAIN = "https://www.awm-muenchen.de"
HEADERS = {"Origin": DOMAIN}  # the backend checks Origin on every POST.

FORM_NAME = "abfuhrkalender"
FIELD = "tx_awmabfuhrkalender_abfuhrkalender"

LOCATION_ID_RE = r"\d+"
CYCLE_STRING_RE = r"(?:\d{3}|\d\/\d);[A-Z]"

# (location-id param, stellplatz key, cycle-string param, leerungszyklus key)
STREAMS = (
    ("r_location_id", "restmuell", "r_collection_cycle_string", "R"),
    ("b_location_id", "bio", "b_collection_cycle_string", "B"),
    ("p_location_id", "papier", "p_collection_cycle_string", "P"),
)


def form_info(html_text: str, form_name: str) -> "tuple[str, dict]":
    """Return the form's action URL and its hidden input fields."""
    soup = BeautifulSoup(html_text, "html.parser")
    form = soup.find("form", id=form_name)
    if not isinstance(form, Tag):
        raise SourceArgumentNotFoundWithSuggestions("street", form_name, [])
    action = form.get("action")
    action_url = f"{DOMAIN}{urllib.parse.unquote(str(action))}"
    hidden = {}
    for tag in form.find_all("input"):
        if isinstance(tag, Tag) and str(tag.get("type", "")).lower() == "hidden":
            hidden[tag.get("name")] = tag.get("value", "")
    return action_url, hidden


def options(soup: BeautifulSoup, attr_name: str, attr_value: str) -> list:
    """The ``<option>``s of the select identified by one attribute."""
    select = soup.find("select", {attr_name: attr_value})
    return select.find_all("option") if isinstance(select, Tag) else []


def _apply_choice(
    args: dict,
    field: str,
    value: str,
    choices: list,
    param_name: str,
    pattern: str,
) -> None:
    """Put the household's answer for one select into the form body.

    A select the page is asking about and the user has not answered is not an
    error in the data: it is a question only they can settle, so it is raised
    with the options to choose from.
    """
    if not value:
        if choices:
            raise SourceArgumentRequiredWithSuggestions(
                param_name,
                "multiple choices returned from AWM service.",
                [f"'{o.get('value')}' for {o.text}" for o in choices],
            )
        return
    match = re.findall(pattern, value)
    if match:
        args[field] = match[0]


class CollectionCalendarRetriever(RetrieverFunc):
    """Drive the form until it yields the ICS links, then fetch every one.

    Submits the address; if the response carries ``a.downloadics`` links the
    wizard is done. Otherwise it answers whichever stage the page is now asking
    about (container locations, then collection cycles) and submits again,
    checking for the links after each. Reaching the end without links means the
    address never resolved, which is reported against ``house_number``.
    """

    def _download_links(self, source: "BaseSource", links: list) -> list[Response]:
        responses = []
        for link in links:
            href = link.get("href")
            r = source.session.get(
                f"{DOMAIN}{urllib.parse.unquote(href)}", headers=HEADERS
            )
            r.raise_for_status()
            responses.append(r)
        return responses

    def _submit(self, source: "BaseSource", action_url: str, args: dict) -> tuple:
        r = source.session.post(action_url, data=args, headers=HEADERS)
        r.raise_for_status()
        return r, BeautifulSoup(r.text, "html.parser")

    def __call__(self, source: "BaseSource") -> "list[Response]":
        session = source.session
        p: Any = source.params

        r = session.get(f"{DOMAIN}/entsorgen/abfuhrkalender", headers=HEADERS)
        r.raise_for_status()
        r.encoding = "utf-8"

        action_url, args = form_info(r.text, FORM_NAME)
        args[f"{FIELD}[strasse]"] = p["street"]
        args[f"{FIELD}[hausnummer]"] = p["house_number"]
        args[f"{FIELD}[section]"] = "address"
        args[f"{FIELD}[submitAbfuhrkalender]"] = "true"

        r, page_soup = self._submit(source, action_url, args)

        links = page_soup.find_all("a", {"class": "downloadics"})
        if links:
            return self._download_links(source, links)

        action_url, args = form_info(r.text, FORM_NAME)

        location_options = {
            key: options(page_soup, "id", f"{FIELD}[stellplatz][{key}]")
            for _loc, key, _cyc, _leer in STREAMS
        }
        if any(location_options.values()):
            for loc_param, key, _cyc, _leer in STREAMS:
                _apply_choice(
                    args,
                    f"{FIELD}[stellplatz][{key}]",
                    p[loc_param],
                    location_options[key],
                    loc_param,
                    LOCATION_ID_RE,
                )

            r, page_soup = self._submit(source, action_url, args)

            links = page_soup.find_all("a", {"class": "downloadics"})
            if links:
                return self._download_links(source, links)

            action_url, args = form_info(r.text, FORM_NAME)

        cycle_options = {
            leer: options(page_soup, "name", f"{FIELD}[leerungszyklus][{leer}]")
            for _loc, _key, _cyc, leer in STREAMS
        }
        if any(cycle_options.values()):
            for _loc, _key, cyc_param, leer in STREAMS:
                _apply_choice(
                    args,
                    f"{FIELD}[leerungszyklus][{leer}]",
                    p[cyc_param],
                    cycle_options[leer],
                    cyc_param,
                    CYCLE_STRING_RE,
                )

            r, page_soup = self._submit(source, action_url, args)

            links = page_soup.find_all("a", {"class": "downloadics"})
            if links:
                return self._download_links(source, links)

        raise SourceArgumentNotFoundWithSuggestions(
            "house_number", f"{p['street']} {p['house_number']}", []
        )
