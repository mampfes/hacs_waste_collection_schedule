from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import dropdown
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.service.RiSKommunalAT import (
    RiSKommunalParser,
    RiSKommunalRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer

_BASE_URL = "https://www.ebbs.gv.at"

# Ebbs's RiSKommunal install does not expose a single combined calendar with a
# filterable third ("Kalendertyp") column the way Eggelsberg does: querying
# kalender.aspx without a `typids` filter returns both zones' rows merged into
# the *same two-column* table, with the zone folded into the residual-waste
# label itself ("Restmüllabfuhr - Müllabfuhrzone 1" / "... 2"). The
# municipality's own site instead links residents to one pre-filtered URL per
# zone, each with its own fixed `typids` set (confirmed live: zone 1's typids
# additionally carry "Gelber Sack", which zone 2 does not get). That is the
# shape `RiSKommunalRetriever`'s `zone_param`/`zone_typids` covers.
_ZONE_TYPIDS = {
    "1": "217676083,225177200,226278459",
    "2": "217678360,226278459",
}

# One source of truth for the zones: the dropdown options and the retriever's
# lookup table are the same set, so adding a zone means editing _ZONE_TYPIDS only.
VALID_ZONES = sorted(_ZONE_TYPIDS)


@final
class Source(BaseSource):
    TITLE = "Gemeinde Ebbs"
    DESCRIPTION = "Source for Gemeinde Ebbs, Tyrol, Austria waste collection."
    URL = _BASE_URL
    COUNTRY = "at"
    RAISE_ON_EMPTY = True
    SOURCE_CODEOWNERS: ClassVar[list] = ["@rr62wghzwp-blip"]

    # The vocabulary this feed actually produces, derived by replaying the
    # recorded cassette. "Gelber Sack" resolves via the shared vocabulary
    # (RECYCLABLES); "Biomüllabfuhr" and the zone-suffixed "Restmüllabfuhr -
    # Müllabfuhrzone N" labels are this provider's own naming and are mapped
    # explicitly below.
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Zone 1": {"zone": "1"},
        "Zone 2": {"zone": "2"},
    }

    PARAMS = (dropdown("zone", VALID_ZONES),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Find your street on https://www.ebbs.gv.at/Muellabfuhrtermine to "
            "determine your collection zone (1 or 2) -- for example, Tafang "
            "is in Zone 2. Residual waste (Restmüllabfuhr) and, in Zone 1, "
            "the yellow-bag collection (Gelber Sack) run on a zone-specific "
            "schedule; organic waste (Biomüllabfuhr) is the same for both "
            "zones."
        ),
        "de": (
            "Suchen Sie Ihre Straße auf https://www.ebbs.gv.at/Muellabfuhrtermine, "
            "um Ihre Müllabfuhrzone (1 oder 2) zu bestimmen -- z. B. liegt "
            "Tafang in Zone 2. Restmüllabfuhr und (nur in Zone 1) die "
            "Gelbe-Sack-Abholung richten sich nach der jeweiligen Zone; die "
            "Biomüllabfuhr ist für beide Zonen gleich."
        ),
    }

    retrieve = RiSKommunalRetriever(
        base_url=_BASE_URL,
        query_params={
            "sprache": "1",
            "menuonr": "225153130",
            "bdatum": "31.12.9999",
        },
        zone_param="zone",
        zone_typids=_ZONE_TYPIDS,
        vdatum_today=True,
    )
    parse = RiSKommunalParser()

    transform = ICSTransformer(
        type_value_map={
            "Biomüllabfuhr": wt.ORGANIC,
            "Restmüllabfuhr - Müllabfuhrzone 1": wt.GENERAL_WASTE,
            "Restmüllabfuhr - Müllabfuhrzone 2": wt.GENERAL_WASTE,
        },
    )

    def __init__(self, zone: str):
        zone = str(zone).strip()
        if zone not in VALID_ZONES:
            raise SourceArgumentNotFoundWithSuggestions(
                "zone", zone, suggestions=VALID_ZONES
            )
        super().__init__(zone=zone)
