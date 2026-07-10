from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, uprn
from waste_collection_schedule.transformers import JsonTransformer
from waste_collection_schedule.waste_types import (
    FOOD_WASTE,
    GARDEN_WASTE,
    GENERAL_WASTE,
    RECYCLABLES,
    WasteType,
)

# Demonstrates: parsers.XmlParser on a real, namespaced SOAP-style XML feed,
# transformed declaratively with JsonTransformer callable keys.
#
# The Whitespace WS endpoint returns one <Collection> element per event, each
# with dedicated <Date> and <Service> children, under the
# http://webservices.whitespacews.com/ namespace. XmlParser does
# root.findall(path) (lxml ElementPath) with no namespace map, so the namespace
# is baked into the path using the {uri}tag form. JsonTransformer's date_key and
# type_key accept callables, which here read each element's <Date>/<Service>
# children (the namespace baked into the path) and map the service to a canonical
# WasteType. An invalid UPRN simply yields a feed with no <Collection> nodes,
# so RAISE_ON_EMPTY surfaces a "check your UPRN" error to the HA UI.

_NS = "{http://webservices.whitespacews.com/}"

_SERVICE_MAP: dict[str, WasteType] = {
    "Refuse Collection Service": GENERAL_WASTE,
    "Recycle Collection Service": RECYCLABLES,
    "Garden Collection Service": GARDEN_WASTE,
    "Food Waste Collection Service": FOOD_WASTE,
}


@final
class Source(BaseSource):
    TITLE = "Cannock Chase Council"
    DESCRIPTION = (
        "Source for cannockchasedc.gov.uk services for Cannock Chase Council, UK."
    )
    URL = "https://www.cannockchasedc.gov.uk"
    COUNTRY = "uk"
    API_URL = "https://ccdc.opendata.onl/DynamicCall.dll"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@markvp"]

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"uprn": "100031640287", "postcode": "WS15 1DN"},
        "Test_002": {"uprn": "100031640289", "postcode": "WS15 1DN"},
        "Test_003": {"uprn": "100031624295", "postcode": "WS11 6DY"},
        "Test_004": {"uprn": "10008163213", "postcode": "WS11 7UD"},
    }

    PARAMS = (uprn(), postcode())

    HOWTO: ClassVar[dict] = {
        "en": (
            "Find your UPRN by visiting https://www.findmyaddress.co.uk/ and "
            "entering your address details, then provide it together with your "
            "postcode."
        ),
    }

    RAISE_ON_EMPTY = True

    retrieve = retrievers.http_post
    # No min_nodes= here: an unknown UPRN legitimately yields zero <Collection>
    # nodes, which RAISE_ON_EMPTY turns into a "check your UPRN" error blaming
    # the right field. A shape guard would instead misreport that as a changed
    # feed (ResponseShapeError), which fires before the empty-result check.
    parse = parsers.XmlParser(f".//{_NS}Collection")
    transform = JsonTransformer(
        date_key=lambda el: el.findtext(f"{_NS}Date"),
        type_key=lambda el: el.findtext(f"{_NS}Service"),
        type_value_map=_SERVICE_MAP,
        parse_date=date_parsers.for_format("%d/%m/%Y %H:%M:%S"),
    )

    WASTE_TYPES: ClassVar[list] = [GENERAL_WASTE, RECYCLABLES, GARDEN_WASTE, FOOD_WASTE]

    def __init__(self, uprn: str | int, postcode: str):
        super().__init__(uprn=str(uprn).zfill(12), postcode=postcode)
        self._data = {
            "Method": "CollectionDates",
            "UPRN": self.params["uprn"],
            "Postcode": self.params["postcode"],
        }
