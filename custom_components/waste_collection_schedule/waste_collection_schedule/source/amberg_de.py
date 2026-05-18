import re
import xml.etree.ElementTree as ET
import zipfile
from datetime import date, timedelta
from io import BytesIO

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequired,
)

TITLE = "Amberg"
DESCRIPTION = "Source for the city of Amberg (Bavaria), Germany."
URL = "https://www.amberg.de"
COUNTRY = "de"

TEST_CASES = {
    "Street: Adalbert-Stifter-Str. (zone A1)": {"street": "Adalbert-Stifter-Str."},
    "Zone: C4 direct": {"zone": "C4"},
    "Street: Barbarastr. (zone B2)": {"street": "Barbarastr."},
}

PARAM_TRANSLATIONS = {
    "en": {"street": "Street", "zone": "Zone"},
    "de": {"street": "Straße", "zone": "Abfuhrgebiet"},
}

PARAM_DESCRIPTIONS = {
    "en": {
        "street": "Street name as it appears in the city's street directory (e.g. Adalbert-Stifter-Str.). Either street or zone must be provided.",
        "zone": "Zone code (e.g. A1, C4). Either street or zone must be provided.",
    },
    "de": {
        "street": "Straßenname wie im Strassenverzeichnis der Stadt (z. B. Adalbert-Stifter-Str.). Entweder Straße oder Abfuhrgebiet muss angegeben werden.",
        "zone": "Abfuhrgebiet (z. B. A1, C4). Entweder Straße oder Abfuhrgebiet muss angegeben werden.",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Visit https://amberg.de/abfallberatung/abfuhrkalender-2026, look up your street in the table, and note the zone code (e.g. A1). You can then use either the street name or the zone code directly.",
    "de": "Besuchen Sie https://amberg.de/abfallberatung/abfuhrkalender-2026, suchen Sie Ihre Straße in der Tabelle, und notieren Sie das Abfuhrgebiet (z. B. A1). Sie können dann entweder den Straßennamen oder das Abfuhrgebiet direkt verwenden.",
}

ICON_MAP = {
    "Rest- und Biomüll": "mdi:trash-can",
    "Papiertonne": "mdi:package-variant",
    "Gelber Sack": "mdi:recycle",
    "Sperrmüll": "mdi:sofa",
    "Häckselgut": "mdi:leaf",
    "Problemmüll": "mdi:biohazard",
}

# All valid zone codes (letter A–E, sub-number 1–4)
VALID_ZONES = [
    f"{letter}{num}"
    for letter in ("A", "B", "C", "D", "E")
    for num in ("1", "2", "3", "4")
]

# Mapping of Dateneingabe column index to waste type name
# Col F (idx 5) = Rest, Col G (idx 6) = Bio (same bin as Rest, skip)
# Col H (idx 7) = Papiertonne, Col I (idx 8) = Gelber Sack
# Col J (idx 9) = Problemmüll, Col K (idx 10) = Häckselgut, Col L (idx 11) = Sperrmüll
WASTE_COLUMNS = {
    5: "Rest- und Biomüll",
    7: "Papiertonne",
    8: "Gelber Sack",
    9: "Problemmüll",
    10: "Häckselgut",
    11: "Sperrmüll",
}

# Excel serial date epoch
_EXCEL_EPOCH = date(1899, 12, 30)

# Base URL for Abfallberatung page (used for year discovery)
_ABFALL_PAGE = "https://amberg.de/abfallberatung/"
# URL templates
_STREET_DIR_URL = "https://amberg.de/fileadmin/Abfallberatung/Abfuhrkalender/{year}/ICS/{year}_Strassenverzeichnis.json"
_XLSX_URL = "https://amberg.de/fileadmin/Abfallberatung/Abfuhrkalender/{year}/ICS/Abfuhrkalender_{year}_Online{zone}.xlsx"


def _discover_year() -> str:
    """Discover the current Abfuhrkalender year from the Abfallberatung overview page."""
    response = requests.get(_ABFALL_PAGE, timeout=30)
    response.raise_for_status()
    match = re.search(r"/abfallberatung/abfuhrkalender-(\d{4})", response.text)
    if match:
        return match.group(1)
    # Fall back to the current calendar year if no match
    return str(date.today().year)


def _parse_xlsx(data: bytes, zone_letter: str, sub_number: str) -> list[Collection]:
    """Parse the Dateneingabe sheet from an xlsx file for the given zone."""
    collections: list[Collection] = []

    with zipfile.ZipFile(BytesIO(data)) as zf:
        # Read shared strings
        ns = {"ns": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        ss_root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
        shared_strings: list[str] = []
        for si in ss_root.findall("ns:si", ns):
            texts = si.findall(".//ns:t", ns)
            shared_strings.append("".join(t.text or "" for t in texts))

        def _cell_value(cell: ET.Element) -> str | None:
            t = cell.get("t", "")
            v_el = cell.find("ns:v", ns)
            if v_el is None:
                return None
            v = v_el.text
            if t == "s" and v is not None:
                return shared_strings[int(v)]
            return v

        def _row_to_list(row: ET.Element, max_cols: int = 14) -> list[str | None]:
            result: list[str | None] = [None] * max_cols
            for cell in row.findall("ns:c", ns):
                ref = cell.get("r", "")
                col_letters = "".join(c for c in ref if c.isalpha())
                col_idx = sum((ord(c) - ord("A") + 1) for c in col_letters) - 1
                if col_idx < max_cols:
                    result[col_idx] = _cell_value(cell)
            return result

        # Locate the Dateneingabe sheet via workbook.xml / relationships
        wb_root = ET.fromstring(zf.read("xl/workbook.xml"))
        rels_root = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
        ns_r = {"r": "http://schemas.openxmlformats.org/package/2006/relationships"}
        rel_map = {
            r.get("Id"): r.get("Target")
            for r in rels_root.findall("r:Relationship", ns_r)
        }
        sheet_path = None
        for sheet_el in wb_root.findall(".//ns:sheet", ns):
            if sheet_el.get("name") == "Dateneingabe":
                rid = sheet_el.get(
                    "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
                )
                if rid and rid in rel_map:
                    sheet_path = "xl/" + rel_map[rid]
                break

        if sheet_path is None:
            raise ValueError("Dateneingabe sheet not found in xlsx")

        sheet_root = ET.fromstring(zf.read(sheet_path))
        rows = sheet_root.findall(".//ns:row", ns)

        # Skip header row (index 0); process data rows
        for row in rows[1:]:
            vals = _row_to_list(row)
            # Column A (idx 0): Excel serial date
            # Column C (idx 2): zone letter
            if not vals[0] or vals[2] != zone_letter:
                continue
            try:
                serial = int(float(vals[0]))
            except (ValueError, TypeError):
                continue
            event_date = _EXCEL_EPOCH + timedelta(days=serial)

            for col_idx, waste_name in WASTE_COLUMNS.items():
                col_val = vals[col_idx]
                if col_val and sub_number in str(col_val):
                    collections.append(
                        Collection(
                            date=event_date,
                            t=waste_name,
                            icon=ICON_MAP.get(waste_name),
                        )
                    )

    return collections


class Source:
    def __init__(
        self,
        street: str | None = None,
        zone: str | None = None,
    ):
        if street is None and zone is None:
            raise SourceArgumentRequired(
                "street or zone",
                "Either 'street' or 'zone' must be provided.",
            )
        self._street = street
        self._zone = zone

    def fetch(self) -> list[Collection]:
        year = _discover_year()

        zone: str
        if self._street is not None:
            # Resolve street name to zone via JSON directory
            dir_url = _STREET_DIR_URL.format(year=year)
            resp = requests.get(dir_url, timeout=30)
            resp.raise_for_status()
            directory = resp.json()
            # The JSON key for the street name is "straße" (unicode ß)
            street_key = (
                next((k for k in directory[0].keys() if k != "gebiet"), None)
                if directory
                else None
            )
            if street_key is None:
                raise ValueError("Unexpected street directory format")

            match = next(
                (entry for entry in directory if entry[street_key] == self._street),
                None,
            )
            if match is None:
                all_streets = sorted(
                    entry[street_key] for entry in directory if street_key in entry
                )
                raise SourceArgumentNotFoundWithSuggestions(
                    "street",
                    self._street,
                    all_streets,
                )
            zone = match["gebiet"].upper()
        else:
            zone = str(self._zone).upper()
            if zone not in VALID_ZONES:
                raise SourceArgumentNotFoundWithSuggestions(
                    "zone",
                    zone,
                    VALID_ZONES,
                )

        zone_letter = zone[0]
        sub_number = zone[1]

        xlsx_url = _XLSX_URL.format(year=year, zone=zone)
        resp = requests.get(xlsx_url, timeout=60)
        resp.raise_for_status()

        return _parse_xlsx(resp.content, zone_letter, sub_number)
