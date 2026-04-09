import logging
import re
import urllib.parse
from datetime import date, datetime, timezone

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

_LOGGER = logging.getLogger(__name__)

TITLE = "Entsorgungsverband Völklingen (EVV)"
DESCRIPTION = "Source for Entsorgungsverband Völklingen waste collection schedules."
URL = "https://www.evv-voelklingen.de"
COUNTRY = "de"
TEST_CASES = {
    "Fürstenhausen, Kaiserstraße 2": {
        "ortsteil": "Fürstenhausen",
        "strasse": "Kaiserstraße",
        "hausnummer": "2",
    },
    "Fürstenhausen, Kaiserstraße 2, Behälterfilter": {
        "ortsteil": "Fürstenhausen",
        "strasse": "Kaiserstraße",
        "hausnummer": "2",
        "behaelter": {"Restmüll": "240", "Papier": "240"},
    },
    "Fürstenhausen, Kaiserstraße 2, Behälterfilter alle": {
        "ortsteil": "Fürstenhausen",
        "strasse": "Kaiserstraße",
        "hausnummer": "2",
        "behaelter": {"Restmüll": "240", "Papier": "240", "PVL": "1100"},
    },
    "Fürstenhausen, Kaiserstraße 2, Behälterfilter alle Papier gross": {
        "ortsteil": "Fürstenhausen",
        "strasse": "Kaiserstraße",
        "hausnummer": "2",
        "behaelter": {"Restmüll": "240", "Papier": "1100", "PVL": "1100"},
    },
    "Fürstenhausen, Zechenstraße": {
        "ortsteil": "Fürstenhausen",
        "strasse": "Zechenstraße",
    },
}

PARAM_TRANSLATIONS = {
    "de": {
        "ortsteil": "Ortsteil",
        "strasse": "Straße",
        "hausnummer": "Hausnummer",
        "behaelter": "Behältergröße (Liter)",
    },
    "en": {
        "behaelter": "Container size",
        "hausnummer": "House Number",
        "ortsteil": "District",
        "strasse": "Street",
    },
    "fr": {
        "behaelter": "Poubelle",
        "hausnummer": "Numéro civique",
        "ortsteil": "District",
        "strasse": "Rue",
    },
    "it": {
        "behaelter": "Contenitori",
        "hausnummer": "numero civico",
        "ortsteil": "frazione",
        "strasse": "Strada",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "ortsteil": "District / city part as shown in the EVV portal (e.g. 'Fürstenhausen', 'Völklingen')",
        "strasse": "Street name as shown in the EVV portal (e.g. 'Kaiserstraße')",
        "hausnummer": "House number (optional, required for some streets)",
        "behaelter": "Mapping of waste type name to container size in litres (e.g. Restmüll: '240', Papier: '1100'). Only specified waste types are filtered; others are shown for all container sizes. If omitted all container sizes are shown.",
    },
    "de": {
        "ortsteil": "Ortsteil wie im EVV-Portal angezeigt (z. B. 'Fürstenhausen', 'Völklingen')",
        "strasse": "Straßenname wie im EVV-Portal angezeigt (z. B. 'Kaiserstraße')",
        "hausnummer": "Hausnummer (optional, für manche Straßen erforderlich)",
        "behaelter": "Zuordnung von Abfallart zu Behältergröße in Litern (z. B. Restmüll: '240', Papier: '1100'). Nur angegebene Abfallarten werden gefiltert; andere werden für alle Behältergrößen angezeigt. Ohne Angabe werden alle Behältergrößen angezeigt.",
    },
}

ICON_MAP = {
    "Restmüll": "mdi:trash-can",
    "Biomüll": "mdi:leaf",
    "Biotonne": "mdi:leaf",
    "Papiertonne": "mdi:package-variant",
    "Papier": "mdi:package-variant",
    "Gelbe Tonne": "mdi:recycle",
    "Gelber Sack": "mdi:recycle",
    "LVP": "mdi:recycle",
    "Sperrmüll": "mdi:delete-circle",
    "Schadstoffmobil": "mdi:biohazard",
}

BASE_URL = "https://buerger-portal-voelklingen.azurewebsites.net/api"

# OData v3 (WCF Data Services) JSON format header
_JSON_HEADERS = {"Accept": "application/json;odata=verbose"}

# OData /Date(milliseconds)/ pattern
_ODATA_DATE_RE = re.compile(r"/Date\((-?\d+)\)/")


def _parse_odata_date(value: str) -> date | None:
    """Convert OData /Date(ms)/ string to a date object."""
    m = _ODATA_DATE_RE.search(value)
    if not m:
        return None
    ms = int(m.group(1))
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).date()


class Source:
    def __init__(
        self,
        ortsteil: str,
        strasse: str,
        hausnummer: str | int | None = None,
        behaelter: dict[str, str | int] | None = None,
    ):
        self._ortsteil = ortsteil
        self._strasse = strasse
        self._hausnummer = str(hausnummer) if hausnummer is not None else None
        # Normalize values: strip trailing "L"/"l" → {"Restmüll": "240L"} → {"Restmüll": "240"}
        self._behaelter: dict[str, str] | None = (
            {k: str(v).strip().rstrip("lL") for k, v in behaelter.items()}
            if behaelter is not None
            else None
        )

        self._orte_id: int | None = None
        self._strassen_id: int | None = None

    # ------------------------------------------------------------------
    # ID resolution
    # ------------------------------------------------------------------

    def _resolve_ids(self) -> None:
        """Resolve ortsteil and strasse names to the numeric IDs required by the API."""
        # Step 1: OrteMitOrtsteilen → flat list [{OrteId, Ortsname, Ortsteilname}]
        r = requests.get(
            f"{BASE_URL}/OrteMitOrtsteilen",
            headers=_JSON_HEADERS,
            timeout=30,
        )
        r.raise_for_status()
        orte_data: list = r.json()["d"]

        orte_id: int | None = None
        valid_ortsteile: list[str] = []
        ortsteil_key = self._ortsteil.strip().lower()

        for row in orte_data:
            name = row.get("Ortsteilname", "").strip()
            valid_ortsteile.append(name)
            if name.lower() == ortsteil_key:
                orte_id = row["OrteId"]

        if orte_id is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "ortsteil", self._ortsteil, valid_ortsteile
            )
        self._orte_id = orte_id

        # Step 2: Strassen with OData filter → [{StrassenId, Name, ...}]
        odata_filter = (
            f"Ort/OrteId eq {self._orte_id} and OrtsteilName eq '{self._ortsteil}'"
        )
        r = requests.get(
            f"{BASE_URL}/Strassen",
            params={"$filter": odata_filter, "$orderby": "Name asc"},
            headers=_JSON_HEADERS,
            timeout=30,
        )
        r.raise_for_status()
        strassen_data: list = r.json()["d"]

        strassen_map: dict[str, int] = {
            s["Name"].strip().lower(): s["StrassenId"] for s in strassen_data
        }
        str_key = self._strasse.strip().lower()
        if str_key not in strassen_map:
            raise SourceArgumentNotFoundWithSuggestions(
                "strasse", self._strasse, [s["Name"] for s in strassen_data]
            )
        self._strassen_id = strassen_map[str_key]

    # ------------------------------------------------------------------
    # Collection date fetch
    # ------------------------------------------------------------------

    def _fetch_year(self, year: int) -> list[Collection]:
        """Fetch collection dates for a given year via AbfuhrtermineAbJahr.

        The URL is built manually to avoid double-encoding by requests and to
        keep OData $ parameters un-encoded (as the server expects them).
        Single-quoted string values are encoded once with urllib.parse.quote.
        """

        def qv(value: str) -> str:
            """Single-quote and percent-encode a string value."""
            return urllib.parse.quote(f"'{value}'")

        expand = (
            "Abfuhrplan,"
            "Abfuhrplan/GefaesstarifArt/Abfallart,"
            "Abfuhrplan/GefaesstarifArt/VolumenObj"
        )
        orderby = (
            "Abfuhrplan/GefaesstarifArt/Abfallart/Name,"
            "Abfuhrplan/GefaesstarifArt/VolumenObj/VolumenWert"
        )
        haus_nr = qv(self._hausnummer) if self._hausnummer else qv("")

        url = (
            f"{BASE_URL}/AbfuhrtermineAbJahr"
            f"?$expand={urllib.parse.quote(expand, safe=',/')}"
            f"&$orderby={urllib.parse.quote(orderby, safe=',/')}"
            f"&orteId={self._orte_id}"
            f"&strassenId={self._strassen_id}"
            f"&ortsteil={qv(self._ortsteil)}"
            f"&hausNr={haus_nr}"
            f"&jahr={year}"
        )
        r = requests.get(
            url,
            headers=_JSON_HEADERS,
            timeout=30,
        )
        r.raise_for_status()
        items: list = r.json()["d"]

        entries: list[Collection] = []
        seen: set[tuple] = set()
        for item in items:
            date_val = _parse_odata_date(item.get("Termin", ""))
            if date_val is None:
                continue

            # Navigate expanded navigation properties
            abfuhrplan = item.get("Abfuhrplan") or {}
            gefaess = abfuhrplan.get("GefaesstarifArt") or {}
            abfallart = gefaess.get("Abfallart") or {}
            waste_type = abfallart.get("Name", "").strip()

            if not waste_type:
                continue

            # Filter by container size per waste type if specified
            if self._behaelter is not None and waste_type in self._behaelter:
                volumen_obj = gefaess.get("VolumenObj") or {}
                volumen_wert = str(volumen_obj.get("VolumenWert") or "").strip()
                if volumen_wert != self._behaelter[waste_type]:
                    continue

            # Deduplicate: without behaelter filter, different bin sizes can produce
            # duplicate (date, type) entries — keep only the first occurrence
            key = (date_val, waste_type)
            if key in seen:
                continue
            seen.add(key)

            icon = next(
                (v for k, v in ICON_MAP.items() if k.lower() in waste_type.lower()),
                None,
            )
            entries.append(Collection(date_val, waste_type, icon))

        return entries

    # ------------------------------------------------------------------
    # Public fetch
    # ------------------------------------------------------------------

    def fetch(self) -> list[Collection]:
        if self._orte_id is None or self._strassen_id is None:
            self._resolve_ids()

        now = datetime.now()
        years = [now.year] + ([now.year + 1] if now.month == 12 else [])

        entries: list[Collection] = []
        for year in years:
            entries.extend(self._fetch_year(year))
        return entries
