"""1Coast - Central Coast (1coast.com.au), Australia.

Demonstrates: a source whose data has two independent shapes depending on
provider state. Getting to the schedule needs an address search (which may
return one exact match, several candidates to disambiguate, or none), then a
GET of the address's collection page. That page always carries a short
"legend" preview (a handful of upcoming collections rendered as HTML,
labelled by full bin name) and a link to a fuller ICS calendar -- but the
linked ICS file 404s in practice about as often as it works (the provider's
own comment: "ics url is sometimes broken"), so the HTML preview is the
usable fallback rather than a rare edge case. No configured retriever
expresses "resolve an address, fetch a page, then conditionally prefer a
second feed over data already on that page", hence a source-defined
retrieve()/parse() pair.

Also fixes a latent bug surfaced by converting this source: the legacy
``_set_address_id`` returned the sole candidate's id when the search found
exactly one match, but that return value was discarded by its caller
(``self._set_address_id()``), leaving the address unresolved and the next
step crashing on an assertion. This version treats a single search result as
the match directly, as the loop below it already does for an exact multi-
candidate match.
"""

from datetime import date, datetime
from typing import ClassVar, final

from bs4 import BeautifulSoup, Tag
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFound,
)
from waste_collection_schedule.service.ICS import ICS
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


def _is_ics_link(tag) -> bool:
    return (
        isinstance(tag, Tag)
        and tag.name == "a"
        and bool(tag.attrs.get("href"))
        and str(tag.attrs["href"]).endswith("ics")
    )


def _fallback_entries(soup: BeautifulSoup) -> "list[tuple[date, str]]":
    """The short HTML "legend" preview, used when the ICS link 404s.

    Iterates each collection block and pairs its bin name with its own
    "Next Collection" date, skipping entries with a blank name (a provider
    quirk that previously crashed the index-based pairing, see #6860).
    """
    entries: list[tuple[date, str]] = []
    for collection in soup.find_all(
        "div", {"class": "booking-list--collection-details"}
    ):
        bin_name_tag = collection.find("span", class_="booking-list--legend-wrapper")
        if bin_name_tag is None:
            continue
        bin_name = bin_name_tag.get_text(strip=True)
        if not bin_name:
            continue
        next_collection = collection.find("span", string="Next Collection")
        if next_collection is None:
            continue
        next_collection = next_collection.find_next_sibling("span").get_text(strip=True)
        # remove the day of the week
        collection_date = next_collection.split(", ", 1)[1]
        entries.append(
            (datetime.strptime(collection_date, "%d-%b-%Y").date(), bin_name)
        )
    return entries


def _ics_entries(text: str) -> "list[tuple[date, str]]":
    """Convert the ICS response, tolerating several VCALENDAR blocks concatenated
    into one response (an observed provider quirk), and dropping duplicates."""
    ics = ICS()
    if text.count("BEGIN:VCALENDAR") == 1:
        collections = ics.convert(text)
    else:
        collections = []
        for calendar in text.split("BEGIN:VCALENDAR")[1:]:
            collections += ics.convert("BEGIN:VCALENDAR" + calendar)

    entries: list = []
    seen: set = set()
    for entry in collections:
        if entry in seen:
            continue
        seen.add(entry)
        entries.append(entry)
    return entries


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

    def retrieve(self, source):
        session = source.session
        address = self.params["address"]

        address_id, address_formatted, collection_params = _resolve_address(
            session, address
        )

        args = {
            "a": "unauth-address-search",
            "address": address_id,
            address_formatted: "",
            "collection[frequency]": collection_params["frequency"],
            "collection[day]": collection_params["day"],
        }
        page = session.get(_COLLECTION_URL, params=args)
        page.raise_for_status()

        soup = BeautifulSoup(page.text, "html.parser")
        ics_link = soup.find(_is_ics_link)
        ics_url = ics_link.get("href") if isinstance(ics_link, Tag) else None
        if not ics_url:
            raise SourceArgumentNotFound(
                "address", address, "could not find a collection calendar link."
            )

        ics_response = session.get(ics_url)
        return page, ics_response

    def parse(self, raw, source):
        page_response, ics_response = raw
        if ics_response.status_code == 404:  # the ICS link is sometimes broken
            return _fallback_entries(BeautifulSoup(page_response.text, "html.parser"))
        return _ics_entries(ics_response.text)

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

    def __init__(self, address: str):
        super().__init__(address=address)
