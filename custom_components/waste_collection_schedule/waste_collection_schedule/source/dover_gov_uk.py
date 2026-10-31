"""Dover District Council (England) bin collection dates."""

from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, preprocessors, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.transformers import JsonTransformer

# The council's "Find your collection dates" page is a Veolia resident portal.
# Its calendar call takes the UPRN directly and answers 404 ("No calendar data
# found") for a property it does not serve. The old collections.dover.gov.uk
# property pages are gone.
API_URL = "https://portal.waste.dover.gov.uk/api/getCalendarData"
COUNCIL_ID = "39"


@final
class Source(BaseSource):
    TITLE = "Dover District Council"
    DESCRIPTION = "Source for Dover District Council."
    URL = "https://www.dover.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "200002423404": {"uprn": 200002423404},
        "100060905828": {"uprn": "100060905828"},
    }

    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unknown UPRN": {"uprn": "999999999999"},
    }

    PARAMS = (uprn(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter the Unique Property Reference Number (UPRN) of your "
            "property. You can find it at https://www.findmyaddress.co.uk/. "
            "Since the v3 pipeline migration, waste types use canonical, "
            "localised names. Update filters, automations and customisations "
            "using the old labels."
        ),
    }

    WASTE_TYPES: ClassVar[list] = [
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
        wt.GENERAL_WASTE,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    retrieve = retrievers.Request(
        API_URL,
        method="POST",
        json=lambda uprn, **_: {"councilId": COUNCIL_ID, "uprn": str(uprn).strip()},
        raise_for_status=False,
    )

    # {"data": [{"updatedAt": ..., "records": [{"service": "Refuse Collection",
    # "actual_scheduled_date": "2026-10-30T00:00:00Z", ...}, ...]}]}
    parse = parsers.ArgumentGuard(
        parsers.JsonParser("data"), argument="uprn", contains='"records"'
    )
    preprocess = preprocessors.ExplodeList("records")

    transform = JsonTransformer(
        date_key="actual_scheduled_date",
        type_key="service",
        parse_date=date_parsers.for_format("%Y-%m-%dT%H:%M:%SZ"),
        type_value_map={
            "Refuse Collection": wt.GENERAL_WASTE,
            "Recycling Collection": wt.RECYCLABLES,
            "Paper/Card Collection": wt.PAPER,
            "Food Collection": wt.FOOD_WASTE,
            "Garden Waste Collection": wt.GARDEN_WASTE,
        },
    )
