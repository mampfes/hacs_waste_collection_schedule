"""Abfallwirtschaftsbetrieb Esslingen (awb-es.de).

Demonstrates: a page that lists several distinct ICS download links (one per
waste-type calendar) rather than a single combined feed, discovered by
scraping the property overview page for every ``t=ics`` link. No configured
retriever expresses "GET a page, scrape N distinct download links off it,
then fetch every one of those", hence a source-defined ``retrieve``/``parse``
pair. When no ICS link is found, the legacy source's city/street
autocomplete-validation calls are preserved so a bad argument is reported
with suggestions rather than a generic "not found".

"Biotonne" and "Papiertonne" already resolve against the standard German
aliases. "Gelbe/r Sack/Tonne", "Papiersammlung (Vereine)" and the two
"Restmüll ...-wöchentlich" cadence labels are Esslingen-specific phrasings
mapped explicitly.
"""

from typing import ClassVar, final

from bs4 import BeautifulSoup
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, street
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import IcsParser
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import GENERAL_WASTE, PAPER, RECYCLABLES

_SEARCH_URL = "https://www.awb-es.de/statics/abfallplus/search.json.php"
_CALENDAR_URL = "https://www.awb-es.de/abfuhr/abfuhrtermine/__Abfuhrtermine.html"


def _suggestions(session, search: str, parent: str, kind: str) -> list[str]:
    r = session.post(
        _SEARCH_URL,
        data={"search": search, "parent": parent, "kind": kind},
    )
    r.raise_for_status()
    return [entry["value"] for entry in r.json()["suggestions"]]


def _validate(session, value: str, parent: str, kind: str, field: str) -> None:
    suggestions = _suggestions(session, value, parent, kind)
    for suggestion in suggestions:
        if suggestion.lower() == value.lower():
            return
    raise SourceArgumentNotFoundWithSuggestions(field, value, suggestions)


@final
class Source(BaseSource):
    TITLE = "Abfallwirtschaftsbetrieb Esslingen"
    DESCRIPTION = "Source for AWB Esslingen, Germany"
    URL = "https://www.awb-es.de"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Aichwald": {"city": "Aichwald", "street": "Alte Dorfstraße Alle Hausnummern"},
        "Kohlberg": {"city": "Kohlberg", "street": "alle Straßen"},
    }

    PARAMS = (
        city(field="city"),
        street(field="street", optional=True),
    )

    transform = ICSTransformer(
        type_value_map={
            "gelbe/r sack/tonne": RECYCLABLES,
            "papiersammlung (vereine)": PAPER,
            "restmüll 2-wöchentlich": GENERAL_WASTE,
            "restmüll 4-wöchentlich": GENERAL_WASTE,
        }
    )

    def __init__(self, city: str, street: "str | None" = None):
        super().__init__(city=city, street=street)

    def retrieve(self, source):
        session = source.session
        city_value = source.params["city"]
        street_value = source.params.get("street")

        r = session.get(
            _CALENDAR_URL,
            params={"city": city_value, "street": street_value, "direct": "true"},
        )
        r.raise_for_status()

        soup = BeautifulSoup(r.text, features="html.parser")
        ics_urls: list[str] = []
        for download in soup.find_all("a", href=True):
            href = str(download["href"])
            # The website lists the same url multiple times; keep it once.
            if "t=ics" in href and href not in ics_urls:
                ics_urls.append(href)

        if not ics_urls:
            _validate(session, city_value, "", "removaldate.city", "city")
            if street_value:
                _validate(
                    session, street_value, city_value, "removaldate.street", "street"
                )
            raise SourceArgumentNotFoundWithSuggestions("street", street_value, [])

        responses = []
        for ics_url in ics_urls:
            resp = session.get(ics_url)
            resp.raise_for_status()
            responses.append(resp)
        return responses

    def parse(self, raw, source):
        ics_parser = IcsParser()
        entries = []
        for response in raw:
            entries.extend(ics_parser(response, source))
        return entries
