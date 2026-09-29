import datetime
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, uprn
from waste_collection_schedule.transformers import HtmlTransformer

_URL = "https://ilforms.wiltshire.gov.uk/wastecollectiondays/wastecollectioncalendar"
_MONTHS = 7

# The calendar answers one month per request, so a schedule is seven of them,
# from the current month on.


def _months(source, _context) -> list[tuple[int, int]]:
    """``(year, month)`` for the current month and the six after it."""
    today = datetime.date.today()
    months = []
    for offset in range(_MONTHS):
        index = today.month - 1 + offset
        months.append((today.year + index // 12, index % 12 + 1))
    return months


@final
class Source(BaseSource):
    TITLE = "Wiltshire Council"
    DESCRIPTION = "Source for wiltshire.gov.uk services for Wiltshire Council"
    URL = "https://wiltshire.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GLASS,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "standard_uprn": {"uprn": "100121085972", "postcode": "BA149QP"},
        "short_uprn": {"uprn": "10093279003", "postcode": "SN128FF"},
        "padded_uprn": {"uprn": "010093279003", "postcode": "SN128FF"},
    }

    PARAMS = (uprn(), postcode())

    retrieve = retrievers.FanOutRetriever(
        targets=_months,
        fetch=retrievers.Request(
            _URL,
            method="POST",
            params=lambda target, _context, uprn, postcode, **_: {
                "Postcode": postcode,
                "Uprn": str(uprn).zfill(12),
                "Month": target[1],
                "Year": target[0],
            },
        ),
    )
    parse = parsers.EachResponse(parsers.HtmlParser("a.event[data-original-datetext]"))
    transform = HtmlTransformer(
        date_getter=lambda el: el["data-original-datetext"],
        type_getter=lambda el: el["data-original-title"],
        parse_date=date_parsers.for_format("%A %d %B, %Y"),
        type_value_map={
            "Household waste": wt.GENERAL_WASTE,
            "Mixed dry recycling (blue lidded bin)": wt.RECYCLABLES,
            "Mixed dry recycling (blue lidded bin) and glass (black box or basket)": [
                wt.RECYCLABLES,
                wt.GLASS,
            ],
            "Chargeable garden waste": wt.GARDEN_WASTE,
        },
    )
