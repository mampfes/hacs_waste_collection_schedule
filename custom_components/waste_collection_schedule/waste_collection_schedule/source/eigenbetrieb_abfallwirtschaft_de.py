"""Eigenbetrieb Abfallwirtschaft Landkreis Spree-Neiße (eigenbetrieb-abfallwirtschaft.de).

Demonstrates: a year-in-URL calendar page whose actual ICS download is behind
a same-page form (an <input name="ics"> marks the form to scrape and
resubmit) rather than a direct link, near year-end best-effort fetching next
year's calendar too (the provider often publishes it early; swallowed if not
yet available). No configured retriever expresses "GET a year page, scrape
and resubmit its own form, optionally repeat for next year", hence a
source-defined retrieve()/parse() pair. The legacy icon lookup tried the
title's first word, falling back to the whole title for the one multi-word
label ("Gelbe(r) Sack/Tonne"); that becomes a preprocess step ahead of a plain
ICSTransformer using the same map.
"""

from datetime import datetime
from typing import ClassVar, final

from bs4 import BeautifulSoup, Tag
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city_id, location_id
from waste_collection_schedule.parsers import IcsParser
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GENERAL_WASTE,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_BASE_URL = "https://www.eigenbetrieb-abfallwirtschaft.de"

_TYPE_VALUE_MAP = {
    "Restmüll": GENERAL_WASTE,
    "Biotonne": ORGANIC,
    "Papiercontainer": PAPER,
    "Gelbe(r) Sack/Tonne": RECYCLABLES,
}


def _fetch_year(session, city: str, street: str, year: int):
    url = f"{_BASE_URL}/termine/abfuhrtermine/{year}/{city}/{street}.html"
    response = session.get(url)
    if response.status_code != 200:
        raise ValueError(
            f"Error loading page {url}, status code {response.status_code}."
        )

    soup = BeautifulSoup(response.text, "html.parser")
    input_element = soup.find("input", {"name": "ics"})
    if not input_element:
        raise ValueError("Didn't find the input named ics.")
    form = input_element.find_parent("form")
    if not isinstance(form, Tag):
        raise ValueError("Didn't find the ics request form.")

    form_data = {}
    for input_tag in form.find_all("input"):
        name = input_tag.get("name")
        value = input_tag.get("value", "")
        form_data[name] = value
    action = form.get("action")
    if not isinstance(action, str):
        raise ValueError("Didn't find the ics form action URL.")
    action_url = _BASE_URL + action

    result = session.post(action_url, data=form_data)
    result.raise_for_status()
    result.encoding = "utf-8"
    return result


@final
class Source(BaseSource):
    TITLE = "Eigenbetrieb Abfallwirtschaft Landkreis Spree-Neiße"
    DESCRIPTION = "Source for Eigenbetrieb Abfallwirtschaft Landkreis Spree-Neiße."
    URL = _BASE_URL
    COUNTRY = "de"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Forst (Lausitz), Rosenweg": {"city": "4", "street": "344"},
        "Peitz, Am See": {"city": "8", "street": "1077"},
        "Guben, Altsprucke": {"city": "5", "street": "410"},
        "Spremberg, Gartenstrasse": {"city": 10, "street": 701},
    }

    PARAMS = (
        city_id(field="city"),
        location_id(field="street"),
    )

    def retrieve(self, source):
        session = source.session
        city = source.params["city"]
        street = source.params["street"]
        now = datetime.now()

        responses = [_fetch_year(session, city, street, now.year)]
        if now.month == 12:
            try:
                responses.append(_fetch_year(session, city, street, now.year + 1))
            except Exception:
                pass
        return responses

    def parse(self, raw, source):
        ics_parser = IcsParser()
        entries = []
        for response in raw:
            entries.extend(ics_parser(response, source))
        return entries

    def preprocess(self, entries, source):
        for date_, name in entries:
            first_word = name.split(" ")[0]
            key = first_word if first_word in _TYPE_VALUE_MAP else name
            yield (date_, key)

    transform = ICSTransformer(type_value_map=_TYPE_VALUE_MAP)

    def __init__(self, city: "str | int", street: "str | int"):
        super().__init__(city=str(city), street=str(street))
