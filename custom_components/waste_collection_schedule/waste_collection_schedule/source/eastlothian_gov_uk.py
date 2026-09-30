from typing import ClassVar, final

from bs4 import BeautifulSoup
from waste_collection_schedule import parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, street_address
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.retrievers import (
    Lookup,
    LookupChainRetriever,
    Request,
)
from waste_collection_schedule.transformers import ICSTransformer

BASE_URL = "https://www.eastlothian.gov.uk"
SCHEDULE_URL = f"{BASE_URL}/waste-collection-schedule"


def _normalize(s: str) -> str:
    return " ".join(s.lower().replace(",", " ").split())


def _address_match(wanted: str, option_text: str) -> bool:
    g_norm = _normalize(wanted)
    o_norm = _normalize(option_text)
    if g_norm in o_norm:
        return True
    # The option may end in the postcode: compare without it.
    o_parts = o_norm.split()
    return len(o_parts) > 3 and g_norm == " ".join(o_parts[:-2])


def _form_build_id(response, *keys, **_) -> str:
    """The Drupal form token the postcode form has to be posted back with."""
    soup = BeautifulSoup(response.text, "html.parser")
    field = soup.find("input", {"name": "form_build_id"})
    value = field.get("value") if field is not None else None
    if not isinstance(value, str):
        raise ValueError("Could not find form_build_id on schedule page")
    return value


def _pick_uprn(response, *keys, postcode, address, **_) -> str:
    """The postcode answers a dropdown of addresses, valued by UPRN."""
    soup = BeautifulSoup(response.text, "html.parser")
    select = soup.find("select", {"name": "uprn"})
    if select is None:
        raise SourceArgumentNotFound(
            "postcode", postcode, "No address options found for postcode"
        )
    options = select.find_all("option")
    for option in options:
        if _address_match(address, option.text):
            return str(option["value"])
    raise SourceArgumentNotFoundWithSuggestions(
        "address",
        address,
        [opt.text for opt in options if opt.get("value")],
    )


@final
class Source(BaseSource):
    TITLE = "East Lothian"
    DESCRIPTION = "Source for East Lothian waste collection."
    URL = "https://www.eastlothian.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.FOOD_WASTE,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "EH21 8GU 4 Laing Loan, Wallyford": {
            "postcode": "EH21 8GU",
            "address": "4 Laing Loan, Wallyford",
        },
        "EH41 4LN Peterhouse, Morham, Haddington": {
            "postcode": "EH41 4LN",
            "address": "Peterhouse, Morham, Haddington",
        },
        "1 Colliers Row Wallyford": {
            "postcode": "EH21 8GX",
            "address": "1 Colliers Row, Wallyford",
        },
    }

    PARAMS = (postcode(), street_address("address"))

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your postcode and your address as it appears in the address "
            "dropdown on https://www.eastlothian.gov.uk/waste-collection-schedule "
            "after searching for your postcode, e.g. '4 Laing Loan, Wallyford'. "
            "The postcode at the end of the entry may be left out."
        ),
    }

    retrieve = LookupChainRetriever(
        steps=(
            Lookup(
                Request(
                    SCHEDULE_URL,
                    method="POST",
                    data=lambda form_build_id, postcode, **_: {
                        "postcode": postcode.strip(),
                        "form_build_id": form_build_id,
                        "form_id": "localgov_waste_collection_postcode_form",
                        "op": "Find",
                    },
                    before=(Lookup(SCHEDULE_URL, pick=_form_build_id),),
                ),
                pick=_pick_uprn,
            ),
        ),
        url=lambda uprn, **_: f"{SCHEDULE_URL}/download/{uprn}",
        raise_for_status=True,
    )
    # "Recycling lidded bins for Food waste and recycling": the waste is what
    # follows " for ", and a combined round names two of them. The calendar also
    # lists a "Download your bin collection calendar" entry, which is no
    # collection.
    parse = parsers.IcsParser(regex=r".+? for (.+)", split_at=r"\s+and\s+")
    transform = ICSTransformer(
        type_value_map={
            "Non recyclable waste": wt.GENERAL_WASTE,
            "Food waste": wt.FOOD_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Garden waste": wt.GARDEN_WASTE,
            "Download your bin collection calendar": None,
        },
    )
