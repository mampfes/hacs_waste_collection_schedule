from typing import ClassVar, final

from bs4 import Tag
from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.transformers import HtmlTransformer
from waste_collection_schedule.waste_types import GENERAL_WASTE, OTHER, RECYCLABLES

# Demonstrates: HtmlTransformer + parsers.HtmlParser(selector) + legacy SSL GET.
# No custom methods needed — retrieve and parse are declarative class attributes.
# The UPRN is baked into the URL via a callable resolved against source.params.


def _cell_text(el: Tag, selector: str) -> str:
    """Return the text of the first matching child cell.

    Raises AttributeError if the cell is missing; HtmlTransformer catches that
    and skips the record, matching the prior behaviour.
    """
    cell = el.select_one(selector)
    if cell is None:
        raise AttributeError(f"no cell matching {selector!r}")
    return cell.text


@final
class Source(BaseSource):
    TITLE = "Aberdeenshire Council"
    DESCRIPTION = "Source for Aberdeenshire Council, UK."
    URL = "https://aberdeenshire.gov.uk"
    COUNTRY = "uk"

    # UPRN/property-id lookup: a wrong id yields no collections, so surface
    # it as an error instead of a silently empty calendar (#6943).
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"uprn": "000151124612"},
        "Test_002": {"uprn": "000151004105"},
        "Test_003": {"uprn": "0151035884"},
        "Test_004": {"uprn": 151170625},
    }

    PARAMS = (uprn(),)

    retrieve = retrievers.LegacySslHttpGetRetriever(
        url=lambda uprn: (
            "https://online.aberdeenshire.gov.uk/Apps/Waste-Collections/Routes/Route/"
            f"{str(uprn).zfill(12)}"
        )
    )
    # `shape` asserts the collection table is present; a redesigned page (no
    # row cells) logs the response and raises ResponseShapeError.
    parse = parsers.HtmlParser("tr", skip=1, require=["tr td"])

    # Explicit WASTE_TYPES: OTHER covers any bin types not in the map below.
    WASTE_TYPES: ClassVar[list] = [RECYCLABLES, GENERAL_WASTE, OTHER]

    transform = HtmlTransformer(
        date_getter=lambda el: _cell_text(el, "td:nth-child(1)").split(" ")[0],
        type_getter=lambda el: _cell_text(el, "td:nth-child(2)"),
        parse_date=date_parsers.for_format("%d/%m/%Y"),
        type_value_map={
            "Mixed recycling and food waste": RECYCLABLES,
            "Refuse and food waste": GENERAL_WASTE,
        },
    )
