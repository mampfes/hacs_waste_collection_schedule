from typing import ClassVar, final

from waste_collection_schedule import date_parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.service.AchieveForms import (
    AchieveFormsMultiLookupRowsParser,
    AchieveFormsRetriever,
    LookupStep,
)
from waste_collection_schedule.transformers import RowTransformer

_HOSTNAME = "gloucester-self.achieveservice.com"
_SECTION = "Your waste collections"

# Per bin: the id field the first lookup returns, then the lookup turning that
# id into a workflow token ("{Type}1"), then the one turning the token into
# the next date ("Next{Type}1DateISO").
_BINS = {
    "Refuse": ("RefuseId", "63f731d2b50d7", "63ca72c70c3b1"),
    "Recycling": ("RecyclingId", "63f89f73018c0", "63cfcf4756b5d"),
    "Food": ("FoodId", "63f8a11714712", "63cfcf8ac7877"),
    "Garden": ("GardenId", "63f8a15776b5d", "63cfcfc1c486c"),
}


def _row(response) -> dict:
    rows = response.get("integration", {}).get("transformed", {}).get("rows_data")
    return (rows or {}).get("0", {}) if isinstance(rows, dict) else {}


def _store_bin_ids(response, context):
    context.update(_row(response))


def _bin_steps(bin_type: str, id_field: str, workflow_id: str, next_id: str):
    """The two lookups for one bin, skipped when the property lacks it."""
    token = f"{bin_type}1"
    return [
        LookupStep(
            workflow_id,
            section=_SECTION,
            form_values=lambda ctx, source: {id_field: {"value": ctx[id_field]}},
            extract=lambda response, ctx: ctx.update(
                {token: _row(response).get(token, "")}
            ),
            when=lambda ctx, source: bool(ctx.get(id_field)),
            no_retry="true",
        ),
        LookupStep(
            next_id,
            section=_SECTION,
            form_values=lambda ctx, source: {token: {"value": ctx[token]}},
            when=lambda ctx, source: bool(ctx.get(token)),
            no_retry="true",
            label=bin_type,
            date_field=f"Next{bin_type}1DateISO",
        ),
    ]


@final
class Source(BaseSource):
    TITLE = "Gloucester City Council"
    DESCRIPTION = "Source for Gloucester City Council, UK, bin collection dates."
    URL = "https://www.gloucester.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "1 Whimbrel Road": {"uprn": 200004478006},
        "10 Whimbrel Road": {"uprn": "200004478021"},
    }

    PARAMS = (uprn(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Find your UPRN by visiting "
            "https://gloucester-self.achieveservice.com/en/service/Bins___Check_your_bin_day "
            "and searching for your address. Your UPRN can also be found at "
            "https://www.findmyaddress.co.uk/."
        ),
    }

    # The landing page answers a non-browser request with 403; the auth API
    # accepts its URL as the uri.
    retrieve = AchieveFormsRetriever(
        hostname=_HOSTNAME,
        initial_url=f"https://{_HOSTNAME}/AchieveForms/",
        skip_landing_page=True,
        collect_all=True,
        steps=[
            LookupStep(
                "63f72ddc8ca25",
                section=_SECTION,
                form_values=lambda ctx, source: {
                    "binUprn": {"value": source.params["uprn"]}
                },
                extract=_store_bin_ids,
                no_retry="true",
            ),
            *(
                step
                for bin_type, lookups in _BINS.items()
                for step in _bin_steps(bin_type, *lookups)
            ),
        ],
    )
    parse = AchieveFormsMultiLookupRowsParser()
    transform = RowTransformer(
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        type_value_map={
            "Refuse": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Food": wt.FOOD_WASTE,
            "Garden": wt.GARDEN_WASTE,
        },
    )
