import datetime
from typing import ClassVar, final

from waste_collection_schedule import parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, text_field
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.transformers import JsonTransformer

API_URL = "https://afvalstoffendienst.nl"


def _compact(value: object) -> str:
    return str(value or "").replace(" ", "").upper()


def _bag_id(response, *_keys, addition=None, **_params) -> str:
    """The BAG id of the address; the first one when the addition matches none."""
    addresses = response.json()
    if not addresses:
        raise SourceArgumentNotFound(
            "postcode", "Address is not within service area. Please check."
        )
    if addition:
        wanted = addition.lower()
        for address in addresses:
            if wanted in (
                (address.get("huisletter") or "").lower(),
                (address.get("toevoeging") or "").lower(),
            ):
                return address["bagid"]
    return addresses[0]["bagid"]


def _targets(_source, _bag_id) -> list:
    """The waste stream names first, then this and next year's calendar."""
    year = datetime.date.today().year
    return ["afvalstromen", year, year + 1]


@final
class Source(BaseSource):
    TITLE = "Afvalstoffendienst.nl"
    DESCRIPTION = (
        "Source for 's Hertogenbosch, Heusden, Vught, Oisterwijk, Altena, Bernheze"
    )
    URL = "https://www.afvalstoffendienst.nl/"
    COUNTRY = "nl"

    # An unknown address answers an empty list; an address without
    # collections would otherwise look like an empty calendar.
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Oisterwijk, 5061AA 1": {
            "postcode": "5061AA",
            "house_number": "1",
        },
        "Heusden, 5256EJ, 32": {
            "postcode": "5256EJ",
            "house_number": "32",
        },
        "Vught, 5262TH 23": {
            "postcode": "5262TH",
            "house_number": "23",
        },
        "Cromvoirt 5266AD 31": {
            "postcode": "5266AH",
            "house_number": "102",
            "addition": "A",
        },
        "Rosmalen 5241AV 18": {
            "postcode": "5241AV",
            "house_number": "18",
        },
        "Heeswijk-Dinther 5473AB 13": {
            "postcode": "5473 AB",
            "house_number": "13",
        },
    }

    PARAMS = (
        postcode(house_field="house_number"),
        text_field("addition", "House Number Addition", optional=True),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter the postcode, house number and (optional) addition of your "
            "home address."
        ),
    }

    WASTE_TYPES: ClassVar[list] = [
        wt.GARDEN_WASTE,
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    retrieve = retrievers.FanOutRetriever(
        prepare=retrievers.Lookup(
            lambda postcode=None, house_number=None, **_: (
                f"{API_URL}/adressen/{_compact(postcode)}:{house_number}"
            ),
            pick=_bag_id,
        ),
        targets=_targets,
        fetch=retrievers.Request(
            lambda target, bag_id, **_: (
                f"{API_URL}/rest/adressen/{bag_id}/afvalstromen"
                if target == "afvalstromen"
                else f"{API_URL}/rest/adressen/{bag_id}/kalender/{target}"
            )
        ),
    )

    parse = parsers.JsonLookupJoin(
        key="afvalstroom_id", value_key="title", into="title", default="Afval"
    )

    transform = JsonTransformer(
        date_key="ophaaldatum",
        type_key="title",
        type_value_map={
            "Restafval": wt.GENERAL_WASTE,
            "Papier en karton": wt.PAPER,
            "Groente, Fruit en Tuinafval en Etensresten": wt.ORGANIC,
            "Plastic en metalen verpakkingen en drinkpakken": wt.RECYCLABLES,
            "Plastic, Metalen verpakkingen en Drinkpakken": wt.RECYCLABLES,
            "Plastic, metalen verpakkingen en drinkpakken": wt.RECYCLABLES,
            "Kerstbomen": wt.GARDEN_WASTE,
        },
    )
