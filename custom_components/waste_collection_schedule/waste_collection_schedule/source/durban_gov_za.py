"""eThekwini Municipality / Durban (durban.gov.za).

Demonstrates: a validated region/area lookup against a maintainer-hosted JSON
index (raising SourceArgumentNotFoundWithSuggestions for either field),
followed by a static per-region/area ICS calendar fetch -- exactly the
TwoStepRetriever shape. The provider's fortnightly recycling round is always
dated to a fixed ISO-week parity in the shared ICS feed regardless of which
physical week that lands on for a given address, so the odd/even user
preference is applied as a preprocess filter/rename ahead of a plain
ICSTransformer.
"""

from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import IcsParser
from waste_collection_schedule.retrievers import TwoStepRetriever
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import GENERAL_WASTE, RECYCLABLES

_ICS_BASE = (
    "https://raw.githubusercontent.com/robtesch/hacs_waste_collection_schedule/"
    "refs/heads/data/durban-gov-za"
)
_INDEX_URL = f"{_ICS_BASE}/index.json"
_ODD_RECYCLING_SUMMARY = "Recycling (odd ISO weeks)"


def _validate_and_get_area(lookup, source) -> str:
    index = lookup.json()
    regions = index.get("regions", {})

    region_key = source.params["region"].strip().lower()
    if region_key not in regions:
        raise SourceArgumentNotFoundWithSuggestions(
            "region", source.params["region"], sorted(regions)
        )

    areas = regions[region_key].get("areas", {})
    area_key = source.params["area"].strip().lower()
    if area_key not in areas:
        raise SourceArgumentNotFoundWithSuggestions(
            "area", source.params["area"], sorted(areas)
        )
    return area_key


@final
class Source(BaseSource):
    TITLE = "eThekwini Municipality"
    DESCRIPTION = (
        "Source for eThekwini Municipality / Durban refuse collection schedules."
    )
    URL = "https://www.durban.gov.za/page/refuse-collection-schedules"
    COUNTRY = "za"
    RAISE_ON_EMPTY = True
    SOURCE_CODEOWNERS: ClassVar[list[str]] = ["@robtesch"]

    TEST_CASES: ClassVar[dict] = {
        "Outer West Hillcrest": {
            "region": "outer_west",
            "area": "hillcrest",
            "recycling_in_even_week": True,
        },
        "Outer West Drummond": {
            "region": "outer_west",
            "area": "drummond_montesseel",
            "recycling_in_even_week": True,
        },
        "North Umdloti": {
            "region": "north",
            "area": "umdloti",
            "recycling_in_even_week": True,
        },
        "North Central Overport": {
            "region": "north_central",
            "area": "overport_drive",
            "recycling_in_even_week": True,
        },
        "South Central Montclair": {
            "region": "south_central",
            "area": "montclair_w3",
            "recycling_in_even_week": True,
        },
        "Inner West Westville": {
            "region": "inner_west",
            "area": "westville",
            "recycling_in_even_week": True,
        },
        "South Umlazi": {
            "region": "south",
            "area": "umlazi_section",
            "recycling_in_even_week": True,
        },
    }

    HOWTO: ClassVar[dict] = {
        "en": (
            "Visit the <a href='https://www.durban.gov.za/page/refuse-collection-schedules'>"
            "refuse collection schedules</a> page, open your region's DOCX file, and find "
            "your suburb or area under the weekday column. Use the matching region "
            "(e.g. outer_west, north, south_central, north_central, inner_west, south) and "
            "collection-area slug shown in that document. For 'Recycling collected on even "
            "ISO weeks', check your last recycling collection date to determine whether it "
            "fell on an even or odd ISO week number."
        ),
    }

    PARAMS = (
        text_field("region", "Region"),
        text_field("area", "Collection Area"),
        text_field(
            "recycling_in_even_week",
            "Recycling collected on even ISO weeks",
            default="true",
            optional=True,
        ),
    )

    retrieve = TwoStepRetriever(
        lookup_url=_INDEX_URL,
        extract=_validate_and_get_area,
        schedule_url=lambda area_key, region, **_: (
            f"{_ICS_BASE}/calendars/{region.strip().lower()}/{area_key}.ics"
        ),
    )
    parse = IcsParser()

    def preprocess(self, entries, source):
        even = bool(source.params.get("recycling_in_even_week", True))
        for date_, summary in entries:
            if summary == _ODD_RECYCLING_SUMMARY:
                if even:
                    continue
                summary = "Recycling"
            elif summary == "Recycling" and not even:
                continue
            yield (date_, summary)

    transform = ICSTransformer(
        type_value_map={"General Waste": GENERAL_WASTE, "Recycling": RECYCLABLES}
    )

    def __init__(
        self,
        region: str,
        area: str,
        recycling_in_even_week: "str | bool" = True,
    ):
        super().__init__(
            region=region,
            area=area,
            recycling_in_even_week=str(recycling_in_even_week).strip().lower()
            in {"true", "yes", "1"},
        )
