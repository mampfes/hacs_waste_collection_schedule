from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, regions, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import municipality
from waste_collection_schedule.transformers import JsonTransformer

_INDEX_URL = "https://abfall.nerdbridge.de/ical/index.json"
_DATA_URL = "https://abfall.nerdbridge.de/json/{year}/abfall-nom-{key}-{year}.json"


@final
class Source(BaseSource):
    TITLE = "Landkreis Northeim (unofficial)"
    DESCRIPTION = (
        "Unofficial waste collection schedule for Landkreis Northeim via "
        "abfall.nerdbridge.de."
    )
    URL = "https://abfall.nerdbridge.de/"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.GLASS,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Einbeck (Bezirk 2)": {"municipality": "Einbeck (Bezirk 2)"},
        "Bad Gandersheim": {"municipality": "Bad Gandersheim"},
        "Northeim (Bezirk 1)": {"municipality": "Northeim (Bezirk 1)"},
    }

    PARAMS = (municipality(),)
    REGIONS = regions.from_yaml("nerdbridge_de", municipality="title")

    HOWTO: ClassVar[dict] = {
        "en": (
            "Go to https://abfall.nerdbridge.de/ and select your municipality. "
            "Use the displayed municipality name."
        ),
        "de": (
            "Gehen Sie zu https://abfall.nerdbridge.de/ und wählen Sie Ihre "
            "Ortschaft aus. Verwenden Sie den angezeigten Namen."
        ),
    }

    # The index maps each town's name to the id its yearly JSON is named by.
    retrieve = retrievers.YearlyRetriever(
        prepare=retrievers.JsonIndexLookup(
            _INDEX_URL, argument="municipality", items=("towns",)
        ),
        fetch=retrievers.YearUrl(_DATA_URL),
    )
    parse = parsers.EachResponse(parsers.JsonParser("dates"))
    transform = JsonTransformer(
        date_key="date",
        type_key="name",
        parse_date=date_parsers.for_format("%Y-%m-%dT%H:%M:%S%z"),
        type_value_map={
            "Hausmüll 2-Wochen-Rhythmus": wt.GENERAL_WASTE,
            "Hausmüll 4-Wochen-Rhythmus": wt.GENERAL_WASTE,
            "Glassammlung": wt.GLASS,
            "Papiersammlung": wt.PAPER,
        },
    )
