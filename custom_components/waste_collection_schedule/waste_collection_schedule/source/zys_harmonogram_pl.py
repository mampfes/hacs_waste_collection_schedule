import datetime
import logging
from collections.abc import Iterator
from typing import Any, final

from bs4 import BeautifulSoup, Tag
from waste_collection_schedule import recurrence
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.transformers import JsonTransformer
from waste_collection_schedule.waste_types import (
    GENERAL_WASTE,
    GLASS,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

# Demonstrates: parsing *worded Polish dates* via the shared recurrence
# vocabulary. The provider (PUK ZYS, smok.net.pl platform) publishes the
# schedule as an HTML table whose first column is a Polish month name plus year
# (e.g. "Styczeń 2026"); each waste-type column lists the day numbers for that
# month. parse() flattens the table into one record per (day, month, type) and
# JsonTransformer turns each into a Collection, with _parse_pl_date resolving the
# Polish month name through recurrence.month() (no hand-rolled month dict).
#
# Address resolution is a four-step lookup (city -> street -> number -> report
# descriptor) handled in retrieve(); the descriptor points at the rendered HTML
# table fetched as the final step.

_LOGGER = logging.getLogger(__name__)

# The platform serves per-commune data; the year segment is the schedule year.
_API_URL = "https://zys-harmonogram.smok.net.pl/{commune}/{year}"

# The Polish column headers map onto canonical waste types. The provider's
# fractions are: mixed municipal waste, paper, metals & plastics, glass, bio.
_TYPE_MAP = {
    "zmieszane odpady komunalne": GENERAL_WASTE,
    "papier": PAPER,
    "metale i tworzywa sztuczne": RECYCLABLES,
    "szkło": GLASS,
    "bioodpady": ORGANIC,
}


def _parse_pl_date(*args: str) -> datetime.date:
    """Parse a "<day> <Polish month> <year>" string into a date.

    Conforms to the ``date_parsers.DateParser`` protocol (last positional arg is
    the date string) so it can be handed to a transformer. The month name is
    resolved through the shared multilingual ``recurrence.month`` vocabulary
    rather than a source-local month dict.
    """
    text = str(args[-1]).strip()
    day_str, month_name, year_str = text.split()
    month = recurrence.month(month_name)
    if month is None:
        raise ValueError(f"Unrecognised Polish month name: {month_name!r}")
    return datetime.date(int(year_str), month, int(day_str))


@final
class Source(BaseSource):
    TITLE = "Kleszczewo/Kostrzyn"
    DESCRIPTION = "Source for Kleszczewo/Kostrzyn commune garbage collection"
    URL = "https://www.puk-zys.pl/index.php"
    COUNTRY = "pl"
    CODEOWNERS = ["@markvp"]
    RAISE_ON_EMPTY = True

    TEST_CASES = {
        "Street Name": {
            "city": "Komorniki",
            "street_name": "Komorniki",
            "street_number": "93/2",
            "commune_name": "Kleszczewo",
        },
    }

    PARAMS = [
        text_field("commune_name", label="Commune"),
        text_field("city", label="City"),
        text_field("street_name", label="Street"),
        text_field("street_number", label="House Number"),
    ]

    HOWTO = {
        "en": (
            "Enter the commune (e.g. 'Kleszczewo'), then your city, street and "
            "house number exactly as they appear in the lookup at "
            "https://www.puk-zys.pl/index.php. Matching is case-insensitive."
        ),
    }

    transformer = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map=_TYPE_MAP,
        parse_date=_parse_pl_date,
    )

    def __init__(
        self, city: str, street_name: str, street_number: str, commune_name: str
    ):
        super().__init__(
            city=city,
            street_name=street_name,
            street_number=street_number,
            commune_name=commune_name,
        )
        self._city = city.strip().upper()
        self._street_name = street_name.strip().upper()
        self._street_number = street_number.strip().upper()
        self._commune_name = commune_name.strip().lower()

    def _lookup(self, base: str, path: str) -> list[dict[str, Any]]:
        response = self.session.get(f"{base}/{path}")
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _match_id(items: list[dict[str, Any]], wanted: str) -> str | None:
        for item in items:
            if str(item.get("value", "")).upper() == wanted:
                return str(item["id"])
        return None

    def retrieve(self, source: "Source"):
        """Resolve the address to a report descriptor and fetch the HTML table.

        Walks the four lookup steps (city -> street -> number -> report), each
        keyed on the previous id, then fetches the rendered schedule HTML.
        """
        base = _API_URL.format(
            commune=self._commune_name, year=datetime.date.today().year
        )

        cities = self._lookup(base, "addresses/cities")
        city_id = self._match_id(cities, self._city)
        if city_id is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "city",
                self._city,
                [str(c.get("value")) for c in cities],
            )

        streets = self._lookup(base, f"addresses/streets/{city_id}")
        street_id = self._match_id(streets, self._street_name)
        if street_id is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "street_name",
                self._street_name,
                [str(s.get("value")) for s in streets],
            )

        numbers = self._lookup(base, f"addresses/numbers/{city_id}/{street_id}")
        number_id = self._match_id(numbers, self._street_number)
        if number_id is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "street_number",
                self._street_number,
                [str(n.get("value")) for n in numbers],
            )

        report_resp = self.session.get(
            f"{base}/reports", params={"type": "html", "id": number_id}
        )
        report_resp.raise_for_status()
        report = report_resp.json()
        if report.get("status") != "success":
            raise SourceArgumentNotFound(
                "street_number",
                self._street_number,
                "the provider could not generate a schedule for this address.",
            )

        html_resp = self.session.get(report["filePath"])
        html_resp.raise_for_status()
        html_resp.encoding = "utf-8"
        return html_resp

    def parse(self, raw: Any, source: "Source") -> Iterator[dict[str, str]]:
        """Flatten the schedule table into one record per (day, month, type).

        The table's first column is a Polish "month year" label; each remaining
        column is a waste type whose cells list the collection day numbers.
        """
        soup = BeautifulSoup(raw.text, "html.parser")

        table = None
        for candidate in soup.find_all("table"):
            headers = [
                th.get_text(strip=True).lower() for th in candidate.find_all("th")
            ]
            if "miesiąc" in headers and "zmieszane odpady komunalne" in headers:
                table = candidate
                break
        if table is None:
            return

        thead = table.find("thead")
        body = table.find("tbody")
        if not isinstance(thead, Tag) or not isinstance(body, Tag):
            return

        # The header has two rows; the second carries the per-column type names.
        header_rows = thead.find_all("tr")
        type_cells = header_rows[-1].find_all(["th", "td"])
        # Column 0 is "Miesiąc"; the rest are waste-type columns.
        column_types = [c.get_text(strip=True) for c in type_cells[1:]]

        for row in body.find_all("tr"):
            cells = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]
            if len(cells) < 2:
                continue

            month_label = cells[0].strip()
            parts = month_label.split()
            if len(parts) == 2:
                month_name, year = parts
            else:
                month_name, year = parts[0], str(datetime.date.today().year)
            if recurrence.month(month_name) is None:
                continue

            for index, waste_type in enumerate(column_types):
                cell_index = index + 1
                if cell_index >= len(cells):
                    continue
                for day in cells[cell_index].replace(" ", "").split(","):
                    if not day.isdigit():
                        continue
                    yield {
                        "date": f"{day} {month_name} {year}",
                        "type": waste_type,
                    }
