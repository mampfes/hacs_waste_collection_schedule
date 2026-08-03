import re
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.collection import Collection

# Demonstrates: parsers.AttributeJsonParser, for a JSON payload embedded inside
# an HTML data-attribute.
#
# Muttenz runs on the Swiss "i-web" municipal CMS. The waste page is fully
# server-rendered, but the collection table is not plain <tr>/<td> markup the
# way the existing HTML-scrape examples (lawrence_ma_us, isaac_qld_gov_au) are.
# Instead the whole schedule ships as a JSON array inside a single
# ``data-entities`` attribute on the table element, and every field inside that
# JSON is itself a fragment of escaped HTML (an <a> for the waste-type name, a
# pair of responsive <span>s for the date). AttributeJsonParser reads exactly
# that shape, and i-web powers many other Swiss municipalities.
#
# The page carries two data-entities blocks: the schedule (records have an
# ``_anlassDate``) and a waste-type legend (records do not), which is what
# ``require_keys`` selects between. Dates are dd.mm.yyyy (Swiss German), which
# dateutil parses, so no custom locale handling is needed.

_TYPE_MAP: dict[str, wt.WasteType] = {
    "Papiersammlung": wt.PAPER,
    "Kunststoffsammlung": wt.RECYCLABLES,
    # "Altmetallabuhr" is the provider's own spelling (a missing "f"); match it
    # verbatim so scrap-metal collections are not silently dropped.
    "Altmetallabuhr": wt.RECYCLABLES,
    "Grünabfuhr": wt.GARDEN_WASTE,
    "Häckseltag": wt.GARDEN_WASTE,
    "Sonderabfallsammlung": wt.HAZARDOUS,
}


@final
class Source(BaseSource):
    TITLE = "Gemeinde Muttenz"
    DESCRIPTION = "Source for the municipality of Muttenz, Switzerland."
    URL = "https://www.muttenz.ch"
    COUNTRY = "ch"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@markvp"]
    API_URL = "https://www.muttenz.ch/abfalldaten"

    TEST_CASES: ClassVar[dict] = {"Muttenz": {}}

    PARAMS = ()

    HOWTO: ClassVar[dict] = {
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
    WASTE_TYPES: ClassVar[list] = [
        wt.PAPER,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
        wt.HAZARDOUS,
    ]

    parse = parsers.AttributeJsonParser(
        "[data-entities]",
        "data-entities",
        "data",
        require_keys=("_anlassDate",),
        strip_html=True,
    )

    def classify(self, record: dict[str, str]) -> Collection | None:
        label = record.get("name")
        date_text = record.get("_anlassDate") or ""
        # The date field renders the same dd.mm.yyyy twice (one span per
        # breakpoint), so take the first match rather than the whole string.
        match = re.search(r"\d{1,2}\.\d{1,2}\.\d{4}", date_text)
        if not label or not match:
            return None
        waste_type = _TYPE_MAP.get(label)
        if waste_type is None:
            return None
        return Collection(date=self.parse_date(match.group()), waste_type=waste_type)
