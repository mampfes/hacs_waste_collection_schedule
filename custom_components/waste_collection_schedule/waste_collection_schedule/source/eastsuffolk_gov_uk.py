import datetime
import re
from typing import ClassVar, final

from waste_collection_schedule import date_parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.service.AchieveForms import (
    AchieveFormsRetriever,
    AchieveFormsRowFieldsPreprocessor,
    AchieveFormsRowsParser,
    LookupStep,
)
from waste_collection_schedule.transformers import RowTransformer

_HOSTNAME = "my.eastsuffolk.gov.uk"

# The descriptive labels open with an emoji ("🟢 General waste - ...").
_LEADING_SYMBOLS_RE = re.compile(r"^[^A-Za-z]+")


def _store_token(response, context):
    rows = response.get("integration", {}).get("transformed", {}).get("rows_data")
    if isinstance(rows, dict):
        context["token"] = rows.get("0", {}).get("AuthenticateResponse", "")


def _collections_form(context, source):
    today = datetime.date.today()
    end = today + datetime.timedelta(days=90)
    return {
        "bartecMode": {"value": "Live"},
        "AuthenticateResponse": {"value": context.get("token", "")},
        "finalUPRN": {"value": source.params["uprn"]},
        "minimum_date": {"value": today.strftime("%Y-%m-%dT00:00:00")},
        "maximum_date": {"value": end.strftime("%Y-%m-%dT00:00:00")},
    }


@final
class Source(BaseSource):
    TITLE = "East Suffolk Council"
    DESCRIPTION = "Source for East Suffolk Council, UK."
    URL = "https://www.eastsuffolk.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
        wt.GENERAL_WASTE,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "106 Mill Lane, Felixstowe, IP11 2LL": {"uprn": "100091126543"},
        "82 Mill Lane, Felixstowe, IP11 2LL": {"uprn": 100091126520},
    }

    PARAMS = (uprn(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Find your UPRN by visiting "
            "https://my.eastsuffolk.gov.uk/service/Bin_collection_dates_finder "
            "and searching for your address. Your UPRN can also be found at "
            "https://www.findmyaddress.co.uk/."
        ),
    }

    # A Bartec token first, then the collections of the next 90 days.
    retrieve = AchieveFormsRetriever(
        hostname=_HOSTNAME,
        service_page="Bin_collection_dates_finder",
        steps=[
            LookupStep(
                "59e73f8bd860c",
                section="Details",
                form_values=lambda ctx, source: {"bartecMode": {"value": "Live"}},
                extract=_store_token,
            ),
            LookupStep(
                "68f900a32e7a4", section="Details", form_values=_collections_form
            ),
        ],
    )
    parse = AchieveFormsRowsParser()
    preprocess = AchieveFormsRowFieldsPreprocessor(
        date_field="CollectionDateFormatted",
        label_fields=("CollectionTypeDescriptive", "CollectionType"),
        first_label_only=True,
    )
    transform = RowTransformer(
        parse_date=date_parsers.for_format("%d/%m/%Y"),
        clean=lambda label: _LEADING_SYMBOLS_RE.sub("", label).strip(),
        type_value_map={
            "Container recycling - standard bin": wt.RECYCLABLES,
            "Food waste - outdoor caddy": wt.FOOD_WASTE,
            "Garden waste - standard bin": wt.GARDEN_WASTE,
            "General waste - standard bin": wt.GENERAL_WASTE,
            "Paper and cardboard - standard bin": wt.PAPER,
        },
        carry_raw_label=True,
    )
