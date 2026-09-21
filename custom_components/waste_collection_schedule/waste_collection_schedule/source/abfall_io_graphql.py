from typing import ClassVar, final

from waste_collection_schedule import field_terms, regions
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    api_key,
    cascading_select,
    waste_types,
)
from waste_collection_schedule.service.AbfallIOGraphQL import (
    AbfallIoGraphQLParser,
    AbfallIoGraphQLRetriever,
    list_choices,
)
from waste_collection_schedule.transformers import JsonTransformer

# Declarative source on the abfall.io v3 GraphQL components (AbfallIoGraphQL-
# Retriever + AbfallIoGraphQLParser). The transformer turns each appointment into a
# Collection, resolving the waste-type name through the shared multilingual
# vocabulary. The provider registry lives here, in the source that owns it.


@final
class Source(BaseSource):
    TITLE = "Abfall.IO / AbfallPlus (GraphQL)"
    DESCRIPTION = "Source for AbfallPlus.de waste collection using the v3 GraphQL API."
    URL = "https://www.abfallplus.de"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True
    # Canonical types observed across the registered providers; the transformer
    # resolves each provider's German labels through the shared vocabulary.
    WASTE_TYPES: ClassVar[list] = [
        wt.GARDEN_WASTE,
        wt.GENERAL_WASTE,
        wt.HAZARDOUS,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

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
        "Entsorgungsbetriebe Essen": {
            "key": "51be67f3758f1fb57b420efe065c0663",
            "idHouseNumber": 74629,
        },
        "KELL Kommunalentsorgung Landkreis Leipzig GmbH, Großpösna": {
            "key": "0d7a92192ba3ae914c028ac37d73e222",
            "idHouseNumber": 1257,
        },
        "Wirtschaftsbetriebe Duisburg (WBD), Buchholz, Altenbrucher Damm 8": {
            "key": "80acad6c77fe9342ebafad29a8c58bf6",
            "idHouseNumber": 72827,
        },
        "Landkreis Göttingen, Scheden": {
            "key": "4b5702d771c82b611c386ebbc7629026",
            "idHouseNumber": 641,
        },
        "Landkreis Böblingen, Böblingen, Dagersheim": {
            "key": "76bdaac8568082d77e7a90cb41129f9b",
            "idHouseNumber": 1057,
        },
        "ASG Nordsachsen, Delitzsch-Beerendorf": {
            "key": "2085afd95285e645e15ee9623d0c5172",
            "idHouseNumber": 360435,
        },
        "Schwarzwald-Baar-Kreis, Königsfeld": {
            "key": "30628292bdd8b43db86a48f7e0d85f85",
            "idHouseNumber": 16437,
        },
        "ASO Abfall-Service Osterholz, Osterholz-Scharmbeck, Ahrensfelder Damm 4": {
            "key": "8b016df0116d1d5094fa339bebea0c65",
            "idHouseNumber": 6644,
        },
        # The whole cascade, as the config flow stores it.
        "ASO Abfall-Service Osterholz, Lübberstedt, Kampstraße 5": {
            "key": "8b016df0116d1d5094fa339bebea0c65",
            "idCity": 2654,
            "idDistrict": 24527,
            "idStreet": 24565,
            "idHouseNumber": 24717,
        },
    }

    # The config flow walks city -> (district) -> (street) -> (house number)
    # and stores the idHouseNumber the retriever reads as the last level, so a
    # configuration.yaml entry with only key + idHouseNumber keeps working.
    PARAMS = (
        api_key("key"),
        cascading_select(
            ("idCity", field_terms.CITY),
            ("idDistrict", field_terms.DISTRICT),
            ("idStreet", field_terms.STREET),
            ("idHouseNumber", field_terms.HOUSE_NUMBER),
        ),
        waste_types("wasteTypes"),
    )

    retrieve = AbfallIoGraphQLRetriever()
    parse = AbfallIoGraphQLParser()
    transform = JsonTransformer(
        date_key="date", type_key=lambda r: r["wasteType"]["name"]
    )

    REGIONS = regions.from_yaml(
        "abfall_io_graphql", country="country", key="service_id"
    )

    @classmethod
    def get_choices(cls, field: str, selections: dict) -> list[tuple[str, str]]:
        """Options for one cascade level given the levels chosen so far.

        Implements the config_params.cascading_select contract: (visible name,
        stored id) pairs walked live from the v3 GraphQL API, or [] when this
        level does not apply to the current selections.
        """
        key = selections.get("key")
        if not key:
            return []
        return list_choices(cls, str(key), field, selections)
