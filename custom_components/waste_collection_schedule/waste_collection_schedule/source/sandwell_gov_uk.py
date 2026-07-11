from datetime import date
from typing import Any, ClassVar, final

from waste_collection_schedule import date_parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.service.AchieveForms import (
    AchieveFormsMultiLookupRowsParser,
    AchieveFormsRetriever,
    LookupStep,
)
from waste_collection_schedule.transformers import RowTransformer
from waste_collection_schedule.waste_types import (
    FOOD_WASTE,
    GARDEN_WASTE,
    GENERAL_WASTE,
    RECYCLABLES,
)

HOSTNAME = "my.sandwell.gov.uk"
INITIAL_URL = (
    "https://my.sandwell.gov.uk/en/AchieveForms/?form_uri=sandbox-publish://"
    "AF-Process-ebaa26a2-393c-4a3c-84f5-e61564192a8a/"
    "AF-Stage-e4c2cb32-db55-4ff5-845c-8b27f87346c4/definition.json"
    "&redirectlink=/en&cancelRedirectLink=/en&consentMessage=yes"
)


def _form_values(ctx: dict, source: Any) -> dict:
    return {
        "Uprn": {"value": source.params["uprn"]},
        "NextCollectionFromDate": {"value": date.today().isoformat()},
    }


@final
class Source(BaseSource):
    TITLE = "Sandwell Council"
    DESCRIPTION = "Source for waste collection services for Sandwell Council."
    URL = "https://my.sandwell.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "uprn_10008535856": {"uprn": "10008535856"},
        "uprn_10008535857": {"uprn": "10008535857"},
    }

    PARAMS = (uprn(),)

    # Sandwell has no chained "one lookup feeds the next" flow: each bin type
    # is an independent runLookup call with the same UPRN, so collect_all
    # returns every step's raw response for the parser to fan out across.
    retrieve = AchieveFormsRetriever(
        hostname=HOSTNAME,
        initial_url=INITIAL_URL,
        skip_landing_page=True,
        collect_all=True,
        steps=[
            LookupStep(
                "686294de50729",
                section="Property details",
                form_values=_form_values,
                label="Household Waste (Grey)",
                date_field="DWDate",
            ),
            LookupStep(
                "68629dd642423",
                section="Property details",
                form_values=_form_values,
                label="Recycling (Blue)",
                date_field="MDRDate",
            ),
            LookupStep(
                "6863a78a1dd8e",
                section="Property details",
                form_values=_form_values,
                label="Food Waste (Brown)",
                date_field="FWDate",
            ),
            LookupStep(
                "686295a88a750",
                section="Property details",
                form_values=_form_values,
                # May be unsubscribed, in which case rows_data is empty.
                label="Garden Waste (Green)",
                date_field="GWDate",
            ),
        ],
    )
    parse = AchieveFormsMultiLookupRowsParser()
    transform = RowTransformer(
        parse_date=date_parsers.for_format("%d/%m/%Y"),
        type_value_map={
            "household waste (grey)": GENERAL_WASTE,
            "recycling (blue)": RECYCLABLES,
            "food waste (brown)": FOOD_WASTE,
            "garden waste (green)": GARDEN_WASTE,
        },
    )

    def __init__(self, uprn: str | int):
        super().__init__(uprn=str(uprn).strip())
