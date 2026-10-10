import datetime
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.preprocessors import RowFilter
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import JsonTransformer

# The town's "Collectes et dépôts" event feed (RSS): one <item> per event,
# its title naming the collection ("Collecte de matières récupérables") and
# <startDay> its date (dd/mm/yyyy, "Aucune" when unset). Drop-off days at the
# municipal garage ("Dépôt de rebuts ...", "... dangereux (RDD)") are not
# collections and are skipped, as are past events (the feed keeps the whole
# year and a placeholder dated 01/01/1970).

FEED_URL = "https://www.villesblg.ca/calendrier-categories/collectes-et-depots/feed/"

_parse_date = date_parsers.for_format("%d/%m/%Y")

# Keyword in the event title -> the short label it is reported under.
_KEYWORDS = (
    ("ordures", "Ordures"),
    ("matières récupérables", "Recyclage"),
    ("résidus verts", "Résidus verts"),
    ("résidus alimentaires", "Résidus alimentaires"),
    ("encombrants", "Encombrants"),
)


def _title(item) -> str:
    return (item.findtext("title") or "").strip()


def _start_day(item) -> str:
    return (item.findtext("startDay") or "").strip()


def _is_upcoming_collection(item, source) -> bool:
    title = _title(item).lower()
    if "rebuts" in title or "dangereux" in title:
        return False
    try:
        return _parse_date(_start_day(item)) >= datetime.date.today()
    except ValueError:  # "Aucune" - no date set
        return False


def _label(title: str) -> str:
    lower = title.lower()
    for keyword, label in _KEYWORDS:
        if keyword in lower:
            return label
    return title.strip()


@final
class Source(BaseSource):
    TITLE = "Ville de Saint-Basile-le-Grand"
    DESCRIPTION = "Source for villesblg.ca waste collection calendar"
    URL = "https://www.villesblg.ca"
    COUNTRY = "ca"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
        wt.FOOD_WASTE,
        wt.BULKY_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test 1": {},
    }

    PARAMS = ()

    HOWTO: ClassVar[dict] = {
        "en": (
            "No arguments required - the calendar is the same for all residents "
            "of Saint-Basile-le-Grand."
        ),
        "fr": (
            "Aucun argument requis - le calendrier est le même pour tous les "
            "résidents de Saint-Basile-le-Grand."
        ),
    }

    retrieve = HttpGetRetriever(url=FEED_URL)
    parse = parsers.XmlParser("channel/item")
    preprocess = RowFilter(_is_upcoming_collection)
    transform = JsonTransformer(
        date_key=_start_day,
        type_key=_title,
        parse_date=_parse_date,
        clean=_label,
        type_value_map={
            "Ordures": wt.GENERAL_WASTE,
            "Recyclage": wt.RECYCLABLES,
            "Résidus verts": wt.GARDEN_WASTE,
            "Résidus alimentaires": wt.FOOD_WASTE,
            "Encombrants": wt.BULKY_WASTE,
        },
    )
