from typing import ClassVar, final

from bs4 import BeautifulSoup
from waste_collection_schedule import parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.preprocessors import TextDatedBlocks
from waste_collection_schedule.retrievers import Lookup, LookupChainRetriever
from waste_collection_schedule.transformers import ICSTransformer

# The public page https://vmab.se/privat/vmabs-tomningskalender embeds the
# calendar service at https://cal.vmab.se/. The address is searched first; the
# id in the list of hits is what the calendar request needs. The schedule comes
# back injected into a script tag as the events of a browsable calendar:
#
#   { title: 'Max 1, Fyrfackskärl', start: '2026-01-07' },
#
# Houses have two "fyrfack" (four-slot) bins, Max 1 and Max 2, each holding
# several waste types, so neither has a single canonical type. Apartment
# buildings and municipal properties are not covered by this service.

API = "https://cal.vmab.se"

_HEADERS = {
    "Accept-Encoding": "identity",
    "Accept": "*/*",
    "Accept-Language": "sv-SE,sv;q=0.9",
}


def _split(street_address: str) -> tuple[str, str]:
    """ "Street 1, City" -> ("Street 1", "City")."""
    street, _, city = street_address.partition(",")
    return street.strip(), city.strip()


def _pickup_id(response, street_address: str, **_) -> str:
    """The id of the search hit matching both street and city."""
    street, city = _split(street_address)
    hits = BeautifulSoup(response.text, "html.parser").select("li[id]")
    for hit in hits:
        street_el = hit.select_one("span.address")
        city_el = hit.select_one("span.city")
        if (
            street_el is not None
            and city_el is not None
            and street_el.get_text() == street
            and city_el.get_text() == city
        ):
            return str(hit["id"])
    raise SourceArgumentNotFound("street_address", street_address)


@final
class Source(BaseSource):
    TITLE = "VMAB"
    DESCRIPTION = "Source for Västblekinge Miljö AB waste collection."
    URL = "https://vmab.se"
    COUNTRY = "se"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [wt.OTHER]

    TEST_CASES: ClassVar[dict] = {
        "Home": {"street_address": "Rosenborgsvägen 35, Karlshamn"},
    }

    PARAMS = (street_address("street_address"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street address and city, separated by a comma, exactly "
            "as they appear when you search for your address on "
            "https://vmab.se/privat/vmabs-tomningskalender, "
            "e.g. `Rosenborgsvägen 35, Karlshamn`. Only houses with the "
            "four-slot bins (Max 1 and Max 2) are covered, not apartment "
            "buildings."
        ),
    }

    retrieve = LookupChainRetriever(
        steps=(
            Lookup(
                f"{API}/search_suggestions.php",
                method="POST",
                data=lambda street_address, **_: {
                    "search_address": _split(street_address)[0]
                },
                headers=_HEADERS,
                pick=_pickup_id,
            ),
        ),
        url=f"{API}/get_data.php",
        method="POST",
        data=lambda pickup_id, street_address, **_: {
            "chosen_address": " ".join(_split(street_address)),
            "chosen_address_pickupid": pickup_id,
        },
        headers=_HEADERS,
    )
    parse = parsers.TextParser()
    # Only the bin name ("Max 1") is kept, as before; a template example in a
    # comment of the page has a time in its date and does not match.
    preprocess = TextDatedBlocks(
        block_pattern=(
            r"title:\s*'(?P<labels>[^',]*)[^']*',\s*"
            r"start:\s*'(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})'"
        ),
    )
    # Max 1: food, burnable, coloured glass, newspapers; Max 2: plastic, paper
    # packaging, clear glass, metal. Each mixes several types.
    transform = ICSTransformer(
        type_value_map={"Max 1": wt.OTHER, "Max 2": wt.OTHER},
        carry_raw_label=True,
    )
