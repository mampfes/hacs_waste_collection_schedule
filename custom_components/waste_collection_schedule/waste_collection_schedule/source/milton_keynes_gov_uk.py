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

_HOSTNAME = "mycouncil.milton-keynes.gov.uk"


@final
class Source(BaseSource):
    TITLE = "Milton Keynes council"
    DESCRIPTION = "Source for Milton Keynes council."
    URL = "milton-keynes.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.ORGANIC, wt.RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "North Row, Central": {"uprn": 25032037},
        "Adelphi Street, Campbell Park": {"uprn": 25044504},
    }

    PARAMS = (uprn(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Find your UPRN at https://www.findmyaddress.co.uk/ by searching for "
            "your address."
        ),
    }

    retrieve = AchieveFormsRetriever(
        hostname=_HOSTNAME,
        initial_url=f"https://{_HOSTNAME}/service/Waste_Collection_Round_Checker",
        skip_landing_page=True,
        auth_test_url=f"https://{_HOSTNAME}/apibroker/domain/{_HOSTNAME}",
        steps=[
            LookupStep(
                "64d9feda3a507",
                form_values=lambda ctx, source: {
                    "uprnCore": {"value": source.params["uprn"]}
                },
            ),
        ],
    )
    parse = AchieveFormsRowsParser()
    # One row per container, with its last and its next collection. The
    # container names vary by property ("Red Plastic Sacks", "1100L Refuse
    # (Black)"); the service name is the stable label. Two sack colours of the
    # recycling service collected on one day are one collection.
    preprocess = AchieveFormsRowFieldsPreprocessor(
        date_field=("NextInstance", "LastInstance"),
        label_fields=("ServiceName",),
        dedupe=True,
    )
    transform = RowTransformer(
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        type_value_map={
            "Communal Refuse Collection": wt.GENERAL_WASTE,
            "Domestic Refuse Collection": wt.GENERAL_WASTE,
            "Communal Recycling Collection": wt.RECYCLABLES,
            "Domestic Recycling Collection": wt.RECYCLABLES,
            "Food and Garden": wt.ORGANIC,
        },
        carry_raw_label=True,
    )
