"""C-Trace (c-trace.de), Germany: a multi-tenant ASP.NET calendar platform.

Demonstrates: a shared platform serving many independent operators
(municipalities/Landkreise), each a "service" under its own path on one of a
few subdomains. Getting to the ICS feed needs a first GET (without following
the redirect) to mint an ASP.NET session id from the ``Location`` header,
then a second GET assembling that session id into the calendar path. No
configured retriever expresses "GET without redirects, read a session id out
of the Location header, GET again with it spliced into the URL", so this
stays a source-defined ``retrieve``.

Every operator in ``SERVICE_MAP`` is preserved as its own ``Region`` (the
typed successor to the legacy ``EXTRA_INFO`` callable), so none of the towns
this source covers are dropped by the conversion.
"""

from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    district,
    house_number,
    municipality,
    street,
    text_field,
)
from waste_collection_schedule.exceptions import SourceArgumentRequired
from waste_collection_schedule.regions import region
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GENERAL_WASTE,
    GLASS,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

DEFAULT_SUBDOMAIN = "web"
DEFAULT_ICAL_URL_FILE = "cal"

BASE_URL = "https://{subdomain}.c-trace.de"

# All waste-type ids: the provider returns every collection when none are
# filtered out, matching the legacy default of "0|1|2|...|299".
_ABFALL_ALL = "|".join(str(i) for i in range(300))

# Do not support Ical Download:
# lekarowarschau-abfallkalender
# web.torgauoschatz2015

SERVICE_MAP: dict[str, dict[str, str]] = {
    "bremenabfallkalender": {
        "title": "Bremer Stadtreinigung",
        "url": "https://www.die-bremer-stadtreinigung.de/",
    },
    "augsburglandkreis": {
        "title": "Abfallwirtschaftsbetrieb Landkreis Augsburg",
        "url": "https://www.awb-landkreis-augsburg.de/",
    },
    "segebergwzv-abfallkalender": {
        "title": "WZV Kreis Segeberg",
        "url": "https://www.wzv.de/",
    },
    "maintauberkreis-abfallkalender": {
        "title": "Landratsamt Main-Tauber-Kreis",
        "url": "https://www.main-tauber-kreis.de/",
    },
    "dietzenbach": {
        "title": "Kreisstadt Dietzenbach",
        "url": "https://www.dietzenbach.de/",
    },
    "rheingauleerungen": {
        "title": "Abfallwirtschaft Rheingau-Taunus-Kreis",
        "url": "https://www.eaw-rheingau-taunus.de/",
    },
    "grossgeraulandkreis-abfallkalender": {
        "title": "Abfallwirtschaftsverband Kreis Groß-Gerau",
        "url": "https://www.awv-gg.de/",
    },
    "bayreuthstadt-abfallkalender": {
        "title": "Stadt Bayreuth",
        "url": "https://www.bayreuth.de/",
    },
    "arnsberg-abfallkalender": {
        "title": "Stadt Arnsberg",
        "url": "https://www.arnsberg.de/",
    },
    "landau": {
        "title": "Entsorgungs- und Wirtschaftsbetrieb Landau in der Pfalz",
        "url": "https://www.ew-landau.de/",
        "subdomain": "apps",
        "full_service_name": "web.landau",
        "ical_url_file": "downloadcal",
    },
    "roth": {
        "title": "Landkreis Roth",
        "url": "https://www.landratsamt-roth.de/",
        "subdomain": "apps",
        "full_service_name": "web.roth",
    },
    "aurich-abfallkalender": {
        "title": "Abfallwirtschaftsbetrieb Landkreis Aurich",
        "url": "https://mkw-grossefehn.de/",
        "subdomain": "apps",
        "full_service_name": "web.aurich-abfallkalender",
    },
    "stwendel": {
        "title": "Kreisstadt St. Wendel",
        "url": "https://www.sankt-wendel.de/",
        "subdomain": "apps",
        "full_service_name": "web.stwendel",
        "ical_url_file": "downloadcal",
    },
    "oberursel": {
        "title": "Bau & Service Oberursel",
        "url": "https://www.bso-oberursel.de/",
        "subdomain": "apps",
        "full_service_name": "web.oberursel",
    },
}


def _resolve_service(ort: str, service: "str | None") -> tuple[str, str, str]:
    """Resolve the (service, subdomain, ical_url_file) triple for a request.

    Mirrors the legacy Source.__init__ resolution exactly, including the
    Bremen compatibility default (the first supported district, historically
    the only one that didn't require an explicit ``service``).
    """
    if service is None:
        if ort == "Bremen":
            service = "bremenabfallkalender"
        else:
            raise SourceArgumentRequired(
                "service", "service is required if ort is not Bremen"
            )

    subdomain = DEFAULT_SUBDOMAIN
    ical_url_file = DEFAULT_ICAL_URL_FILE
    entry = SERVICE_MAP.get(service)
    if entry is not None:
        subdomain = entry.get("subdomain", subdomain)
        ical_url_file = entry.get("ical_url_file", ical_url_file)
        service = entry.get("full_service_name", service)
    return service, subdomain, ical_url_file


@final
class Source(BaseSource):
    TITLE = "C-Trace"
    DESCRIPTION = "Source for C-Trace.de."
    URL = "https://c-trace.de/"
    COUNTRY = "de"

    WASTE_TYPES: ClassVar[list] = [
        GENERAL_WASTE,
        GLASS,
        ORGANIC,
        PAPER,
        RECYCLABLES,
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
        service, subdomain, ical_url_file = _resolve_service(ort, service)
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

    def retrieve(self, source):
        p = self.params
        base_url = BASE_URL.format(subdomain=p["subdomain"])

        r = self.session.get(
            f"{base_url}/{p['service']}/Abfallkalender", allow_redirects=False
        )

        session_id = ""
        location = r.headers.get("location")
        if location:
            # session_id like "(S(r3bme50igdgsp2lstgxxhvs2))"
            parts = location.split("/")
            if len(parts) > 2:
                session_id = parts[2]

        args = {
            "Ort": p["ort"],
            "Gemeinde": p["gemeinde"],
            "Strasse": p["strasse"],
            "Hausnr": p["hausnummer"],
            "Abfall": p["abfall"],
        }
        if p["ortsteil"]:
            args["Ortsteil"] = p["ortsteil"]

        r = self.session.get(
            f"{base_url}/{p['service']}/{session_id}/abfallkalender/{p['ical_url_file']}",
            params=args,
        )
        r.raise_for_status()
        r.encoding = "utf-8-sig"
        return r
