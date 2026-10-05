from typing import ClassVar, final

from waste_collection_schedule import date_parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, text_field
from waste_collection_schedule.service.LocalGovWasteCollectionAjax import (
    AjaxCollectionDaysParser,
    ajax_form_retriever,
)
from waste_collection_schedule.transformers import RowTransformer


@final
class Source(BaseSource):
    TITLE = "Rochford District Council"
    DESCRIPTION = "Source for Rochford District Council, UK."
    URL = "https://www.rochford.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GARDEN_WASTE,
        wt.RECYCLABLES,
        wt.GENERAL_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Station View, Rochford": {
            "postcode": "SS4 1AS",
            "uprn": "E05010853-10014203194",
        },
        "Windermere Ave, Hullbridge": {
            "postcode": "SS5 6JT",
            "uprn": "E05010850-100090575867",
        },
    }

    PARAMS = (
        postcode(),
        text_field("uprn", "UPRN (ward code and UPRN)"),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Go to https://www.rochford.gov.uk/bins-and-collections and enter your "
            "postcode, then press 'Find'. Open the address dropdown that appears and "
            "select your address. The 'uprn' is the value of the selected option in "
            "that dropdown: a composite of the ward code and UPRN separated by a "
            "hyphen, e.g. 'E05010853-10014203194'. You can read it from the page's "
            "HTML source (the <option value> attribute)."
        ),
    }

    retrieve = ajax_form_retriever("https://www.rochford.gov.uk/bins-and-collections")
    parse = AjaxCollectionDaysParser()
    transform = RowTransformer(
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        type_value_map={
            "Compost": wt.GARDEN_WASTE,
            "Recyclables": wt.RECYCLABLES,
            "Non-recyclables": wt.GENERAL_WASTE,
        },
    )
