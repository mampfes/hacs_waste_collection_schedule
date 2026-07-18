"""Landkreis Neumarkt, Germany (abfuhrplan-landkreis-neumarkt.de).

Demonstrates: a city/street URL path that, on a 404, needs a *second* request
just to work out which argument was wrong -- a bad street 404s the page but a
valid-city listing to build suggestions from; a bad city means even that
listing 404s, so the suggestions must instead be the valid *city* list. Once
the page resolves, its "download the calendar" form is scraped for every
hidden field, button and select (the request differs slightly from provider
to provider without documented meaning) and POSTed back for the ICS. No
configured retriever expresses "GET, and on 404 make a second request to
decide which of two arguments to blame", hence a source-defined retrieve().
"""

from typing import ClassVar, final

from bs4 import BeautifulSoup
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, street
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import IcsParser
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GENERAL_WASTE,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_BASE_URL = "https://www.abfuhrplan-landkreis-neumarkt.de"


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


def _get_all_streets(session, city_arg: str) -> "list[str]":
    """Valid streets for a city -- or, if the city itself is unknown, raises
    with the valid city list instead."""
    r = session.get(f"{_BASE_URL}/{city_arg}")
    if r.status_code == 404:
        cities = _parse_list_items(session.get(_BASE_URL).text)
        raise SourceArgumentNotFoundWithSuggestions("city", city_arg, cities)
    r.raise_for_status()
    return _parse_list_items(r.text)


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
    TITLE = "Landkreis Neumarkt"
    DESCRIPTION = "Source for Landkreis Neumarkt."
    URL = _BASE_URL
    COUNTRY = "de"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "dietfurt industriestrasse": {"city": "dietfurt", "street": "industriestrasse"},
        "Parsberg, Bogenmühle": {"city": "parsberg", "street": "bogenmuehle"},
    }

    PARAMS = (
        city(field="city"),
        street(field="street"),
    )

    def retrieve(self, source):
        session = source.session
        city_arg = self.params["city"]
        street_arg = self.params["street"]

        r = session.get(f"{_BASE_URL}/{city_arg}/{street_arg}")
        if r.status_code == 404:
            streets = _get_all_streets(session, city_arg)
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
            "Papiertonne": PAPER,
            "Gelber Sack": RECYCLABLES,
            "Biotonne": ORGANIC,
        }
    )

    def __init__(self, city: str, street: str):
        super().__init__(city=_prepare_arg(city), street=_prepare_arg(street))
