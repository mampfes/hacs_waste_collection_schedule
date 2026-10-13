from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.service.FirmstepSelfService import (
    FirmstepAddressFormRetriever,
)
from waste_collection_schedule.transformers import HtmlTransformer

FORM_URL = (
    "https://selfservice-torbay.servicebuilder.co.uk/renderform"
    "?t=62&k=09B72FF904A21A4B01A72AB6CCF28DC95105031C"
)
RENDER_URL = "https://selfservice-torbay.servicebuilder.co.uk/RenderForm"


def _col(row, index: int) -> str:
    return row.select("div.col")[index].get_text(strip=True)


@final
class Source(BaseSource):
    TITLE = "Torbay Council"
    DESCRIPTION = "Source for waste collection services for Torbay Council, Devon, UK."
    URL = "https://www.torbay.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "30 Dart Avenue, Torquay, TQ2 7NG": {"uprn": "100040542066"},
        "5 First Avenue, St Marychurch, Torquay, TQ1 4JB": {"uprn": "100040543309"},
    }

    PARAMS = (uprn(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Your Unique Property Reference Number (UPRN). "
            "Find yours at https://www.findmyaddress.co.uk/."
        ),
    }

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES, wt.GARDEN_WASTE]

    # The portal's field wants the UPRN prefixed with "U".
    retrieve = FirmstepAddressFormRetriever(
        form_url=FORM_URL,
        render_url=RENDER_URL,
        address_lookup_url=None,
        value_field="FF1168",
        value_prefix="U",
        address_param="uprn",
    )
    parse = parsers.HtmlParser("#resiCollectionDetails .resirow")
    transform = HtmlTransformer(
        date_getter=lambda row: _col(row, 1),
        type_getter=lambda row: _col(row, 2),
        parse_date=date_parsers.for_format("%A %d %B %Y"),
        skip_unparseable_dates=True,
        type_value_map={
            "Domestic Collection Service": wt.GENERAL_WASTE,
            "Recycling Collection Service": wt.RECYCLABLES,
            "Garden Waste Collection Service": wt.GARDEN_WASTE,
        },
    )
