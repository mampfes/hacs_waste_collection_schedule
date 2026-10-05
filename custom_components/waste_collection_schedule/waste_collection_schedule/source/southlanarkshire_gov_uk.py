import re
from typing import ClassVar, final

from waste_collection_schedule import date_parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, uprn
from waste_collection_schedule.service.BartecPublicDashboard import (
    BartecDashboardParser,
    BartecDashboardRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer

_BIN_SIZE = re.compile(r"\s+(FW\s+)?\d+\s*l$", re.IGNORECASE)


@final
class Source(BaseSource):
    TITLE = "South Lanarkshire Council"
    DESCRIPTION = "Source for South Lanarkshire Council waste collection."
    URL = "https://wasteservices.southlanarkshire.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.FOOD_WASTE,
        wt.GENERAL_WASTE,
        wt.GLASS,
        wt.ORGANIC,
        wt.PAPER,
    ]

    TEST_CASES: ClassVar[dict] = {
        "1 Clincarthill Road, Glasgow, G73 2LF": {
            "postcode": "G73 2LF",
            "uprn": 484129473,
        },
        "55 Chapel Court, Glasgow, G73 1UR": {"postcode": "G73 1UR", "uprn": 484000600},
        "Flat 1 10, Burnside Lane, Hamilton, ML3 6QP": {
            "postcode": "ML3 6QP",
            "uprn": 484073020,
        },
        "2 Braxfield Road, Lanark, ML11 9AB": {
            "postcode": "ML11 9AB",
            "uprn": 484118513,
        },
    }

    PARAMS = (postcode(), uprn())

    HOWTO: ClassVar[dict] = {
        "en": "Find your UPRN using FindMyAddress "
        "(https://www.findmyaddress.co.uk/search) or UPRN.uk "
        "(https://uprn.uk) - search for your address and note the UPRN "
        "shown. Alternatively, visit "
        "https://wasteservices.southlanarkshire.gov.uk/PublicDashboard, "
        "enter your postcode, select your property, then inspect the "
        "dropdown option (right-click > Inspect Element) and note the "
        "numeric value= attribute."
    }

    retrieve = BartecDashboardRetriever(
        "https://wasteservices.southlanarkshire.gov.uk/PublicDashboard"
    )
    parse = BartecDashboardParser()
    # Rounds are named by bin colour, some with the bin's size appended
    # ("Burgundy Bin FW 140l"); the size is dropped before mapping.
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        clean=lambda label: _BIN_SIZE.sub("", label),
        type_value_map={
            "black bin": wt.GENERAL_WASTE,
            "blue bin": wt.PAPER,
            "grey bin": wt.GLASS,
            "burgundy bin": wt.ORGANIC,
            "food bin only": wt.FOOD_WASTE,
            "food and garden": wt.ORGANIC,
        },
    )
