"""Abfallwirtschaftsbetrieb Esslingen (awb-es.de).

Composes: :class:`~waste_collection_schedule.retrievers.FanOutRetriever`. The
council's own page lists several distinct ICS download links (one per
waste-type calendar) rather than a single combined feed, so listing them by
scraping that page for every ``t=ics`` link is the fan-out's ``targets`` step
and each link is one fetched response. When no ICS link is found, the legacy
source's city/street autocomplete-validation calls are preserved so a bad
argument is reported with suggestions rather than a generic "not found".

The links themselves point at ``api.abfall.io``, but this is not the
:mod:`~waste_collection_schedule.service.AbfallIO` platform's server-side
wizard: the council embeds a ready-made customer key and calendar id in a
plain export URL, so there is no cascade to walk and nothing for
``AbfallIoRetriever`` to do. The ``statics/abfallplus`` autocomplete on the
council's own host is likewise its own small endpoint, not the app platform in
:mod:`~waste_collection_schedule.service.AppAbfallplusDe`.

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
from waste_collection_schedule import parsers, retrievers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, dropdown, street
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.preprocessors import RowFilter
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


def _keep_chosen_cadence(record, source) -> bool:
    """Drop the general-waste series the resident did not choose."""
    cadence = source.params.get("restmuell_cadence") if source is not None else None
    if not cadence:
        return True
    return not _is_unselected_restmuell(record[1], cadence)


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


def _ics_urls(source, _context=None) -> list[str]:
    """The fan-out's targets: every ICS download the property page lists.

    An address that resolves to no download at all is almost always a misspelt
    city or street, so the site's own autocomplete is asked which values it
    does know before the error is raised.
    """
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
            _validate(session, street_value, city_value, "removaldate.street", "street")
        raise SourceArgumentNotFoundWithSuggestions("street", street_value, [])

    return ics_urls


def _download_feed(source, url: str, _context=None):
    r = source.session.get(url)
    r.raise_for_status()
    return r


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

    retrieve = retrievers.FanOutRetriever(
        targets=_ics_urls,
        fetch=_download_feed,
    )
    parse = parsers.EachResponse(parsers.IcsParser())
    preprocess = RowFilter(_keep_chosen_cadence)

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
