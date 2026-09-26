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
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, dropdown, street
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.preprocessors import RowFilter
from waste_collection_schedule.retrievers import Lookup
from waste_collection_schedule.transformers import ICSTransformer

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


def _ics_links(response, **_) -> list[str]:
    """Every ICS download the property page lists, each once."""
    soup = BeautifulSoup(response.text, features="html.parser")
    ics_urls: list[str] = []
    for download in soup.find_all("a", href=True):
        href = str(download["href"])
        # The website lists the same url multiple times; keep it once.
        if "t=ics" in href and href not in ics_urls:
            ics_urls.append(href)
    return ics_urls


def _validate(argument: str, kind: str, parent) -> Lookup:
    """Ask the site's autocomplete whether it knows the configured value.

    Only asked when the property page listed no download at all, which is
    almost always a misspelt city or street: the error then carries the values
    the site does know.
    """

    def pick(response, *keys, **params) -> None:
        value = params[argument]
        suggestions = [entry["value"] for entry in response.json()["suggestions"]]
        for suggestion in suggestions:
            if suggestion.lower() == value.lower():
                return
        raise SourceArgumentNotFoundWithSuggestions(argument, value, suggestions)

    return Lookup(
        _SEARCH_URL,
        method="POST",
        data=lambda *keys, **params: {
            "search": params[argument],
            "parent": parent(**params),
            "kind": kind,
        },
        when=lambda links, *_, **params: not links and bool(params.get(argument)),
        pick=pick,
    )


def _ics_urls(source, context: tuple) -> list[str]:
    """The fan-out's targets: the downloads, once the address is known good."""
    links = context[0]
    if not links:
        raise SourceArgumentNotFoundWithSuggestions(
            "street", source.params.get("street"), []
        )
    return links


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
        prepare=retrievers.Chain(
            Lookup(
                _CALENDAR_URL,
                params=lambda city, street=None, **_: {
                    "city": city,
                    "street": street,
                    "direct": "true",
                },
                pick=_ics_links,
            ),
            _validate("city", "removaldate.city", parent=lambda **_: ""),
            _validate("street", "removaldate.street", parent=lambda city, **_: city),
        ),
        targets=_ics_urls,
        fetch=retrievers.Request(lambda url, context, **_: url),
    )
    parse = parsers.EachResponse(parsers.IcsParser())
    preprocess = RowFilter(_keep_chosen_cadence)

    transform = ICSTransformer(
        type_value_map={
            "biotonne": wt.ORGANIC,
            "gelbe/r sack/tonne": wt.RECYCLABLES,
            "papiersammlung (vereine)": wt.PAPER,
            "restmüll 2-wöchentlich": wt.GENERAL_WASTE,
            "restmüll 4-wöchentlich": wt.GENERAL_WASTE,
        }
    )
