import datetime
from typing import ClassVar, final

from bs4 import Tag
from waste_collection_schedule import parsers, recurrence, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import dropdown
from waste_collection_schedule.transformers import HtmlTransformer

# Demonstrates: HtmlTransformer over one table with a French long date
# ("lundi, 28 septembre 2026"). The date getter returns a date directly, so no
# date parser is involved; the month name resolves through recurrence.month().

_TOURS = {"A": 1, "B": 2}

# Types whose cell carries collecting instructions after the name.
_WITH_INSTRUCTIONS = ("Déchets toxiques", "Cartons en vrac")


def _row_type(row: Tag) -> str:
    """The collection type, without the collecting instructions some carry."""
    cell = row.select("td")[1].get_text(strip=True)
    for prefix in _WITH_INSTRUCTIONS:
        if cell.startswith(prefix):
            return prefix
    return cell


def _row_date(row: Tag) -> datetime.date:
    """``lundi, 28 septembre 2026`` as a date."""
    text = row.select("td")[2].get_text(strip=True).split(", ")[1]
    day, month_name, year = text.split()
    month = recurrence.month(month_name)
    if month is None:
        raise ValueError(f"unknown month {month_name!r}")
    return datetime.date(int(year), month, int(day))


@final
class Source(BaseSource):
    TITLE = "Esch-sur-Alzette"
    DESCRIPTION = "Source script for administration.esch.lu, communal website of the city of Esch-sur-Alzette in Luxembourg"
    URL = "https://esch.lu"
    COUNTRY = "lu"
    IGNORE_DUPLICATES_DEFAULT = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.PAPER,
        wt.ORGANIC,
        wt.GLASS,
        wt.RECYCLABLES,
        wt.HAZARDOUS,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Zone A": {"zone": "A"},
        "Zone B": {"zone": "B"},
    }

    PARAMS = (dropdown("zone", list(_TOURS), label="Zone"),)

    retrieve = retrievers.HttpGetRetriever(
        url="https://administration.esch.lu/dechets/",
        params=lambda zone, **_: {"street": 0, "tour": _TOURS[zone]},
    )
    parse = parsers.HtmlParser("#garbage-table tr", require=["#garbage-table"])
    transform = HtmlTransformer(
        date_getter=_row_date,
        type_getter=_row_type,
        type_value_map={
            "Poubelle ménage": wt.GENERAL_WASTE,
            "Container ménage": wt.GENERAL_WASTE,
            "Papier": wt.PAPER,
            "Organique": wt.ORGANIC,
            "Verre": wt.GLASS,
            "Valorlux": wt.RECYCLABLES,
            "Déchets toxiques": wt.HAZARDOUS,
            # The cardboard collection is for companies only.
            "Cartons en vrac": None,
        },
        # "Poubelle ménage" and "Container ménage" are both general waste and
        # can fall on the same day.
        carry_raw_label=True,
    )
