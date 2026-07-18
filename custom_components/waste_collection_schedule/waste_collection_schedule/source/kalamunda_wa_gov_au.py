import re
from datetime import date, timedelta
from typing import Any, ClassVar, final

from waste_collection_schedule import date_parsers, recurrence, response_shape
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import dropdown, text_field
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.preprocessors import RecurrenceExpander, Schedule
from waste_collection_schedule.service.IntraMaps import (
    IntraMapsRetriever,
    MapsClientConfig,
)
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import GENERAL_WASTE, ORGANIC, RECYCLABLES

# Kalamunda's IntraMaps response keys each collection column TWICE: once as a
# "header" field whose name and value both just repeat the column's own label
# (e.g. name=value="Next FOGO Collection"), and once as the real data field,
# whose name carries a descriptive caption plus the cadence word
# ("Lime Green Lid Bin ( Green Waste FOGO ) : Every Week") and whose value is
# the actual next-collection date or weekday ("Every Wednesday"). The cadence
# word lives ONLY in that caption, which the shared IntraMapsPanelParser
# discards (it keeps column/value, not name). So this source defines a small
# local parser that duplicates the panel-field traversal (not IntraMaps.py's
# private helper) purely to retain `name`; _describe then uses name != value
# to drop the header row and reads the cadence word from name.

SUBURBS = (
    "BICKLEY",
    "CANNING MILLS",
    "CARMEL",
    "FORRESTFIELD",
    "GOOSEBERRY HILL",
    "HACKETTS GULLY",
    "HIGH WYCOMBE",
    "KALAMUNDA",
    "LESMURDIE",
    "MAIDA VALE",
    "PAULLS VALLEY",
    "PICKERING BROOK",
    "PIESSE BROOK",
    "RESERVOIR",
    "WALLISTON",
    "WATTLE GROVE",
)

INTRAMAPS_CONFIG = MapsClientConfig(
    base_url="https://kalamunda.spatial.t1cloud.com",
    instance="spatial/intramaps",
    config_id="38999f30-1676-4524-b501-0130581a2ba2",
    project="d44a7973-329f-4626-9e09-35afeacc8724",
)

# IntraMaps column name -> canonical waste type. Both the header and data
# field for a given collection share the same column, so this alone can't
# tell them apart; that's what _describe's name/value check is for.
_TYPE_MAP = {
    "General_Next_Date": GENERAL_WASTE,
    "Recycle_Next_Date": RECYCLABLES,
    "Next FOGO Collection": ORGANIC,
}

# Values are free text such as "22 July 2026, Wednesday" or "Every Wednesday";
# pull out just the date/weekday rather than parsing the whole string.
_DATE_RE = re.compile(r"(\d{1,2}\s+\w+\s+\d{4})")
_WEEKDAY_RE = re.compile(
    r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday)", re.IGNORECASE
)

# The council's own bin-day tool projects recurring collections one year
# ahead of today; match that horizon so the converted source finds the same
# range of dates as the legacy fetch().
_HORIZON = timedelta(days=365)


class _NamedPanelParser(Parser["list[dict[str, str]]"]):
    """Like IntraMapsPanelParser, but also keeps each field's caption (`name`).

    Duplicates the shared parser's panel-field traversal locally (rather than
    reaching into ``IntraMaps.py``'s private ``_panel_fields`` helper) so this
    stays entirely source-side: the only difference from the shared parser is
    that it keeps ``name`` alongside ``column``/``value``, since Kalamunda's
    cadence word is never present anywhere else.
    """

    def __init__(self, panel: str = "info1"):
        self.panel = panel

    def __call__(
        self, response: dict[str, Any], source: BaseSource | None = None
    ) -> list[dict[str, str]]:
        response_shape.expect(
            isinstance(response, dict) and "infoPanels" in response,
            source_name=response_shape.source_name(source),
            detail="IntraMaps response has no 'infoPanels'",
            raw=response,
        )
        fields = (
            (response or {})
            .get("infoPanels", {})
            .get(self.panel, {})
            .get("feature", {})
            .get("fields", [])
        )
        records: list[dict[str, str]] = []
        for field in fields:
            value = field.get("value", {})
            if isinstance(value, dict):
                records.append(
                    {
                        "name": field.get("name", ""),
                        "column": value.get("column", ""),
                        "value": value.get("value", ""),
                    }
                )
        return records


def _describe(record, source):
    column = record.get("column", "")
    if column not in _TYPE_MAP:
        return
    name = record.get("name", "").strip()
    text = record.get("value", "").strip()
    if not text or not name or text == name:
        # The header row for this column repeats its own label as both name
        # and value; only the real data row carries a distinct value.
        return

    date_match = _DATE_RE.search(text)
    if date_match:
        try:
            start = date_parsers.auto(date_match.group(1))
        except (ValueError, TypeError):
            return
    else:
        weekday_match = _WEEKDAY_RE.search(text)
        if not weekday_match:
            return
        weekday = recurrence.weekday(weekday_match.group(1))
        if weekday is None:
            return
        start = recurrence.next_weekday(weekday)

    # The cadence word lives in the caption ("... : Alternate Fortnight" /
    # "... : Every Week"), never in the value itself.
    name_lower = name.lower()
    if "fortnight" in name_lower:
        yield Schedule(
            column, start, recurrence.FORTNIGHTLY, until=date.today() + _HORIZON
        )
    elif "week" in name_lower:
        yield Schedule(column, start, recurrence.WEEKLY, until=date.today() + _HORIZON)
    else:
        yield Schedule(column, start, count=1)


@final
class Source(BaseSource):
    TITLE = "City of Kalamunda"
    DESCRIPTION = "Source for the City of Kalamunda rubbish collection."
    URL = (
        "https://www.kalamunda.wa.gov.au/kerbside-3-bin-system/collection-days/bin-day"
    )
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Kalamunda Hotel": {
            "suburb": "Kalamunda",
            "street_name": "Railway Road",
            "street_number": "43",
        },
        "Gooseberry Hill Multi-Use Facility": {
            "suburb": "Gooseberry hill",
            "street_name": "Ledger Road",
            "street_number": "42",
        },
        "High Wycombe Public Library": {
            "suburb": "High Wycombe",
            "street_name": "Markham Road",
            "street_number": "15",
        },
    }

    PARAMS = (
        dropdown("suburb", list(SUBURBS), label="Suburb"),
        text_field("street_name", "Street Name"),
        text_field("street_number", "Street Number"),
    )

    retrieve = IntraMapsRetriever(INTRAMAPS_CONFIG, address="address", suburb="suburb")
    parse = _NamedPanelParser()
    preprocess = RecurrenceExpander(_describe)

    transform = ICSTransformer(type_value_map=_TYPE_MAP)

    def __init__(self, suburb: str, street_name: str, street_number: str):
        suburb_upper = suburb.strip().upper()
        if suburb_upper not in SUBURBS:
            raise SourceArgumentNotFoundWithSuggestions("suburb", suburb, list(SUBURBS))

        # Search results come back empty when the suburb is appended to the
        # address string, so it's passed separately for disambiguation.
        address = f"{street_number} {street_name}"
        super().__init__(
            suburb=suburb,
            street_name=street_name,
            street_number=street_number,
            address=address,
        )
