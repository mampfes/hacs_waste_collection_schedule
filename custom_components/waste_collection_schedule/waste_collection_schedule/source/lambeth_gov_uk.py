from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.preprocessors import RowFilter
from waste_collection_schedule.transformers import JsonTransformer

_TYPE_MAP = {
    "Domestic Food Collection Service": wt.FOOD_WASTE,
    "Domestic Recycling Collection Service": wt.RECYCLABLES,
    "Domestic Refuse Collection Service": wt.GENERAL_WASTE,
    "Domestic Garden Collection Service": wt.GARDEN_WASTE,
}


def _is_collection(record, source) -> bool:
    """A scheduled collection of a published service (ended services have no next date)."""
    return bool(record.get("NextCollectionDate")) and (
        record.get("ServiceDescription") in _TYPE_MAP
    )


@final
class Source(BaseSource):
    TITLE = "London Borough of Lambeth"
    DESCRIPTION = "Source for London Borough of Lambeth"
    URL = "https://www.lambeth.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Sternhold Avenue": {"uprn": "100021893293"},
        "Sibella Road": {"uprn": "100021889496"},
        "Hoadly Road": {"uprn": "100021852695"},
    }

    WASTE_TYPES: ClassVar[list] = [
        wt.FOOD_WASTE,
        wt.RECYCLABLES,
        wt.GENERAL_WASTE,
        wt.GARDEN_WASTE,
    ]

    PARAMS = (uprn(),)

    HOWTO: ClassVar[dict] = {
        "en": "Find your UPRN at https://www.findmyaddress.co.uk/",
    }

    retrieve = retrievers.Request(
        "https://wasteservice.lambeth.gov.uk/WhitespaceComms/GetServicesByUprn",
        method="POST",
        json=lambda uprn, **_: {
            "uprn": str(uprn),
            "includeEventTypes": False,
            "includeFlags": True,
        },
    )

    parse = parsers.JsonParser("SiteServices")

    preprocess = RowFilter(_is_collection)

    transform = JsonTransformer(
        date_key="NextCollectionDate",
        type_key="ServiceDescription",
        type_value_map=_TYPE_MAP,
        parse_date=date_parsers.for_format("%d/%m/%Y"),
    )
