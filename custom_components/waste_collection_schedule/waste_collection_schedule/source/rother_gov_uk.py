import re
from typing import ClassVar, final

from bs4 import Tag
from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.transformers import HtmlTransformer

_PREFIX = "find-my-nearest-bindays-"


def _date_text(span: Tag) -> str:
    """ "Tuesday 6th October" without its ordinal suffix and without a year."""
    return re.sub(r"(\d)(st|nd|rd|th)", r"\1", span.get_text().strip())


def _bin_type(span: Tag) -> str:
    """The service is named by the span's class, ``find-my-nearest-bindays-refuse``."""
    for name in span.get("class") or []:
        if name.startswith(_PREFIX) and name != f"{_PREFIX}date":
            return name[len(_PREFIX) :]
    return ""


@final
class Source(BaseSource):
    TITLE = "Rother District Council"
    DESCRIPTION = "Source for Rother District Council."
    URL = "https://www.rother.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_01": {"uprn": 10002653856},
        "Test_02": {"uprn": 100060102891},
    }

    PARAMS = (uprn("uprn"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Your UPRN is shown on https://www.rother.gov.uk once you look up "
            "your address under 'Your bin days'; you can also find it on "
            "https://www.findmyaddress.co.uk/."
        ),
    }

    retrieve = retrievers.Request(
        "https://www.rother.gov.uk/wp-admin/admin-ajax.php",
        method="POST",
        data=lambda uprn, **_: {"action": "get_address_data", "uprn": uprn},
        timeout=10,
    )

    # The answer is JSON, {"success": bool, "data": "<html fragment>"}. A garden
    # waste subscription not taken out shows a "Sign up" link instead of a date.
    parse = parsers.HtmlParser(
        "span.find-my-nearest-bindays-date",
        from_json_key="data",
    )

    transform = HtmlTransformer(
        date_getter=_date_text,
        type_getter=_bin_type,
        parse_date=date_parsers.nearest_year("%A %d %B"),
        type_value_map={
            "refuse": wt.GENERAL_WASTE,
            "recycling": wt.RECYCLABLES,
            "food": wt.FOOD_WASTE,
            "garden": wt.GARDEN_WASTE,
        },
        skip_unparseable_dates=True,
    )
