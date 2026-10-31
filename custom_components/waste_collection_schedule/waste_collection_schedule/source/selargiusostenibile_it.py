"""Selargius domestic town-centre calendar, including its two independent zones."""

import calendar
import datetime
from typing import ClassVar, final

from waste_collection_schedule import config_params
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.service.PdfMarkerCalendar import (
    Marker,
    MarkerCalendarParser,
)
from waste_collection_schedule.transformers import ICSTransformer

_PDF = (
    "https://selargiusostenibile.it/wp-content/uploads/2026/02/"
    "Calendario-SELARGIUS-26-27-UD-CENTRO-ABITATO-rev2.pdf"
)
_PAPER_AREAS = ["Selargius paese", "Su Planu e Is Corrias"]
_TYPES = {
    "Organico": wt.ORGANIC,
    "Plastica": wt.PLASTIC,
    "Vetro, alluminio e acciaio": [wt.GLASS, wt.METAL],
    "Carta Selargius paese": wt.PAPER,
    "Carta Su Planu e Is Corrias": wt.PAPER,
    "Secco A": wt.GENERAL_WASTE,
    "Secco B": wt.GENERAL_WASTE,
}


def _url(url, zone, paper_area):
    for field, value, choices in (
        ("zone", zone, ["A", "B"]),
        ("paper_area", paper_area, _PAPER_AREAS),
    ):
        if value not in choices:
            raise SourceArgumentNotFoundWithSuggestions(field, value, choices)
    return url


def _household(records, source):
    first, last = min(day for day, _ in records), max(day for day, _ in records)
    start = first.replace(day=1)
    end = last.replace(day=calendar.monthrange(last.year, last.month)[1])
    if not start <= datetime.date.today() <= end:
        raise ValueError("The calendar has expired; download the current domestic PDF")
    paper = "Carta " + source.params["paper_area"]
    residual = "Secco " + source.params["zone"]
    for day, label in records:
        if label.startswith("Carta ") and label != paper:
            continue
        if label.startswith("Secco ") and label != residual:
            continue
        yield day, label


@final
class Source(BaseSource):
    TITLE = "Selargius Sostenibile"
    DESCRIPTION = "Source for domestic waste collection in Selargius, Sardinia, Italy."
    URL = "https://selargiusostenibile.it"
    COUNTRY = "it"
    RAISE_ON_EMPTY = True
    TEST_CASES: ClassVar[dict] = {
        "Via Roma 1, zone A, Selargius paese": {
            "url": _PDF,
            "zone": "A",
            "paper_area": "Selargius paese",
        },
        "Via Pira Michelangelo 1, zone B, Selargius paese": {
            "url": _PDF,
            "zone": "B",
            "paper_area": "Selargius paese",
        },
        "Via Ariosto 1, zone A, Su Planu": {
            "url": _PDF,
            "zone": "A",
            "paper_area": "Su Planu e Is Corrias",
        },
    }
    PARAMS = (
        config_params.text_field("url", "Domestic calendar PDF URL"),
        config_params.dropdown("zone", ["A", "B"], "Residual waste zone"),
        config_params.dropdown("paper_area", _PAPER_AREAS, "Paper collection area"),
    )
    HOWTO: ClassVar[dict] = {
        "en": (
            "Copy the link to the current UTENZE DOMESTICHE / CENTRO ABITATO PDF "
            "on https://selargiusostenibile.it. Find your residual-waste zone A or B "
            "in the street list at the beginning of that PDF. Independently choose "
            "Selargius paese or Su Planu e Is Corrias for paper. Update the URL when "
            "a new calendar is published. The supported layout is the March-February "
            "booklet with two months across facing pages. Oil and textiles are "
            "collected only by appointment and have no dates in this source."
        )
    }
    retrieve = HttpGetRetriever(url=_url)
    parse = MarkerCalendarParser(
        [
            Marker(
                "Organico", (0.308, 0.644, 0.747, 0.315), width=(5, 16), height=(7, 24)
            ),
            Marker("Plastica", (0, 0.24, 0.77, 0), width=(3, 15), height=(7, 24)),
            Marker(
                "Vetro, alluminio e acciaio",
                (0.22, 0.549, 0.314),
                width=(3, 15),
                height=(7, 24),
            ),
            Marker(
                "Carta Selargius paese",
                (0.145, 0.541, 0.753),
                width=(11, 13),
                height=(15, 18),
                stroke_only=False,
            ),
            Marker(
                "Carta Su Planu e Is Corrias",
                (0.145, 0.541, 0.753),
                width=(11, 13),
                height=(15, 18),
                stroke_only=True,
            ),
        ],
        first_month=3,
        year_pattern=r"MARZO\s+(20\d{2})",
        weekdays=("LUN", "MAR", "MER", "GIO", "VEN", "SAB", "DOM"),
        row_reach=160,
        continuation_pages=True,
        include_strokes=True,
        text_markers={"A": "Secco A", "B": "Secco B"},
        min_markers=350,
    )
    preprocess = staticmethod(_household)
    transform = ICSTransformer(type_value_map=_TYPES)
