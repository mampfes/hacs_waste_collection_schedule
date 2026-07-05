import datetime

import requests
from bs4 import BeautifulSoup

from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequiredWithSuggestions,
)

# Shared client for the "SEPAN" waste-schedule platform, used (via different
# deployments/base URLs) by sepan_remondis_pl.py, zys_harmonogram_pl.py and
# alba_com_pl.py. All three expose the identical address-resolution and
# HTML-report API; see issue #6749 for the consolidation rationale.

POLISH_MONTHS = {
    "STYCZEŃ": 1,
    "LUTY": 2,
    "MARZEC": 3,
    "KWIECIEŃ": 4,
    "MAJ": 5,
    "CZERWIEC": 6,
    "LIPIEC": 7,
    "SIERPIEŃ": 8,
    "WRZESIEŃ": 9,
    "PAŹDZIERNIK": 10,
    "LISTOPAD": 11,
    "GRUDZIEŃ": 12,
}


class SepanClient:
    """Client for the SEPAN waste-schedule platform.

    `base_urls` is a list of candidate base URLs tried in order (first
    success wins); this preserves each source's existing year-suffix /
    fallback-URL retry behaviour without duplicating it three times.
    """

    def __init__(self, base_urls: list[str]):
        self._base_urls = base_urls

    def resolve_address(self, city: str, street: str, number: str) -> str:
        """Resolve city/street/number to an address id, trying each base URL
        in turn. Returns the address id used by fetch_schedule()."""
        last_error: Exception | None = None
        for base_url in self._base_urls:
            try:
                return self._resolve_address_at(base_url, city, street, number)
            except (
                SourceArgumentNotFoundWithSuggestions,
                SourceArgumentRequiredWithSuggestions,
            ):
                # A well-formed response that just didn't match: no point
                # retrying against another base URL, the argument is wrong.
                raise
            except Exception as e:  # noqa: BLE001 - network/format failures only
                last_error = e
                continue
        raise last_error or Exception("Could not resolve address: no base URL worked")

    def _resolve_address_at(
        self, base_url: str, city: str, street: str, number: str
    ) -> str:
        city = city.upper().strip()
        street = street.upper().strip()
        number = str(number).strip()

        cities = requests.get(f"{base_url}/addresses/cities", timeout=30).json()
        city_suggestions = [c["value"] for c in cities]
        if not city:
            raise SourceArgumentRequiredWithSuggestions(
                "city", "Select your city.", city_suggestions
            )
        city_match = next(
            (c for c in cities if c["value"].upper().strip() == city), None
        )
        if not city_match:
            raise SourceArgumentNotFoundWithSuggestions("city", city, city_suggestions)
        city_id = city_match["id"]

        streets = requests.get(
            f"{base_url}/addresses/streets/{city_id}", timeout=30
        ).json()
        street_suggestions = [s["value"] for s in streets]
        if not street:
            raise SourceArgumentRequiredWithSuggestions(
                "street", "Select your street.", street_suggestions
            )
        street_match = next(
            (s for s in streets if s["value"].upper().strip() == street), None
        )
        if not street_match:
            raise SourceArgumentNotFoundWithSuggestions(
                "street", street, street_suggestions
            )
        street_id = street_match["id"]

        numbers = requests.get(
            f"{base_url}/addresses/numbers/{city_id}/{street_id}", timeout=30
        ).json()
        number_suggestions = [str(n["value"]) for n in numbers]
        if not number:
            raise SourceArgumentRequiredWithSuggestions(
                "number", "Select your house number.", number_suggestions
            )
        number_match = next(
            (n for n in numbers if str(n["value"]).strip() == number), None
        )
        if not number_match:
            raise SourceArgumentNotFoundWithSuggestions(
                "number", number, number_suggestions
            )

        self._resolved_base_url = base_url
        return number_match["id"]

    def fetch_report_html(self, address_id: str) -> str:
        """Fetch the raw HTML report for a resolved address id.

        Parsing is intentionally left to the caller: the three known SEPAN
        deployments don't all render the report table the same way (see
        `parse_month_name_table` for the format shared by zys_harmonogram_pl
        and alba_com_pl; sepan_remondis_pl uses its own positional parser).
        """
        base_url = getattr(self, "_resolved_base_url", None)
        if base_url is None:
            raise Exception("fetch_report_html() called before resolve_address()")

        report = requests.get(
            f"{base_url}/reports",
            params={"type": "html", "id": address_id},
            timeout=30,
        ).json()
        if report.get("status") != "success":
            raise Exception("fetch report failed")

        return requests.get(report["filePath"], timeout=30).content.decode("utf-8")

    def fetch_schedule(self, address_id: str) -> list[tuple[datetime.date, str]]:
        """Fetch and parse the HTML report using the shared month-name table
        format (see `parse_month_name_table`)."""
        return parse_month_name_table(self.fetch_report_html(address_id))


def parse_month_name_table(html: str) -> list[tuple[datetime.date, str]]:
    """Parse a SEPAN report table whose rows are "<Month> <Year>" plus one
    comma-separated-days cell per waste-type column (the format used by
    zys_harmonogram_pl and alba_com_pl's deployments).

    Column names are read from the header row itself (rather than assumed
    by position) because some deployments have a two-row <thead> (an outer
    grouping row plus the real per-column names) — only the row that
    actually contains "Miesiąc" is used for header names, so the extra
    grouping row's cells don't get misread as data columns.
    """
    soup = BeautifulSoup(html, "html.parser")

    table = None
    headers: list[str] = []
    for t in soup.find_all("table"):
        for header_row in t.find_all("tr"):
            row_th_texts = [th.get_text(strip=True) for th in header_row.find_all("th")]
            if "Miesiąc" in row_th_texts:
                table = t
                headers = row_th_texts[1:]
                break
        if table is not None:
            break

    if table is None:
        raise Exception("Schedule table not found in HTML response")

    entries: list[tuple[datetime.date, str]] = []
    tbody = table.find("tbody")
    rows = tbody.find_all("tr") if tbody else table.find_all("tr")
    for row in rows:
        cells = row.find_all("td")
        if not cells:
            continue

        parts = cells[0].get_text(strip=True).split()
        if len(parts) < 2:
            continue

        month = POLISH_MONTHS.get(parts[0].upper())
        if not month:
            continue
        year = int(parts[-1])

        for i, cell in enumerate(cells[1:]):
            if i >= len(headers):
                break
            days_text = cell.get_text(strip=True)
            if not days_text:
                continue

            waste_type = headers[i]
            for day_str in days_text.split(","):
                day_str = day_str.strip()
                if not day_str.isdigit():
                    continue
                try:
                    entries.append(
                        (
                            datetime.date(year, month, int(day_str)),
                            waste_type,
                        )
                    )
                except ValueError:
                    pass

    return entries
