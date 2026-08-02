"""C-Trace (c-trace.de), Germany: a multi-tenant ASP.NET calendar platform.

One ASP.NET application serving many independent operators (municipalities and
Landkreise), each a "service" under its own path on one of a few c-trace.de
subdomains. :data:`SERVICE_MAP` is the operator registry: adding a c-trace
operator is a row here plus, where the operator deviates, its ``subdomain`` /
``full_service_name`` / ``ical_url_file`` overrides.

Getting to an operator's ICS feed is a two-request handshake:

1. GET the calendar page *without following the redirect*. The application
   answers ``302`` with a cookieless ASP.NET session id spliced into the
   ``Location`` path (``/<service>/(S(r3bme50igdgsp2lstgxxhvs2))/Abfallkalender``).
2. GET the calendar file with that session id spliced back into the path and
   the address as query arguments.

:class:`CTraceCalendarRetriever` is that handshake, so a source on this
platform is metadata plus ``retrieve = CTraceCalendarRetriever()``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from waste_collection_schedule.exceptions import SourceArgumentRequired
from waste_collection_schedule.retrievers import Response, RetrieverFunc

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource

BASE_URL = "https://{subdomain}.c-trace.de"
CALENDAR_PATH = "Abfallkalender"
CALENDAR_FILE_PATH = "abfallkalender"

DEFAULT_SUBDOMAIN = "web"
DEFAULT_ICAL_URL_FILE = "cal"

# The operator whose calendar answers when no ``service`` is given. Historically
# the only supported one, so existing Bremen configurations omit it.
DEFAULT_SERVICE_ORT = "Bremen"
DEFAULT_SERVICE = "bremenabfallkalender"

# Feed encoding: c-trace serves its ICS with a UTF-8 BOM.
ICAL_ENCODING = "utf-8-sig"

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


def resolve_service(ort: str, service: str | None) -> tuple[str, str, str]:
    """Resolve the (service, subdomain, ical_url_file) triple for a request.

    ``service`` is the :data:`SERVICE_MAP` key the user configures; the value it
    resolves to is the operator's path on the server, which for the ``apps``
    subdomain is prefixed (``landau`` -> ``web.landau``). Includes the Bremen
    compatibility default: historically the only supported operator, so a
    configuration naming that ``ort`` and no ``service`` still works.
    """
    if service is None:
        if ort == DEFAULT_SERVICE_ORT:
            service = DEFAULT_SERVICE
        else:
            raise SourceArgumentRequired(
                "service", f"service is required if ort is not {DEFAULT_SERVICE_ORT}"
            )

    subdomain = DEFAULT_SUBDOMAIN
    ical_url_file = DEFAULT_ICAL_URL_FILE
    entry = SERVICE_MAP.get(service)
    if entry is not None:
        subdomain = entry.get("subdomain", subdomain)
        ical_url_file = entry.get("ical_url_file", ical_url_file)
        service = entry.get("full_service_name", service)
    return service, subdomain, ical_url_file


def session_id_from_location(location: str | None) -> str:
    """Read the cookieless ASP.NET session id out of a redirect ``Location``.

    ``/<service>/(S(r3bme50igdgsp2lstgxxhvs2))/Abfallkalender`` -> the
    ``(S(...))`` segment. Returns ``""`` when the application answered without
    a redirect, which yields a session-less calendar URL: the same request the
    legacy source made, and one the application still answers.
    """
    if not location:
        return ""
    parts = location.split("/")
    return parts[2] if len(parts) > 2 else ""


class CTraceCalendarRetriever(RetrieverFunc):
    """Fetch an operator's ICS feed through the c-trace session handshake.

    Reads the operator and address straight from ``source.params``, which the
    source fills from :func:`resolve_service` and its own configuration
    arguments: ``subdomain``, ``service`` and ``ical_url_file`` locate the
    operator, and ``ort`` / ``gemeinde`` / ``strasse`` / ``hausnummer`` /
    ``ortsteil`` / ``abfall`` are the calendar's own query arguments (the names
    are the platform's, not one council's).
    """

    def __call__(self, source: BaseSource) -> Response:
        p = source.params
        base_url = BASE_URL.format(subdomain=p["subdomain"])

        redirect = source.session.get(
            f"{base_url}/{p['service']}/{CALENDAR_PATH}", allow_redirects=False
        )
        session_id = session_id_from_location(redirect.headers.get("location"))

        args = {
            "Ort": p["ort"],
            "Gemeinde": p["gemeinde"],
            "Strasse": p["strasse"],
            "Hausnr": p["hausnummer"],
            "Abfall": p["abfall"],
        }
        if p["ortsteil"]:
            args["Ortsteil"] = p["ortsteil"]

        response = source.session.get(
            f"{base_url}/{p['service']}/{session_id}"
            f"/{CALENDAR_FILE_PATH}/{p['ical_url_file']}",
            params=args,
        )
        response.raise_for_status()
        response.encoding = ICAL_ENCODING
        return response
