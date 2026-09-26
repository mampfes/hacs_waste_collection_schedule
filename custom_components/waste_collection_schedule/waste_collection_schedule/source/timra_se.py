from typing import ClassVar, final

from waste_collection_schedule import date_parsers, preprocessors
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.service.ArcGis import (
    ArcGisDistinctValues,
    ArcGisFeatureParser,
    ArcGisFeatureRetriever,
    WebMapLayer,
)
from waste_collection_schedule.transformers import RowTransformer

# Timrå republishes the schedule each year as a new hosted service (its name
# carries the publish date) and repoints this web map at it.
_LAYER = WebMapLayer(
    "https://kartor.timra.se/portal/sharing/rest/content/items/"
    "f77cab36aa3043d0b9dfeaeb679a23bd/data"
)


def _quote(value: str) -> str:
    return value.replace("'", "''")


@final
class Source(BaseSource):
    TITLE = "Timrå kommun"
    DESCRIPTION = "Source for Timrå kommun (Sweden) waste collection."
    URL = "https://www.timra.se"
    COUNTRY = "se"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "Aspen 195": {"address": "Aspen 195"},
        "Tuna 112": {"address": "Tuna 112"},
        "Torsboda 130": {"address": "Torsboda 130"},
    }

    PARAMS = (street_address("address"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter the property address exactly as shown on the Timrå kommun "
            "waste collection map (Belägenhetsadress), e.g. 'Aspen 195'. You can "
            "look up the address at https://kartor.timra.se/portal/apps/experiencebuilder/experience/?id=186668f9efeb458c926d85a978fe85de"
        ),
    }

    retrieve = ArcGisFeatureRetriever(
        _LAYER,
        where=lambda address, **_: f"UPPER(beladress) = UPPER('{_quote(address)}')",
        out_fields="beladress,karl1,karl2",
        result_record_count=1,
    )
    parse = ArcGisFeatureParser(
        argument="address",
        suggestions=ArcGisDistinctValues(
            _LAYER,
            "beladress",
            where=lambda address, **_: (
                f"UPPER(beladress) LIKE UPPER('%{_quote(address)}%')"
            ),
            limit=10,
        ),
    )
    # Each four-compartment bin's field lists this year's dates as "d/m".
    preprocess = preprocessors.DateFields(
        fields={"karl1": "Fyrfackskärl 1", "karl2": "Fyrfackskärl 2"},
        parse_date=date_parsers.in_current_year("%d/%m"),
        split=",",
    )
    transform = RowTransformer(
        type_value_map={
            "Fyrfackskärl 1": wt.RECYCLABLES,
            "Fyrfackskärl 2": wt.GENERAL_WASTE,
        },
    )
