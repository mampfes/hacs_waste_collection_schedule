import re
from typing import ClassVar, final

from waste_collection_schedule import parsers, preprocessors, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import dropdown
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.service.MarkedPdfCalendar import MarkedPdfCalendarParser
from waste_collection_schedule.transformers import JsonTransformer


def _route(record, source):
    route = source.params["route"] if source else "Aussentour"
    if route not in ("Innentour", "Aussentour", "Sigerswil"):
        raise SourceArgumentNotFoundWithSuggestions(
            "route", route, ["Innentour", "Aussentour", "Sigerswil"]
        )
    if record["type"] != "general" or route == "Innentour":
        return True
    text = " ".join(record["calendar_text"].upper().split())
    rules = re.findall(
        r"(UNGERADE|GERADE) WOCHEN:\s*(.*?)(?=(?:UNGERADE|GERADE) WOCHEN:|ALTPAPIERSAMMLUNG)",
        text,
    )
    for parity, area in rules:
        if "SIGERSWIL" in area and (("EXKL" in area) == (route == "Aussentour")):
            return record["date"].isocalendar().week % 2 == (
                1 if parity == "UNGERADE" else 0
            )
    raise ValueError("The published calendar has no recognised route restrictions")


@final
class Source(BaseSource):
    TITLE = "Grosswangen"
    DESCRIPTION = "Waste collection calendar for Grosswangen, Switzerland."
    URL = "https://www.grosswangen.ch"
    COUNTRY = "ch"
    TEST_CASES: ClassVar[dict] = {
        "TEST": {},
        "Innentour": {"route": "Innentour"},
        "Sigerswil": {"route": "Sigerswil"},
    }
    PARAMS = (
        dropdown(
            "route",
            ["Aussentour", "Innentour", "Sigerswil"],
            "Collection route",
            default="Aussentour",
        ),
    )
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.GARDEN_WASTE,
        wt.METAL,
        wt.ELECTRONICS,
    ]
    HOWTO: ClassVar[dict] = {
        "en": "Choose your refuse route: Aussentour (default), Innentour, or Sigerswil. Other collection types use the municipality-wide dates printed in the calendar. Since the v3 pipeline migration, waste types use canonical, localised names; update filters, automations and customisations using the old labels."
    }
    retrieve = retrievers.FanOutRetriever(
        prepare=retrievers.Lookup(
            "https://www.grosswangen.ch/sublinks/abfallkalender",
            pick=retrievers.yearly_links(r"entsorgungskalender-(20\d{2})\.pdf"),
        ),
        targets=lambda source, urls: urls,
        fetch=retrievers.Request(lambda target, urls, **_: target),
    )
    parse = parsers.EachResponse(
        MarkedPdfCalendarParser(
            pages=(0,),
            months=(
                "Januar",
                "Februar",
                "März",
                "April",
                "Mai",
                "Juni",
                "Juli",
                "August",
                "September",
                "Oktober",
                "November",
                "Dezember",
            ),
            weekdays=("Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"),
            year_pattern=r"ENTSORGUNGSKALENDER (20\d{2})",
            alignment="left",
            colors={
                "general": ((0.419608, 0.556863, 0.682353),),
                "organic": ((0, 0.8, 0.4),),
                "paper": ((0.6, 0.4, 0.2), (0.74902, 0.498039, 0.247059), (1, 0, 0)),
                "garden": ((0.603922, 0.341176, 0.803922),),
                "metal": ((0.698039,) * 3,),
                "electronics": ((0.698039,) * 3,),
            },
            font_colors={"paper": ((1, 0, 0),)},
        )
    )
    preprocess = preprocessors.RowFilter(_route)
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={
            "general": wt.GENERAL_WASTE,
            "organic": wt.ORGANIC,
            "paper": wt.PAPER,
            "garden": wt.GARDEN_WASTE,
            "metal": wt.METAL,
            "electronics": wt.ELECTRONICS,
        },
    )
