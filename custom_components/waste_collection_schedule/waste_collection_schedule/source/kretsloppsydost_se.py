from typing import Any, ClassVar, final

from waste_collection_schedule import date_parsers, parsers, preprocessors, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.transformers import JsonTransformer

API = "https://api-universal.appbolaget.se/waste/addresses"

# The site's own front end sends these with every request; the API answers 4xx
# without the unit and source headers.
HEADERS = {
    "Module": "universal",
    "Unit": "df5afeaf-0698-4f02-ba64-212aa4f3264c",
    "Source": "kretsloppsydost.se",
    "Timezone": "Europe/Stockholm",
    "App-Version": "3",
}


def _label(item: dict) -> str:
    return f"{item['address']}, {item['city']}"


def _uuid(response, **params) -> str:
    """The uuid of the search hit matching the configured street address."""
    wanted = params["street_address"].casefold()
    items = response.json().get("data") or []
    for item in items:
        if _label(item).casefold() == wanted:
            return item["uuid"]
    street = wanted.split(",")[0].strip()
    matches = [item for item in items if item["address"].casefold() == street]
    if len(matches) == 1:
        return matches[0]["uuid"]
    raise SourceArgumentNotFoundWithSuggestions(
        "street_address", params["street_address"], [_label(item) for item in items]
    )


def _dates(service: dict, source: Any) -> list[str]:
    """Every collection of a service, falling back to its next one."""
    dates = [c["collection_at"] for c in service.get("collections") or []]
    return [d[:10] for d in dates or [service["collection_at"]]]


@final
class Source(BaseSource):
    TITLE = "Kretslopp Sydost"
    DESCRIPTION = (
        "Source for Kretslopp Sydost (Sävsjö, Vetlanda, Nybro, Kalmar, Alstermo)."
    )
    URL = "https://kretsloppsydost.se"
    COUNTRY = "se"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@bbr111"]
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Hägnevägen 1, Sävsjö": {"street_address": "Hägnevägen 1, Sävsjö"},
        "Skolgatan 1, Sävsjö": {"street_address": "Skolgatan 1, Sävsjö"},
    }

    PARAMS = (street_address("street_address"),)

    WASTE_TYPES: ClassVar[list] = [
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
        wt.GENERAL_WASTE,
        wt.OTHER,
        wt.RECYCLABLES,
    ]

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street address and place as the search on "
            "kretsloppsydost.se lists it, for example 'Hägnevägen 1, Sävsjö'."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                f"{API}/search",
                params=lambda street_address, **_: {
                    "query": street_address.split(",")[0].strip()
                },
                headers=HEADERS,
                pick=_uuid,
            ),
        ),
        url=lambda uuid, **_: f"{API}/{uuid}",
        headers=HEADERS,
        raise_for_status=True,
    )
    parse = parsers.JsonParser("data", "properties")
    preprocess = preprocessors.Compose(
        preprocessors.ExplodeList("services"),
        preprocessors.ExplodeList(_dates, into="date"),
    )
    transform = JsonTransformer(
        date_key="date",
        type_key=lambda record: record["code"]["description"],
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        type_value_map={
            "Kärl 1": wt.GENERAL_WASTE,
            "Kärl 2": wt.RECYCLABLES,
            "Hushåll": wt.GENERAL_WASTE,
            "Restavfall": wt.GENERAL_WASTE,
            "Matavfall": wt.FOOD_WASTE,
            "Trädgård": wt.GARDEN_WASTE,
            "Slam2": wt.OTHER,
            "Slam3": wt.OTHER,
        },
        carry_raw_label=True,
    )
