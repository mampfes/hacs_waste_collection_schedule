from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.transformers import HtmlTransformer

CALENDAR_URL = "http://app.newark-sherwooddc.gov.uk/bincollection/calendar"

_TYPE_MAP = {
    "recycle": wt.RECYCLABLES,
    "refuse": wt.GENERAL_WASTE,
    "garden": wt.GARDEN_WASTE,
    "glass": wt.GLASS,
}


def _date(row) -> str:
    """The month table's "November 2025" heading plus the row's day, "Wednesday 5th"."""
    heading = row.find_parent("table").find("th").get_text(strip=True)
    day = row.find("td").get_text(strip=True).rsplit(" ", 1)[-1]
    return f"{day.rstrip('stndrh')} {heading}"


def _type(row) -> str:
    return next(c for c in row["class"] if c.startswith("bin_"))[len("bin_") :]


@final
class Source(BaseSource):
    TITLE = "Newark & Sherwood District Council"
    DESCRIPTION = "Source for Newark & Sherwood services."
    URL = "https://www.newark-sherwooddc.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.RECYCLABLES,
        wt.GENERAL_WASTE,
        wt.GARDEN_WASTE,
        wt.GLASS,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Edwinstowe": {"uprn": "010091747078"},
        "Ollerton": {"uprn": 100031463343},
        "Clipstone": {"uprn": "010091745473"},
    }

    PARAMS = (uprn(),)

    # The calendar covers twelve months; ``nc=1`` asks for the twelve after it.
    # That second page is a bonus: an error page parses to no rows.
    retrieve = retrievers.FanOutRetriever(
        targets=lambda source, context: [{}, {"nc": "1"}],
        fetch=retrievers.Request(
            CALENDAR_URL,
            params=lambda extra, context, uprn, **_: {"pid": uprn, **extra},
            raise_for_status=False,
        ),
    )
    parse = parsers.EachResponse(parsers.HtmlParser("tr[class^=bin_]"))
    transform = HtmlTransformer(
        date_getter=_date,
        type_getter=_type,
        type_value_map=_TYPE_MAP,
        parse_date=date_parsers.for_format("%d %B %Y"),
    )
