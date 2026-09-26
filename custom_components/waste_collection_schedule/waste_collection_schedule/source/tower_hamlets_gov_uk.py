import datetime
from typing import Any, ClassVar, final

from waste_collection_schedule import date_parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.service.AchieveForms import (
    AchieveFormsRetriever,
    AchieveFormsRowFieldsPreprocessor,
    AchieveFormsRowsParser,
    GetStep,
    LookupStep,
)
from waste_collection_schedule.transformers import RowTransformer

_HOSTNAME = "towerhamlets-self.achieveservice.com"
_LOOKUP_ID = "654ba9e6a9886"


def _extract_csrf(response: dict, context: dict) -> None:
    context["csrf"] = response["data"]["csrfToken"]


def _form_values(context: dict, source: Any) -> dict:
    uprn_value = source.params["uprn"]
    return {
        "howCheck": {"value": "property"},
        "NextCollectionFromDate": {"value": datetime.date.today().isoformat()},
        "addressDetails": {"value": {"Section 1": {"Address": {"value": uprn_value}}}},
        "AccountSiteUPRN": {"value": uprn_value},
        "TH_uprn": {"value": uprn_value},
    }


@final
class Source(BaseSource):
    TITLE = "London Borough of Tower Hamlets"
    DESCRIPTION = "Source for London Borough of Tower Hamlets"
    URL = "https://www.towerhamlets.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Celtic St": {"uprn": "6085613"},
        "Ernest St": {"uprn": "6034631"},
        "Blue Anchor Yard": {"uprn": "6007545"},
    }

    PARAMS = (uprn(),)

    HOWTO: ClassVar[dict] = {
        "en": "Find your UPRN at https://www.findmyaddress.co.uk/",
    }

    # The collection lookup wants the CSRF token from /api/nextref as a header.
    retrieve = AchieveFormsRetriever(
        hostname=_HOSTNAME,
        initial_url=(
            f"https://{_HOSTNAME}/service/Check_your_waste_and_recycling_collection_days"
        ),
        steps=[
            GetStep(f"https://{_HOSTNAME}/api/nextref", extract=_extract_csrf),
            LookupStep(
                _LOOKUP_ID,
                section="Section 2",
                form_values=_form_values,
                headers=lambda ctx, source: {"X-CSRF-Token": ctx["csrf"]},
            ),
        ],
    )
    parse = AchieveFormsRowsParser()
    # One row per collection; the date carries no year ("14 October").
    preprocess = AchieveFormsRowFieldsPreprocessor(
        date_field="CollectionDate",
        label_fields=("CollectionService",),
        parse_date=date_parsers.next_weekday("%d %B"),
    )
    transform = RowTransformer(
        type_value_map={
            "General Waste": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Food/Garden Waste": wt.ORGANIC,
            "Food Waste": wt.FOOD_WASTE,
            "Garden Waste": wt.GARDEN_WASTE,
        },
    )
