from typing import ClassVar, final

from waste_collection_schedule import date_parsers, tls
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.service.SalesforceAuraApex import (
    AuraApexRetriever,
    AuraServiceUnitsParser,
)
from waste_collection_schedule.transformers import RowTransformer

# myaccount.chesterfield.gov.uk sends its leaf certificate without the issuing
# "GlobalSign GCC R3 EV TLS CA 2025" intermediate, so certifi alone cannot
# verify it. The retriever completes the chain from the leaf's AIA URL
# (tls.AIA) instead of shipping that intermediate, which had to be replaced
# whenever the host renewed under another one.

_TYPE_MAP = {
    "Domestic Refuse": wt.GENERAL_WASTE,
    "Domestic Recycling": wt.RECYCLABLES,
    "Domestic Food": wt.FOOD_WASTE,
    "Domestic Paid Garden": wt.GARDEN_WASTE,
}


@final
class Source(BaseSource):
    TITLE = "Chesterfield Borough Council"
    DESCRIPTION = (
        "Source for waste collection services for Chesterfield Borough Council"
    )
    URL = "https://www.chesterfield.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"uprn": 74023685},
        "Test_002": {"uprn": "74009625"},
        "Test_003": {"uprn": "74035689"},
        "Test_004": {"uprn": "74020930"},
    }

    PARAMS = (uprn(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "An easy way to discover your Unique Property Reference Number (UPRN) "
            "is by going to [FindMyAddress.co.uk](https://www.findmyaddress.co.uk/) "
            "and entering your address details."
        ),
    }

    retrieve = AuraApexRetriever(
        "myaccount.chesterfield.gov.uk",
        app="cbc_VE_CollectionDaysLO",
        page_uri="/bins-and-recycling/bin-collections/check-bin-collections.aspx",
        classname="CBC_VE_CollectionDays",
        method="getServicesByUPRN",
        params=lambda uprn, **_: {
            "propertyUprn": str(uprn),
            "executedFrom": "Main Website",
        },
        verify=tls.AIA,
    )
    parse = AuraServiceUnitsParser()
    transform = RowTransformer(
        parse_date=date_parsers.in_timezone("Europe/London"),
        clean=lambda label: label.removeprefix("Collect "),
        type_value_map=_TYPE_MAP,
    )
