"""SAB Magdeburg (magdeburg.de).

Demonstrates: a single static ICS GET that, only on an *empty* result, falls
back to a second lookup request for street-name suggestions. That secondary
request fires on the error path only, which is what ``IcsFeedsParser``'s
``suggestions`` hook is for. The feed's stray ``DTEND`` lines (a date-time end
on an all-day start) are repaired for every provider by the ICS service, and
the title prefix comes off in the transformer's ``clean``.
"""

import re
from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.retrievers import HttpGetRetriever, Suggestions
from waste_collection_schedule.service.ICS import IcsFeedsParser
from waste_collection_schedule.transformers import ICSTransformer

_ICS_URL = "https://st-magdeburg.server.smart-village.app/waste_calendar/export"
_STREET_LIST_URL = "https://sab.ssl.metageneric.de/app/sab_i_tp/index.php"
_PREFIX = "Abfallkalender: "


def _similar_streets(response, street: str, **_) -> list[str]:
    """Streets the provider does know that share the given street's first word."""
    streets = re.findall(r'option value="([^"]+)"', response.text)
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

    REGIONS = ()

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

    parse = IcsFeedsParser(
        parsers.IcsParser(),
        argument="street",
        suggestions=Suggestions(
            _STREET_LIST_URL, pick=_similar_streets, fallback=[], timeout=15
        ),
    )

    transform = ICSTransformer(
        type_value_map={
            "Restabfall": wt.GENERAL_WASTE,
            "Altpapier": wt.PAPER,
            "Gelbe Tonne": wt.RECYCLABLES,
            "Bioabfall": wt.ORGANIC,
        },
        clean=lambda label: (
            "Gelbe Tonne"
            if "Gelbe Tonne" in label.removeprefix(_PREFIX)
            else label.removeprefix(_PREFIX)
        ),
    )
