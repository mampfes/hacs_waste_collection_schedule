from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.preprocessors import WeekdayRecurrence
from waste_collection_schedule.service.ArcGis import (
    ArcGisFeatureParser,
    ArcGisFeatureRetriever,
    parcel_centroid,
)
from waste_collection_schedule.transformers import ICSTransformer

_PROPERTY_URL = "https://maps.taupodc.govt.nz/server/rest/services/property/Rateable_Property/FeatureServer/0"
_REFUSE_URL = "https://services7.arcgis.com/S7DHOirgbYgdtrbR/arcgis/rest/services/Refuse_Collection/FeatureServer/0"


def _where(address: str, **_) -> str:
    """Properties whose address starts with the one given (so "9 Richmond
    Avenue" does not also find "79 Richmond Avenue")."""
    escaped = address.strip().replace("'", "''")
    return f"UPPER(address) LIKE UPPER('{escaped}%')"


@final
class Source(BaseSource):
    TITLE = "Taupō District Council"
    DESCRIPTION = "Source for Taupō District Council kerbside collection."
    URL = "https://www.taupodc.govt.nz"
    COUNTRY = "nz"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE]

    TEST_CASES: ClassVar[dict] = {
        "9 Richmond Avenue Taupo": {"address": "9 Richmond Avenue Taupo"},
        "72 Wharewaka Road Taupo": {"address": "72 Wharewaka Road Taupo"},
        "48 Lake Terrace Taupo": {"address": "48 Lake Terrace Taupo"},
    }

    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unknown address": {"address": "999 Nowhere Road Taupo"},
    }

    PARAMS = (street_address(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter the street address as it appears on the Taupō District "
            "Council property map, e.g. '9 Richmond Avenue Taupo'."
        ),
    }

    # The council's rateable-property layer locates the address (NZTM), and
    # its refuse layer names the collection day(s) there ("Tuesday & Friday").
    retrieve = ArcGisFeatureRetriever(
        _REFUSE_URL,
        out_fields="Collection_Day,Location",
        point=parcel_centroid(
            _PROPERTY_URL,
            where=_where,
            disambiguate_by="address",
            out_fields="address",
            result_record_count=5,
            wkid=2193,
        ),
    )
    parse = ArcGisFeatureParser(argument="address")
    preprocess = WeekdayRecurrence(
        day="Collection_Day", keys="Kerbside Collection", count=52
    )
    transform = ICSTransformer(type_value_map={"Kerbside Collection": wt.GENERAL_WASTE})
