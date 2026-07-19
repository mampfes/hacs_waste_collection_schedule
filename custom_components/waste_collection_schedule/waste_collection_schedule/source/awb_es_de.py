"""Abfallwirtschaftsbetrieb Esslingen (awb-es.de).

Demonstrates: a page that lists several distinct ICS download links (one per
waste-type calendar) rather than a single combined feed, discovered by
scraping the property overview page for every ``t=ics`` link. No configured
retriever expresses "GET a page, scrape N distinct download links off it,
then fetch every one of those", hence a source-defined ``retrieve``/``parse``
pair. When no ICS link is found, the legacy source's city/street
autocomplete-validation calls are preserved so a bad argument is reported
with suggestions rather than a generic "not found".

"Papiertonne" already resolves against the standard German aliases (to the
same PAPER that "Papiersammlung (Vereine)" is mapped to). "Biotonne",
"Gelbe/r Sack/Tonne" and the two "Restmüll ...-wöchentlich" cadence labels are
mapped explicitly: the Esslingen-specific phrasings would not otherwise
resolve, and mapping "Biotonne" (which would resolve by alias) declares ORGANIC
in the source's WASTE_TYPES rather than leaving it to runtime alias resolution.

The one calendar carries both the 2-weekly and the 4-weekly general-waste
series, and a household follows one of them. The optional ``restmuell_cadence``
argument keeps only the chosen series, so the general-waste sensor shows a
single household's collection dates rather than both cadences merged.
"""

from typing import ClassVar, final

from bs4 import BeautifulSoup
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, dropdown, street
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import IcsParser
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GENERAL_WASTE,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_SEARCH_URL = "https://www.awb-es.de/statics/abfallplus/search.json.php"
_CALENDAR_URL = "https://www.awb-es.de/abfuhr/abfuhrtermine/__Abfuhrtermine.html"

# Esslingen publishes both the 2-weekly and the 4-weekly general-waste
# (Restmüll) series in one calendar; a household is on one of them. When the
# resident picks their cadence the other series is dropped, so the general-waste
# sensor shows only their own collection dates.
_CADENCES = ("2-wöchentlich", "4-wöchentlich")


def _is_unselected_restmuell(summary: str, cadence: str) -> bool:
    """True if ``summary`` is a Restmüll cadence line other than ``cadence``.

    A plain "Restmüll" line (no cadence) and every non-Restmüll type are kept.
    """
    low = summary.lower()
    if "restmüll" not in low:
        return False
    return any(c in low and c != cadence.lower() for c in _CADENCES)


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
        dropdown(
            "restmuell_cadence",
            list(_CADENCES),
            label="Restmüll collection interval",
            optional=True,
        ),
    )

    transform = ICSTransformer(
        type_value_map={
            "biotonne": ORGANIC,
            "gelbe/r sack/tonne": RECYCLABLES,
            "papiersammlung (vereine)": PAPER,
            "restmüll 2-wöchentlich": GENERAL_WASTE,
            "restmüll 4-wöchentlich": GENERAL_WASTE,
        }
    )

    def __init__(
        self,
        city: str,
        street: "str | None" = None,
        restmuell_cadence: "str | None" = None,
    ):
        super().__init__(city=city, street=street, restmuell_cadence=restmuell_cadence)

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
        cadence = source.params.get("restmuell_cadence")
        entries = []
        for response in raw:
            for date, summary in ics_parser(response, source):
                if cadence and _is_unselected_restmuell(summary, cadence):
                    continue
                entries.append((date, summary))
        return entries
