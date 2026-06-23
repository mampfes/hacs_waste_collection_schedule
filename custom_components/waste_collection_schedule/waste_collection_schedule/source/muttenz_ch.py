import json
import re
from typing import Any, final

from bs4 import BeautifulSoup
from waste_collection_schedule import date_parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.collection import Collection
from waste_collection_schedule.waste_types import (
    GARDEN_WASTE,
    HAZARDOUS,
    PAPER,
    RECYCLABLES,
    WasteType,
)

# Demonstrates: a JSON payload embedded inside an HTML data-attribute.
#
# Muttenz runs on the Swiss "i-web" municipal CMS. The waste page is fully
# server-rendered, but the collection table is not plain <tr>/<td> markup the
# way the existing HTML-scrape examples (lawrence_ma_us, isaac_qld_gov_au) are.
# Instead the whole schedule ships as a JSON array inside a single
# ``data-entities`` attribute on the table element, and every field inside that
# JSON is itself a fragment of escaped HTML (an <a> for the waste-type name, a
# pair of responsive <span>s for the date). So the parse shape is: pick the
# attribute, read its JSON (BeautifulSoup already HTML-unescapes attribute
# values), then strip the nested HTML out of each record's fields. That is a
# distinct wrinkle from both the flat-JSON-API and the table-scrape examples,
# and i-web powers many other Swiss municipalities, so the pattern generalises.
#
# The page carries two data-entities blocks: the schedule (records have an
# ``_anlassDate``) and a waste-type legend (records do not). The parser keeps
# only the block whose records carry a date. Dates are dd.mm.yyyy (Swiss
# German), which dateutil parses, so no custom locale handling is needed; the
# wrinkle here is purely the embedded-JSON-in-an-attribute parse.

_TYPE_MAP: dict[str, WasteType] = {
    "Papiersammlung": PAPER,
    "Kunststoffsammlung": RECYCLABLES,
    # "Altmetallabuhr" is the provider's own spelling (a missing "f"); match it
    # verbatim so scrap-metal collections are not silently dropped.
    "Altmetallabuhr": RECYCLABLES,
    "Grünabfuhr": GARDEN_WASTE,
    "Häckseltag": GARDEN_WASTE,
    "Sonderabfallsammlung": HAZARDOUS,
}


def _strip_html(fragment: str) -> str:
    """Return the visible text of an HTML fragment, whitespace-collapsed."""
    return BeautifulSoup(fragment or "", "html.parser").get_text(" ", strip=True)


@final
class Source(BaseSource):
    TITLE = "Gemeinde Muttenz"
    DESCRIPTION = "Source for the municipality of Muttenz, Switzerland."
    URL = "https://www.muttenz.ch"
    COUNTRY = "ch"
    CODEOWNERS = ["@markvp"]
    API_URL = "https://www.muttenz.ch/abfalldaten"

    TEST_CASES: dict = {"Muttenz": {}}

    PARAMS: list = []

    HOWTO = {
        "en": (
            "Muttenz publishes a single municipality-wide collection calendar, "
            "so no address or other argument is required."
        ),
        "de": (
            "Muttenz veröffentlicht einen einzigen gemeindeweiten Abfallkalender, "
            "daher ist kein Argument erforderlich."
        ),
    }

    RAISE_ON_EMPTY = True

    parse_date = date_parsers.for_format("%d.%m.%Y")

    # The shared multilingual resolver covers de, so a label such as
    # "Papiersammlung" would resolve on its own; the map is kept explicit so the
    # produced WASTE_TYPES are pinned and a renamed label is mapped, not silently
    # preserved verbatim.
    WASTE_TYPES = [PAPER, RECYCLABLES, GARDEN_WASTE, HAZARDOUS]

    def parse(self, response: Any, source: "Source") -> list[dict[str, str]]:
        """Pull the schedule out of the table's ``data-entities`` JSON blob.

        The page has two such blobs; only the schedule's records carry an
        ``_anlassDate`` field, so that is how the right one is selected. Each
        record's ``name`` (waste type) and ``_anlassDate`` (date) are fragments
        of HTML, reduced here to plain text for ``classify`` to consume.
        """
        soup = BeautifulSoup(response.text, "html.parser")
        for element in soup.select("[data-entities]"):
            blob = element["data-entities"]
            if not isinstance(blob, str):
                continue
            try:
                rows = json.loads(blob).get("data", [])
            except (ValueError, TypeError):
                continue
            if not any("_anlassDate" in row for row in rows):
                continue
            return [
                {
                    "type": _strip_html(row.get("name", "")),
                    "date": _strip_html(row.get("_anlassDate", "")),
                }
                for row in rows
            ]
        return []

    def classify(self, record: dict[str, str]) -> Collection | None:
        label = record.get("type")
        date_text = record.get("date") or ""
        # The date field renders the same dd.mm.yyyy twice (one span per
        # breakpoint), so take the first match rather than the whole string.
        match = re.search(r"\d{1,2}\.\d{1,2}\.\d{4}", date_text)
        if not label or not match:
            return None
        waste_type = _TYPE_MAP.get(label)
        if waste_type is None:
            return None
        return Collection(date=self.parse_date(match.group()), waste_type=waste_type)
