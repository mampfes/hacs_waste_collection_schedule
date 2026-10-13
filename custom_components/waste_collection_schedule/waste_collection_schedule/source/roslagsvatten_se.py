import re
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import dropdown, street_address
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.transformers import RowTransformer

API_URL = "https://roslagsvatten.se/schedule"
HEADERS = {"X-Requested-With": "XMLHttpRequest", "Accept": "application/json"}


def _building_id(response, *_keys, street_address: str = "", **_params) -> str:
    """The building id of the first address the search matched."""
    results = response.json()
    html = results[0].get("data", "") if results else ""
    match = re.search(r'data-bid="(\d+)"', html)
    if not match:
        raise SourceArgumentNotFound("street_address", street_address)
    return match.group(1)


@final
class Source(BaseSource):
    TITLE = "Roslagsvatten"
    DESCRIPTION = (
        "Source for Roslagsvatten waste collection (Österåker, Vaxholm and Ekerö)."
    )
    URL = "https://roslagsvatten.se"
    COUNTRY = "se"
    RAISE_ON_EMPTY = True

    HOWTO: ClassVar[dict] = {
        "en": "Enter the address as the Roslagsvatten schedule search writes it, street and number followed by the locality, e.g. `Andromedavägen 1, Åkersberga`, and pick your municipality.",
    }

    WASTE_TYPES: ClassVar[list] = [wt.FOOD_WASTE, wt.GENERAL_WASTE, wt.OTHER]

    TEST_CASES: ClassVar[dict] = {
        "Österaker Test": {
            "street_address": "Andromedavägen 1, Åkersberga",
            "municipality": "osteraker",
        },
        "Vaxholm Test": {
            "street_address": "Hamngatan 1, Vaxholm",
            "municipality": "vaxholm",
        },
        "Ekerö Test": {
            "street_address": "Ekerö Kyrkväg 1, Ekerö",
            "municipality": "ekero",
        },
    }

    PARAMS = (
        street_address("street_address"),
        dropdown("municipality", ["osteraker", "vaxholm", "ekero"]),
    )

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                f"{API_URL}/search",
                method="POST",
                json=lambda street_address, municipality, **_: {
                    "searchText": street_address,
                    "municipality": municipality,
                },
                headers=HEADERS,
                pick=_building_id,
            ),
        ),
        url=f"{API_URL}/fetch",
        method="POST",
        json=lambda building_id, municipality, **_: {
            "buildingId": building_id,
            "municipality": municipality,
        },
        headers=HEADERS,
    )

    parse = parsers.HtmlLabelledDates(
        "div.waste-schedule-inner",
        label="h3",
        date="p:nth-of-type(2)",
        date_pattern=r"Nästa hämtning:\s*(\S.*)",
        from_json_key=(0, "data"),
    )

    transform = RowTransformer(
        parse_date=date_parsers.first_of(
            date_parsers.for_format("%Y-%m-%d"), date_parsers.iso_week()
        ),
        type_value_map={
            "Restavfall": wt.GENERAL_WASTE,
            "Matavfall": wt.FOOD_WASTE,
            "Rest- matavfall": wt.FOOD_WASTE,
            # Septic/sludge emptying has no canonical type.
            "Slam": wt.OTHER,
        },
        carry_raw_label=True,
    )
