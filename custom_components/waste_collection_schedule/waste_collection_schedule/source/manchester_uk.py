import datetime
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, preprocessors
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.service.VerintCloud import (
    VerintCloudRetriever,
    VerintStep,
)
from waste_collection_schedule.transformers import RowTransformer

_TYPE_MAP = {
    "Black bin": wt.GENERAL_WASTE,
    "Blue bin": wt.PAPER,
    "Brown bin": wt.RECYCLABLES,
    "Green Bin": wt.ORGANIC,
}


def _date_range(days_back: int, days_ahead: int) -> dict[str, str]:
    now = datetime.datetime.now()
    return {
        "nextCollectionFromDate": (now - datetime.timedelta(days=days_back)).strftime(
            "%Y-%m-%d"
        ),
        "nextCollectionToDate": (now + datetime.timedelta(days=days_ahead)).strftime(
            "%Y-%m-%d"
        ),
    }


@final
class Source(BaseSource):
    TITLE = "Manchester City Council"
    DESCRIPTION = "Source for bin collection services for Manchester City Council, UK."
    URL = "https://www.manchester.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.PAPER,
        wt.RECYCLABLES,
        wt.ORGANIC,
    ]

    TEST_CASES: ClassVar[dict] = {
        "domestic #1": {"uprn": "77065560"},
        "domestic #2": {"uprn": "77121299"},
        "domestic #3": {"uprn": "10093076834"},
        "domestic #4": {"uprn": "77100451"},
        "domestic #5": {"uprn": "77141200"},
    }

    PARAMS = (uprn(),)

    HOWTO: ClassVar[dict] = {
        "en": "Find your UPRN at https://www.findmyaddress.co.uk/.",
    }

    retrieve = VerintCloudRetriever(
        "https://manchester.form.uk.empro.verintcloudservices.com/",
        form="sr_bin_coll_day_checker",
        headers={
            "referer": "https://manchester.portal.uk.empro.verintcloudservices.com/"
        },
        steps=(
            VerintStep(
                "api/custom?action=bin_checker-get_bin_col_info"
                "&actionedby=_KDF_custom&loadform=true&access=citizen&locale=en",
                data=lambda previous, uprn, **_: {
                    "uprn": str(uprn),
                    **_date_range(days_back=1, days_ahead=365),
                },
            ),
        ),
    )
    parse = parsers.JsonParser("data")
    # One field per bin, holding all of its dates separated by ";".
    preprocess = preprocessors.DateFields(
        fields={
            "ahtm_dates_black_bin": "Black bin",
            "ahtm_dates_blue_pulpable_bin": "Blue bin",
            "ahtm_dates_brown_commingled_bin": "Brown bin",
            "ahtm_dates_green_organic_bin": "Green Bin",
        },
        split=";",
        parse_date=date_parsers.for_format("%d/%m/%Y %H:%M:%S"),
    )
    transform = RowTransformer(type_value_map=_TYPE_MAP)
