from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    city,
    district,
    house_number,
    street,
)
from waste_collection_schedule.retrievers import LookupChainRetriever
from waste_collection_schedule.service.Blupassion import (
    BlupassionApp,
    BlupassionParser,
)
from waste_collection_schedule.transformers import RowTransformer

# The AWB Bad Kreuznach app runs on the blupassion City App backend (appId 44);
# the address walk and the day-frequency calendars are the platform's, in
# ``service/Blupassion.py``.
_APP = BlupassionApp(
    44,
    city="ort",
    part_of_city="stadtteil",
    street="strasse",
    house_number="nummer",
)


@final
class Source(BaseSource):
    TITLE = "AWB Bad Kreuznach"
    DESCRIPTION = "Source for AWB Bad Kreuznach."
    URL = "https://www.awb-kh.de"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Hargesheim": {"ort": "Hargesheim"},
        "Bad Kreuznach": {
            "ort": "Bad Kreuznach",
            "strasse": "adalbert-stifter-straße",
            "nummer": "3",
        },
        "Bad Kreuznach OT Bad Münster-Ebernburg": {
            "ort": "Bad Kreuznach OT Bad Münster-Ebernburg",
            "strasse": "am Götzenfels",
        },
        "Stromberg": {"ort": "Stromberg", "stadtteil": "Schindeldorf"},
        "Altenbamberg": {"ort": "Altenbamberg"},
    }

    PARAMS = (
        city(field="ort"),
        district(field="stadtteil", optional=True),
        street(field="strasse", optional=True),
        house_number(field="nummer", optional=True),
    )

    retrieve = LookupChainRetriever(
        steps=_APP.steps(),
        url=_APP.calendar_url,
        params=_APP.calendar_params,
        headers={"Accept": "application/json, text/plain, */*"},
    )
    parse = BlupassionParser()
    transform = RowTransformer()
