import datetime
from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.preprocessors import DateFields
from waste_collection_schedule.service.ArcGis import (
    ArcGisFeatureParser,
    ArcGisFeatureRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer

_LAYER_URL = "https://www.maps.north-ayrshire.gov.uk/arcgis/rest/services/AGOL/YourLocationLive/MapServer/8"


def _date(value) -> datetime.date | None:
    """A bin's next date ("30/09/2026"); an empty field is no collection."""
    try:
        return datetime.datetime.strptime(str(value).strip(), "%d/%m/%Y").date()
    except ValueError:
        return None


@final
class Source(BaseSource):
    TITLE = "North Ayrshire Council"
    DESCRIPTION = "Source for north-ayrshire.gov.uk services for North Ayrshire"
    URL = "https://www.north-ayrshire.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.GLASS,
        wt.ORGANIC,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"uprn": "126043248"},
        "Test_002": {"uprn": 126021147},
        "Test_003": {"uprn": 126091148},
        "Test_004": {"uprn": "126000270"},
    }

    PARAMS = (uprn(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Find your UPRN at https://www.findmyaddress.co.uk/ by searching for "
            "your address."
        ),
    }

    retrieve = ArcGisFeatureRetriever(
        _LAYER_URL, where=lambda uprn, **_: f"UPRN = '{uprn}'"
    )
    parse = ArcGisFeatureParser(argument="uprn")
    # One feature per property with the next date of each bin, by lid colour.
    preprocess = DateFields(
        fields={
            "BLUE_DATE_TEXT": "Blue",
            "GREY_DATE_TEXT": "Grey",
            "PURPLE_DATE_TEXT": "Purple",
            "BROWN_DATE_TEXT": "Brown",
        },
        parse_date=_date,
    )
    transform = ICSTransformer(
        type_value_map={
            "Grey": wt.GENERAL_WASTE,
            "Blue": wt.RECYCLABLES,
            "Purple": wt.GLASS,
            "Brown": wt.ORGANIC,
        },
        carry_raw_label=True,
    )
