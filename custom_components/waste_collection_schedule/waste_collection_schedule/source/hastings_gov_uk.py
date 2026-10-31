"""Hastings Borough Council (England) bin collection dates."""

from typing import ClassVar, final
from zoneinfo import ZoneInfo

from waste_collection_schedule import date_parsers, parsers, preprocessors, tls
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, text_field, uprn
from waste_collection_schedule.field_terms import POSTCODE
from waste_collection_schedule.retrievers import Request
from waste_collection_schedule.transformers import JsonTransformer

# The council's "my area" web service. It answers {"d": [service, ...]}, each
# service carrying its upcoming dates as .NET "/Date(<ms>)/" stamps, and
# {"d": null} for an unknown UPRN. The host sends its leaf certificate without
# the "GeoTrust TLS RSA CA G1" intermediate, so the request completes the chain
# from the certificate's AIA URL (tls.AIA) rather than skipping verification,
# which is what the legacy source did.
API_URL = (
    "https://el2.hastings.gov.uk/MyArea/CollectionDays.asmx/"
    "LookupCollectionDaysByService"
)


def _epoch_ms(record) -> str:
    """The milliseconds inside a .NET ``/Date(1793664000000)/`` stamp."""
    return "".join(filter(str.isdigit, record["date"]))


def _service(record) -> str:
    """ "Rubbish collection service" -> "Rubbish"."""
    return record["Service"].removesuffix("collection service").strip()


@final
class Source(BaseSource):
    TITLE = "Hastings Borough Council"
    DESCRIPTION = (
        "Source for hastings.gov.uk services for Hastings Borough Council, UK."
    )
    URL = "https://www.hastings.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"postcode": "TN34 1QF", "house_number": 36, "uprn": 100060038877},
        "Test_002": {
            "postcode": "TN34 2DL",
            "house_number": "28A",
            "uprn": "10070609836",
        },
        "Test_003": {"postcode": "TN37 7QH", "house_number": 5, "uprn": "100060041770"},
    }

    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unknown UPRN": {"uprn": "999999999999"},
    }

    # postcode and house_number are not used any more; they stay optional so
    # existing configurations keep working.
    PARAMS = (
        uprn(),
        text_field("postcode", term=POSTCODE, optional=True),
        house_number(optional=True),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "An easy way to discover your Unique Property Reference Number "
            "(UPRN) is by going to https://www.findmyaddress.co.uk/ and entering "
            "your address details. Leave postcode and house_number empty: they "
            "are no longer used. Since the v3 pipeline migration, waste types "
            "use canonical, localised names. Update filters, automations and "
            "customisations using the old labels."
        ),
    }

    WASTE_TYPES: ClassVar[list] = [
        wt.FOOD_WASTE,
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
    ]

    retrieve = Request(
        API_URL,
        method="POST",
        json=lambda uprn, **_: {"Uprn": str(uprn).strip()},
        verify=tls.AIA,
    )
    parse = parsers.JsonParser("d")
    preprocess = preprocessors.ExplodeList("Dates", into="date")
    transform = JsonTransformer(
        date_key=_epoch_ms,
        type_key=_service,
        parse_date=date_parsers.from_epoch("ms", tz=ZoneInfo("Europe/London")),
        type_value_map={
            "Food waste": wt.FOOD_WASTE,
            "Rubbish": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
        },
    )
