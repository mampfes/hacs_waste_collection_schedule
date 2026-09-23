"""Mill Valley Refuse Service (MVRS), Marin County, California, USA.

Demonstrates ``FanOutRetriever`` over a fixed set of public calendars. MVRS
publishes one alternating-week residential recycling schedule for its whole
service area as three public Google Calendars, embedded on
https://www.millvalleyrefuse.com/residential-services : container recycling and
paper recycling are collected on alternating weeks (citywide), and a third
calendar carries office-closure / holiday service notices. Garbage and compost
are weekly on each address's normal route day and are not published in a
machine-readable feed.

The two recycling calendars carry no waste type in their events, so the type is
the calendar's own name (``IcsFeedsParser(labels=...)``), and each marks a
recycling week with an all-day event on every day of it, so
``CollapseWeeks`` reduces a stream to one entry per week. Each week is dated the
Sunday that starts it, shifted to the resident's ``pickup_day`` when one is
given.
"""

from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import dropdown
from waste_collection_schedule.preprocessors import CollapseWeeks
from waste_collection_schedule.retrievers import FanOutRetriever
from waste_collection_schedule.service.ICS import IcsFeedsParser
from waste_collection_schedule.transformers import ICSTransformer

_CALENDAR_URL = "https://calendar.google.com/calendar/ical/{}/public/basic.ics"

_CONTAINER_RECYCLING = "Container Recycling"
_PAPER_RECYCLING = "Paper Recycling"

# The calendars, in the order they are fetched (and labelled below).
_CALENDARS = [
    _CALENDAR_URL.format("uokfjeogcqe0daugrn58mvkgo0%40group.calendar.google.com"),
    _CALENDAR_URL.format("d5mdlvop2qp45vmstm6gs5p1kg%40group.calendar.google.com"),
    # Office-closure / holiday service notices.
    _CALENDAR_URL.format("millvalleyrefuse%40gmail.com"),
]

_WEEKDAYS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


@final
class Source(BaseSource):
    TITLE = "Mill Valley Refuse Service"
    DESCRIPTION = (
        "Source for Mill Valley Refuse Service (MVRS), Marin County, California, USA."
    )
    URL = "https://www.millvalleyrefuse.com"
    COUNTRY = "us"

    WASTE_TYPES: ClassVar[list] = [wt.RECYCLABLES, wt.PAPER, wt.OTHER]

    TEST_CASES: ClassVar[dict] = {
        "Whole service area": {},
        "With pickup day (Wednesday)": {"pickup_day": "Wednesday"},
        "With pickup day (Tuesday)": {"pickup_day": "Tuesday"},
    }

    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unknown pickup day": {"pickup_day": "Funday"},
    }

    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            "No address lookup is required. Mill Valley Refuse Service publishes a "
            "single alternating-week recycling schedule for its whole service area "
            "(Mill Valley, Corte Madera, Tiburon, Belvedere, Strawberry and "
            "unincorporated Marin). Optionally set 'pickup_day' to the weekday your "
            "street is serviced so each collection lands on your actual pickup day "
            "instead of the start of the week."
        ),
    }

    # MVRS collects Monday-Friday depending on the street. If omitted, each
    # recycling week is marked on the Sunday it begins.
    PARAMS = (dropdown("pickup_day", _WEEKDAYS, label="Pickup day", optional=True),)

    retrieve = FanOutRetriever(targets=lambda source, context: _CALENDARS)

    parse = IcsFeedsParser(
        parsers.IcsParser(),
        labels=[_CONTAINER_RECYCLING, _PAPER_RECYCLING, None],
    )

    preprocess = CollapseWeeks(
        keys=[_CONTAINER_RECYCLING, _PAPER_RECYCLING], day="pickup_day"
    )

    # The holiday calendar's own titles are the notices ("Office Closed - No
    # Collection Service"), which the raw label keeps as the description.
    transform = ICSTransformer(
        type_value_map={
            _CONTAINER_RECYCLING: wt.RECYCLABLES,
            _PAPER_RECYCLING: wt.PAPER,
            "Office Closed - Collection Service as Usual": wt.OTHER,
            "Office Closed - No Collection Service": wt.OTHER,
        },
        carry_raw_label=True,
    )
