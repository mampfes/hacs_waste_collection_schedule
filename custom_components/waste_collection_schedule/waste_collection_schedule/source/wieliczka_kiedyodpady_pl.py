from typing import ClassVar, final

from waste_collection_schedule import preprocessors, retrievers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, house_number, integer, street
from waste_collection_schedule.service import Kiedyodpady
from waste_collection_schedule.source.kiedyodpady_pl import Source as KiedySource


@final
class Source(BaseSource):
    TITLE = "Wieliczka Kiedy Odpady (Deprecated)"
    DESCRIPTION = "Source for Wieliczka Kiedy Odpady schedules."
    URL = "https://wieliczka.kiedyodpady.pl"
    COUNTRY = "pl"
    TEST_CASES: ClassVar[dict] = {
        "Wieliczka (miasto), ul. Adama Asnyka, pozostałe": {
            "city": "Wieliczka (miasto)",
            "street": "ul. Adama Asnyka",
            "number": "pozostałe",
        }
    }
    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unknown locality": {"city": "zzzznotreal"},
        "Unknown house number": {
            "city": "Wieliczka (miasto)",
            "street": "ul. Adama Asnyka",
            "number": "zzzznotreal",
        },
    }
    PARAMS = (
        city(),
        street(optional=True),
        house_number("number", optional=True),
        integer("lookahead_days", "Lookahead days", default=35),
    )
    WASTE_TYPES = KiedySource.WASTE_TYPES
    HOWTO: ClassVar[dict] = {
        "en": "This source name remains deprecated; prefer kiedyodpady_pl with municipality=wieliczka. Existing city, street and number arguments remain unchanged. Copy them from the public Wieliczka address selector. The default lookahead remains 35 days. Types now use the canonical platform vocabulary; update filters and customisations using old labels. Combined metals/plastics dates yield both canonical categories."
    }
    retrieve = retrievers.WithParams(
        Kiedyodpady.ScheduleRetriever(), municipality="wieliczka"
    )
    parse = Kiedyodpady.ScheduleParser()
    preprocess = preprocessors.Compose(
        preprocessors.LogOnce(
            "wieliczka_kiedyodpady_pl is deprecated; use kiedyodpady_pl instead",
            logger=__name__,
        ),
        preprocessors.DefaultPreprocessor(),
    )
    transform = KiedySource.transform
