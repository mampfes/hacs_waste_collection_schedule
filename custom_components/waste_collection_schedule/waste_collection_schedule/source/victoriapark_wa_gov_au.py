from typing import ClassVar, final
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from waste_collection_schedule import retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import integer, text_field
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.service.ColourWeekCalendar import WeekRows
from waste_collection_schedule.service.PdfImageCalendar import (
    ColourBin,
    ColourGridCalendarParser,
    RasterColourGridParser,
)
from waste_collection_schedule.transformers import RowTransformer


def _calendar_url(response, group, **_):
    if group not in (1, 2):
        raise SourceArgumentNotFoundWithSuggestions("group", group, ["1", "2"])
    soup = BeautifulSoup(response.text, "html.parser")
    links = [
        urljoin(response.url, str(a["href"]))
        for a in soup.select("a[href]")
        if a.get_text(" ", strip=True).lower() == f"group {group} calendar"
    ]
    if len(links) != 1:
        raise ValueError("Current Victoria Park group calendar link is missing")
    return links[0]


@final
class Source(BaseSource):
    TITLE = "Town of Victoria Park"
    DESCRIPTION = "Source for www.victoriapark.wa.gov.au Waste Collection Services"
    URL = "https://www.victoriapark.wa.gov.au"
    TEST_CASES: ClassVar[dict] = {
        "Group 1 Monday": {"group": 1, "day": "Monday"},
        "Group 2 Friday": {"group": 2, "day": "Friday"},
        "Group 1 Wednesday": {"group": 1, "day": "Wednesday"},
    }
    COUNTRY = "au"
    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unknown group": {"group": 3, "day": "Monday"},
        "Weekend": {"group": 1, "day": "Sunday"},
    }
    PARAMS = (
        integer("group", "Collection group"),
        text_field("day", "Collection weekday"),
    )
    WASTE_TYPES: ClassVar[list] = [wt.ORGANIC, wt.RECYCLABLES, wt.GENERAL_WASTE]
    HOWTO: ClassVar[dict] = {
        "en": "Find your collection group (1 or 2) and weekday on the council Bins and Collections page. The current linked July-June image calendar supplies the actual red/yellow weeks and public-holiday replacement dates. Dates stop at its published end; no fixed historical anchor is used. Since the v3 pipeline migration, waste types use canonical, localised names; update filters, automations and customisations using the old labels."
    }
    retrieve = retrievers.Request(
        lambda calendar_url, **_: calendar_url,
        before=(
            retrievers.Lookup(
                "https://www.victoriapark.wa.gov.au/residents/waste-and-recycling/bins-and-collections.aspx",
                pick=_calendar_url,
            ),
        ),
    )
    parse = RasterColourGridParser(
        ColourGridCalendarParser(
            header_matches=lambda r, g, b: (
                (80 < r < 190 and 110 < g < 200 and b > g + 10)
                or (r > 160 and g > 180 and 80 < b < r - 20)
            ),
            bins=[
                ColourBin("yellow", lambda r, g, b: r > 180 and g > 160 and b < 120),
                ColourBin("red", lambda r, g, b: r > 170 and g < 140 and b < 150),
                ColourBin(
                    "holiday",
                    lambda r, g, b: 40 < r < 180 and g > r + 25 and b > r + 10,
                ),
            ],
            start_month=7,
            ref_width=991,
            row1_ratio=0.28,
            row_pitch_ratio=0.12,
            sample_half_x=8,
            sample_half_y=7,
            fill_threshold=25,
            min_collections=250,
            min_weekday_share=0.1,
            max_per_month=25,
        ),
        complete_weekdays=(0, 1, 2, 3, 4),
    )
    preprocess = WeekRows(weekly_keys=("organic",))
    transform = RowTransformer(
        type_value_map={
            "yellow": wt.RECYCLABLES,
            "red": wt.GENERAL_WASTE,
            "organic": wt.ORGANIC,
        }
    )
