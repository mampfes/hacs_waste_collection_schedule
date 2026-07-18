import datetime
import re
import xml.etree.ElementTree
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from bs4 import BeautifulSoup

from waste_collection_schedule import recurrence, response_shape
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequiredWithSuggestions,
)
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource

# Shared retriever/parser for the "SEPAN" (aka "ICHI System") waste-schedule
# platform, used (via different deployments/base URLs) by sepan_remondis_pl.py,
# alba_com_pl.py and ichisystem_eu.py. zys_harmonogram_pl.py runs on the same
# platform but has its own, independently-migrated pipeline source. All four
# expose the identical address-resolution API; see issue #6749 for the
# consolidation rationale and issue #6763 for the /years+token report flow.

# --------------------------------------------------------------------------- #
# Pipeline components (BaseSource architecture)
#
#     retrieve = SepanRetriever(base_urls=..., city="city", street="street",
#                                number="number", use_years=True)
#     parse    = SepanReportParser()               # header-based table
#       or
#     parse    = SepanPositionalReportParser(name_map=...)  # positional table
#
# SepanRetriever performs ALL HTTP (address resolution across the candidate
# base URLs, then one or more report fetches) via source.session and returns
# the raw HTML report(s) it gathered, bundled as
# {"reports": [{"html": ..., "year": int | None}, ...]}. The parsers do no
# I/O: SepanReportParser reuses parse_month_name_table (the header-based table
# format shared by alba_com_pl / ichisystem_eu); SepanPositionalReportParser
# reuses parse_positional_table (sepan_remondis_pl's positional format, whose
# report tables don't reliably expose parseable header text).
# --------------------------------------------------------------------------- #

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


class SepanRetriever(RetrieverFunc):
    """Resolve a Polish address on a SEPAN/ICHI System deployment and fetch
    its schedule report(s) as raw HTML.

    ``base_urls`` is a list of candidate base URLs (or a zero-arg callable
    returning one, for a deployment whose path is year-suffixed), tried in
    order; the first that resolves the address wins. This preserves each
    deployment's year-suffixed-folder / fallback-URL retry behaviour without
    duplicating it per source.

    ``city``/``street``/``number`` are the ``source.params`` field names
    holding the address to resolve.

    When ``use_years`` is True (deployments exposing a `/years` endpoint, see
    issue #6763), every available report year is fetched and returned;
    otherwise (or when the deployment has no `/years` endpoint) a single,
    "current" report is fetched, matching the older/simpler deployments.
    """

    def __init__(
        self,
        base_urls: "list[str] | Callable[[], list[str]]",
        city: str = "city",
        street: str = "street",
        number: str = "number",
        use_years: bool = True,
    ):
        self.base_urls = base_urls
        self.city = city
        self.street = street
        self.number = number
        self.use_years = use_years

    def __call__(self, source: "BaseSource") -> dict[str, Any]:
        params = source.params
        city = params.get(self.city) or ""
        street = params.get(self.street) or ""
        number = params.get(self.number) or ""
        base_urls = self.base_urls() if callable(self.base_urls) else self.base_urls

        base_url, address_id, number_match = self._resolve_address(
            source, base_urls, city, street, number
        )

        if self.use_years:
            years = self._fetch_years(source, base_url)
            if years:
                token = (number_match or {}).get("token")
                reports = self._fetch_year_reports(
                    source, base_url, address_id, years, token
                )
                if reports:
                    return {"reports": reports}

        html = self._fetch_report_html(source, base_url, address_id)
        return {"reports": [{"html": html, "year": None}]}

    def _resolve_address(
        self,
        source: "BaseSource",
        base_urls: list[str],
        city: str,
        street: str,
        number: str,
    ) -> "tuple[str, str, dict | None]":
        last_error: Exception | None = None
        for base_url in base_urls:
            try:
                return self._resolve_at(source, base_url, city, street, number)
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

    def _resolve_at(
        self, source: "BaseSource", base_url: str, city: str, street: str, number: str
    ) -> "tuple[str, str, dict | None]":
        city_n = normalize_pl(city)
        street_n = normalize_pl(street)
        number_n = str(number).strip()

        cities = source.session.get(f"{base_url}/addresses/cities").json()
        city_suggestions = [c["value"] for c in cities]
        if not city_n:
            raise SourceArgumentRequiredWithSuggestions(
                self.city, "Select your city.", city_suggestions
            )
        city_match = next(
            (c for c in cities if normalize_pl(c["value"]) == city_n), None
        )
        if not city_match:
            raise SourceArgumentNotFoundWithSuggestions(
                self.city, city, city_suggestions
            )
        city_id = city_match["id"]

        streets = source.session.get(f"{base_url}/addresses/streets/{city_id}").json()
        street_suggestions = [s["value"] for s in streets]
        if not street_n:
            raise SourceArgumentRequiredWithSuggestions(
                self.street, "Select your street.", street_suggestions
            )
        street_match = next(
            (s for s in streets if normalize_pl(s["value"]) == street_n), None
        )
        if not street_match:
            raise SourceArgumentNotFoundWithSuggestions(
                self.street, street, street_suggestions
            )
        street_id = street_match["id"]

        numbers = source.session.get(
            f"{base_url}/addresses/numbers/{city_id}/{street_id}"
        ).json()
        number_suggestions = [str(n["value"]) for n in numbers]
        if not number_n:
            raise SourceArgumentRequiredWithSuggestions(
                self.number, "Select your house number.", number_suggestions
            )
        number_match = next(
            (n for n in numbers if str(n["value"]).strip() == number_n), None
        )
        if not number_match:
            raise SourceArgumentNotFoundWithSuggestions(
                self.number, number, number_suggestions
            )

        return base_url, number_match["id"], number_match

    def _fetch_years(self, source: "BaseSource", base_url: str) -> "list[dict] | None":
        """Return this deployment's report years (list of {"id", "value"}),
        or None if it doesn't expose a `/years` endpoint (or the endpoint
        errors/returns something unexpected). Older/simpler SEPAN
        deployments only expose the current report via `/reports` without a
        `yearId`; newer ones (see issue #6763) expose `/years` plus a
        per-address `token` (already returned alongside the address id by
        `/addresses/numbers/...`) to fetch any year's report on demand."""
        try:
            resp = source.session.get(f"{base_url}/years")
            resp.raise_for_status()
            years = resp.json()
        except Exception:
            return None
        if not isinstance(years, list) or not years:
            return None
        return years

    def _fetch_year_reports(
        self,
        source: "BaseSource",
        base_url: str,
        address_id: str,
        years: list[dict],
        token: "str | None",
    ) -> "list[dict[str, Any]]":
        reports: list[dict[str, Any]] = []
        for year_entry in years:
            try:
                year_value = int(year_entry["value"])
            except (KeyError, TypeError, ValueError):
                continue
            try:
                html = self._fetch_report_html(
                    source,
                    base_url,
                    address_id,
                    year_id=year_entry.get("id"),
                    token=token,
                )
            except Exception:
                continue
            reports.append({"html": html, "year": year_value})
        return reports

    def _fetch_report_html(
        self,
        source: "BaseSource",
        base_url: str,
        address_id: str,
        year_id: "str | None" = None,
        token: "str | None" = None,
    ) -> str:
        """Fetch the raw HTML report for a resolved address id.

        If `year_id` (and the matching `token`, as returned alongside the
        address id by `_resolve_at`'s underlying `/addresses/numbers/...`
        call) are given, the report for that specific year is requested;
        otherwise the deployment's default/current report is requested
        (previous behaviour, still used by deployments without a `/years`
        endpoint).
        """
        params: dict[str, Any] = {"type": "html", "id": address_id}
        if year_id is not None:
            params["responseType"] = "json"
            params["token"] = token
            params["yearId"] = year_id

        report = source.session.get(f"{base_url}/reports", params=params).json()
        if report.get("status") != "success":
            raise SourceArgumentNotFound(
                self.number,
                address_id,
                "the provider could not generate a schedule for this address.",
            )

        html_resp = source.session.get(report["filePath"])
        return html_resp.content.decode("utf-8")


def parse_month_name_table(
    html: str, year: "int | None" = None
) -> "list[tuple[datetime.date, str]]":
    """Parse a SEPAN report table whose rows are one comma-separated-days
    cell per waste-type column, keyed by a leading "<Month>" or
    "<Month> <Year>" cell (the format used by alba_com_pl and
    ichisystem_eu's deployments).

    Column names are read from the header row itself (rather than assumed
    by position) because some deployments have a two-row <thead> (an outer
    grouping row plus the real per-column names) — only the row that
    actually contains "Miesiąc" is used for header names, so the extra
    grouping row's cells don't get misread as data columns.

    Some deployments (e.g. ichisystem_eu) render just the month name
    without a year in each row, relying on the report having been requested
    for a specific year (see `SepanRetriever`'s /years+token flow); pass
    that year explicitly via `year` for those. If a row's first cell does
    include a year (as alba_com_pl does), that embedded year always takes
    precedence over `year`.

    The month name is resolved through the shared multilingual
    ``recurrence.month`` vocabulary (which covers Polish) rather than a
    source-local month dict.
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

        month = recurrence.month(parts[0])
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


def parse_positional_table(
    html: str, year: int, name_map: dict[int, str]
) -> "list[tuple[datetime.date, str]]":
    """Parse a SEPAN report table whose rows are Jan..Dec by position (not by
    header text) and whose columns are fixed waste-type categories keyed by
    position in `name_map` (the format used by sepan_remondis_pl, whose
    report tables don't reliably expose parseable header text, unlike
    alba_com_pl / ichisystem_eu)."""
    table_html = html[html.find("<table") : html.rfind("</table>") + 8]
    tree = xml.etree.ElementTree.fromstring(table_html)  # nosec B314

    entries: list[tuple[datetime.date, str]] = []
    for row_index, row in enumerate(tree.findall(".//tr")):
        if row_index > 0:
            for cell_index, cell in enumerate(row.findall(".//td")):
                if cell_index > 0 and isinstance(cell.text, str):
                    for day in cell.text.split(","):
                        entries.append(
                            (
                                datetime.date(year, row_index - 1, int(day)),
                                name_map[cell_index],
                            )
                        )
    return entries


class SepanReportParser(Parser["list[tuple[datetime.date, str]]"]):
    """Decode the raw ``reports`` list into ``(date, label)`` rows via the
    shared header-based month-name table format (`parse_month_name_table`).

    Merges and deduplicates entries across every report gathered by
    `SepanRetriever` (more than one when the deployment exposes a `/years`
    endpoint). Does no I/O, so it runs standalone against a cached
    ``{"reports": [...]}`` fixture.
    """

    def __call__(
        self, raw: dict[str, Any], source: "BaseSource | None" = None
    ) -> "list[tuple[datetime.date, str]]":
        response_shape.expect(
            isinstance(raw, dict) and bool(raw.get("reports")),
            source_name=response_shape.source_name(source),
            detail="Sepan response missing 'reports'",
            raw=raw,
        )

        entries: list[tuple[datetime.date, str]] = []
        seen: set[tuple[datetime.date, str]] = set()
        for report in raw["reports"]:
            for entry in parse_month_name_table(
                report["html"], year=report.get("year")
            ):
                if entry in seen:
                    continue
                seen.add(entry)
                entries.append(entry)
        return entries


class SepanPositionalReportParser(Parser["list[tuple[datetime.date, str]]"]):
    """Decode the raw ``reports`` list into ``(date, label)`` rows via the
    positional table format (`parse_positional_table`), used by
    sepan_remondis_pl.

    Does no I/O, so it runs standalone against a cached ``{"reports": [...]}``
    fixture.
    """

    def __init__(self, name_map: dict[int, str]):
        self._name_map = name_map

    def __call__(
        self, raw: dict[str, Any], source: "BaseSource | None" = None
    ) -> "list[tuple[datetime.date, str]]":
        response_shape.expect(
            isinstance(raw, dict) and bool(raw.get("reports")),
            source_name=response_shape.source_name(source),
            detail="Sepan response missing 'reports'",
            raw=raw,
        )

        entries: list[tuple[datetime.date, str]] = []
        for report in raw["reports"]:
            year = report.get("year") or datetime.date.today().year
            entries.extend(parse_positional_table(report["html"], year, self._name_map))
        return entries
