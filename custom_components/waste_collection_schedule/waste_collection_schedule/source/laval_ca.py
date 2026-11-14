"""Laval (Quebec, Canada) collection calendar.

The city's public API serves an iCal feed keyed by a property roll number
(``matricule``) and a collection zone (``codeZone``):

``https://api-prd.laval.ca/ext/sitewebsearch-ext/v1/collecte/export-ics``.

Users who do not already know these values can look them up on the city's
address search page (https://www.laval.ca/recherche-par-adresse/). This source
does not scrape that page; both fields are entered as labelled text.

Replaces the generic ICS YAML preset ``doc/ics/yaml/laval_ca.yaml`` (issue
#5803). Existing configs that use the generic ``ics`` source with the same
export URL keep working; the named picker entry is retired.
"""

from __future__ import annotations

import re
from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.exceptions import SourceArgumentExceptionMultiple
from waste_collection_schedule.service.ICS import IcsFeedsParser, IcsSessionRetriever
from waste_collection_schedule.transformers import ICSTransformer

_BASE_URL = "https://www.laval.ca"
_CALENDAR_URL = "https://api-prd.laval.ca/ext/sitewebsearch-ext/v1/collecte/export-ics"
_ADDRESS_SEARCH_URL = "https://www.laval.ca/recherche-par-adresse/"


def _clean_summary(summary: str) -> str:
    """Keep the waste-type word from ``Collecte - Organique`` titles."""
    match = re.match(r"Collecte\s*-\s*(.*)$", summary)
    return match.group(1).strip() if match else summary.strip()


@final
class Source(BaseSource):
    TITLE = "Laval (QC)"
    DESCRIPTION = "Source for collection calendars in Laval, Quebec, Canada."
    URL = _BASE_URL
    COUNTRY = "ca"
    SOURCE_CODEOWNERS: ClassVar[list[str]] = ["@bbr111"]
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Default": {
            "matricule": "8546-45-9730-2-000-0000",
            "codeZone": "12",
        },
    }

    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unknown property": {"matricule": "0000", "codeZone": "00"},
    }

    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            "Enter your property roll number (matricule) and collection zone "
            f"(codeZone). If you do not know them, look up your address at "
            f"{_ADDRESS_SEARCH_URL}."
        ),
        "fr": (
            "Saisissez votre numéro de matricule et votre code de zone de "
            "collecte (codeZone). Si vous ne les connaissez pas, recherchez "
            f"votre adresse sur {_ADDRESS_SEARCH_URL}."
        ),
    }

    PARAMS = (
        text_field("matricule", "Matricule (property roll number)"),
        text_field("codeZone", "Zone code"),
    )

    retrieve = IcsSessionRetriever(
        feed_url=_CALENDAR_URL,
        feed_params=lambda matricule, codeZone, **_: {
            "matricule": matricule,
            "codeZone": codeZone,
        },
        lookahead_month=None,
    )

    parse = IcsFeedsParser(parsers.IcsParser())

    transform = ICSTransformer(
        clean=_clean_summary,
        type_value_map={
            "Déchets": wt.GENERAL_WASTE,
            "Organique": wt.ORGANIC,
            "Récupération": wt.RECYCLABLES,
        },
    )

    def _raise_empty(self) -> None:
        raise SourceArgumentExceptionMultiple(
            ("matricule", "codeZone"),
            "No calendar was returned for this matricule and zone code.",
        )
