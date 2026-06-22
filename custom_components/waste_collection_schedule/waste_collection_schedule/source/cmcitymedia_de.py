import datetime
from typing import final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.collection import Collection
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.regions import Region, region
from waste_collection_schedule.service.CMCityMedia import (
    CMCityMediaParser,
    CMCityMediaRetriever,
)
from waste_collection_schedule.waste_types import ALL_TYPES, preserved, resolve

# Declarative source on the CM City Media components (CMCityMediaRetriever +
# CMCityMediaParser). The provider registry lives here, in the source that owns
# it; each entry carries the homepage id (hpid) the user selects and the realm
# the API needs. classify() resolves each item's German type name onto a
# canonical WasteType via the shared multilingual vocabulary.

URL = "https://cmcitymedia.de"

_PROVIDERS = [
    {"hpid": 415, "realm": 41500, "region": "Gemeinde Blankenheim"},
    {
        "hpid": 95,
        "realm": 9501,
        "region": "Landkreis Schwäbisch Hall",
        "disabled": True,
    },
    {"hpid": 1, "realm": 100, "region": "Gemeinde Bühlerzell", "disabled": True},
    {
        "hpid": 107,
        "realm": 10701,
        "region": "Gemeinde Kressbronn am Bodensee",
        "disabled": True,
    },
    {"hpid": 168, "realm": 16801, "region": "Hohenlohekreis", "disabled": True},
    {"hpid": 225, "realm": 22500, "region": "Gemeinde Deggenhausertal"},
    {"hpid": 233, "realm": 23301, "region": "Stadt Kraichtal", "disabled": True},
    {"hpid": 248, "realm": 24800, "region": "Gemeinde Kappelrodeck", "disabled": True},
    {"hpid": 331, "realm": 33100, "region": "Gemeinde Schutterwald"},
    {"hpid": 374, "realm": 37401, "region": "Gemeinde Aschheim", "disabled": True},
    {
        "hpid": 390,
        "realm": 39000,
        "region": "Gemeinde Mittelbiberach",
        "disabled": True,
    },
    {"hpid": 391, "realm": 39100, "region": "Stadt Ehingen", "disabled": True},
    {
        "hpid": 420,
        "realm": 42000,
        "region": "Gemeinde Senden (Westfalen)",
        "disabled": True,
    },
    {"hpid": 421, "realm": 42100, "region": "Stadt Emden", "disabled": True},
    {"hpid": 424, "realm": 42400, "region": "Stadt Emmendingen"},
    {"hpid": 426, "realm": 42600, "region": "Gemeinde Kalletal"},
    {"hpid": 441, "realm": 44100, "region": "Stadt Messstetten"},
    {"hpid": 447, "realm": 44700, "region": "Gemeinde Oberstadion", "disabled": True},
]


@final
class Source(BaseSource):
    TITLE = "CM City Media - Müllkalender"
    DESCRIPTION = "Source script for cmcitymedia.de"
    URL = URL
    COUNTRY = "de"
    # A fixed-provider source: an empty schedule is a legitimate "no collections
    # in the window" result, so do not RAISE_ON_EMPTY (matches the legacy source
    # which returned []).
    # classify() resolves open-ended German labels via the shared vocabulary,
    # so any canonical type may appear.
    WASTE_TYPES = list(ALL_TYPES)

    # Both cases exercise the enabled Blankenheim provider (district-based and
    # realmid-override paths); disabled providers serve no data so are not tested.
    TEST_CASES = {
        "Blankenheim - Bezirk F: Lindweiler, Rohr": {"hpid": 415, "district": 1371},
        "Blankenheim": {"hpid": 415, "realmid": 41500},
    }

    PARAMS = [
        text_field("hpid", "Homepage id"),
        text_field("realmid", "Realm id (optional override)", optional=True),
        text_field("district", "District (optional)", optional=True),
    ]

    retrieve = CMCityMediaRetriever()
    parse = CMCityMediaParser()

    @staticmethod
    def REGIONS() -> list[Region]:
        return [
            region(p["region"], url=URL, hpid=p["hpid"])
            for p in _PROVIDERS
            if not p.get("disabled", False)
        ]

    def __init__(self, hpid, realmid=None, district=None):
        # Resolve the realm the API needs from the provider registry (the user
        # selects only the hpid); realmid stays an explicit override.
        realm = realmid
        if realm is None:
            provider = next((p for p in _PROVIDERS if p["hpid"] == hpid), None)
            if provider is not None:
                realm = provider["realm"]
        super().__init__(hpid=hpid, realmid=realmid, district=district, realm=realm)

    def classify(self, record) -> Collection | None:
        date = datetime.datetime.strptime(record["date"], "%Y-%m-%d").date()
        name = record["name"]
        return Collection(date=date, waste_type=resolve(name) or preserved(name))
