from typing import ClassVar, final

from bs4 import Tag
from waste_collection_schedule import date_parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.parsers import HtmlParser
from waste_collection_schedule.service.AchieveForms import (
    AchieveFormsRetriever,
    LookupStep,
)
from waste_collection_schedule.transformers import HtmlTransformer
from waste_collection_schedule.waste_types import (
    FOOD_WASTE,
    GARDEN_WASTE,
    GENERAL_WASTE,
    RECYCLABLES,
)

HOSTNAME = "myaccount.wrexham.gov.uk"
INITIAL_URL = (
    "https://myaccount.wrexham.gov.uk/en/AchieveForms/?form_uri=sandbox-publish://"
    "AF-Process-ceb55423-9f5d-4124-b713-805ac7a73e3e/"
    "AF-Stage-854336b9-1221-4e6a-88d7-785fb2f8e340/definition.json"
    "&redirectlink=/en&cancelRedirectLink=/en&consentMessage=yes&noLoginPrompt=1"
)
LOOKUP_ID = "5beab9a792bb5"


def _row_date(li: Tag) -> "str | None":
    """The collection date from the first cell of this <li>'s own table row."""
    row = li.find_parent("tr")
    cell = row.find("td") if row is not None else None
    return cell.get_text(strip=True) if isinstance(cell, Tag) else None


@final
class Source(BaseSource):
    TITLE = "Wrexham County Borough Council"
    DESCRIPTION = "Source for Wrexham County Borough Council."
    URL = "https://www.wrexham.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Duck Farm, Gresford, LL12 8YT": {"uprn": "100100940408"},
        "Regent St, Wrexham, LL11 1SA": {"uprn": "10096241365"},
        "Hill Crest, Wrexham, LL13 8RN": {"uprn": "100100860092"},
    }

    PARAMS = (uprn(),)

    retrieve = AchieveFormsRetriever(
        hostname=HOSTNAME,
        initial_url=INITIAL_URL,
        auth_test_url=f"https://{HOSTNAME}/apibroker/domain/{HOSTNAME}",
        steps=[
            LookupStep(
                LOOKUP_ID,
                form_values=lambda ctx, source: {
                    "UPRN": {"value": source.params["uprn"]},
                    "NoWeeks": {"name": "NoWeeks", "value": "2"},
                },
            ),
        ],
    )
    # The schedule is an HTML table embedded inside a JSON field of the
    # runLookup response; HtmlParser's from_json_key drills straight to it
    # (the raw dict from AchieveFormsRetriever needs no .json() call). Each
    # date row lists the bins collected that day as <li>s in its second cell,
    # so selecting the <li>s makes one record per collection, and the date
    # comes off the first cell of the <li>'s own row.
    parse = HtmlParser(
        "tr td:nth-of-type(2) li",
        from_json_key=(
            "integration",
            "transformed",
            "rows_data",
            "0",
            "UpcomingCollections",
        ),
    )
    transform = HtmlTransformer(
        date_getter=_row_date,
        type_getter=lambda li: li.get_text(strip=True),
        parse_date=date_parsers.for_format("%d/%m/%Y"),
        # A single <li> can name a combined round ("Recycling / food").
        type_value_map={
            "recycling / food": [RECYCLABLES, FOOD_WASTE],
            "garden waste": GARDEN_WASTE,
            "general waste": GENERAL_WASTE,
        },
    )

    def __init__(self, uprn: str | int):
        super().__init__(uprn=str(uprn).zfill(12))
