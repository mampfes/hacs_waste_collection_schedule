from datetime import datetime
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, preprocessors, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.transformers import JsonTransformer

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.wastenet.org.nz/3-bin-day-finder",
}


def _address(response, address, **_):
    wanted = address.replace(" INVERCARGILL", ", Invercargill").strip()
    candidates = response.json()
    for candidate in candidates:
        if candidate["address"].lower() == wanted.lower():
            return candidate["address"]
    partial = [
        c["address"] for c in candidates if wanted.lower() in c["address"].lower()
    ]
    if len(partial) == 1:
        return partial[0]
    raise SourceArgumentNotFoundWithSuggestions(
        "address",
        wanted,
        partial[:10] if partial else [c["address"] for c in candidates[:5]],
    )


def _round(record):
    week = record["collection"]["Week"]
    return (
        "Yellow Week ICC"
        if week == "Yellow Week" and record.get("Council", 1) == 1
        else week
    )


@final
class Source(BaseSource):
    TITLE = "Gore, Invercargill & Southland"
    DESCRIPTION = "Source for Wastenet.org.nz."
    URL = "https://www.wastenet.org.nz"
    COUNTRY = "nz"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@etamtlosz"]
    TEST_CASES: ClassVar[dict] = {
        "166 Lewis Street, Invercargill": {"address": "166 Lewis Street, Invercargill"},
        "Old Format: 199 Crawford Street INVERCARGILL": {
            "address": "199 Crawford Street INVERCARGILL"
        },
        "Old Format: 156 Tay Street INVERCARGILL": {
            "address": "156 Tay Street INVERCARGILL"
        },
        "Gore: 1 Anderson Place": {"address": "1 Anderson Place, Gore"},
        "ICC: 32 Gladstone Terrace, Invercargill": {
            "address": "32 Gladstone Terrace, Invercargill"
        },
        "ICC: 15 King Street, Invercargill": {
            "address": "15 King Street, Invercargill"
        },
        "ICC: 132 Leet Street, Invercargill": {
            "address": "132 Leet Street, Invercargill"
        },
        "ICC: 20 Rodney Street, Invercargill": {
            "address": "20 Rodney Street, Invercargill"
        },
        "ICC: 34 Lothian Crescent, Invercargill": {
            "address": "34 Lothian Crescent, Invercargill"
        },
        "ICC: 69 Chesney Street, Invercargill": {
            "address": "69 Chesney Street, Invercargill"
        },
    }
    PARAMS = (street_address(),)
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES]
    HOWTO: ClassVar[dict] = {
        "en": (
            "Visit https://www.wastenet.org.nz and find your property address. "
            "Use the full address, e.g. '166 Lewis Street, Invercargill' or "
            "'1 Anderson Place, Gore'. Since the v3 pipeline migration, waste "
            "types use canonical, localised names; update filters, automations "
            "and customisations using the old labels."
        ),
    }
    retrieve = retrievers.Request(
        "https://www.wastenet.org.nz/client-api/icc/rubbish/search",
        headers=HEADERS,
        before=(
            retrievers.Lookup(
                "https://www.wastenet.org.nz/client-api/icc/rubbish/address-list",
                headers=HEADERS,
                pick=_address,
            ),
        ),
        params=lambda canonical_address, **_: {
            "address": canonical_address,
            "date": datetime.now().date().isoformat(),
        },
    )
    parse = parsers.JsonParser()
    preprocess = preprocessors.Compose(
        preprocessors.ExplodeList("NextDates", into="collection"),
        preprocessors.RowFilter(
            lambda record, source: (
                record["collection"]["Week"] in ("Red Week", "Yellow Week")
            )
        ),
    )
    transform = JsonTransformer(
        date_key=lambda record: record["collection"]["Date"],
        type_key=_round,
        parse_date=date_parsers.auto,
        type_value_map={
            "Red Week": wt.GENERAL_WASTE,
            "Yellow Week": wt.RECYCLABLES,
            "Yellow Week ICC": [wt.GENERAL_WASTE, wt.RECYCLABLES],
        },
    )
