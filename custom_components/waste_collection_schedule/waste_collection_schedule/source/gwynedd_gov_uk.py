import re
from typing import ClassVar, final

from bs4 import Tag
from bs4.element import NavigableString
from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import HtmlTransformer

# Under "Next collection dates:", one list item per round: "Blue box / food
# waste: Thursday 01/10/2026", sometimes followed by a <p> note.


def _line(item: Tag) -> str:
    return " ".join(
        str(part) for part in item.children if isinstance(part, NavigableString)
    ).strip()


def _date(item: Tag) -> str:
    match = re.search(r"\d{2}/\d{2}/\d{4}", _line(item))
    if match is None:
        raise ValueError("no date")
    return match.group(0)


@final
class Source(BaseSource):
    TITLE = "Gwynedd"
    DESCRIPTION = "Source for Gwynedd."
    URL = "https://www.gwynedd.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "200003177805": {"uprn": 200003177805},
        "200003175227": {"uprn": "200003175227"},
        "10070340900": {"uprn": 10070340900},
    }

    PARAMS = (uprn(),)

    retrieve = HttpGetRetriever(
        url=lambda uprn, **_: (
            f"https://diogel.gwynedd.llyw.cymru/Daearyddol/en/LleDwinByw/Index/{uprn}"
        ),
    )
    parse = parsers.HtmlParser("h6:-soup-contains('Next collection dates') + ul > li")
    transform = HtmlTransformer(
        date_getter=_date,
        type_getter=lambda item: _line(item).split(":")[0].strip(),
        parse_date=date_parsers.for_format("%d/%m/%Y"),
        type_value_map={
            "Blue box / food waste": [wt.RECYCLABLES, wt.FOOD_WASTE],
            "Green bin": wt.GENERAL_WASTE,
            "Brown bin (garden waste)": wt.GARDEN_WASTE,
        },
    )
