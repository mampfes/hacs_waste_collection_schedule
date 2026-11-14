"""Ginsheim-Gustavsburg (Hesse, Germany) collection calendar.

The municipality calendar at https://abfallkalender.gigu.de offers a static
district choice (Ginsheim, Gustavsburg) and an iCal export via POST to
``/export/ical``. The previous ICS preset posted to ``/export``, which now
returns HTTP 405; this source uses the current form action. Export IDs were
verified against the live form and the resulting ICS titles:

* ``2`` — Ginsheim
* ``3`` — Gustavsburg

(``1`` is the on-site filter's "Alle" and only contains shared events such as
yellow-bin and hazardous collections; those shared events are already included
in each district's own export. The retired YAML howto incorrectly documented
``1`` as Ginsheim and ``2`` as Gustavsburg.)

``dateFrom`` / ``dateTo`` are computed from the calendar year (current year
plus the next, when published). All waste categories offered by the form are
requested.

Replaces the generic ICS YAML preset ``doc/ics/yaml/gigu_de.yaml`` (issue
#5803). Existing configs that use the generic ``ics`` source keep working only
if their URL is still valid; a stored POST to ``/export`` no longer is. The
named picker entry is retired.
"""

from __future__ import annotations

import re
from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import dropdown
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.service.ICS import IcsFeedsParser, IcsSessionRetriever
from waste_collection_schedule.transformers import ICSTransformer

_BASE_URL = "https://abfallkalender.gigu.de"
_EXPORT_URL = f"{_BASE_URL}/export/ical"
_CATEGORIES = [str(i) for i in range(1, 10)]

# Labels shown in the export form, mapped to the live export IDs (Nov 2026).
_DISTRICTS = {
    "Ginsheim": "2",
    "Gustavsburg": "3",
}


def _clean_summary(summary: str) -> str:
    """Drop the `` - Ginsheim`` / `` - Gustavsburg`` / `` - Alle`` suffix."""
    return re.sub(r"\s+-\s+(Ginsheim|Gustavsburg|Alle)$", "", summary).strip()


def _export_data(district: str, year: int, **_: object) -> list[tuple[str, str]]:
    try:
        district_id = _DISTRICTS[district]
    except KeyError:
        raise SourceArgumentNotFoundWithSuggestions(
            "district", district, list(_DISTRICTS)
        ) from None
    # curl_cffi stringifies list-valued ``data`` instead of repeating the key,
    # which the export form then rejects with the HTML page (HTTP 200). Flatten
    # categories to repeated ``(category, id)`` pairs.
    return [
        ("dateFrom", f"{year}-01-01"),
        ("dateTo", f"{year}-12-31"),
        ("district", district_id),
        *[("category", category) for category in _CATEGORIES],
    ]


@final
class Source(BaseSource):
    TITLE = "Ginsheim-Gustavsburg"
    DESCRIPTION = "Source for Ginsheim-Gustavsburg, Hesse, Germany."
    URL = "https://www.gigu.de"
    COUNTRY = "de"
    SOURCE_CODEOWNERS: ClassVar[list[str]] = ["@bbr111"]
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.ORGANIC,
        wt.PAPER,
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
        wt.BULKY_WASTE,
        wt.HAZARDOUS,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Ginsheim": {"district": "Ginsheim"},
        "Gustavsburg": {"district": "Gustavsburg"},
    }

    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unknown district": {"district": "Nirgendwo"},
    }

    HOWTO: ClassVar[dict[str, str]] = {
        "en": "Select your district (Ginsheim or Gustavsburg).",
        "de": "Wählen Sie Ihren Stadtteil (Ginsheim oder Gustavsburg).",
    }

    PARAMS = (dropdown("district", list(_DISTRICTS), "District"),)

    retrieve = IcsSessionRetriever(
        steps=[
            {
                "method": "POST",
                "url": _EXPORT_URL,
                "data": _export_data,
                "headers": {"Content-Type": "application/x-www-form-urlencoded"},
            }
        ],
        feed_url=None,
        lookahead_month=1,
    )

    parse = IcsFeedsParser(parsers.IcsParser())

    transform = ICSTransformer(
        clean=_clean_summary,
        type_value_map={
            "Grüne Tonne": wt.ORGANIC,
            "Blaue Tonne": wt.PAPER,
            "Graue Tonne": wt.GENERAL_WASTE,
            "Gelbe Tonne": wt.RECYCLABLES,
            "Weihnachtsbäume": wt.GARDEN_WASTE,
            "Sperrmüll": wt.BULKY_WASTE,
            "Grünmüll": wt.GARDEN_WASTE,
            "Schadstoffmobil": wt.HAZARDOUS,
            # Recycling-centre opening days, not a household collection.
            "Recyclinghof geöffnet": None,
        },
    )
