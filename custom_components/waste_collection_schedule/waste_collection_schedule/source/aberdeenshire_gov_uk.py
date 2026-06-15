from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.transformers import HtmlTransformer
from waste_collection_schedule.waste_types import GENERAL_WASTE, OTHER, RECYCLABLES

# Demonstrates: HtmlTransformer + parsers.HtmlParser(selector) + legacy SSL GET.
# No custom methods needed — retrieve and parse are declarative class attributes.
# The UPRN is baked into the URL via a callable resolved against source.params.


class Source(BaseSource):
    TITLE = "Aberdeenshire Council"
    DESCRIPTION = "Source for Aberdeenshire Council, UK."
    URL = "https://aberdeenshire.gov.uk"
    COUNTRY = "uk"

    TEST_CASES = {
        "Test_001": {"uprn": "000151124612"},
        "Test_002": {"uprn": "000151004105"},
        "Test_003": {"uprn": "0151035884"},
        "Test_004": {"uprn": 151170625},
    }

    PARAMS = [uprn()]

    retrieve = retrievers.LegacySslHttpGetRetriever(
        url=lambda uprn: (
            "https://online.aberdeenshire.gov.uk/Apps/Waste-Collections/Routes/Route/"
            f"{str(uprn).zfill(12)}"
        )
    )
    parse = parsers.HtmlParser("tr", skip=1)  # table rows, skip header

    # Explicit WASTE_TYPES: OTHER covers any bin types not in the map below.
    WASTE_TYPES = [RECYCLABLES, GENERAL_WASTE, OTHER]

    transformer = HtmlTransformer(
        date_getter=lambda el: el.select_one("td:nth-child(1)").text.split(" ")[0],
        type_getter=lambda el: el.select_one("td:nth-child(2)").text,
        parse_date=date_parsers.for_format("%d/%m/%Y"),
        type_value_map={
            "Mixed recycling and food waste": RECYCLABLES,
            "Refuse and food waste": GENERAL_WASTE,
        },
    )
