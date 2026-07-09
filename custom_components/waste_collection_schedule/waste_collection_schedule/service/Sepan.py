import datetime
import re

import requests
from bs4 import BeautifulSoup

from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequiredWithSuggestions,
)

# Shared client for the "SEPAN" (aka "ICHI System") waste-schedule platform,
# used (via different deployments/base URLs) by sepan_remondis_pl.py,
# zys_harmonogram_pl.py, alba_com_pl.py and ichisystem_eu.py. All four expose
# the identical address-resolution API; see issue #6749 for the
# consolidation rationale and issue #6763 for the /years+token report flow.

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

_PL_DIACRITICS = str.maketrans(
    {
        "ą": "a",
        "Ą": "a",
        "ć": "c",
        "Ć": "c",
        "ę": "e",
        "Ę": "e",
        "ł": "l",
        "Ł": "l",
        "ń": "n",
        "Ń": "n",
        "ó": "o",
        "Ó": "o",
        "ś": "s",
        "Ś": "s",
        "ź": "z",
        "Ź": "z",
        "ż": "z",
        "Ż": "z",
    }
)


def normalize_pl(text: str) -> str:
    """Normalise Polish text for matching: uppercase, drop diacritics,
    collapse whitespace. This lets e.g. "Swiety Marcin" (diacritics
    dropped, as many users type) still match a platform's "ŚWIĘTY MARCIN"
    listing. See issue #6763."""
    return re.sub(r"\s+", " ", text.translate(_PL_DIACRITICS).upper()).strip()


class SepanClient:
    """Client for the SEPAN waste-schedule platform.

    `base_urls` is a list of candidate base URLs tried in order (first
    success wins); this preserves each source's existing year-suffix /
    fallback-URL retry behaviour without duplicating it three times.
    """

    def __init__(self, base_urls: list[str]):
        self._base_urls = base_urls
        self._resolved_base_url: str | None = None
        self._resolved_number: dict | None = None

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
            except Exception as e:
                last_error = e
                continue
        raise last_error or Exception("Could not resolve address: no base URL worked")

    def _resolve_address_at(
        self, base_url: str, city: str, street: str, number: str
    ) -> str:
        city = normalize_pl(city)
        street = normalize_pl(street)
        number = str(number).strip()

        cities = requests.get(f"{base_url}/addresses/cities", timeout=30).json()
        city_suggestions = [c["value"] for c in cities]
        if not city:
            raise SourceArgumentRequiredWithSuggestions(
                "city", "Select your city.", city_suggestions
            )
        city_match = next((c for c in cities if normalize_pl(c["value"]) == city), None)
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
            (s for s in streets if normalize_pl(s["value"]) == street), None
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
        self._resolved_number = number_match
        return number_match["id"]

    def _fetch_years(self) -> list[dict] | None:
        """Return this deployment's report years (list of {"id", "value"}),
        or None if it doesn't expose a `/years` endpoint (or the endpoint
        errors/returns something unexpected). Older/simpler SEPAN
        deployments only expose the current report via `/reports` without a
        `yearId`; newer ones (see issue #6763) expose `/years` plus a
        per-address `token` (already returned alongside the address id by
        `/addresses/numbers/...`) to fetch any year's report on demand."""
        if self._resolved_base_url is None:
            return None
        try:
            resp = requests.get(f"{self._resolved_base_url}/years", timeout=30)
            resp.raise_for_status()
            years = resp.json()
        except Exception:
            return None
        if not isinstance(years, list) or not years:
            return None
        return years

    def fetch_report_html(
        self,
        address_id: str,
        year_id: str | None = None,
        token: str | None = None,
    ) -> str:
        """Fetch the raw HTML report for a resolved address id.

        If `year_id` (and the matching `token`, as returned alongside the
        address id by `resolve_address()`'s underlying
        `/addresses/numbers/...` call) are given, the report for that
        specific year is requested; otherwise the deployment's
        default/current report is requested (previous behaviour, still used
        by deployments without a `/years` endpoint).

        Parsing is intentionally left to the caller: the known SEPAN
        deployments don't all render the report table the same way (see
        `parse_month_name_table` for the format shared by zys_harmonogram_pl,
        alba_com_pl and ichisystem_eu; sepan_remondis_pl uses its own
        positional parser).
        """
        base_url = self._resolved_base_url
        if base_url is None:
            raise Exception("fetch_report_html() called before resolve_address()")

        params: dict[str, str | None] = {"type": "html", "id": address_id}
        if year_id is not None:
            params["responseType"] = "json"
            params["token"] = token
            params["yearId"] = year_id

        report = requests.get(
            f"{base_url}/reports",
            params=params,
            timeout=30,
        ).json()
        if report.get("status") != "success":
            raise Exception("fetch report failed")

        return requests.get(report["filePath"], timeout=30).content.decode("utf-8")

    def fetch_schedule(self, address_id: str) -> list[tuple[datetime.date, str]]:
        """Fetch and parse the HTML report(s) using the shared month-name
        table format (see `parse_month_name_table`).

        If the deployment exposes a `/years` endpoint, every available
        year's report is fetched (using the `token` returned alongside the
        address id by `resolve_address()`) and merged, deduplicating
        entries. This is more robust across a calendar-year rollover than
        guessing a year-suffixed base URL (see issue #6763). Deployments
        without a `/years` endpoint fall back to the single "current"
        report returned by `/reports` (previous behaviour).
        """
        years = self._fetch_years()
        if not years:
            return parse_month_name_table(self.fetch_report_html(address_id))

        token = (self._resolved_number or {}).get("token")
        entries: list[tuple[datetime.date, str]] = []
        seen: set[tuple[datetime.date, str]] = set()
        for year_entry in years:
            try:
                year_value = int(year_entry["value"])
            except (KeyError, TypeError, ValueError):
                continue
            try:
                html = self.fetch_report_html(
                    address_id, year_id=year_entry.get("id"), token=token
                )
            except Exception:
                continue
            for entry in parse_month_name_table(html, year=year_value):
                if entry in seen:
                    continue
                seen.add(entry)
                entries.append(entry)
        return entries


def parse_month_name_table(
    html: str, year: int | None = None
) -> list[tuple[datetime.date, str]]:
    """Parse a SEPAN report table whose rows are one comma-separated-days
    cell per waste-type column, keyed by a leading "<Month>" or
    "<Month> <Year>" cell (the format used by zys_harmonogram_pl,
    alba_com_pl and ichisystem_eu's deployments).

    Column names are read from the header row itself (rather than assumed
    by position) because some deployments have a two-row <thead> (an outer
    grouping row plus the real per-column names) — only the row that
    actually contains "Miesiąc" is used for header names, so the extra
    grouping row's cells don't get misread as data columns.

    Some deployments (e.g. ichisystem_eu) render just the month name
    without a year in each row, relying on the report having been requested
    for a specific year (see `SepanClient.fetch_schedule`'s /years+token
    flow); pass that year explicitly via `year` for those. If a row's first
    cell does include a year (as zys_harmonogram_pl / alba_com_pl do), that
    embedded year always takes precedence over `year`.
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
        if not parts:
            continue

        month = POLISH_MONTHS.get(parts[0].upper())
        if not month:
            continue

        if len(parts) >= 2 and parts[-1].isdigit():
            row_year = int(parts[-1])
        elif year is not None:
            row_year = year
        else:
            continue

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
                            datetime.date(row_year, month, int(day_str)),
                            waste_type,
                        )
                    )
                except ValueError:
                    pass

    return entries
