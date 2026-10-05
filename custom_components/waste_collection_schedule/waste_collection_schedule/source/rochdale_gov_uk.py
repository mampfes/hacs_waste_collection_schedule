import datetime
from typing import ClassVar, final

from waste_collection_schedule import date_parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.service.AchieveForms import (
    AchieveFormsIndexedFieldsPreprocessor,
    AchieveFormsRetriever,
    AchieveFormsRowsParser,
    LookupStep,
)
from waste_collection_schedule.transformers import JsonTransformer

_HOSTNAME = "rochdale-self.achieveservice.com"
_SECTION = "Location details"


def _store_token(response, context):
    rows = response.get("integration", {}).get("transformed", {}).get("rows_data")
    if isinstance(rows, dict):
        context["token"] = rows.get("0", {}).get("bartecToken", "")


def _calendar_form(context, source):
    today = datetime.date.today()
    end = today + datetime.timedelta(days=365)
    return {
        "propertyUPRN": {"value": source.params["uprn"]},
        "bartecToken": {"value": context.get("token", "")},
        "dateAnnualMinimum": {"value": today.strftime("%Y-%m-%dT00:00:00")},
        "dateAnnualMaximum": {"value": end.strftime("%Y-%m-%dT23:59:59")},
    }


@final
class Source(BaseSource):
    TITLE = "Rochdale Borough Council"
    DESCRIPTION = "Source for Rochdale Borough Council, UK."
    URL = "https://www.rochdale.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.GLASS, wt.ORGANIC, wt.PAPER]

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"uprn": "10094359340"},
        "Test_002": {"uprn": "23030658"},
        "Test_003": {"uprn": "23011384"},
        "Test_004": {"uprn": "23045922"},
    }

    PARAMS = (uprn(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Find your UPRN at https://www.findmyaddress.co.uk/ by searching for "
            "your address."
        ),
    }

    # A Bartec token first, then the year's calendar from today.
    retrieve = AchieveFormsRetriever(
        hostname=_HOSTNAME,
        service_page="Bins___view_your_waste_collection_calendar",
        skip_landing_page=True,
        auth_test_url=f"https://{_HOSTNAME}/apibroker/domain/{_HOSTNAME}",
        steps=[
            LookupStep(
                "6846c784a46b5",
                section=_SECTION,
                form_values=lambda ctx, source: {
                    "propertyUPRN": {"value": source.params["uprn"]}
                },
                extract=_store_token,
            ),
            LookupStep(
                "68b58a1364572",
                section=_SECTION,
                form_values=_calendar_form,
                no_retry="true",
            ),
        ],
    )
    parse = AchieveFormsRowsParser()
    # The next collections, flattened into one row as numbered field groups
    # (bartecAnnualBin1Type / ...Day / ...Month); the dates carry no year.
    preprocess = AchieveFormsIndexedFieldsPreprocessor(
        "bartecAnnualBin", require=("Type", "Day", "Month")
    )
    transform = JsonTransformer(
        date_key=lambda group: f"{group['Day']} {group['Month']}",
        type_key="Type",
        parse_date=date_parsers.next_weekday("%d %B"),
        type_value_map={
            "General Waste": wt.GENERAL_WASTE,
            "Paper and Cardboard": wt.PAPER,
            "Glass and Bottles": wt.GLASS,
            "Food and Garden": wt.ORGANIC,
        },
        carry_raw_label=True,
    )
