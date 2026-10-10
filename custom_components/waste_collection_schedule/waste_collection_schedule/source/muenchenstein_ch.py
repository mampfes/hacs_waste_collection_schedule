import datetime
from typing import ClassVar, final

from waste_collection_schedule import recurrence
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.field_terms import DISTRICT
from waste_collection_schedule.preprocessors import RecurrenceExpander, Schedule
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.service.IWeb import (
    AbfalldatenRows,
    abfalldaten_parser,
)
from waste_collection_schedule.transformers import ICSTransformer

# Münchenstein runs on the i-web CMS: the dated collections (paper, cardboard,
# shredding service, ...) come from the /abfuhrdaten table, filtered to the
# waste district by its name or id (491 Ost, 492 West).
#
# The weekly residual-waste collection ("Kehricht und Kleinsperrgut brennbar")
# is not listed with dates. The website only names its weekday per district:
# Tuesday in Abfuhrkreis Ost, Friday in Abfuhrkreis West. The next four
# occurrences, today included, are projected from that.

KEHRICHT = "Kehricht und Kleinsperrgut brennbar"
_EAST = ("Abfuhrkreis Ost", "491")
_TUESDAY, _FRIDAY = 1, 4


def _kehricht(_record, source):
    district = str(source.params["waste_district"]).strip() if source else ""
    weekday = _TUESDAY if district in _EAST else _FRIDAY
    today = datetime.date.today()
    first = today + datetime.timedelta(days=(weekday - today.weekday()) % 7)
    yield Schedule(KEHRICHT, first, recurrence.WEEKLY, 4)


_DATED_ROWS = AbfalldatenRows(area="waste_district")
_KEHRICHT_ROWS = RecurrenceExpander(_kehricht)


def _rows(records, source=None):
    yield from _DATED_ROWS(records, source)
    yield from _KEHRICHT_ROWS([None], source)


@final
class Source(BaseSource):
    TITLE = "Münchenstein"
    DESCRIPTION = "Source for Muenchenstein waste collection."
    URL = "https://www.muenchenstein.ch"
    COUNTRY = "ch"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.PAPER,
        wt.GARDEN_WASTE,
        wt.RECYCLABLES,
        wt.BULKY_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Abfuhrkreis Ost": {"waste_district": "Abfuhrkreis Ost"},
        "Abfuhrkreis West": {"waste_district": "492"},
    }

    PARAMS = (text_field("waste_district", term=DISTRICT),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your waste district, Abfuhrkreis Ost or Abfuhrkreis West, or "
            "its ID: 491 for Ost, 492 for West."
        ),
        "de": (
            "Geben Sie Ihren Abfuhrkreis ein, Abfuhrkreis Ost oder Abfuhrkreis "
            "West, oder seine ID: 491 für Ost, 492 für West."
        ),
    }

    retrieve = HttpGetRetriever(url="https://www.muenchenstein.ch/abfuhrdaten")
    parse = abfalldaten_parser()
    preprocess = staticmethod(_rows)
    transform = ICSTransformer(
        # Paper and cardboard are separate rounds; keep the label to tell them
        # apart.
        carry_raw_label=True,
        type_value_map={
            KEHRICHT: wt.GENERAL_WASTE,
            "Papierabfuhr": wt.PAPER,
            "Kartonabfuhr": wt.PAPER,
            "Häckseldienst": wt.GARDEN_WASTE,
            # Large scrap-metal items, not packaging metal.
            "Metallabfuhr": wt.RECYCLABLES,
            "Grobsperrgut (brennbar)": wt.BULKY_WASTE,
        },
    )
