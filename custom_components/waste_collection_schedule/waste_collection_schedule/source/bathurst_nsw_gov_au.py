import re
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, recurrence
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.preprocessors import RecurrenceExpander, Schedule
from waste_collection_schedule.service.IntraMaps import (
    IntraMapsPanelParser,
    IntraMapsRetriever,
    MapsClientConfig,
)
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import GENERAL_WASTE, ORGANIC, RECYCLABLES

# Address + suburb lookup (IntraMapsRetriever's optional suburb disambiguates
# multiple search matches). Two columns are weekly (a bare weekday name);
# Recycling is fortnightly with an explicit "next date". The only
# source-specific code is _describe, which tells each column apart.

INTRAMAPS_CONFIG = MapsClientConfig(
    base_url="https://maps.bathurst.nsw.gov.au",
    instance="IntraMaps23A",
    project="00000000-0000-0000-0000-000000000000",
    lite_config_id="24d1884e-fc58-45df-bca0-11bddc554781",
    module_id="aa22688c-60ba-4db6-8db1-60f89ba2c5ed",
)

# IntraMaps column name -> canonical waste type.
_TYPE_MAP = {
    "Garbage": GENERAL_WASTE,
    "Organic": ORGANIC,
    "Recycling": RECYCLABLES,
}

# Columns whose value is a bare weekday name (weekly); every other mapped
# column is a fortnightly "next date" field.
_WEEKLY_COLUMNS = {"Garbage", "Organic"}

# The Recycling value is free text such as "Thursday, 23 July 2026"; pull out
# just the date rather than parsing the whole string, in case the provider
# prefixes it with wording dateutil can't handle unaided (e.g. "next").
_DATE_RE = re.compile(r"(\d{1,2}\s+\w+\s+\d{4})")


def _describe(record, source):
    column = record.get("column", "")
    if column not in _TYPE_MAP:
        return
    text = record.get("value", "").strip()
    if not text:
        return

    if column in _WEEKLY_COLUMNS:
        weekday = recurrence.weekday(text)
        if weekday is None:
            return
        yield Schedule(column, recurrence.next_weekday(weekday), recurrence.WEEKLY, 26)
        return

    match = _DATE_RE.search(text)
    if not match:
        return
    try:
        next_date = date_parsers.auto(match.group(1))
    except (ValueError, TypeError):
        return
    yield Schedule(column, next_date, recurrence.FORTNIGHTLY, 13)


@final
class Source(BaseSource):
    TITLE = "Bathurst Regional Council"
    DESCRIPTION = "Source for Bathurst Regional Council (NSW) waste collection."
    URL = (
        "https://www.bathurst.nsw.gov.au/Services/Waste-Recycling/"
        "Waste-Recycling-Calendar"
    )
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    SOURCE_CODEOWNERS: ClassVar[list[str]] = ["@Wolfieeewolf"]

    TEST_CASES: ClassVar[dict] = {
        "Howick Street": {"address": "230 Howick St", "suburb": "Bathurst"},
        "Keppel Street": {"address": "1 Keppel St", "suburb": "Bathurst"},
    }

    PARAMS = (
        text_field("address", "Street Address"),
        text_field("suburb", "Suburb"),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street address and suburb "
            "(e.g. address '230 Howick St', suburb 'Bathurst'). "
            "Search at https://maps.bathurst.nsw.gov.au/IntraMaps23A/"
            "ApplicationEngine/frontend/mapbuilder/default.htm"
            "?configId=00000000-0000-0000-0000-000000000000"
            "&liteConfigId=24d1884e-fc58-45df-bca0-11bddc554781"
        ),
    }

    retrieve = IntraMapsRetriever(INTRAMAPS_CONFIG, address="address", suburb="suburb")
    parse = IntraMapsPanelParser()
    preprocess = RecurrenceExpander(_describe)

    transform = ICSTransformer(type_value_map=_TYPE_MAP)

    def __init__(self, address: str, suburb: str):
        super().__init__(address=address, suburb=suburb)
