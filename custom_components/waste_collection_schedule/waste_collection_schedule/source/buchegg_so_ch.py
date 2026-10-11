from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import alternatives, dropdown
from waste_collection_schedule.parsers import EachResponse
from waste_collection_schedule.preprocessors import Compose, RowRelabel
from waste_collection_schedule.service.IWeb import AbfalldatenRows, abfalldaten_parser
from waste_collection_schedule.service.Localcities import (
    CalendarParser,
    Combined,
    PlaceRows,
    calendar_retriever,
)
from waste_collection_schedule.transformers import ICSTransformer

VILLAGES = [
    "Aetigkofen",
    "Aetingen",
    "Bibern",
    "Brittern",
    "Brügglen",
    "Gossliwil",
    "Hessigkofen",
    "Küttigkofen",
    "Kyburg-Buchegg",
    "Lüterswil-Gächliwil",
    "Mühledorf",
    "Tscheppach",
]

# localcities.ch names the villages for the waste paper collection; it adds the
# canton to the ambiguous ones and shortens Lüterswil-Gächliwil.
_LOCALCITIES_NAME = {
    "Bibern": "Bibern SO",
    "Lüterswil-Gächliwil": "Lüterswil",
    "Mühledorf": "Mühledorf SO",
}


def _village(source) -> str:
    return str(
        source.params.get("locality") or source.params.get("ortschaft") or ""
    ).strip()


def _belongs(place: str, source) -> bool:
    """Whether a row is for the village: a waste paper row names it (localcities.ch
    spelling), a household or green waste row lists its villages after the type."""
    village = _village(source)
    if place == _LOCALCITIES_NAME.get(village, village):
        return True
    return place.startswith(("Kehricht", "Grün")) and village.casefold() in (
        place.casefold()
    )


@final
class Source(BaseSource):
    TITLE = "Buchegg"
    DESCRIPTION = (
        "Source for waste collection schedule of Gemeinde Buchegg (SO), Switzerland."
    )
    URL = "https://www.buchegg-so.ch"
    COUNTRY = "ch"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.ORGANIC, wt.PAPER]

    TEST_CASES: ClassVar[dict] = {
        "Aetingen": {"locality": "Aetingen"},
        "Bibern": {"locality": "Bibern"},
        "Aetigkofen": {"locality": "Aetigkofen"},
        "Mühledorf": {"locality": "Mühledorf"},
        "Kyburg-Buchegg": {"locality": "Kyburg-Buchegg"},
        "Lüterswil-Gächliwil": {"locality": "Lüterswil-Gächliwil"},
        "Gossliwil": {"locality": "Gossliwil"},
        "Tscheppach (deprecated ortschaft param)": {"ortschaft": "Tscheppach"},
    }

    PARAMS = (
        alternatives(
            [dropdown("locality", VILLAGES, "Village")],
            [dropdown("ortschaft", VILLAGES, "Village (deprecated)")],
        ),
    )

    HOWTO: ClassVar[dict] = {
        "en": "Select your village from the list. `ortschaft` is the deprecated name of `locality`.",
        "de": "Wählen Sie Ihre Ortschaft aus der Liste. `ortschaft` ist der veraltete Name von `locality`.",
    }

    retrieve = calendar_retriever(
        "https://www.localcities.ch/de/entsorgung/buchegg/3385",
        also=("https://www.buchegg-so.ch/abfalldaten",),
    )
    parse = Combined(
        CalendarParser(),
        EachResponse(abfalldaten_parser(), then=AbfalldatenRows()),
    )
    preprocess = Compose(
        PlaceRows(match=_belongs),
        RowRelabel(
            vocabulary=("Kehrichtabfuhr", "Grüngutabfuhr", "Grünabfuhr", "Altpapier")
        ),
    )
    transform = ICSTransformer(
        type_value_map={
            "Kehrichtabfuhr": wt.GENERAL_WASTE,
            "Grüngutabfuhr": wt.ORGANIC,
            "Grünabfuhr": wt.ORGANIC,
            "Altpapier": wt.PAPER,
            # localcities.ch also lists the green waste, which the municipality's
            # own page gives (the source reads only the waste paper from there).
            "Grünabfälle": None,
        }
    )
