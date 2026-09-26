from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.service.ArcGis import ArcGisFeatureRetriever
from waste_collection_schedule.transformers import HtmlTransformer

_LAYER_URL = (
    "https://gis.rdc.govt.nz/server/rest/services/Core/RdcServices/MapServer/125"
)


@final
class Source(BaseSource):
    TITLE = "Rotorua Lakes Council"
    DESCRIPTION = "Source for Rotorua Lakes Council"
    URL = "https://www.rotorualakescouncil.nz"
    COUNTRY = "nz"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "Test1": {"address": "1061 Haupapa Street"},
        "Test2": {"address": "369 state highway 33"},
        "Test3": {"address": "17 Tihi road"},
        "Test4": {"address": "12a robin st"},
        "Test5": {"address": "25 kaska rd"},
    }

    PARAMS = (street_address("address"),)

    HOWTO: ClassVar[dict] = {
        "en": "Enter your street address, e.g. '1061 Haupapa Street'.",
    }

    retrieve = ArcGisFeatureRetriever(
        _LAYER_URL,
        address=lambda address, **_: f"{address}, Rotorua, New Zealand",
        out_fields="Collection",
    )
    # The matched zone's "Collection" field is an HTML list, one item per
    # upcoming week: "<li><b>Rubbish and recycling</b><br/>Wednesday 07 Oct 2026".
    parse = parsers.ArgumentGuard(
        parsers.HtmlParser(
            "li", from_json_key=("features", 0, "attributes", "Collection")
        ),
        argument="address",
        contains='"attributes"',
        hint="The address must be within the Rotorua Lakes district.",
    )
    transform = HtmlTransformer(
        date_getter=lambda li: li.get_text("|", strip=True).split("|")[-1],
        type_getter=lambda li: li.get_text("|", strip=True).split("|")[0],
        parse_date=date_parsers.for_format("%A %d %b %Y"),
        type_value_map={
            "Rubbish only": wt.GENERAL_WASTE,
            "Rubbish and recycling": [wt.GENERAL_WASTE, wt.RECYCLABLES],
        },
    )
