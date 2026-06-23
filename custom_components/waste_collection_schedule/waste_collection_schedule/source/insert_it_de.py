from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    alternatives,
    house_number,
    location_id,
    municipality,
    street,
)
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.regions import Region, region
from waste_collection_schedule.service.InsertITDe import (
    BASE_URL,
    InsertItParser,
    InsertItRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer, label_cleaner
from waste_collection_schedule.waste_types import ALL_TYPES

# Declarative source on the Insert IT components. The per-region configuration
# travels with each provider entry (the app path, the ICS regex, and an optional
# type-name remap), rather than living in separate parallel maps keyed by
# municipality. The remap (only some municipalities need one) is applied as a
# per-instance ICSTransformer clean step, set in __init__ from the provider.

_LEERUNG = r"Leerung:\s+(.*)\s+\(.*\)"

_PROVIDERS = [
    {
        "municipality": "Hattingen",
        "title": "Abfallkalender Hattingen",
        "path": "BmsAbfallkalenderHattingen",
        "regex": _LEERUNG,
    },
    {
        "municipality": "Herne",
        "title": "Abfallkalender Herne",
        "path": "BmsAbfallkalenderHerne",
        "regex": _LEERUNG,
    },
    {
        "municipality": "Kassel",
        "title": "Abfallkalender Kassel",
        "path": "BmsAbfallkalenderKassel",
        "regex": _LEERUNG,
    },
    {
        "municipality": "Krefeld",
        "title": "GSAK APP / Krefeld",
        "path": "BmsAbfallkalenderKrefeld",
        "regex": _LEERUNG,
    },
    {
        "municipality": "Luebeck",
        "title": "Abfallkalender Luebeck",
        "path": "BmsAbfallkalenderLuebeck",
        "regex": _LEERUNG,
    },
    {
        "municipality": "Mannheim",
        "title": "Abfallkalender Mannheim",
        "path": "BmsAbfallkalenderMannheim",
        "regex": r"Leerung:\s+(.*)",
        "types": {
            "Rest": "Restmüll",
            "Wertstoff": "Sack/Tonne gelb",
            "Bio": "Biomüll",
            "Papier": "Altpapier",
            "Grünschnitt": "Grünschnitt",
        },
    },
    {
        "municipality": "Offenbach",
        "title": "Abfallkalender Offenbach",
        "path": "BmsAbfallkalenderOffenbach",
        "regex": _LEERUNG,
    },
]

_BY_MUNICIPALITY = {p["municipality"]: p for p in _PROVIDERS}


# Not @final: offenbach_de subclasses this as a deprecated alias.
class Source(BaseSource):
    TITLE = "Insert IT Apps"
    DESCRIPTION = "Source for Apps by Insert IT"
    URL = "https://insert-infotech.de/"
    COUNTRY = "de"
    # classify() resolves open-ended German labels via the shared vocabulary,
    # so any canonical type may appear.
    WASTE_TYPES = list(ALL_TYPES)

    TEST_CASES = {
        "Offenbach Address": {
            "municipality": "Offenbach",
            "street": "Kaiserstraße",
            "hnr": 1,
        },
        "Offenbach Location ID": {"municipality": "Offenbach", "location_id": 7036},
        "Mannheim Address": {"municipality": "Mannheim", "street": "A 3", "hnr": 1},
        "Mannheim Location ID": {"municipality": "Mannheim", "location_id": 430650},
    }

    PARAMS = [
        municipality("municipality"),
        alternatives(
            [location_id("location_id")],
            [street("street"), house_number("hnr")],
        ),
    ]

    retrieve = InsertItRetriever()
    parse = InsertItParser()
    transform = ICSTransformer()

    @staticmethod
    def REGIONS() -> list[Region]:
        return [
            region(
                p["title"],
                url=f"{BASE_URL}/{p['path']}",
                municipality=p["municipality"],
            )
            for p in _PROVIDERS
        ]

    def __init__(self, municipality, street=None, hnr=None, location_id=None):
        provider = _BY_MUNICIPALITY.get(municipality)
        if provider is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "municipality", municipality, list(_BY_MUNICIPALITY)
            )
        # Only some municipalities relabel their types; apply that region's remap
        # as a per-instance clean step before the canonical resolve.
        types = provider.get("types")
        if types:
            self.transform = ICSTransformer(clean=label_cleaner(remap=types))
        super().__init__(
            municipality=municipality,
            street=street,
            hnr=hnr,
            location_id=location_id,
            path=provider["path"],
            regex=provider["regex"],
        )
