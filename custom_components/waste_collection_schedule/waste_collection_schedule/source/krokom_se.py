from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, street_address
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.transformers import JsonTransformer

_PAGE_URL = (
    "https://krokom.se/bo-trafik-och-miljo/avfall-och-atervinning/avfallshamtning.html"
)
_API = "https://krokom.avfallsapp.se/api/widget/nova/v1/next-pickup"

# Public client token of the "När kommer sopbilen?" widget on krokom.se, set as
# a static Authorization header in the widget's bundle-trashcar.js. Not a user
# secret: every visitor's browser sends it. The API answers 500 without it.
_HEADERS = {"Authorization": "Bearer MmOfiFDp4j6xivvYzWpOX55yBWl7zqWGu9j4MyA86cc0691c"}


def _normalise(value: str) -> str:
    return " ".join(value.split()).casefold()


def _street_query(*_, address: str, **__) -> dict:
    """The widget searches by street text; a trailing ", <town>" is not part of it."""
    return {"address": address.split(",")[0].strip()}


def _pick_plant(response, *_, address: str, city: str | None = None, **__) -> str:
    """The search answers ``{"<TOWN>": [{address, zip_city, plant_number}, ...]}``.

    ``plant_number`` is an encrypted token that changes with every search, so it
    is resolved on each fetch rather than stored.
    """
    data = response.json()
    entries = [e for group in data.values() for e in group] if data else []
    street, _sep, town = address.partition(",")
    town = (city or town).strip()
    matches = [
        e
        for e in entries
        if _normalise(e["address"]) == _normalise(street)
        and (not town or _normalise(e["zip_city"]) == _normalise(town))
    ]
    if not matches:
        raise SourceArgumentNotFoundWithSuggestions(
            "address",
            address,
            sorted({f"{e['address']}, {e['zip_city'].title()}" for e in entries}),
        )
    return matches[0]["plant_number"]


@final
class Source(BaseSource):
    TITLE = "Krokom"
    DESCRIPTION = "Waste collection schedule for Krokom Municipality, Sweden."
    URL = _PAGE_URL
    COUNTRY = "se"
    RAISE_ON_EMPTY = True
    SOURCE_CODEOWNERS: ClassVar[list] = ["@bbr111"]

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE]

    TEST_CASES: ClassVar[dict] = {
        "Bergfinkvägen 3, Ås": {"address": "Bergfinkvägen 3", "city": "Ås"},
        "Offerdalsvägen 1": {"address": "Offerdalsvägen 1"},
        "Storgatan 10, Föllinge": {"address": "Storgatan 10, Föllinge"},
    }

    PARAMS = (street_address("address"), city("city", optional=True))

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street and house number as shown by the 'När kommer "
            "sopbilen?' search on the [Krokom waste page]"
            f"({_PAGE_URL}), e.g. `Offerdalsvägen 1`. If the same street name "
            "exists in several towns, also enter the town (e.g. `Föllinge`). "
            "The service only publishes the next collection date."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                f"{_API}/search",
                params=_street_query,
                headers=_HEADERS,
                pick=_pick_plant,
            ),
        ),
        url=f"{_API}/address",
        method="POST",
        params=lambda plant_id, **_: {"plant_id": plant_id},
        headers=_HEADERS,
        raise_for_status=True,
    )

    parse = parsers.JsonParser("bins")

    transform = JsonTransformer(
        date_key="pickup_date",
        type_key="type",
        parse_date=date_parsers.for_format("%Y-%m-%d"),
    )
