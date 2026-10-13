from typing import ClassVar, final

from waste_collection_schedule import retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street
from waste_collection_schedule.service import TsCeskyBrod
from waste_collection_schedule.transformers import ICSTransformer

# Demonstrates: a schedule page that publishes weekday rules per street instead
# of dates. The street lists are read from the live page and projected onto
# dates by the shared TsCeskyBrod expander.

_PAGE_URL = "https://www.tsceskybrod.cz/pravidelny-svoz-odpadu"


@final
class Source(BaseSource):
    TITLE = "Technické služby Český Brod"
    DESCRIPTION = "Source for waste collection in Český Brod"
    URL = "https://www.tsceskybrod.cz/"
    COUNTRY = "cz"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Monday": {"street": "nám. Arnošta z Pardubic"},
        "Tuesday": {"street": "Klučovská"},
        "Wednesday_no_accent_characters": {"street": "Jiriho Wolkera"},
        "Wednesday": {"street": "Ke Spravedlnosti"},
        "Friday": {"street": "Prokopa Velikého"},
    }

    PARAMS = (street("street"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            f"Visit {_PAGE_URL} and enter the street or location name exactly as "
            "listed in the table."
        ),
    }

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.PLASTIC,
    ]

    retrieve = retrievers.HttpGetRetriever(url=_PAGE_URL)
    parse = TsCeskyBrod.TsCeskyBrodParser()
    preprocess = TsCeskyBrod.TsCeskyBrodExpander()
    transform = ICSTransformer(
        type_value_map={
            TsCeskyBrod.RESIDUAL: wt.GENERAL_WASTE,
            TsCeskyBrod.ORGANIC: wt.ORGANIC,
            TsCeskyBrod.PAPER: wt.PAPER,
            TsCeskyBrod.PLASTIC: wt.PLASTIC,
        },
    )
