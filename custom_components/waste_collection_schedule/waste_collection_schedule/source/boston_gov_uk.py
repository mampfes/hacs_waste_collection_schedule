from typing import ClassVar, final

from waste_collection_schedule import date_parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, postcode
from waste_collection_schedule.service.GossForm import (
    GossFormRetriever,
    GossStep,
    GossVariablesParser,
    serialized_variables,
)
from waste_collection_schedule.transformers import JsonTransformer

_FORM = "BBCWASTECOLLECTIONSV2"


def _first_uprn(response, **_) -> str:
    """The UPRN of the first address the search offered, placeholders aside."""
    options = (
        serialized_variables(response, _FORM)
        .get("ADDRESSUPRN_OPTIONDATA", {})
        .get("value", [])
    )
    for option in options:
        uprn, label = option[0], option[1]
        if uprn and str(uprn).strip() and label != "Select address":
            return str(uprn)
    return ""


@final
class Source(BaseSource):
    TITLE = "Boston Borough Council"
    DESCRIPTION = (
        "Source for www.boston.gov.uk services for Boston Borough Council, UK."
    )
    URL = "https://www.boston.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.PAPER,
    ]

    TEST_CASES: ClassVar[dict] = {
        "43 Tarry Hill, Swineshead, PE20 3LW": {
            "postcode": "PE20 3LW",
            "property": "43",
        },
        "The Old Vicarage, Church Close, PE21 6NE": {
            "postcode": "PE21 6NE",
            "property": "10",
        },
    }

    PARAMS = (postcode(), house_number("property", optional=True))

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your postcode and property name or number as they appear on the "
            "Boston Borough Council website: "
            "https://www.boston.gov.uk/article/27449/Your-Waste-Collections"
        ),
    }

    retrieve = GossFormRetriever(
        "https://www.boston.gov.uk/article/27449/Your-Waste-Collections",
        form=_FORM,
        steps=(
            GossStep(
                "COLLECTIONS_START10",
                fields=lambda response, postcode, property=None, **_: {
                    "COLLECTIONS_SEARCHPROPERTYNAMENUMBER": property or "",
                    "COLLECTIONS_SEARCHPOSTCODE": postcode,
                },
                argument="postcode",
            ),
            GossStep(
                "ADDRESS_NEXT3",
                fields=lambda response, **_: {
                    "ADDRESS_ADDRESSUPRN": _first_uprn(response)
                },
            ),
        ),
    )
    parse = GossVariablesParser(_FORM, "collectionsData", "value", "jobs")
    transform = JsonTransformer(
        date_key="NextDate",
        type_key="Type",
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        type_value_map={
            "refusebin": wt.GENERAL_WASTE,
            "recyclingbin": wt.RECYCLABLES,
            "papercardbin": wt.PAPER,
            "greenbin": wt.GARDEN_WASTE,
            "foodbin": wt.FOOD_WASTE,
        },
    )
