from typing import ClassVar, final

from waste_collection_schedule import parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.transformers import HtmlTransformer


def _cell(row, index: int) -> str | None:
    cells = row.find_all("td")
    return cells[index].get_text(strip=True) if len(cells) > 4 else None


def _scheme(row) -> str | None:
    """The scheme column, reduced to the fraction it collects."""
    name = (_cell(row, 1) or "").lower()
    if "rest" in name and "mad" in name:
        return "rest-mad"
    if "plast" in name and "glas" in name:
        return "plast-glas"
    if "papir" in name:
        return "papir"
    return None


@final
class Source(BaseSource):
    TITLE = "Reno Djurs"
    DESCRIPTION = "Reno Djurs collections for Djursland"
    URL = "https://renodjurs.dk"
    COUNTRY = "dk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.FOOD_WASTE,
        wt.RECYCLABLES,
        wt.PAPER,
    ]

    TEST_CASES: ClassVar[dict] = {
        "TestCase1": {"id": "46000"},
        "TestCase2": {"id": "45000"},
        "TestCase3": {"id": 44000},
        "12320": {"id": 12320},
    }

    PARAMS = (text_field("id", "Address ID"),)

    HOWTO: ClassVar[dict] = {
        "en": "Open https://minside.renodjurs.dk, search your address and copy the number after `id=` in the address bar of the 'Ordninger' page.",
    }

    retrieve = retrievers.Request(
        "https://minside.renodjurs.dk/Ordninger.aspx",
        params=lambda id, **_: {"id": str(id)},
    )
    parse = parsers.HtmlParser("table.table tr", require=["table.table"])
    transform = HtmlTransformer(
        date_getter=lambda row: _cell(row, 4),
        type_getter=_scheme,
        type_value_map={
            "rest-mad": [wt.GENERAL_WASTE, wt.FOOD_WASTE],
            "plast-glas": wt.RECYCLABLES,
            "papir": wt.PAPER,
        },
        skip_unparseable_dates=True,
    )
