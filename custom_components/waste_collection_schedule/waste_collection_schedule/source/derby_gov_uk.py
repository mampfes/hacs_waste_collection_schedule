from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    house_number,
    location_id,
    text_field,
)
from waste_collection_schedule.field_terms import POSTCODE
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import HtmlTransformer

# Derby's bin-day page lists one ``div.binresult`` per bin and date: the bin is
# the image's alt text ("Black bin") and the date the leading <strong>
# ("Thursday, 15 October 2026:").


@final
class Source(BaseSource):
    TITLE = "Derby City Council"
    DESCRIPTION = "Source for Derby.gov.uk services for Derby City Council, UK."
    URL = "https://derby.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
        wt.FOOD_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        # Derby City council wants specific addresses, and they can't
        # be business addresses. Hopefully these are suitably generic..
        "22A Wood Road, Chaddesden, Derby, DE21 4LU": {
            # The flat above Bargain Hut on Wood Road
            "premises_id": "10010688168"
        },
        "Allestree Home Improvements, 512 Duffield Road, Derby, DE22 2DL": {
            "premises_id": "100030310335"
        },
    }

    # post_code and house_number are not used any more; they stay optional so
    # existing configurations keep working.
    PARAMS = (
        location_id("premises_id"),
        text_field("post_code", term=POSTCODE, optional=True),
        house_number(optional=True),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Search your address on <https://secure.derby.gov.uk/binday>. The url "
            "will contain your premises ID, e.g. "
            "`https://secure.derby.gov.uk/binday/BinDays/10010688168?...` where "
            "`10010688168` is the premises ID. Leave post_code and house_number "
            "empty: they are no longer used."
        ),
    }

    retrieve = HttpGetRetriever(
        url=lambda premises_id, **_: (
            f"https://secure.derby.gov.uk/binday/Bindays/{premises_id}"
        ),
    )
    parse = parsers.HtmlParser("div.binresult")
    transform = HtmlTransformer(
        date_getter=lambda result: result.strong.get_text(strip=True),
        type_getter=lambda result: result.img["alt"],
        parse_date=date_parsers.for_format("%A, %d %B %Y:"),
        skip_unparseable_dates=True,
        type_value_map={
            "Black bin": wt.GENERAL_WASTE,
            "Blue bin": wt.RECYCLABLES,
            "Brown bin": wt.GARDEN_WASTE,
            "Food bin": wt.FOOD_WASTE,
        },
    )
