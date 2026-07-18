from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import api_key, text_field, waste_types
from waste_collection_schedule.regions import Region, region
from waste_collection_schedule.service.AbfallIOGraphQL import (
    AbfallIoGraphQLParser,
    AbfallIoGraphQLRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer
from waste_collection_schedule.waste_types import ALL_TYPES

# Declarative source on the abfall.io v3 GraphQL components (AbfallIoGraphQL-
# Retriever + AbfallIoGraphQLParser). The transformer turns each appointment into a
# Collection, resolving the waste-type name through the shared multilingual
# vocabulary. The provider registry lives here, in the source that owns it.

_PROVIDERS = [
    {
        "title": "Landkreis Märkisch-Oderland",
        "url": "https://www.maerkisch-oderland.de/",
        "service_id": "efb75cbd1f08fae1d4e47ae72a85c655",
    },
    {
        "title": "Holding Graz",
        "url": "https://www.holding-graz.at/",
        "service_id": "1c230a689579b6d3ddb9ceb5a56c6072",
        "country": "at",
    },
    {
        "title": "Landkreis Reutlingen",
        "url": "https://www.kreis-reutlingen.de/",
        "service_id": "15f69fab91c4cae50d9dbb5bcfd383f0",
    },
]


@final
class Source(BaseSource):
    TITLE = "Abfall.IO / AbfallPlus (GraphQL)"
    DESCRIPTION = "Source for AbfallPlus.de waste collection using the v3 GraphQL API."
    URL = "https://www.abfallplus.de"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True
    # The transformer resolves each provider's open-ended German labels through the
    # shared multilingual vocabulary, so any canonical type may appear.
    WASTE_TYPES: ClassVar[list] = list(ALL_TYPES)

    TEST_CASES: ClassVar[dict] = {
        "Altlandsberg": {
            "key": "efb75cbd1f08fae1d4e47ae72a85c655",
            "idHouseNumber": 4136,
        },
        "Strausberg": {
            "key": "efb75cbd1f08fae1d4e47ae72a85c655",
            "idHouseNumber": 5985,
        },
        "Graz (Rudersdorfer Straße 60)": {
            "key": "1c230a689579b6d3ddb9ceb5a56c6072",
            "idHouseNumber": 31972,
        },
        "Landkreis Reutlingen, Wannweil, Bahnhofstraße 5": {
            "key": "15f69fab91c4cae50d9dbb5bcfd383f0",
            "idHouseNumber": 58444,
        },
    }

    PARAMS = (
        api_key("key"),
        text_field("idHouseNumber", "House number ID"),
        waste_types("wasteTypes"),
    )

    retrieve = AbfallIoGraphQLRetriever()
    parse = AbfallIoGraphQLParser()
    transform = JsonTransformer(
        date_key="date", type_key=lambda r: r["wasteType"]["name"]
    )

    @staticmethod
    def REGIONS() -> list[Region]:
        return [
            region(
                s["title"],
                url=s["url"],
                country=s.get("country"),
                key=s["service_id"],
            )
            for s in _PROVIDERS
        ]

    def __init__(self, key, idHouseNumber, wasteTypes=None):
        super().__init__(key=key, idHouseNumber=idHouseNumber, wasteTypes=wasteTypes)
