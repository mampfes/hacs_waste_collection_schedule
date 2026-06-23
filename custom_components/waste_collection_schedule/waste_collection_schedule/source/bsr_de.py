import datetime
from collections.abc import Iterable
from typing import Any, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.collection import Collection
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.parsers import JsonParser
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.waste_types import (
    GARDEN_WASTE,
    GENERAL_WASTE,
    ORGANIC,
    RECYCLABLES,
    WasteType,
    preserved,
)

# Berliner Stadtreinigungsbetriebe (BSR) publishes a per-address collection
# schedule behind an OData endpoint keyed by a "schedule_id" (AddrKey). The
# response carries a ``dates`` object mapping an ISO date to a list of pickups;
# each pickup names a category code and the disposal company. We resolve each
# code onto a canonical WasteType, preserving the original label verbatim when a
# non-BSR company runs the round (so the user still sees who is collecting).

ENDPOINT_PICKUPS = "https://umnewforms.bsr.de/p/de.bsr.adressen.app/abfuhrEvents"
FILTERTEMPLATE_PICKUPS = (
    "AddrKey eq '{id}' and "
    "DateFrom eq datetime'{year_from}-{month:02d}-01T00:00:00' and "
    "DateTo eq datetime'{year_to}-{month:02d}-01T00:00:00'"
)

# BSR category code -> (canonical WasteType, German display label). The label is
# the verbatim text BSR uses; it is shown unchanged when another company runs
# the round, so the codes map straight to a type here rather than going through
# the shared resolver.
_CATEGORIES: dict[str, tuple[WasteType, str]] = {
    "BI": (ORGANIC, "Biogut"),
    "HM": (GENERAL_WASTE, "Hausmüll"),
    "LT": (GARDEN_WASTE, "Laubtonne"),
    "WS": (RECYCLABLES, "Wertstoffe"),
    "WB": (GARDEN_WASTE, "Weihnachtsbaum"),
}


def _filter(schedule_id: str, **_: Any) -> dict[str, str]:
    now = datetime.datetime.now()
    return {
        "filter": FILTERTEMPLATE_PICKUPS.format(
            id=schedule_id,
            year_from=now.year,
            month=now.month,
            year_to=now.year + 1,
        )
    }


@final
class Source(BaseSource):
    TITLE = "Berliner Stadtreinigungsbetriebe"
    DESCRIPTION = "Source for Berliner Stadtreinigungsbetriebe waste collection."
    URL = "https://bsr.de"
    COUNTRY = "de"
    # An empty result for a valid schedule_id is a genuine "no collections in the
    # window" answer, but the schedule_id is the only address-lookup input, so a
    # typo yields nothing useful — raise to surface a clear error in the UI.
    RAISE_ON_EMPTY = True
    # classify() may preserve an unknown company-suffixed label, so the produced
    # set is open-ended beyond the four canonical types the codes resolve to.
    WASTE_TYPES = [GENERAL_WASTE, RECYCLABLES, ORGANIC, GARDEN_WASTE]

    TEST_CASES = {
        "Hufeland_45a": {"schedule_id": "04901100010300413840045A"},
        "Marktstr_1": {"schedule_id": "049011000105000297900010"},
    }

    PARAMS = [text_field("schedule_id", "Schedule id")]

    retrieve = HttpGetRetriever(url=ENDPOINT_PICKUPS, params=_filter)
    parse = JsonParser("dates")

    def __init__(self, schedule_id: str) -> None:
        super().__init__(schedule_id=schedule_id)

    def preprocess(
        self, dates: Any, source: "BaseSource | None" = None
    ) -> Iterable[dict[str, Any]]:
        # ``dates`` maps an ISO date to a list of pickups; flatten to one record
        # per pickup so classify() handles each individually.
        if not dates:
            return
        for pickups in dates.values():
            yield from pickups

    def classify(self, record: dict[str, Any]) -> Collection | None:
        date = datetime.datetime.strptime(
            record["serviceDate_actual"], "%d.%m.%Y"
        ).date()
        waste_type, label = _CATEGORIES.get(
            record["category"],
            (None, f"Unbekannter Müll ({record['category']})"),
        )
        company = record.get("disposalComp")
        if company and company != "BSR":
            # Another company runs this round: keep the verbatim, company-tagged
            # label rather than collapsing it onto the canonical type.
            return Collection(date=date, waste_type=preserved(f"{label} ({company})"))
        return Collection(date=date, waste_type=waste_type or preserved(label))
