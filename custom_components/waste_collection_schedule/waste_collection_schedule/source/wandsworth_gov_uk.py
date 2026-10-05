import re
from typing import ClassVar, final

from waste_collection_schedule import date_parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.parsers import HtmlParser
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import HtmlTransformer


def _date_text(collection) -> str | None:
    """The date of ``Next: Thursday 8 October 2026`` / ``Previous: ... Completed 9.53am``."""
    match = re.search(r"\d{1,2} [A-Za-z]+ \d{4}", collection.get_text(" ", strip=True))
    return match.group(0) if match else None


def _service(collection) -> str:
    """The ``<h4>`` heading naming the service the ``div.collections`` block belongs to."""
    heading = collection.find_parent("div", class_="collections").find_previous_sibling(
        "h4"
    )
    return heading.get_text(strip=True)


@final
class Source(BaseSource):
    TITLE = "Wandsworth Council"
    DESCRIPTION = (
        "Source for Wandsworth Council for the London Borough of Wandsworth, UK."
    )
    URL = "https://www.wandsworth.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.FOOD_WASTE,
        wt.RECYCLABLES,
        wt.GENERAL_WASTE,
        wt.GARDEN_WASTE,
        wt.ELECTRONICS,
    ]

    TEST_CASES: ClassVar[dict] = {
        "100022659217": {"uprn": 100022659217},
        "100022611611": {"uprn": 100022611611},
        "10091501435": {"uprn": "10091501435"},
    }

    PARAMS = (uprn(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "You can find your UPRN by visiting "
            "[Find My Address](https://www.findmyaddress.co.uk) and entering "
            "your address details."
        ),
    }

    # The Wandsworth site can be slow, hence the long timeout.
    retrieve = HttpGetRetriever(
        "https://www.wandsworth.gov.uk/my-property/",
        params=lambda uprn, **_: {"UPRN": uprn, "propertyidentified": "Select"},
        timeout=90,
    )

    # One div.collection per "Next:" / "Previous:" date, under the h4 of its service.
    parse = HtmlParser("div.collections div.collection")

    transform = HtmlTransformer(
        date_getter=_date_text,
        type_getter=_service,
        parse_date=date_parsers.for_format("%d %B %Y"),
        skip_unparseable_dates=True,
        type_value_map={
            "Food waste": wt.FOOD_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Rubbish": wt.GENERAL_WASTE,
            "Rubbish/Garden waste": [wt.GENERAL_WASTE, wt.GARDEN_WASTE],
            "Small electrical items": wt.ELECTRONICS,
        },
    )
