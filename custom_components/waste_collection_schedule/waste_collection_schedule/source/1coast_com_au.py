"""1Coast - Central Coast (1coast.com.au), Australia.

Composes: :class:`~waste_collection_schedule.retrievers.LookupChainRetriever`
(resolve the address, then GET its collection page) as the ``prepare`` step of
a :class:`~waste_collection_schedule.retrievers.FallbackRetriever`, read by
:class:`~waste_collection_schedule.parsers.FirstNonEmptyBranch`.

The collection page always carries a short "legend" preview (a handful of
upcoming collections rendered as HTML, labelled by full bin name) and a link to
a fuller ICS calendar, but the linked ICS file 404s in practice about as often
as it works (the provider's own comment: "ics url is sometimes broken"). So the
ICS is one branch and the preview already in hand is the other, reached with
:func:`~waste_collection_schedule.retrievers.reuse_prepared` rather than a
second request.

Also fixes a latent bug surfaced by converting this source: the legacy
``_set_address_id`` returned the sole candidate's id when the search found
exactly one match, but that return value was discarded by its caller
(``self._set_address_id()``), leaving the address unresolved and the next
step crashing on an assertion. This version treats a single search result as
the match directly, as the loop below it already does for an exact multi-
candidate match.
"""

from typing import Any, ClassVar, final

from waste_collection_schedule import date_parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFound,
)
from waste_collection_schedule.parsers import (
    FirstNonEmptyBranch,
    HtmlLabelledDates,
    IcsParser,
)
from waste_collection_schedule.retrievers import (
    Branch,
    FallbackRetriever,
    LookupChainRetriever,
    follow_link,
    reuse_prepared,
)
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GARDEN_WASTE,
    GENERAL_WASTE,
    GLASS,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_SEARCH_URL = "https://1coast.com.au/ajax.php"
_COLLECTION_URL = (
    "https://1coast.com.au/bin-collection/bin-collection-day-address-details"
)


def _normalise(address: str) -> str:
    return address.lower().replace(" ", "").replace(",", "").replace(".", "")


def _resolve_address(session, address: str) -> "tuple[str, str, dict]":
    """Resolve an address to (address_id, formatted_address, collection_params)."""
    r = session.get(_SEARCH_URL, params={"a": "search", "s": address})
    r.raise_for_status()
    data = r.json()

    if not data:
        raise SourceArgumentNotFound("address", address)

    if len(data) == 1:
        addr = data[0]
        return addr["id"], ",".join(addr["name"]), addr["collection"]

    address_names = []
    for addr in data:
        addr_name = " ".join(addr["name"])
        address_names.append(addr_name)
        if _normalise(addr_name) == _normalise(address):
            return addr["id"], ",".join(addr["name"]), addr["collection"]

    raise SourceArgAmbiguousWithSuggestions("address", address, address_names)


def _resolve_address_step(source, keys: tuple) -> "tuple[str, str, dict]":
    """The LookupChainRetriever step: the address, as the page GET needs it."""
    return _resolve_address(source.session, source.params["address"])


def _collection_page_params(resolved: tuple, **params: Any) -> dict:
    """The collection page's query string.

    The formatted address is sent as a bare *key* with an empty value, which is
    the provider's own convention, not a mistake here.
    """
    address_id, address_formatted, collection = resolved
    return {
        "a": "unauth-address-search",
        "address": address_id,
        address_formatted: "",
        "collection[frequency]": collection["frequency"],
        "collection[day]": collection["day"],
    }


_collection_page = LookupChainRetriever(
    steps=(_resolve_address_step,),
    url=_COLLECTION_URL,
    params=_collection_page_params,
    raise_for_status=True,
)


@final
class Source(BaseSource):
    TITLE = "1Coast - Central Coast"
    DESCRIPTION = "Source for 1Coast - Central Coast."
    URL = "https://1coast.com.au/"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "RHODIN DR, LONG JETTY, CENTRAL COAST 2261": {
            "address": "9 RHODIN DR, LONG JETTY CENTRAL COAST 2261"
        },
        "GERMAINE AVE, BATEAU BAY, CENTRAL COAST 2261": {
            "address": "12 GERMAINE AVE BATEAU BAY CENTRAL COAST 2261"
        },
        "56 EVERGLADES CR, WOY WOY. CENTRAL COAST 2256": {
            "address": "56 EVERGLADES CR, WOY WOY. CENTRAL COAST 2256"
        },
    }

    PARAMS = (text_field("address", "Address"),)

    retrieve = FallbackRetriever(
        Branch("ics", follow_link(r"ics$")),
        Branch("page", reuse_prepared),
        prepare=_collection_page,
    )

    parse = FirstNonEmptyBranch(
        {
            # The provider sometimes glues several VCALENDAR blocks into one
            # response; concatenated reads all of them and drops the repeats
            # across the seam.
            "ics": IcsParser(concatenated=True),
            # The legend preview: one card per round, each with its own name and
            # its own "Next Collection" caption. The pattern drops the weekday
            # the date is prefixed with ("Fri, 17-Jul-2026").
            "page": HtmlLabelledDates(
                "div.booking-list--collection-details",
                label="span.booking-list--legend-wrapper",
                date_after="Next Collection",
                date_pattern=r", (.+)$",
                parse_date=date_parsers.for_format("%d-%b-%Y"),
            ),
        }
    )

    transform = ICSTransformer(
        type_value_map={
            "Trash": GENERAL_WASTE,
            "Glass": GLASS,
            "Bio": ORGANIC,
            "Paper": PAPER,
            "Recycle": RECYCLABLES,
            "240L Yellow Lid Recycle Bin": RECYCLABLES,
            "140L Red Lid General Waste Bin": GENERAL_WASTE,
            "240L Green Lid Garden Vegetation Bin": GARDEN_WASTE,
        }
    )
