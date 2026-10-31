"""Ipswich Borough Council (England) bin collection dates."""

import re
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, preprocessors, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import location_id
from waste_collection_schedule.transformers import RowTransformer

# The street's "Collections by month" page: an <h4> per month ("November 2026")
# followed by a <dl> whose <dt> names a bin and whose <dd> lists that month's
# days ("3rd, 10th, 17th, Wed 23rd, 31st"). An unknown id answers 404.
SCHEDULE_URL = "https://app.ipswich.gov.uk/bin-collection-better-recycling/months/{}"
_DAY = re.compile(r"(\d{1,2})(?:st|nd|rd|th)\b", re.IGNORECASE)


def _month_dates(dt, source) -> list[tuple[str, str]]:
    """``(date, bin)`` rows for one <dt>: its <dd>'s days in the <h4>'s month."""
    heading = dt.find_previous("h4")
    days = dt.find_next_sibling("dd")
    if heading is None or days is None:
        return []
    month = heading.get_text(strip=True)
    label = dt.get_text(strip=True)
    return [(f"{day} {month}", label) for day in _DAY.findall(days.get_text())]


@final
class Source(BaseSource):
    TITLE = "Ipswich Borough Council"
    DESCRIPTION = (
        "Source for waste collection schedules provided by Ipswich Borough Council, UK."
    )
    URL = "https://www.ipswich.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "High Street (id 549)": {"location_id": 549},
    }

    PARAMS = (location_id(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Visit https://app.ipswich.gov.uk/bin-collection-better-recycling/ "
            "and search for your street. Once your schedule is displayed the URL "
            "ends with /weeks/<number>: use that number as the location ID "
            "(e.g. 549). Since the v3 pipeline migration, waste types use "
            "canonical, localised names. Update filters, automations and "
            "customisations using the old labels."
        ),
    }

    WASTE_TYPES: ClassVar[list] = [
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
        wt.GENERAL_WASTE,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    retrieve = retrievers.Request(
        lambda location_id, **_: SCHEDULE_URL.format(int(str(location_id).strip())),
        raise_for_status=False,
    )

    parse = parsers.ArgumentGuard(
        parsers.HtmlParser("article dl dt"),
        argument="location_id",
        contains="Collections by month",
    )
    preprocess = preprocessors.ExplodeList(_month_dates)

    # Blue: plastics, cans, glass and cartons; green-lidded: paper and card.
    transform = RowTransformer(
        parse_date=date_parsers.for_format("%d %B %Y"),
        type_value_map={
            "Large food waste caddy": wt.FOOD_WASTE,
            "Black refuse bin": wt.GENERAL_WASTE,
            "Blue recycling bin": wt.RECYCLABLES,
            "Green-lidded recycling bin": wt.PAPER,
            "Brown garden waste bin": wt.GARDEN_WASTE,
        },
    )
