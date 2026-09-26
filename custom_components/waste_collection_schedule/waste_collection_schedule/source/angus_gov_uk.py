import datetime
from typing import ClassVar, final

from waste_collection_schedule import date_parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, uprn
from waste_collection_schedule.service.AchieveForms import (
    AchieveFormsRetriever,
    AchieveFormsRowFieldsPreprocessor,
    AchieveFormsXmlRowsParser,
    LookupStep,
)
from waste_collection_schedule.transformers import RowTransformer

_HOSTNAME = "myangus.angus.gov.uk"
_SECTION = "Section 3"


def _search_form(context, source):
    return {
        "search": {
            "value": source.params["postcode"].replace(" ", "").lower(),
            "value_changed": True,
        },
        "select_NewAddress": {"value": ""},
    }


def _select_form(context, source):
    today = datetime.date.today().isoformat()
    code = source.params["postcode"].upper()
    property_id = source.params["uprn"]
    return {
        "select_NewAddress": {"value": property_id, "value_changed": True},
        "search": {"value": code.replace(" ", "").lower(), "value_changed": True},
        "serviceUPRN": {"value": property_id, "value_changed": True},
        "formatted_search": {"value": code, "value_changed": True},
        "chooseADate": {"value": today, "value_changed": True},
        "currentDate": {"value": today, "value_changed": True},
    }


@final
class Source(BaseSource):
    TITLE = "Angus Council"
    DESCRIPTION = "Source for Angus Council (MyAngus/Granicus)"
    URL = "https://www.angus.gov.uk"
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
        "Test": {"uprn": "117097214", "postcode": "DD11 2RH"},
    }

    PARAMS = (uprn(), postcode())

    HOWTO: ClassVar[dict] = {
        "en": (
            "Find your UPRN at https://www.findmyaddress.co.uk/ by searching for "
            "your address, and enter the property's postcode."
        ),
    }

    # The form searches the postcode first, then selects the property.
    retrieve = AchieveFormsRetriever(
        hostname=_HOSTNAME,
        service_page="Bin_collection_dates_V3",
        steps=[
            LookupStep("686cdfffd9945", section=_SECTION, form_values=_search_form),
            LookupStep("66587d491feab", section=_SECTION, form_values=_select_form),
        ],
    )
    # The answer is the integration's XML: one row per collection, named by
    # the bin's lid colour, with 1900-01-01 for a bin the property lacks.
    parse = AchieveFormsXmlRowsParser()
    preprocess = AchieveFormsRowFieldsPreprocessor(
        date_field="binDate",
        label_fields=("binTypeList",),
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        min_year=2000,
    )
    # https://www.angus.gov.uk/bins_litter_and_recycling/what_goes_in_your_bins
    transform = RowTransformer(
        type_value_map={
            "Purple": wt.GENERAL_WASTE,
            "Grey": wt.RECYCLABLES,
            "Blue": wt.PAPER,
            "Brown": wt.FOOD_WASTE,
            "Green": wt.GARDEN_WASTE,
        },
        carry_raw_label=True,
    )
