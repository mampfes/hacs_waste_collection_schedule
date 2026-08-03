"""C-Trace (c-trace.de), Germany: a multi-tenant ASP.NET calendar platform.

Demonstrates: a shared platform serving many independent operators
(municipalities/Landkreise), each a "service" under its own path on one of a
few subdomains. The platform itself (its operator registry and the cookieless
ASP.NET session handshake that leads to the ICS feed) lives in
``service/CTrace.py``, so this source is metadata plus a composition of shared
steps.

Every operator in ``SERVICE_MAP`` is preserved as its own ``Region`` (the
typed successor to the legacy ``EXTRA_INFO`` callable), so none of the towns
this source covers are dropped by the conversion.
"""

from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    district,
    house_number,
    municipality,
    street,
    text_field,
)
from waste_collection_schedule.regions import region
from waste_collection_schedule.service.CTrace import (
    SERVICE_MAP,
    CTraceCalendarRetriever,
    resolve_service,
)
from waste_collection_schedule.transformers import ICSTransformer

# All waste-type ids: the provider returns every collection when none are
# filtered out, matching the legacy default of "0|1|2|...|299".
_ABFALL_ALL = "|".join(str(i) for i in range(300))


@final
class Source(BaseSource):
    TITLE = "C-Trace"
    DESCRIPTION = "Source for C-Trace.de."
    URL = "https://c-trace.de/"
    COUNTRY = "de"

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.GLASS,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Bremen": {"ort": "Bremen", "strasse": "Abbentorstraße", "hausnummer": 5},
        "AugsburgLand": {
            "ort": "Königsbrunn",
            "strasse": "Marktplatz",
            "hausnummer": 7,
            "service": "augsburglandkreis",
        },
        "landau": {
            "strasse": "Am Kindergarten",
            "hausnummer": 1,
            "service": "landau",
        },
        "WZV": {
            "ort": "Bark",
            "strasse": "Birkenweg",
            "hausnummer": 1,
            "service": "segebergwzv-abfallkalender",
        },
        "oberursel": {
            "service": "oberursel",
            "strasse": "Ahornweg",
            "hausnummer": "8a",
        },
        "roth": {
            "ort": "Georgensgmünd",
            "strasse": "Mauk",
            "hausnummer": 2,
            "service": "roth",
        },
        "Groß-Gerau landkreis: Gernsheim (without ortsteil)": {
            "ort": "Gernsheim am Rhein",
            "strasse": "Alsbacher Straße",
            "hausnummer": 4,
            "service": "grossgeraulandkreis-abfallkalender",
        },
        "Groß-Gerau landkreis: Riedstadt (with ortsteil)": {
            "ort": "Riedstadt",
            "ortsteil": "Crumstadt",
            "strasse": "Am Lohrrain",
            "hausnummer": 3,
            "service": "grossgeraulandkreis-abfallkalender",
        },
        "Aurich Kirchdorf": {
            "ort": "Kirchdorf",
            "gemeinde": "Aurich",
            "strasse": "Am Reidigermeer",
            "hausnummer": "2d/e",
            "service": "aurich-abfallkalender",
        },
        "MainTauber 4-weekly": {
            "ort": "Tauberbischofsheim",
            "strasse": "Hauptstraße",
            "hausnummer": 1,
            "service": "maintauberkreis-abfallkalender",
            "abfall": "0|1|2|5",
        },
    }

    # One structure, many independent operators: preserve every one of
    # SERVICE_MAP's towns as its own Region so none are dropped from the
    # generated README / sources.json listings.
    REGIONS = tuple(
        region(entry["title"], url=entry["url"], service=key)
        for key, entry in SERVICE_MAP.items()
    )

    PARAMS = (
        street(field="strasse"),
        house_number(field="hausnummer"),
        municipality(field="gemeinde", optional=True),
        district(field="ort", optional=True),
        text_field("ortsteil", "Subdistrict", optional=True),
        text_field("service", "Operator", optional=True),
        text_field("abfall", "Waste type IDs", optional=True),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "'service' selects your operator (e.g. 'landau', "
            "'augsburglandkreis'); leave it empty only if 'ort' is 'Bremen'. "
            "'abfall' is a pipe-separated list of waste-type ids (e.g. "
            "'0|1|2|5') to restrict which types are fetched; leave it empty "
            "to fetch all types. Visit your provider's calendar page to see "
            "which ids correspond to which waste types."
        ),
    }

    retrieve = CTraceCalendarRetriever()
    parse = parsers.IcsParser(regex=r"Abfuhr: (.*)")
    transform = ICSTransformer()

    def __init__(
        self,
        strasse: str,
        hausnummer: "str | int",
        gemeinde: str = "",
        ort: str = "",
        ortsteil: str = "",
        service: "str | None" = None,
        abfall: str = "",
    ):
        service, subdomain, ical_url_file = resolve_service(ort, service)
        if not gemeinde:
            gemeinde = ort
        if not abfall:
            abfall = _ABFALL_ALL
        super().__init__(
            strasse=strasse,
            hausnummer=hausnummer,
            gemeinde=gemeinde,
            ort=ort,
            ortsteil=ortsteil,
            service=service,
            abfall=abfall,
            subdomain=subdomain,
            ical_url_file=ical_url_file,
        )
