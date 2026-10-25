import re
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, preprocessors, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, uprn
from waste_collection_schedule.transformers import JsonTransformer

API_URL = "https://api.blackpool.gov.uk/api/bartec"
_JOB_NAME = re.compile(r"^Empty(?: Bin)?(?: \d+\w+)? ([A-Za-z &]+?)( \d+\w)?$")


def _job_type(record):
    match = _JOB_NAME.search(record["jobField"]["nameField"])
    return match.group(1).strip() if match else ""


@final
class Source(BaseSource):
    TITLE = "Blackpool Council"
    DESCRIPTION = "Source for blackpool.gov.uk services for Blackpool Council, UK."
    URL = "https://blackpool.gov.uk"
    COUNTRY = "uk"
    # Bartec returns jobsField=null with Chrome impersonation, even for valid
    # addresses. Both the token and schedule calls need a neutral session.
    IMPERSONATE = None

    TEST_CASES: ClassVar[dict] = {
        "Test1": {"postcode": "FY1 4DZ", "uprn": "100010802829"},
        "Test2": {"postcode": "FY3 9RQ", "uprn": "100010842301"},
        "Test3": {"postcode": "FY1 2HR", "uprn": 100012606962},
    }
    PARAMS = (postcode(), uprn())
    HOWTO: ClassVar[dict] = {
        "en": (
            "Find your UPRN at https://www.findmyaddress.co.uk/ by entering your address. "
            "Since the v3 pipeline migration, waste types use canonical, localised "
            "names. Update filters, automations and customisations using the old labels."
        ),
    }
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.PAPER,
        wt.GARDEN_WASTE,
        wt.FOOD_WASTE,
    ]

    retrieve = retrievers.Request(
        f"{API_URL}/collection/PremiseJobs",
        method="POST",
        before=(
            retrievers.Lookup(
                f"{API_URL}/security/token",
                pick=lambda response, **_: response.text.strip('"'),
            ),
        ),
        json=lambda token, postcode, uprn, **_: {
            "UPRN": str(uprn),
            "USRN": "",
            "PostCode": str(postcode),
            "StreetNumber": "",
            "CurrentUser": {"UserId": "", "Token": token},
        },
    )
    parse = parsers.JsonParser("jobsField")
    preprocess = preprocessors.RowFilter(lambda record, source: bool(_job_type(record)))
    transform = JsonTransformer(
        date_key=lambda record: record["jobField"]["scheduledStartField"],
        type_key=_job_type,
        parse_date=date_parsers.for_format("%Y-%m-%dT%H:%M:%S"),
        type_value_map={
            "Domestic Refuse": wt.GENERAL_WASTE,
            "Dry Recycling": wt.RECYCLABLES,
            "Brown Sack": wt.PAPER,
            "Paper & Card": wt.PAPER,
            "Green Waste": wt.GARDEN_WASTE,
            "Food Caddy": wt.FOOD_WASTE,
        },
    )
