from typing import Any, ClassVar, final
from urllib.parse import urlencode

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.date_parsers import for_format
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.retrievers import TwoStepRetriever
from waste_collection_schedule.transformers import RowTransformer
from waste_collection_schedule.waste_types import (
    GENERAL_WASTE,
    GLASS,
    ORGANIC,
    RECYCLABLES,
)

# Merri-bek's own schedule API is not an ArcGIS endpoint: an ArcGIS FeatureServer
# lookup resolves the address to a point plus a handful of rate/zone codes,
# which then feed Merri-bek's separate AddressDetails REST API for the actual
# schedule. That "lookup -> key -> schedule" shape is exactly what the generic,
# platform-agnostic retrievers.TwoStepRetriever expresses -- it is not
# ArcGIS-specific, so it is used declaratively here rather than a hand-rolled
# two-request retrieve().

FEATURE_QUERY_URL = "https://services6.arcgis.com/8L5sOwfzTAvcvQur/ArcGIS/rest/services/WasteServices4Bin/FeatureServer/0/query"
ADDRESS_DETAILS_URL = "https://www.merri-bek.vic.gov.au/api/AddressDetails"

# AddressDetails response key -> waste-type key emitted for that key's dates.
ALL_BIN_DAYS = "allBinDays"
ALL_RECYCLE_DAYS = "allRecycleDays"
ALL_FOGO_DAYS = "allFogoDays"
ALL_GLASS_DAYS = "allGlassDays"

_TYPE_MAP = {
    ALL_BIN_DAYS: GENERAL_WASTE,
    ALL_RECYCLE_DAYS: RECYCLABLES,
    ALL_FOGO_DAYS: ORGANIC,
    ALL_GLASS_DAYS: GLASS,
}


def _lookup_url(address: str, **_: Any) -> str:
    params = {
        "where": f"EZI_Address LIKE '{address}%'",
        "outFields": (
            "EZI_Address,Waste_Rate_Code,Recycling_Rate_Code,"
            "FOGO_Rate_Code,Glass_Rate_Code,Day,Zone,GlassWeek"
        ),
        "returnGeometry": "true",
        "f": "json",
    }
    return f"{FEATURE_QUERY_URL}?{urlencode(params)}"


def _extract_feature(lookup_response, source) -> dict:
    lookup_response.raise_for_status()
    features = lookup_response.json().get("features")
    if not features:
        raise SourceArgumentNotFound("address", source.params["address"])
    return features[0]


def _schedule_url(feature: dict, address: str, **_: Any) -> str:
    attr = feature["attributes"]
    geom = feature["geometry"]
    params = {
        "xPoint": geom["x"],
        "yPoint": geom["y"],
        "wasteDay": attr["Day"],
        "wasteRateCode": attr["Waste_Rate_Code"],
        "recycleRateCode": attr["Recycling_Rate_Code"],
        "fogoRateCode": attr["FOGO_Rate_Code"],
        "glassRateCode": attr["Glass_Rate_Code"],
        "zone": attr["Zone"],
        "glassWeekNumber": attr["GlassWeek"],
        "address": attr["EZI_Address"],
        "cpage": "86612",
    }
    return f"{ADDRESS_DETAILS_URL}?{urlencode(params)}"


@final
class Source(BaseSource):
    TITLE = "Merri-bek City Council"
    DESCRIPTION = "Source for Merri-bek City Council (VIC) rubbish collection."
    URL = "https://www.merri-bek.vic.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Monday": {"address": "1 Vincent Street Oak Park 3046"},
        "Tuesday": {"address": "10 Gaffney Street Coburg North 3058"},
    }

    PARAMS = (text_field("address", "Street Address"),)

    retrieve = TwoStepRetriever(
        lookup_url=_lookup_url,
        extract=_extract_feature,
        schedule_url=_schedule_url,
    )
    transform = RowTransformer(
        parse_date=for_format("%d-%m-%Y"),
        type_value_map=_TYPE_MAP,
    )

    def __init__(self, address: str):
        super().__init__(address=address.strip())

    def parse(self, response, source: "Source | None" = None) -> list[tuple[str, str]]:
        response.raise_for_status()
        data = response.json()
        if not data:
            raise SourceArgumentNotFound("address", self.params["address"])
        schedule = data[0]

        seen: set[tuple[str, str]] = set()
        records: list[tuple[str, str]] = []
        for api_key in _TYPE_MAP:
            for collection_date in schedule.get(api_key, []):
                record = (collection_date, api_key)
                if record in seen:
                    continue
                seen.add(record)
                records.append(record)
        return records
