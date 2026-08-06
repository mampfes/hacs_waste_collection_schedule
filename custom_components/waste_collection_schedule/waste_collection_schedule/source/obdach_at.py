from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.service.RiSKommunalAT import (
    RiSKommunalParser,
    RiSKommunalRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer

_BASE_URL = "https://www.obdach.gv.at"


@final
class Source(BaseSource):
    TITLE = "Marktgemeinde Obdach"
    DESCRIPTION = "Source for Marktgemeinde Obdach, AT"
    URL = "https://www.obdach.gv.at/"
    COUNTRY = "at"
    RAISE_ON_EMPTY = True

    # Derived by replaying the cassette, which this source could not do before:
    # it had none, so nothing had ever checked what it produces. Biomüll
    # resolves via the shared vocabulary rather than being listed below.
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.ORGANIC,
    ]

    TEST_CASES: ClassVar[dict] = {
        "TestSource": {},
    }

    PARAMS = ()

    # Like Gössendorf, Obdach's calendar defaults to today only, so requesting
    # it bare returned whatever happened to fall on the day the sensor updated:
    # one collection, or none. ``bdatum`` opens the window, and the install
    # paginates its list rendering ten dates at a time.
    retrieve = RiSKommunalRetriever(
        base_url=_BASE_URL,
        query_params={
            "bdatum": "31.12.9999",
            "detailonr": "225229638",
            "menuonr": "225229639",
            "typ": "225229638",
        },
    )
    parse = RiSKommunalParser(paginate_list=True)

    # Biomüll auto-resolves via the shared vocabulary. "Gelber Sack/Tonne"
    # combines both recyclables-bin names in one label and misses the
    # separate "gelber sack"/"gelbe tonne" aliases, so it needs an explicit
    # entry; the Restmüll labels carry a collection-area suffix.
    # "Altstoffsammelzentrum" is the recycling depot's opening days, not a
    # round. It used to be preserved verbatim, which put a waste type on a
    # user's calendar for days when nothing is collected; it is now dropped, on
    # the same reasoning as Angern's "Recyclinghof".
    transform = ICSTransformer(
        type_value_map={
            "Gelber Sack/Tonne": wt.RECYCLABLES,
            "Restmüll Abfuhrbereich 1": wt.GENERAL_WASTE,
            "Restmüll Abfuhrbereich 2": wt.GENERAL_WASTE,
            "Altstoffsammelzentrum": None,
        },
    )
