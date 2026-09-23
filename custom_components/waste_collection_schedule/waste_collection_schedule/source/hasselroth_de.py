"""Gemeinde Hasselroth (Hesse, Germany).

Demonstrates ``IcsIndexRetriever``'s labelled selection with ``every_match``:
the municipality publishes one ICS file per district (Ortsteil) *and year* on a
stable page, and regenerates each download link (with a fresh access token in
the query string) every year, so the current links are always discovered rather
than hardcoded. Each link names its district in its label
("Download: Kalender 2026 Neuenhasslau.ics"), and the user's district selects
every file carrying that name, so the schedule is the years together.
"""

import re
from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import district
from waste_collection_schedule.service.ICS import IcsFeedsParser, IcsIndexRetriever
from waste_collection_schedule.transformers import ICSTransformer

_PAGE_URL = "https://www.hasselroth.de/buergerportal/rathaus/abfallentsorgung/ics/"

# Matches link labels like "Download: Kalender 2026 Neuenhasslau.ics"
_CALENDAR_LINK_PATTERN = re.compile(r"Kalender\s+\d{4}\s+([^.]+)\.ics", re.IGNORECASE)


# The feed labels each pickup "<bin> <district code> [(<variant>)]", e.g.
# "Restmüll Ndm (ohne rot)" or "Sperr. Gartenabfälle Go". The bin is the first
# word; the rest says which district and which schedule variant it is.
_TYPE_VALUE_MAP = {
    "altpapier": wt.PAPER,
    "biomüll": wt.ORGANIC,
    "gelbe": wt.RECYCLABLES,
    "restmüll": wt.GENERAL_WASTE,
    "sperrmüll": wt.BULKY_WASTE,
    "sperr.": wt.BULKY_WASTE,
}


def _bin(label: str) -> str:
    return label.split(" ")[0]


def _district_name(anchor) -> str | None:
    """The district a download link serves, read off its title or text."""
    label = anchor.get("title") or anchor.get_text() or anchor["href"]
    match = _CALENDAR_LINK_PATTERN.search(label)
    return match.group(1).strip() if match else None


@final
class Source(BaseSource):
    TITLE = "Gemeinde Hasselroth"
    DESCRIPTION = "Source for Gemeinde Hasselroth, Hesse, Germany waste collection."
    URL = "https://www.hasselroth.de"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
        wt.BULKY_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Neuenhasslau": {"district": "Neuenhasslau"},
        "Niedermittlau": {"district": "Niedermittlau"},
        "Gondsroth": {"district": "Gondsroth"},
    }

    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            "The Hasselroth district (Ortsteil), e.g. 'Neuenhasslau', "
            "'Niedermittlau' or 'Gondsroth'."
        ),
        "de": (
            "Der Hasselrother Ortsteil, z. B. 'Neuenhasslau', 'Niedermittlau' "
            "oder 'Gondsroth'."
        ),
    }

    PARAMS = (district(),)

    retrieve = IcsIndexRetriever(
        index_url=_PAGE_URL,
        pattern=r"\.ics",
        label=_district_name,
        argument="district",
        every_match=True,
    )

    parse = IcsFeedsParser(parsers.IcsParser())

    # The label's tail ("(alle)" against "(ohne rot)") tells two different
    # schedules of one bin apart, so the raw label is kept as the description.
    transform = ICSTransformer(
        clean=_bin, type_value_map=_TYPE_VALUE_MAP, carry_raw_label=True
    )
