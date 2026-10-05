import datetime
from typing import ClassVar, final

from waste_collection_schedule import date_parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, uprn
from waste_collection_schedule.service.AchieveForms import (
    AchieveFormsRetriever,
    AchieveFormsRowFieldsPreprocessor,
    AchieveFormsRowsParser,
    LookupStep,
)
from waste_collection_schedule.transformers import RowTransformer

_HOSTNAME = "my.midlothian.gov.uk"


def _form(context, source):
    today = datetime.date.today()
    return {
        "postcode": {"value": source.params["postcode"]},
        "UPRN": {"value": source.params["uprn"]},
        "uprn": {"value": source.params["uprn"]},
        "fromDate": {"value": today.strftime("%Y-%m-%d")},
        "toDate": {
            "value": (today + datetime.timedelta(days=365)).strftime("%Y-%m-%d")
        },
    }


@final
class Source(BaseSource):
    TITLE = "Midlothian Council"
    DESCRIPTION = "Source script for my.midlothian.gov.uk bin collections"
    URL = "https://my.midlothian.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
        wt.GENERAL_WASTE,
        wt.GLASS,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test1": {"uprn": "120001401", "postcode": "EH26 8AG"},
    }

    PARAMS = (uprn(), postcode())

    HOWTO: ClassVar[dict] = {
        "en": "Find your UPRN and postcode from your council documents or invoices.",
    }

    # A year of collections from today.
    retrieve = AchieveFormsRetriever(
        hostname=_HOSTNAME,
        initial_url=f"https://{_HOSTNAME}/",
        skip_landing_page=True,
        auth_test_url=f"https://{_HOSTNAME}/apibroker/domain/{_HOSTNAME}",
        steps=[LookupStep("69948bdca6012", form_values=_form)],
    )
    parse = AchieveFormsRowsParser()
    preprocess = AchieveFormsRowFieldsPreprocessor(
        date_field="Date", label_fields=("Service",)
    )
    transform = RowTransformer(
        parse_date=date_parsers.for_format("%d/%m/%Y %H:%M:%S"),
        type_value_map={
            "Card Collection Service": wt.PAPER,
            "Food Collection Service": wt.FOOD_WASTE,
            "Garden Collection Service": wt.GARDEN_WASTE,
            "Glass Collection Service": wt.GLASS,
            "Recycling Collection Service": wt.RECYCLABLES,
            "Residual Collection Service": wt.GENERAL_WASTE,
        },
    )
