"""SAB Magdeburg (magdeburg.de).

Demonstrates: a single static ICS GET that, only on an *empty* result, falls
back to a second lookup request for street-name suggestions. That secondary
request only fires on the error path, so it lives in a source-defined
``parse`` override (which also strips the feed's stray ``DTEND`` lines and its
title prefix) rather than in ``retrieve``.
"""

import re
from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.regions import region
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.service.ICS import ICS
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GENERAL_WASTE,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_ICS_URL = "https://st-magdeburg.server.smart-village.app/waste_calendar/export"
_STREET_LIST_URL = "https://sab.ssl.metageneric.de/app/sab_i_tp/index.php"
_PREFIX = "Abfallkalender: "


def _street_suggestions(session, street: str) -> list[str]:
    try:
        r = session.get(_STREET_LIST_URL, timeout=15)
        r.raise_for_status()
    except Exception:
        return []
    streets = re.findall(r'option value="([^"]+)"', r.text)
    query = street.split()[0].lower() if street else ""
    return [s for s in streets if query in s.lower()][:20]


@final
class Source(BaseSource):
    TITLE = "Städtischer Abfallwirtschaftsbetrieb Magdeburg"
    DESCRIPTION = "Source for SAB Magdeburg waste collection schedule."
    URL = "https://www.magdeburg.de"
    COUNTRY = "de"

    TEST_CASES: ClassVar[dict] = {
        "Halberstädter Chaussee 66": {"street": "Halberstädter Chaussee 66"},
        "Agnetenstraße 10": {"street": "Agnetenstraße 10"},
    }

    REGIONS = (
        region(
            "SAB Magdeburg Abfuhrkalender",
            url="https://sab.ssl.metageneric.de/app/sab_i_tp/index.php",
            country="de",
        ),
    )

    PARAMS = (text_field("street", label="Street and house number"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street name and house number as shown on the SAB "
            "Magdeburg website (e.g. 'Halberstädter Chaussee 66'). Search at "
            "https://sab.ssl.metageneric.de/app/sab_i_tp/index.php"
        ),
        "de": (
            "Geben Sie Ihren Straßennamen und die Hausnummer ein, wie auf der "
            "SAB Magdeburg Webseite angezeigt (z.B. 'Halberstädter Chaussee "
            "66'). Suchen Sie unter "
            "https://sab.ssl.metageneric.de/app/sab_i_tp/index.php"
        ),
    }

    RAISE_ON_EMPTY = True

    retrieve = HttpGetRetriever(
        url=_ICS_URL,
        params=lambda street, **_: {"street": street, "city": "Magdeburg"},
    )

    def parse(self, response, source=None):
        # Remove DTEND lines — they use datetime format while DTSTART uses
        # date-only, which causes icalevents comparison errors. DTEND is not
        # needed for parsing.
        text = re.sub(r"DTEND:[^\r\n]+\r?\n", "", response.text)
        events = ICS().convert(text)

        if not events and source is not None:
            street = source.params["street"]
            suggestions = _street_suggestions(source.session, street)
            if suggestions:
                raise SourceArgumentNotFoundWithSuggestions(
                    "street", street, suggestions
                )
            raise SourceArgumentNotFound("street", street)

        return events

    transform = ICSTransformer(
        type_value_map={
            "Restabfall": GENERAL_WASTE,
            "Altpapier": PAPER,
            "Gelbe Tonne": RECYCLABLES,
            "Bioabfall": ORGANIC,
        },
        clean=lambda label: (
            "Gelbe Tonne"
            if "Gelbe Tonne" in label.removeprefix(_PREFIX)
            else label.removeprefix(_PREFIX)
        ),
    )

    def __init__(self, street: str):
        super().__init__(street=street)
