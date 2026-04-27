import csv
import logging
from datetime import datetime

import requests

from ..collection import Collection
from ..exceptions import (
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequiredWithSuggestions,
)

TITLE = "Luxembourg"
DESCRIPTION = "Source for Luxembourg waste collection using data.public.lu"
URL = "https://data.public.lu"
COUNTRY = "lu"

_LOGGER = logging.getLogger(__name__)

CSV_URL = "https://data.public.lu/fr/datasets/r/c3805ec5-7836-49a4-9983-effaf81910d0"

_ALL_STREETS = "Toutes les rues"

ICON_MAP = {
    "Biodéchets": "mdi:compost",
    "Conteneur pour déchets ménagers": "mdi:trash-can",
    "Déchets de verdure": "mdi:leaf",
    "Déchets d'équipements électriques et électroniques": "mdi:television-classic",
    "Déchets d’équipements électriques et électroniques": "mdi:television-classic",
    "Déchets encombrants": "mdi:sofa",
    "Déchets encombrants en vrac": "mdi:sofa",
    "Déchets ménagers en mélange": "mdi:trash-can",
    "Déchets recyclables": "mdi:recycle",
    "Ferraille": "mdi:nail",
    "Papier/Carton": "mdi:paper-roll",
    "Papier/Carton (commerces)": "mdi:paper-roll",
    "Papier/Carton – 40L": "mdi:paper-roll",
    "PMC": "mdi:recycle-variant",
    "SuperDrecksKëscht": "mdi:hazard-lights",
    "Valorlux": "mdi:recycle",
    "Verre": "mdi:bottle-wine",
    "Verre (commerces)": "mdi:bottle-wine",
    "Verre – 40L": "mdi:bottle-wine",
    "Vieux bois": "mdi:pine-tree",
    "Vieux vêtements": "mdi:hanger",
}

TEST_CASES = {
    "Beaufort": {"municipality": "Beaufort"},
    "Reisdorf": {"municipality": "Reisdorf"},
    "Bech - specific street": {
        "municipality": "Bech",
        "locality": "Bech",
        "street": "Am Biirk",
    },
    "Pétange - Rodange": {
        "municipality": "Pétange",
        "locality": "Rodange",
        "street": "Rue Willy Huberty",
    },
}


def _fetch_rows() -> list[dict]:
    """Fetch and parse the CSV."""
    response = requests.get(CSV_URL, timeout=30)
    response.raise_for_status()
    content = response.content.decode("utf-8-sig")
    reader = csv.DictReader(content.splitlines(), delimiter=";", quotechar='"')
    return list(reader)


class Source:
    def __init__(
        self,
        municipality: str,
        locality: str | None = None,
        street: str | None = None,
    ):
        self._commune = municipality.strip()
        self._localite = locality.strip() if locality else None
        self._rue = street.strip() if street else None

    def fetch(self) -> list[Collection]:
        rows = _fetch_rows()

        # --- Validate municipality ---
        all_communes = sorted(
            {r.get("Commune", "").strip() for r in rows if r.get("Commune", "").strip()}
        )
        if self._commune not in all_communes:
            raise SourceArgumentNotFoundWithSuggestions(
                "municipality", self._commune, all_communes
            )

        commune_rows = [
            r for r in rows if r.get("Commune", "").strip() == self._commune
        ]

        # --- Validate / resolve locality ---
        all_localites = sorted(
            {
                r.get("Localité", "").strip()
                for r in commune_rows
                if r.get("Localité", "").strip()
            }
        )

        if all_localites:
            # This municipality has per-locality rows
            if self._localite is None:
                raise SourceArgumentRequiredWithSuggestions(
                    "locality",
                    "required to narrow down the collection schedule",
                    all_localites,
                )
            if self._localite not in all_localites:
                raise SourceArgumentNotFoundWithSuggestions(
                    "locality", self._localite, all_localites
                )

            # Include rows matching the locality AND rows with no locality (municipality-wide)
            localite_rows = [
                r
                for r in commune_rows
                if r.get("Localité", "").strip() in (self._localite, "")
            ]
        else:
            # Commune has no locality breakdown — use all municipality rows
            localite_rows = commune_rows

        # --- Validate / resolve street ---
        all_rues = sorted(
            {
                r.get("Rue", "").strip()
                for r in localite_rows
                if r.get("Rue", "").strip() and r.get("Rue", "").strip() != _ALL_STREETS
            }
        )

        if all_rues:
            # Has per-street rows (beyond "Toutes les rues")
            if self._rue is None:
                raise SourceArgumentRequiredWithSuggestions(
                    "street",
                    "required to narrow down the collection schedule",
                    all_rues,
                )
            if self._rue not in all_rues:
                raise SourceArgumentNotFoundWithSuggestions(
                    "street", self._rue, all_rues
                )

            active_rows = [
                r
                for r in localite_rows
                if r.get("Rue", "").strip() in (self._rue, _ALL_STREETS)
            ]
        else:
            active_rows = localite_rows

        # --- Build collections (deduplicated by date+type) ---
        entries = []
        seen: set[tuple] = set()

        for row in active_rows:
            date_str = row.get("Date", "").strip()
            waste_type = row.get("Type de collecte", "").strip()

            if not date_str or not waste_type:
                continue

            try:
                pickup_date = datetime.strptime(date_str, "%d/%m/%Y").date()
            except ValueError:
                _LOGGER.warning("Unrecognised date format: %s", date_str)
                continue

            key = (pickup_date, waste_type)
            if key in seen:
                continue
            seen.add(key)

            entries.append(
                Collection(
                    date=pickup_date,
                    t=waste_type,
                    icon=ICON_MAP.get(waste_type, "mdi:trash-can"),
                )
            )

        return entries
