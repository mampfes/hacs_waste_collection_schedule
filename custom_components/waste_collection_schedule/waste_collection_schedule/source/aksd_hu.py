from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street
from waste_collection_schedule.preprocessors import (
    Compose,
    RecurrenceExpander,
    RowFilter,
)
from waste_collection_schedule.service.AksdCalendar import (
    CalendarParser,
    CalendarRetriever,
    in_season,
)
from waste_collection_schedule.transformers import RowTransformer


@final
class Source(BaseSource):
    TITLE = "AKSD Debrecen"
    DESCRIPTION = (
        "Source for waste collection in Debrecen, Hungary, provided by A.K.S.D. Kft."
    )
    URL = "https://www.aksd.hu"
    COUNTRY = "hu"
    TEST_CASES: ClassVar[dict] = {
        "Kinizsi utca": {"street": "Kinizsi utca"},
        "Ábel utca": {"street": "Ábel utca"},
        "Abigél utca (no accents)": {"street": "abigel utca"},
    }
    HOWTO: ClassVar[dict] = {
        "en": "Enter the street name exactly as it appears in the street search at https://www.aksd.hu/hulladeknaptar (e.g. `Kinizsi utca`). Upper/lower case and accents are ignored.",
        "de": "Geben Sie den Straßennamen genau so ein, wie er in der Straßensuche auf https://www.aksd.hu/hulladeknaptar erscheint (z. B. `Kinizsi utca`). Groß-/Kleinschreibung und Akzente werden ignoriert.",
    }
    PARAMS = (street(),)

    retrieve = CalendarRetriever()
    parse = CalendarParser()
    preprocess = Compose(
        RecurrenceExpander(lambda schedule, _: (schedule,)),
        RowFilter(in_season),
    )
    transform = RowTransformer(
        type_value_map={
            "General waste": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Garden waste (bin)": wt.GARDEN_WASTE,
            "Garden waste (bag)": wt.GARDEN_WASTE,
            "Food waste": wt.FOOD_WASTE,
        },
    )
