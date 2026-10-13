from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.transformers import RowTransformer

_BASE_URL = "https://service.folkestone-hythe.gov.uk/webapp/myarea"


def _page_url(*_, uprn, **__) -> str:
    return f"{_BASE_URL}/index.php?uprn={uprn}&tab=collections"


# Flats are listed with a "Communal" prefix; both map to the same type.
_TYPE_MAP = {
    "Recycling (mixed)": wt.RECYCLABLES,
    "Paper & Card": wt.PAPER,
    "Food Waste": wt.FOOD_WASTE,
    "General Waste": wt.GENERAL_WASTE,
    "Garden Waste": wt.GARDEN_WASTE,
    "Communal Recycling (mixed)": wt.RECYCLABLES,
    "Communal Paper & Card": wt.PAPER,
    "Communal Food Waste": wt.FOOD_WASTE,
    "Communal General Waste": wt.GENERAL_WASTE,
    "Communal Garden Waste": wt.GARDEN_WASTE,
}


@final
class Source(BaseSource):
    TITLE = "Folkestone and Hythe District Council"
    DESCRIPTION = "Source for Folkestone and Hythe District Council, United Kingdom."
    URL = "https://www.folkestone-hythe.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.FOOD_WASTE,
        wt.RECYCLABLES,
        wt.PAPER,
        wt.GENERAL_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Folkestone_Test": {"uprn": 50032102},
        "Hythe_Test": {"uprn": "50019287"},
    }

    PARAMS = (uprn(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Find your UPRN at [FindMyAddress.co.uk](https://www.findmyaddress.co.uk/)."
        ),
    }

    # The collections are loaded by JavaScript from api_collections.php; the
    # page itself is requested first to obtain the session cookie.
    retrieve = retrievers.Request(
        f"{_BASE_URL}/api_collections.php",
        params=lambda *_, uprn, **__: {"uprn": str(uprn)},
        headers=lambda *_, uprn, **__: {
            "Referer": _page_url(uprn=uprn),
            "X-Requested-With": "fetch",
        },
        before=[
            retrievers.Lookup(
                lambda *_, uprn, **__: _page_url(uprn=uprn),
                pick=lambda *_, **__: None,
            )
        ],
    )

    parse = parsers.HtmlLabelledDates(
        "article.service-card",
        label=".service-title",
        date=".service-next time",
        date_pattern=r"\d{1,2} \w+ \d{4}",
        parse_date=date_parsers.for_format("%d %B %Y"),
    )

    transform = RowTransformer(type_value_map=_TYPE_MAP)
