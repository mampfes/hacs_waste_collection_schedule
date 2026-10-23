import json
from typing import ClassVar, final

from waste_collection_schedule import recurrence
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import district
from waste_collection_schedule.parsers import JsVarParser
from waste_collection_schedule.preprocessors import (
    ArgumentLookup,
    Compose,
    RecurrenceExpander,
    Schedule,
)
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import ICSTransformer

# The collection rounds are the placemarks of a public Google My Maps embed. The
# page ships the whole map as a JSON document held in a JavaScript string; each
# placemark carries a "nom" (district) and a "description" such as
#   "Collecte des Ordures Ménagères => Mardi, Vendredi | Matin\n
#    Collecte des déchets Recyclables => Jeudi | Après midi".

_MAP_URL = "https://www.google.com/maps/d/embed?mid=192kaU1tycR1QLrQuF_1hhIdtwghc1GDg"

_TYPE_MAP = {
    "Collecte des Ordures Ménagères": wt.GENERAL_WASTE,
    "Collecte des déchets Recyclables": wt.RECYCLABLES,
}


def _placemarks(node, found: dict[str, str]) -> None:
    """Collect ``{district: description}`` from the nested map document."""
    if not isinstance(node, list):
        return
    if (
        len(node) > 1
        and isinstance(node[0], list)
        and isinstance(node[1], list)
        and node[0]
        and node[1]
        and node[0][0] == "nom"
        and node[1][0] == "description"
    ):
        description = node[1][1][0]
        # "BASSENS 1 et BASSENS 2" is one placemark serving both districts.
        for name in node[0][1][0].split(" et "):
            found[name.strip()] = description
        found[node[0][1][0].strip()] = description
    for child in node:
        _placemarks(child, found)


def _districts(page_data: str, source) -> dict[str, str]:
    found: dict[str, str] = {}
    _placemarks(json.loads(page_data), found)
    return found


def _describe(description: str, source):
    for line in description.split("\n"):
        label, _, days = line.partition("=>")
        label = label.strip()
        for day in days.split("|")[0].split(","):
            weekday = recurrence.weekday(day)
            if label and weekday is not None:
                yield Schedule(
                    label, recurrence.next_weekday(weekday), recurrence.WEEKLY, 20
                )


@final
class Source(BaseSource):
    TITLE = "Sivom Rive Droite - Bassens"
    DESCRIPTION = "Source for Sivom Rive Droite."
    URL = "https://www.sivom-rivedroite.fr/"
    COUNTRY = "fr"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "BASSENS 3": {"district": "BASSENS 3"},
        "BASSENS 1": {"district": "BASSENS 1 et BASSENS 2"},
    }

    PARAMS = (district(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your district exactly as named on the collection map at "
            "https://www.sivom-rivedroite.fr/ (e.g. 'BASSENS 3')."
        ),
    }

    retrieve = HttpGetRetriever(_MAP_URL)
    parse = JsVarParser("_pageData")
    preprocess = Compose(
        ArgumentLookup(_districts, argument="district"),
        RecurrenceExpander(_describe),
    )
    transform = ICSTransformer(type_value_map=_TYPE_MAP)
