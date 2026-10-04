import json
import re
from datetime import date
from typing import ClassVar, final

from waste_collection_schedule import parsers, recurrence, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.preprocessors import (
    ArgumentLookup,
    Compose,
    RecurrenceExpander,
    Schedule,
)
from waste_collection_schedule.transformers import ICSTransformer

_PAGE_URL = "https://www.ostersund.se/bygga-bo-klimat-och-miljo/avfall-och-atervinning/nar-kommer-sopbilen.html"

# Matches every `AppRegistry.registerInitialState('<portletId>', {...});`
# call embedded in the server-rendered page. The waste search widget's
# portlet id is treated as an implementation detail and not hardcoded here;
# instead the correct payload is identified by the presence of the
# "result"/"query" keys, which is more resilient to a future re-deploy of
# the widget under a different portlet id.
_STATE_RE = re.compile(r"registerInitialState\('[^']+',(\{.*?\})\);", re.DOTALL)

_LABEL = "Hushållsavfall"

# Household waste (residual + food waste) is collected together on a fixed
# fortnightly cadence for single-family homes ("Sopbilen hämtar ditt avfall
# var fjortonde dag"). The page only exposes the next pickup date, so future
# occurrences are extrapolated at a 14-day interval.
_NUMBER_OF_COLLECTIONS = 26


def _addresses(text, source=None) -> dict:
    """The search results of the page, keyed by address."""
    for match in _STATE_RE.finditer(text):
        try:
            payload = json.loads(match.group(1))
        except json.JSONDecodeError:
            continue
        if "result" in payload and "query" in payload:
            return {
                f"{item['address']}".title(): item
                for item in payload["result"]
                if item.get("address")
            }
    raise SourceArgumentNotFound(
        "address",
        source.params.get("address") if source is not None else None,
        message_addition="the schedule page could not be parsed, it may have changed format.",
    )


def _describe(record, source):
    """One fortnightly series from the next pickup date; none if it is not published."""
    next_date = (record.get("nextPickup") or {}).get("nextPickupDate")
    if next_date:
        yield Schedule(
            _LABEL,
            date.fromisoformat(next_date),
            recurrence.FORTNIGHTLY,
            _NUMBER_OF_COLLECTIONS,
        )


@final
class Source(BaseSource):
    TITLE = "Östersunds kommun"
    DESCRIPTION = "Source for Östersunds kommun waste collection schedule, Sweden."
    URL = "https://www.ostersund.se"
    COUNTRY = "se"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE]

    TEST_CASES: ClassVar[dict] = {
        "Återgången 1": {"address": "Återgången 1"},
        "Strandgatan 13": {"address": "Strandgatan 13"},
    }

    PARAMS = (street_address("address"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Go to the collection search on "
            f"[ostersund.se]({_PAGE_URL}), search for your address and copy the "
            "street name and house number exactly as shown in the results list, "
            "e.g. 'Återgången 1'. Only single-family homes in Östersunds kommun "
            "are covered; apartment buildings and businesses are not listed."
        ),
        "de": (
            "Öffnen Sie die Abfuhrsuche auf "
            f"[ostersund.se]({_PAGE_URL}), suchen Sie Ihre Adresse und übernehmen "
            "Sie Straßenname und Hausnummer genau wie in der Ergebnisliste "
            "angezeigt, z. B. 'Återgången 1'. Es werden nur Einfamilienhäuser in "
            "der Gemeinde Östersund unterstützt; Mehrfamilienhäuser und Firmen "
            "sind nicht gelistet."
        ),
    }

    retrieve = retrievers.HttpGetRetriever(
        url=_PAGE_URL,
        params=lambda address, **_: {"query": address},
    )

    parse = parsers.TextParser()

    preprocess = Compose(
        ArgumentLookup(_addresses, argument="address"),
        RecurrenceExpander(_describe),
    )

    transform = ICSTransformer(type_value_map={_LABEL: wt.GENERAL_WASTE})
