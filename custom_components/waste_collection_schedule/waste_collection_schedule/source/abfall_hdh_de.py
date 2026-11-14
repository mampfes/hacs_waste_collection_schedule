"""Landkreis Heidenheim (Baden-Württemberg, Germany) collection calendar.

The public iCal export is a POST to
``https://mobil.abfallwirtschaft-heidenheim.de/ical.php`` with the municipality
(``gemeinde``), district (``ortsteil``) and optional street (``strasse``). Waste
type toggles (``bio``, ``garten``, ``gs``, ``rest``, ``papier``,
``papiertonne``) are sent as in the retired ICS preset and default to on.
``jahr`` is computed from the calendar year (current year plus the next, when
published); it is not hard-coded.

This source talks only to the public ``ical.php`` endpoint. It does not use the
login-protected service portal. An unknown address is answered with HTTP 500.

Replaces the generic ICS YAML preset ``doc/ics/yaml/abfall_hdh_de.yaml`` (issue
#5803). Existing configs that use the generic ``ics`` source with the same POST
URL and params keep working; the named picker entry is retired.
"""

from __future__ import annotations

import re
from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import district, municipality, street
from waste_collection_schedule.exceptions import SourceArgumentExceptionMultiple
from waste_collection_schedule.service.ICS import IcsFeedsParser, IcsSessionRetriever
from waste_collection_schedule.transformers import ICSTransformer

_EXPORT_URL = "https://mobil.abfallwirtschaft-heidenheim.de/ical.php"
# Static waste-type toggles from the retired ICS preset (1 = include).
_WASTE_TOGGLES = {
    "bio": "1",
    "garten": "1",
    "gs": "1",
    "rest": "1",
    "papier": "1",
    "papiertonne": "1",
}


def _clean_summary(summary: str) -> str:
    """Drop the trailing ``Bereitstellung`` used on every event title."""
    return re.sub(r"\s*Bereitstellung$", "", summary).strip()


def _export_data(
    gemeinde: str,
    ortsteil: str,
    year: int,
    strasse: str | None = None,
    **_: object,
) -> dict[str, str]:
    return {
        "jahr": str(year),
        "gemeinde": gemeinde,
        "ortsteil": ortsteil,
        "strasse": strasse or "",
        "tag": "0",
        "uhrzeit": "",
        **_WASTE_TOGGLES,
    }


@final
class Source(BaseSource):
    TITLE = "Landkreis Heidenheim"
    DESCRIPTION = "Source for Landkreis Heidenheim, Baden-Württemberg, Germany."
    URL = "https://abfall-hdh.de"
    COUNTRY = "de"
    SOURCE_CODEOWNERS: ClassVar[list[str]] = ["@bbr111"]
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.ORGANIC,
        wt.PAPER,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Dischingen Hofen": {
            "gemeinde": "Dischingen",
            "ortsteil": "Hofen",
        },
        "Heidenheim, Heidenheim, Hauptstraße": {
            "gemeinde": "Heidenheim",
            "ortsteil": "Heidenheim",
            "strasse": "Hauptstraße",
        },
    }

    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            "Enter your municipality (Gemeinde), district (Ortsteil) and, if "
            "the calendar asks for one, the street. The waste-type toggles of "
            "the previous ICS preset are requested automatically."
        ),
        "de": (
            "Geben Sie Ihre Gemeinde, den Ortsteil und — falls der Kalender "
            "eine verlangt — die Straße ein. Die Abfallart-Schalter des "
            "bisherigen ICS-Presets werden automatisch mitgeschickt."
        ),
    }

    PARAMS = (
        municipality("gemeinde"),
        district("ortsteil"),
        street("strasse", optional=True),
    )

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

    parse = IcsFeedsParser(parsers.IcsParser(split_at=r"\+"))

    transform = ICSTransformer(
        clean=_clean_summary,
        type_value_map={
            "Restmüll": wt.GENERAL_WASTE,
            "Gelber Sack": wt.RECYCLABLES,
            "Biomüll": wt.ORGANIC,
            "Altpapier": wt.PAPER,
            "Papiertonne": wt.PAPER,
            "Gartenabfälle": wt.GARDEN_WASTE,
        },
    )

    def _raise_empty(self) -> None:
        raise SourceArgumentExceptionMultiple(
            ("gemeinde", "ortsteil", "strasse"),
            "No calendar was returned for this municipality, district and street.",
        )
