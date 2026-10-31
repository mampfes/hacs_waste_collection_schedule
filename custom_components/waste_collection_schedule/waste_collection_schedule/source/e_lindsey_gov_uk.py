import re
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.service.EastLindseyCalendar import (
    GardenCalendarParser,
    LookupParser,
    garden_calendar_urls,
)
from waste_collection_schedule.service.GossForm import (
    GossFormRetriever,
    GossStep,
    encode_variables,
)
from waste_collection_schedule.transformers import RowTransformer


@final
class Source(BaseSource):
    TITLE = "East Lindsey District Council"
    DESCRIPTION = "Source for East Lindsey District Council waste collection."
    URL = "https://www.e-lindsey.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.PAPER,
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "13 Firbeck Avenue, Skegness": {"uprn": "100030786099"},
    }

    PARAMS = (uprn(),)

    HOWTO: ClassVar[dict] = {
        "en": "Find your UPRN using a tool like findmyaddress.co.uk or finders.io."
    }

    # The form's name carries the financial year (WASTECOLLECTIONDAYS202627), so
    # it is matched rather than spelled; NLPGEL is East Lindsey's address gazetteer.
    # The reply names the next refuse, recycling, purple-bin and food-waste
    # dates and the garden-waste calendar PDF, which is read for its dated
    # collections.
    retrieve = retrievers.FanOutRetriever(
        prepare=GossFormRetriever(
            "https://www.e-lindsey.gov.uk/mywastecollections",
            form=re.compile(r"WASTECOLLECTIONDAYS\d+"),
            steps=(
                GossStep(
                    "LOOKUP_FIELD2",
                    fields=lambda response, uprn, **_: {
                        "VARIABLES": encode_variables(
                            {"ADDRESSSOURCE": "NLPGEL", "ADDRESSUPRN": str(uprn)}
                        ),
                        "LOOKUP_CHOSENADDRESS": str(uprn),
                    },
                    argument="uprn",
                ),
            ),
        ),
        targets=garden_calendar_urls,
        fetch=retrievers.Request(lambda url, *_, **__: url),
        include_prepared=True,
    )
    parse = parsers.EachResponse(
        parsers.ByBodyPrefix(
            {"%PDF-": GardenCalendarParser(label="Garden Waste")},
            default=LookupParser(),
        )
    )
    transform = RowTransformer(
        parse_date=date_parsers.DateParserAuto(),
        type_value_map={
            "Refuse": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Purple Bin": wt.PAPER,
            "Food Waste": wt.FOOD_WASTE,
            "Garden Waste": wt.GARDEN_WASTE,
        },
    )
