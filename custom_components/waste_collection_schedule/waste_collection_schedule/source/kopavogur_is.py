import datetime
from typing import ClassVar, final

from waste_collection_schedule import parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import district
from waste_collection_schedule.service.KopavogurCalendar import ROUNDS, CalendarParser
from waste_collection_schedule.transformers import ICSTransformer

_PDF_URL = "https://eldri.kopavogur.is/static/files/Sorphirda/sorphirdudagatal-{year}-{round}.pdf"


def _calendar_urls(_source, _context) -> list[str]:
    """One calendar PDF per round for the current year."""
    year = datetime.date.today().year
    return [_PDF_URL.format(year=year, round=name) for name in ROUNDS]


@final
class Source(BaseSource):
    TITLE = "Kópavogsbær"
    DESCRIPTION = "Source for Kópavogur, Iceland (Kubbur collection calendar)"
    URL = "https://www.kopavogur.is"
    COUNTRY = "is"
    SOURCE_CODEOWNERS: ClassVar[list[str]] = ["@rhubarbgarden"]
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "Vesturbær": {"district": "Vesturbær - Smárahverfi"},
        "Austurbær sunnan": {"district": "Austurbær sunnan Álfhólsvegar"},
        "Austurbær norðan": {"district": "Austurbær norðan Álfhólsvegar"},
        "Lindir": {"district": "Lindir, Salir, Kórar, Hvörf og Þing"},
    }

    PARAMS = (district(),)

    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            "Enter the collection district (zone) as shown in the legend of the "
            "calendar: Vesturbær - Smárahverfi, Austurbær sunnan Álfhólsvegar, "
            "Austurbær norðan Álfhólsvegar or Lindir, Salir, Kórar, Hvörf og Þing. "
            "A partial, case-insensitive match is accepted."
        ),
    }

    retrieve = retrievers.FanOutRetriever(
        targets=_calendar_urls,
        fetch=retrievers.Request(lambda url, _context, **_: url, timeout=30),
    )
    parse = parsers.EachResponse(CalendarParser())
    transform = ICSTransformer(
        type_value_map={
            "Almennt sorp og matarleifar": wt.GENERAL_WASTE,
            "Pappi/pappír og plast": wt.RECYCLABLES,
        }
    )
