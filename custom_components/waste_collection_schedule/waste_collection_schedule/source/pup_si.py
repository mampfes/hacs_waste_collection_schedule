from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import location_id
from waste_collection_schedule.transformers import HtmlTransformer


def _heading(li) -> str:
    """The bin heading above a date, without its colour suffix.

    Headings read "Mešana embalaža (zabojnik z rumenim pokrovom)": the part in
    brackets only describes the bin.
    """
    return li.find_previous("b").get_text(strip=True).split(" (")[0]


@final
class Source(BaseSource):
    TITLE = "PUP Saubermacher"
    DESCRIPTION = "Source for PUP Saubermacher."
    URL = "https://www.pup-saubermacher.si/"
    COUNTRY = "si"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.RECYCLABLES,
        wt.GENERAL_WASTE,
        wt.ORGANIC,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Sostanj 1": {"place_id": 412177},
        "Sostanj 2": {"place_id": 100911},
    }

    PARAMS = (location_id("place_id"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Find your place_id (Odjemno mesto number) on your monthly PUP bill, "
            "or visit https://www.pup-saubermacher.si/index.php/domov/urnik-odvoza-odpadkov"
        ),
    }

    retrieve = retrievers.Request(
        "https://www.pup-saubermacher.si/index.php/domov/urnik-odvoza-odpadkov",
        params=lambda place_id, **_: {"q": place_id},
        encoding="utf-8",
    )

    # Each bin is a bold heading followed by a list of "16.09.2026 sreda" dates.
    parse = parsers.HtmlParser("b + br + ul > li")

    transform = HtmlTransformer(
        date_getter=lambda li: li.get_text(strip=True).split(" ")[0],
        type_getter=_heading,
        type_value_map={
            "Mešana embalaža": wt.RECYCLABLES,
            "Mešani komunalni odpadki": wt.GENERAL_WASTE,
            "Biološki odpadki": wt.ORGANIC,
        },
        parse_date=date_parsers.for_format("%d.%m.%Y"),
        skip_unparseable_dates=True,
    )
