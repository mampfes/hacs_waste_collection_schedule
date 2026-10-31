"""SYVALORM's published colour calendar, including next year's route changes."""

from typing import ClassVar, final

from waste_collection_schedule import parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import municipality
from waste_collection_schedule.service.FrenchColourCalendar import syvalorm_rows
from waste_collection_schedule.transformers import ICSTransformer

_INDEX = "https://www.syvalorm.fr/omr-smirgeomes/"


@final
class Source(BaseSource):
    TITLE = "SYVALORM Loir & Sarthe"
    DESCRIPTION = "Waste collection dates from SYVALORM's published calendars."
    URL = "https://www.syvalorm.fr"
    COUNTRY = "fr"
    RAISE_ON_EMPTY = True
    PARAMS = (municipality(),)
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES]
    TEST_CASES: ClassVar[dict] = {"Beillé": {"municipality": "Beillé"}}
    HOWTO: ClassVar[dict] = {
        "en": "Enter your commune as printed on the map in the calendar at https://www.syvalorm.fr/omr-smirgeomes/. Residual waste and packaging are collected together. Only dates in the published annual calendars are returned; current and future calendars are read separately to account for route changes.",
    }
    retrieve = retrievers.FanOutRetriever(
        prepare=retrievers.Lookup(
            _INDEX,
            pick=retrievers.yearly_links(r"SYVALORM-Calendrier-(20\d\d)-HD\.pdf$"),
        ),
        targets=lambda source, urls: urls,
    )
    parse = parsers.EachResponse(
        parsers.PdfWordLayoutParser(min_words=300, min_vectors=100, include_points=True)
    )
    preprocess = staticmethod(syvalorm_rows)
    transform = ICSTransformer(
        type_value_map={"general": wt.GENERAL_WASTE, "recycling": wt.RECYCLABLES}
    )
