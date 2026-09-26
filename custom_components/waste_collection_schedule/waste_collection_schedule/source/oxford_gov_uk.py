from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, uprn
from waste_collection_schedule.preprocessors import (
    Compose,
    Deduplicate,
    TextGroupedDates,
)
from waste_collection_schedule.service.JaduXfp import XfpFormRetriever
from waste_collection_schedule.transformers import ICSTransformer

# The results page states each round in a sentence: "Your next refuse
# collections: Thursday 01 October 2026, Thursday 15 October 2026". The two
# dates are the same when only one is scheduled.

_TYPE_MAP = {
    "Your next refuse collections": wt.GENERAL_WASTE,
    "Your next recycling collections": wt.RECYCLABLES,
    "Your next garden collections": wt.GARDEN_WASTE,
    "Your next food collections": wt.FOOD_WASTE,
    # Ends the last round's sentence, so later text on the page is not read
    # as its dates.
    "Your Bin Zone is": None,
}


@final
class Source(BaseSource):
    TITLE = "Oxford City Council"
    DESCRIPTION = "Source for oxford.gov.uk services for Oxford, UK."
    URL = "https://oxford.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
        wt.FOOD_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Magdalen Road": {"uprn": "100120827594", "postcode": "OX4 1RB"},
        "Oliver Road (brown bin too)": {"uprn": "100120831804", "postcode": "OX4 2JH"},
    }

    PARAMS = (uprn(), postcode())

    HOWTO: ClassVar[dict] = {
        "en": (
            "Go to https://www.oxford.gov.uk/xfp/form/142 and enter your "
            "postcode. The UPRN is the option value of your address in the "
            "address dropdown (browser dev tools); you can also look it up on "
            "https://www.findmyaddress.co.uk/."
        ),
    }

    retrieve = XfpFormRetriever(
        "https://www.oxford.gov.uk/xfp/form/142",
        page="12",
        question="q6ad4e3bf432c83230a0347a6eea6c805c672efeb",
    )
    parse = parsers.HtmlTextParser()
    preprocess = Compose(
        TextGroupedDates(
            keys=_TYPE_MAP,
            date_pattern=r"\b(?P<day>\d{1,2}) (?P<month>[A-Za-z]+) (?P<year>\d{4})\b",
        ),
        Deduplicate(),
    )
    transform = ICSTransformer(type_value_map=_TYPE_MAP)
