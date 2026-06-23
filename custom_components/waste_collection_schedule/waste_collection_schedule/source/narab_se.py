import datetime
from typing import Any, final

from bs4 import BeautifulSoup
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.collection import Collection
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.exceptions import (
    SourceArgumentException,
    SourceArgumentNotFound,
)
from waste_collection_schedule.waste_types import ALL_TYPES, preserved, resolve

# Declarative conversion of the NÅRAB source. NÅRAB's calendar lives on a
# separate service (narabtomningskalender.se) reached in two GET steps: an
# address autocomplete that yields the opaque ids (hsG/hsO/knR/abK/nrA), then a
# calendar endpoint returning an HTML month grid. Those two steps and the grid
# parsing don't fit a configured retriever/parser, so they stay as a retrieve()
# method returning the address-resolved calendar response and a parse() method
# that yields per-pickup records. classify() maps each provider code to its
# Swedish label, then onto a canonical WasteType via the shared vocabulary
# (falling back to the verbatim label when Swedish has no canonical match).

API_URL_FETCH_ADDRESS = (
    "https://www.narabtomningskalender.se/basfiler/system_ladda_adresser.php"
)
API_URL_FETCH_COLLECTIONS = (
    "https://www.narabtomningskalender.se/basfiler/online_kalender_skapa.php"
)

# Map collection codes to their Swedish trash-type label.
_COLLECTION_LABELS = {
    "B1": "BEDA Kärl 1 - Förpackningar av Papper, Plast, Metall och Ofärgat glas",
    "B2": "BEDA Kärl 2 - Matavfall, Restavfall, Tidningar och Färgat glas",
    "LB": "LILLBEDA (endast Kärl 2) - Matavfall, Restavfall, Tidningar och Färgat glas",
    "KK": "Restavfallskärl",
    "HAS": "Restavfallskärl",
    "HASD": "Mat- & Restavfall delat kärl",
    "HAO": "Restavfallskärl",
    "HAX": "Restavfallskärl",
    "FG": "Färgat glas",
    "OFG": "Ofärgat glas",
    "HPL": "Hårdplast",
    "PLF": "Plastförpackningar",
    "MAT": "Matavfall",
    "MET": "Metallförpackningar",
    "MPL": "Mjukplast",
    "ORG": "Matavfall",
    "PAPP": "Pappersförpackningar",
    "TIDN": "Tidningar",
    "WELL": "Wellpapp",
    "TRG": "Trädgårdskärl",
    "LAT": "Latrin",
    "BATT": "Batterier",
    "FETT": "Fett",
    "OLJA": "Olja",
    "SLAM": "Slam",
    "FA": "FA",
}

# Map Swedish month names to month numbers.
_SWEDISH_MONTHS = {
    "Januari": 1,
    "Februari": 2,
    "Mars": 3,
    "April": 4,
    "Maj": 5,
    "Juni": 6,
    "Juli": 7,
    "Augusti": 8,
    "September": 9,
    "Oktober": 10,
    "November": 11,
    "December": 12,
}


@final
class Source(BaseSource):
    TITLE = "Nårab - Norra Åsbo Renhållnings AB"
    DESCRIPTION = "Source script for narab.se"
    URL = "https://narab.se"
    COUNTRY = "se"
    # classify() resolves open-ended Swedish labels via the shared vocabulary,
    # so any canonical type may appear.
    WASTE_TYPES = list(ALL_TYPES)

    TEST_CASES = {
        "Residential - Villa": {"address": "Helsingborgsvägen 31", "kundNr": 25494},
        "Residential - Apartment": {"address": "Hallandsvägen 9", "kundNr": 13726},
        "Commercial": {"address": "Hallandsvägen 9", "kundNr": 33159},
    }

    PARAMS = [
        text_field("address", "Address for collection"),
        text_field("kundNr", "Customer number", optional=True),
    ]

    HOWTO = {
        "en": "Enter your address. If more than one collection shares the "
        "address, also provide your customer number (kundNr). Fetch your "
        "calendar at narabtomningskalender.se and run narabKUNDNRData.value in "
        "the browser console to read it.",
    }

    def __init__(self, address: str, kundNr: int = 0):
        super().__init__(address=address, kundNr=kundNr)
        self._address = address
        self._kundNr = kundNr

    @staticmethod
    def _parse_address_list(text: str) -> list[dict[str, str]]:
        addresses = []
        for line in text.strip().splitlines():
            parts = line.split("|")
            if len(parts) != 5:
                raise ValueError(f"Expected 5 parts in line, got {len(parts)}: {line}")
            hsG, hsO, knR, abK, nrA = (p.strip() for p in parts)
            addresses.append(
                {"hsG": hsG, "hsO": hsO, "knR": knR, "abK": abK, "nrA": nrA}
            )
        return addresses

    def retrieve(self, source: "Source") -> Any:
        # Resolve the address to the opaque ids the calendar endpoint needs.
        r = self.session.get(
            API_URL_FETCH_ADDRESS,
            params={
                "svar": self._address,
                "limit": "500",
                "timestamp": str(int(datetime.datetime.now().timestamp() * 1000)),
            },
        )
        r.raise_for_status()

        addresses = self._parse_address_list(r.text)
        if len(addresses) == 1:
            hsG, hsO, knR, abK, nrA = addresses[0].values()
        elif len(addresses) > 1:
            if self._kundNr == 0:
                raise SourceArgumentException(
                    argument="address",
                    message=f"Multiple values found for the argument 'address' with the value '{self._address}'",
                )
            hsG = hsO = knR = abK = nrA = ""
            for addr in addresses:
                if addr["knR"] == str(self._kundNr):
                    hsG, hsO, knR, abK, nrA = addr.values()
                    break
            if not (hsG and hsO and knR and abK and nrA):
                raise SourceArgumentException(
                    argument="kundNr",
                    message=f"No results found for the argument 'kundNr' with the value '{self._kundNr}'. Please check the value and verify the address.",
                )
        else:
            raise SourceArgumentNotFound(
                argument="address",
                value=self._address,
            )

        # Request the calendar data. clid is a static value, might need to be
        # updated if it's ever changed on the API side.
        return self.session.get(
            API_URL_FETCH_COLLECTIONS,
            params={
                "hsG": hsG,
                "hsO": hsO,
                "knR": knR,
                "abK": abK,
                "nrA": nrA,
                "lang": "sv",
                "clid": "e97828682dc80c2b36df990778fb41a1",
            },
        )

    def parse(self, response: Any, source: "Source") -> list[dict[str, Any]]:
        soup = BeautifulSoup(response.text, "html.parser")

        pickup_data = []
        for month_table in soup.select("#mainKalender table"):
            month_header = month_table.find("td", colspan="7")
            if not month_header:
                continue
            month_name = month_header.get_text(strip=True)

            for day_cell in month_table.find_all("td"):
                # Remove <span> elements so we don't confuse their numbers with
                # the day number.
                cell_no_spans = BeautifulSoup(day_cell.decode_contents(), "html.parser")
                for sp in cell_no_spans.find_all("span"):
                    sp.decompose()

                stripped = cell_no_spans.get_text(strip=True)
                day_text = stripped.split()[0] if stripped else None
                if not (day_text and day_text.isdigit()):
                    continue
                day_number = int(day_text)

                # Loop over all spans in this cell (multiple trash types possible).
                for span in day_cell.find_all("span"):
                    classes = span.get("class", [])
                    trash_type = classes[0] if classes else None
                    if trash_type:
                        pickup_data.append(
                            {
                                "month": month_name,
                                "day": day_number,
                                "trash_type": trash_type,
                            }
                        )

        # Remove duplicates (same month, day, trash_type more than once).
        unique_data = []
        seen = set()
        for entry in pickup_data:
            key = (entry["month"], entry["day"], entry["trash_type"])
            if key not in seen:
                seen.add(key)
                unique_data.append(entry)
        return unique_data

    def classify(self, record: dict[str, Any]) -> Collection | None:
        month = record["month"]
        # The header reads e.g. "Januari - 2026".
        if " - " not in month:
            return None
        month_name, year_str = month.split(" - ")
        month_number = _SWEDISH_MONTHS.get(month_name)
        if not month_number:
            return None

        # The class is e.g. "MAT", "MAT-F" or "MAT-H" (moved/holiday markers);
        # the base code before the suffix identifies the waste type.
        base_code = record["trash_type"].split("-")[0]
        label = _COLLECTION_LABELS.get(base_code)
        if label is None:
            return None

        date = datetime.date(year=int(year_str), month=month_number, day=record["day"])
        return Collection(
            date=date,
            waste_type=resolve(label) or preserved(label),
        )
