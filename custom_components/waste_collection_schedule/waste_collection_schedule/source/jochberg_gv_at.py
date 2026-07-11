from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.parsers import IcsParser
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.service.RiSKommunalAT import ICS_AQN, ICS_PATH
from waste_collection_schedule.transformers import ICSTransformer

# Demonstrates: a RiSKommunal municipality that publishes only an ICS feed
# (CalendarService.ashx) rather than the HTML calendar. There is no dedicated
# RiSKommunal ICS retriever in the pipeline yet, so this is expressed with the
# generic HttpGetRetriever + IcsParser, reusing the platform's public
# ICS_AQN/ICS_PATH constants to build the one static feed URL. The single
# "Restmüll" calendar resolves via the shared vocabulary; no type_value_map
# entry is needed.

_BASE_URL = "https://www.jochberg.gv.at"
_GNR = "312"
_DO = "MjI1NTczMjE0"
_ICS_URL = f"{_BASE_URL}{ICS_PATH}?aqn={ICS_AQN}&sprache=1&gnr={_GNR}&do={_DO}"


@final
class Source(BaseSource):
    TITLE = "Jochberg"
    DESCRIPTION = "Waste collection schedule for the municipality of Jochberg, Austria."
    URL = _BASE_URL
    COUNTRY = "at"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@bbr111"]

    TEST_CASES: ClassVar[dict] = {
        "Jochberg": {},
    }

    PARAMS = ()

    retrieve = HttpGetRetriever(url=_ICS_URL)
    parse = IcsParser()
    transform = ICSTransformer()
