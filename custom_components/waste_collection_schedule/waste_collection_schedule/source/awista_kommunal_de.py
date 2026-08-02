"""AWISTA Kommunal GmbH (Düsseldorf), Germany.

A Next.js single-page app whose address search is a React Server Component
"server action" rather than a documented REST endpoint. The shared
``retrievers.NextActionRetriever`` handles that platform shape: it scrapes the
page's JS chunks for the action id tagged ``searchAddressAction``, posts the
address to it, and fetches the resolved calendar. All this source supplies is
the action's name, its argument, how to read the address id out of the result,
and where the calendar lives.
"""

from typing import Any, ClassVar, final

from waste_collection_schedule import parsers, retrievers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    alternatives,
    house_number,
    street,
    text_field,
)
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GENERAL_WASTE,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

DOMAIN = "https://www.awista-kommunal.de"
BASE_URL = f"{DOMAIN}/abfallkalender"


def _clean_label(label: str) -> str:
    """Strip the service-tier suffix, e.g. "Restmüll (Vollservice)" -> "Restmüll"."""
    return label.split(" (")[0].strip()


def _address(street: "str | None", house_number: "str | None") -> str:
    return f"{street} {house_number}"


def _address_id(result: Any, source: BaseSource) -> str:
    """Read the calendar's address id out of the search action's result."""
    address = _address(source.params.get("street"), source.params.get("house_number"))
    if result is None:
        raise SourceArgumentNotFoundWithSuggestions("street", address, [])

    items = result.get("items") or []
    if not items and result.get("addressIdForQuery"):
        return result["addressIdForQuery"]
    if not items:
        raise SourceArgumentNotFoundWithSuggestions("street", address, [])
    return items[0]["id"]


@final
class Source(BaseSource):
    TITLE = "AWISTA Kommunal GmbH (Düsseldorf)"
    DESCRIPTION = "Source for AWISTA Kommunal GmbH, Düsseldorf, Germany."
    URL = "https://www.awista-kommunal.de/abfallkalender"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True
    SOURCE_CODEOWNERS: ClassVar[list] = ["@Zaunei"]

    TEST_CASES: ClassVar[dict] = {
        "Merkurstraße 45": {"street": "Merkurstraße", "house_number": "45"},
        "Freiligrathstraße 19": {"street": "Freiligrathstraße", "house_number": "19"},
        "Sommersstraße 9 (UUID)": {"uuid": "5d1c4832-fd49-4fa7-a4e3-60dbe116cbc0"},
    }

    PARAMS = (
        alternatives(
            [text_field("uuid", "UUID")],
            [street(field="street"), house_number(field="house_number")],
        ),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Provide 'street' and 'house_number' as you would type them into "
            "the address search at "
            "https://www.awista-kommunal.de/abfallkalender. Alternatively, "
            "search for your address on that page and copy the UUID from the "
            "browser URL bar (e.g. "
            "https://www.awista-kommunal.de/abfallkalender/<uuid>) into "
            "'uuid'; if 'uuid' is given, the address arguments are ignored."
        ),
    }

    retrieve = retrievers.NextActionRetriever(
        page_url=BASE_URL,
        action_name="searchAddressAction",
        arguments=lambda street, house_number, **_: [_address(street, house_number)],
        extract=_address_id,
        schedule_url=lambda key, **_: f"{BASE_URL}/{key}/calendar.ics",
        direct_key=lambda source: source.params.get("uuid"),
    )
    parse = parsers.IcsParser()
    transform = ICSTransformer(
        clean=_clean_label,
        type_value_map={
            "Restmüll": GENERAL_WASTE,
            "Bioabfall": ORGANIC,
            "Papier": PAPER,
            "Wertstofftonne": RECYCLABLES,
        },
    )

    def __init__(
        self,
        street: "str | None" = None,
        house_number: "str | None" = None,
        uuid: "str | None" = None,
    ):
        super().__init__(street=street, house_number=house_number, uuid=uuid)
