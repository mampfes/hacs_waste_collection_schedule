"""AWG Wuppertal (awg-wuppertal.de).

Demonstrates: a two-stage scrape (an autocomplete street lookup, tolerating a
truncated retry when the term has no match, then a form scrape/POST that
reveals per-waste-type "als iCal" download links) that no configured
retriever expresses, followed by an ICS fetch per link. No dedicated
retriever exists for this shape yet, so the whole flow is a source-defined
retrieve()/parse() pair; the split-at-"-" title trim (defensive against a
suffixed ICS summary) becomes a preprocess step ahead of a plain
ICSTransformer.
"""

from typing import ClassVar, final

from bs4 import BeautifulSoup
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import IcsParser
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    BULKY_WASTE,
    GENERAL_WASTE,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_BASE_URL = "https://awg-wuppertal.de"
_API_URL = f"{_BASE_URL}/privatkunden/abfallkalender.html"


def _is_ical_link_text(text: "str | None") -> bool:
    return text is not None and text.lower().strip().endswith("als ical")


def _search_street(session, term: str) -> list[str]:
    r = session.get(
        _API_URL, params={"eID": "wastecalendar_autocomplete", "term": term}
    )
    r.raise_for_status()
    data = r.json()
    if not data and len(term) > 3:
        return _search_street(session, term[:-1])
    return data


def _confirm_street(session, street_name: str) -> str:
    candidates = _search_street(session, street_name)
    for candidate in candidates:
        if street_name.lower().replace(" ", "") == candidate.lower().replace(" ", ""):
            return candidate
    raise SourceArgumentNotFoundWithSuggestions("street", street_name, candidates)


@final
class Source(BaseSource):
    TITLE = "AWG Wuppertal"
    DESCRIPTION = "Source for AWG Wuppertal."
    URL = _BASE_URL
    COUNTRY = "de"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {"Hauptstraße": {"street": "Hauptstraße"}}

    PARAMS = (street(field="street"),)

    def retrieve(self, source):
        session = source.session
        confirmed_street = _confirm_street(session, source.params["street"])

        page = session.get(_API_URL)
        page.raise_for_status()
        soup = BeautifulSoup(page.text, "html.parser")
        form = soup.select_one("form[name='demand']")
        if form is None:
            raise ValueError("Could not find form element on initial page")

        action = form["action"]
        if not isinstance(action, str):
            raise ValueError("Could not find form action")
        if action.startswith("/"):
            action = _BASE_URL + action

        data = {}
        for input_tag in form.select("input"):
            if "name" not in input_tag.attrs or "value" not in input_tag.attrs:
                continue
            data[input_tag["name"]] = input_tag["value"]
        data["tx_bwwastecalendar_pi1[demand][streetname]"] = confirmed_street

        result = session.post(action, data=data)
        soup = BeautifulSoup(result.text, "html.parser")

        ical_links = soup.find_all("a", string=_is_ical_link_text)
        responses = []
        for link in ical_links:
            href = link["href"]
            if href.startswith("/"):
                href = _BASE_URL + href
            r = session.get(href)
            r.raise_for_status()
            responses.append(r)
        return responses

    def parse(self, raw, source):
        ics_parser = IcsParser(split_at="/", regex=r"(.*)/ !!! Terminverschiebung !!!")
        entries = []
        for response in raw:
            entries.extend(ics_parser(response, source))
        return entries

    def preprocess(self, entries, source):
        for date_, name in entries:
            yield (date_, name.split("-")[0].strip())

    transform = ICSTransformer(
        type_value_map={
            "Restmüll": GENERAL_WASTE,
            "Gelb": RECYCLABLES,
            "Bio": ORGANIC,
            "Papier": PAPER,
            "Sperrmüll": BULKY_WASTE,
        }
    )

    def __init__(self, street: str):
        super().__init__(street=street)
