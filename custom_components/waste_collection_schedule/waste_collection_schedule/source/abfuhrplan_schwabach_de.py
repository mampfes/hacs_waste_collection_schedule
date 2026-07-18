"""City of Schwabach, Germany (abfuhrplan-schwabach.de).

Highly based on abfuhrplan_landkreis_neumarkt_de's shape, but with only a
street path (no city segment) and no suggestion fallback beyond a single
street list. Demonstrates: on a 404, a second request lists every valid
street to suggest from; once the page resolves, its "download the calendar"
form is scraped for every hidden field, button and select and POSTed back
for the ICS. No configured retriever expresses "GET, and on 404 make a
second request for suggestions", hence a source-defined retrieve().
"""

from typing import ClassVar, final

from bs4 import BeautifulSoup
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import IcsParser
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GENERAL_WASTE,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

# Trailing slash is part of the provider's own URL structure; the getical
# endpoint below is requested with a doubled slash to match, matching the
# legacy source's (accidental but working) request shape.
_BASE_URL = "https://www.abfuhrplan-schwabach.de/"


def _prepare_arg(arg: str) -> str:
    return (
        arg.lower()
        .strip()
        .replace(" ", "-")
        .replace("(", "")
        .replace(")", "")
        .replace("ä", "ae")
        .replace("ö", "oe")
        .replace("ü", "ue")
        .replace("ß", "ss")
        .replace(",", "")
    )


def _parse_list_items(html: str) -> "list[str]":
    soup = BeautifulSoup(html, "html.parser")
    elements = []
    for item in soup.select("li.list-group-item"):
        a = item.select_one("a")
        if not a:
            continue
        href = a.get("href")
        if not isinstance(href, str):
            continue
        href_name = href.split("/")[-1]
        if href_name == _prepare_arg(item.text.lower().strip()):
            elements.append(item.text.strip())
        else:
            elements.append(href_name)
    return elements


def _scrape_getical_form(html: str) -> "dict[str, str | int]":
    soup = BeautifulSoup(html, "html.parser")
    form = soup.select_one('form[action="/getical"]')
    if not form:
        raise SourceArgumentNotFoundWithSuggestions("street", "", [])

    data: dict = {}
    for input_ in form.select("input") + form.select("button"):
        name = input_.get("name")
        value = input_.get("value")
        if not isinstance(name, str) or not isinstance(value, str):
            continue
        data[name] = value
    for select in form.select("select"):
        name = select.get("name")
        if not isinstance(name, str):
            continue
        data[name] = 0
    return data


@final
class Source(BaseSource):
    TITLE = "Schwabach"
    DESCRIPTION = "Source for the city of Schwabach"
    URL = _BASE_URL
    COUNTRY = "de"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Am Alten Friedhof 3, 3a": {"street": "Am Alten Friedhof 3, 3a"},
        "Äußere Rittersbacher Straße": {"street": "Äußere Rittersbacher Straße"},
    }

    PARAMS = (street(field="street"),)

    def retrieve(self, source):
        session = source.session
        street_arg = self.params["street"]

        r = session.get(f"{_BASE_URL}{street_arg}")
        if r.status_code == 404:
            streets = _parse_list_items(session.get(_BASE_URL).text)
            raise SourceArgumentNotFoundWithSuggestions("street", street_arg, streets)
        r.raise_for_status()

        data = _scrape_getical_form(r.text)
        r = session.post(f"{_BASE_URL}/getical", data=data)
        r.raise_for_status()
        return r

    parse = IcsParser()
    transform = ICSTransformer(
        type_value_map={
            "Restmüll": GENERAL_WASTE,
            "Restmüllcontainer": GENERAL_WASTE,
            "Papiertonne": PAPER,
            "Gelber Sack": RECYCLABLES,
            "Biotonne": ORGANIC,
            "Biocontainer": ORGANIC,
        }
    )

    def __init__(self, street: str):
        super().__init__(street=_prepare_arg(street))
