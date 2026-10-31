"""Ottawa Valley Waste Recovery Centre: Petawawa's published calendar icons."""

import datetime
from typing import ClassVar, final

from waste_collection_schedule import config_params
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.retrievers import PdfLinkRetriever
from waste_collection_schedule.service.PdfIconCalendar import (
    CollectionWeekday,
    IconMonthGridParser,
)
from waste_collection_schedule.transformers import JsonTransformer


def _current_calendar(matches):
    current = [m for m in matches if int(m[1]) <= datetime.date.today().year]
    if not current:
        raise ValueError("No published Petawawa calendar for the current year")
    return max(current, key=lambda match: int(match[1]))


@final
class Source(BaseSource):
    TITLE = "Ottawa Valley Waste Recovery Centre (Petawawa)"
    DESCRIPTION = "Source for the Town of Petawawa's curbside collection calendar."
    URL = "https://ovwrc.com"
    COUNTRY = "ca"
    RAISE_ON_EMPTY = True
    TEST_CASES: ClassVar[dict] = {
        "Petawawa Wednesday route": {"day": "Wednesday"},
        "Petawawa Thursday route": {"day": "Thursday"},
        "Petawawa Friday route": {"day": "Friday"},
    }
    PARAMS = (
        config_params.dropdown(
            "day", ["Wednesday", "Thursday", "Friday"], "Regular collection day"
        ),
    )
    HOWTO: ClassVar[dict] = {
        "en": (
            "Open https://ovwrc.com/curbside-collection-calendars/ and consult the "
            "map in the Town of Petawawa calendar to find your regular Wednesday, "
            "Thursday or Friday route. Choose that usual day, even in a holiday "
            "week; the source uses the actual printed collection dates. It reads "
            "green carts, blue paper boxes, yellow container bins, garbage and "
            "natural Christmas trees. Separate leaf/yard-waste and large-item "
            "collections are not supported. Pembroke and Laurentian Valley use "
            "other calendars and are not supported. First-time PDF parsing can "
            "take several seconds; an unchanged document reuses the parsed grid."
        )
    }
    retrieve = PdfLinkRetriever(
        index_url="https://ovwrc.com/curbside-collection-calendars/",
        pattern=r"OVWRC_CollectionsSchedule_(20\d{2})_\d{2}_Petawawa[^/]*\.pdf",
        select=_current_calendar,
    )
    parse = IconMonthGridParser(
        page=1,
        legend={
            "Green": "Green cart",
            "Paper": "Paper",
            "Containers": "Containers",
            "Garbage": "Garbage",
            "Christmas": "Christmas trees",
        },
        min_months=15,
    )
    preprocess = CollectionWeekday()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        description_key="description",
        type_value_map={
            "Green cart": wt.ORGANIC,
            "Paper": wt.PAPER,
            "Containers": wt.RECYCLABLES,
            "Garbage": wt.GENERAL_WASTE,
            "Christmas trees": wt.GARDEN_WASTE,
        },
        carry_raw_label=True,
    )
