"""The "your next bin collections" widget of Jadu CMS sites (UK councils).

Councils running Jadu (Cherwell, Lichfield, Wyre, Barnet, ...) render a
property's next collections as one box per round, each with a heading and a
date without a year, the ordinal written out::

    <div class="boxed">
      <h3 class="bin-collection-tasks__heading">
        <span class="visually-hidden">Your next </span>Blue Bin
        <span class="visually-hidden"> collection</span></h3>
      <p class="bin-collection-tasks__date">29th September</p>
    </div>

:func:`tasks_parser` reads that into ``(date, label)`` rows, the year being
the one that puts the date nearest today (the list crosses the new year in
December). :func:`clean_heading` drops the screen-reader wording around the
label. Some councils use the older ``bin-collection__`` class names with the
weekday in the date ("Wednesday, 30th September"); pass the selectors and
``date_format`` for those.
"""

import re

from waste_collection_schedule import date_parsers
from waste_collection_schedule.parsers import HtmlLabelledDates

_ORDINAL = re.compile(r"(\d)(st|nd|rd|th)\b")


def strip_ordinal(text: str) -> str:
    """ "29th September" -> "29 September"."""
    return _ORDINAL.sub(r"\1", text)


def clean_heading(label: str) -> str:
    """ "Your next Blue Bin collection" -> "Blue Bin"."""
    return label.removeprefix("Your next").removesuffix("collection").strip()


def tasks_parser(
    *,
    block: str = "div.boxed:has(.bin-collection-tasks__heading)",
    heading: str = ".bin-collection-tasks__heading",
    date: str = ".bin-collection-tasks__date",
    date_format: str = "%d %B",
) -> HtmlLabelledDates:
    """``(date, heading)`` rows, one per box."""
    parse = date_parsers.nearest_year(date_format)
    return HtmlLabelledDates(
        block,
        label=heading,
        date=date,
        parse_date=lambda text: parse(strip_ordinal(text)),
    )
