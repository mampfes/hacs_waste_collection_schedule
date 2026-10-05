import re
from typing import Any, ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.preprocessors import (
    Compose,
    Deduplicate,
    SplitByFields,
)
from waste_collection_schedule.service.ArcGis import (
    ArcGisFeatureParser,
    ArcGisFeatureRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer

# Layer 125 (Refuse_Collection), which this source used to read, never gained
# the FOGO (food and garden organics) round that starts in October 2026.
_LAYER_URL = (
    "https://gis.rdc.govt.nz/server/rest/services/Core/RdcServices/MapServer/160"
)

# Newest first, so Deduplicate keeps the later field for a date two of them
# share: in the week FOGO starts, RubbishCollection1 still carries the pre-FOGO
# round ("Recycling and Rubbish") for the date RubbishCollection3 lists as
# "Recycling and FOGO". RubbishCollection2 is blank in every zone.
_FIELDS = (
    "RubbishCollection4",
    "RubbishCollection3",
    "RubbishCollection2",
    "RubbishCollection1",
)

# "Tuesday 06/10/2026 Recycling and FOGO". Zones without kerbside collection
# hold a sentence ("No Collection: Take rubbish to ...") that doesn't match.
_ENTRY = re.compile(r"^\s*\w+day\s+(\d{2}/\d{2}/\d{4})\s+(.+?)\s*$")


def _entry_part(record: dict[str, Any], group: int) -> str | None:
    match = _ENTRY.match(record.get("entry") or "")
    return match[group] if match else None


@final
class Source(BaseSource):
    TITLE = "Rotorua Lakes Council"
    DESCRIPTION = "Source for Rotorua Lakes Council"
    URL = "https://www.rotorualakescouncil.nz"
    COUNTRY = "nz"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES, wt.ORGANIC]

    TEST_CASES: ClassVar[dict] = {
        "Test1": {"address": "1061 Haupapa Street"},
        "Test2": {"address": "369 state highway 33"},
        "Test3": {"address": "17 Tihi road"},
        "Test4": {"address": "12a robin st"},
        "Test5": {"address": "25 kaska rd"},
    }

    PARAMS = (street_address("address"),)

    HOWTO: ClassVar[dict] = {
        "en": "Enter your street address, e.g. '1061 Haupapa Street'.",
    }

    retrieve = ArcGisFeatureRetriever(
        _LAYER_URL,
        address=lambda address, **_: f"{address}, Rotorua, New Zealand",
        out_fields=",".join(_FIELDS),
    )
    parse = parsers.ArgumentGuard(
        ArcGisFeatureParser(),
        argument="address",
        contains='"attributes"',
        hint="The address must be within the Rotorua Lakes district.",
    )
    preprocess = Compose(
        SplitByFields(src_keys=_FIELDS, dst_key="entry"),
        Deduplicate(key=lambda record: _entry_part(record, 1)),
    )
    transform = JsonTransformer(
        date_key=lambda record: _entry_part(record, 1),
        type_key=lambda record: _entry_part(record, 2),
        parse_date=date_parsers.for_format("%d/%m/%Y"),
        type_value_map={
            "Rubbish only": wt.GENERAL_WASTE,
            "Recycling and Rubbish": [wt.RECYCLABLES, wt.GENERAL_WASTE],
            "Rubbish and FOGO": [wt.GENERAL_WASTE, wt.ORGANIC],
            "Recycling and FOGO": [wt.RECYCLABLES, wt.ORGANIC],
            # CBD, Glenholme and Kuirau, where only food premises have a FOGO bin.
            "Rubbish (and FOGO for food premises)": wt.GENERAL_WASTE,
            "Recycling and Rubbish (and FOGO for food premises)": [
                wt.RECYCLABLES,
                wt.GENERAL_WASTE,
            ],
        },
    )
