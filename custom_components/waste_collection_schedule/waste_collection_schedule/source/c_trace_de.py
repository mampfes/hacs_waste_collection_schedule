import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "C-Trace"
DESCRIPTION = "Source for C-Trace.de."
URL = "https://c-trace.de/"
EXTRA_INFO = [
    {
        "title": "Bremener Stadreinigung",
        "url": "https://www.die-bremer-stadtreinigung.de/",
    },
    {
        "title": "AWB Landkreis Augsburg",
        "url": "https://www.awb-landkreis-augsburg.de/",
    },
    {
        "title": "WZV Kreis Segeberg",
        "url": "https://www.wzv.de/",
    },
]
TEST_CASES = {
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
        "service": "web.landau",
    },
    "WZV": {
        "ort": "Bark",
        "strasse": "Birkenweg",
        "hausnummer": 1,
        "service": "segebergwzv-abfallkalender",
    },
    "oberursel-ohne-web": {
        "service": "oberursel",
        "strasse": "Ahornweg",
        "hausnummer": "8a",
    },
    "roth.mit-web": {
        "ort": "Georgensgmünd",
        "strasse": "Mauk",
        "hausnummer": 2,
        "service": "web.roth",
    },
}

DEFAULT_SUBDOMAIN = "web"
DEFAULT_ICAL_URL_FILE = "cal"

# Do not support Ical Download:
# lekarowarschau-abfallkalender
# web.torgauoschatz2015


APPS_MAP = {
    "landau": {
        "subdomain": "apps",
        "full_service_name": "web.landau",
        "ical_url_file": "downloadcal",
    },
    "roth": {
        "subdomain": "apps",
        "full_service_name": "web.roth",
    },
    "aurich-abfallkalender": {
        "subdomain": "apps",
        "full_service_name": "web.aurich-abfallkalender",
    },
    "stwendel": {
        "subdomain": "apps",
        "full_service_name": "web.stwendel",
        "ical_url_file": "downloadcal",
    },
    "lekarowarschau-abfallkalender": {
        "subdomain": "apps",
        "full_service_name": "web.lekarowarschau-abfallkalender",
    },
    "oberursel": {
        "subdomain": "apps",
        "full_service_name": "web.oberursel",
    }
}

BASE_URL = "https://{subdomain}.c-trace.de"


class Source:
    def __init__(self, strasse, hausnummer, ort="", service=None):
        # Compatibility handling for Bremen which was the first supported
        # district and didn't require to set a service name.
        if service is None:
            if ort == "Bremen":
                service = "bremenabfallkalender"
            else:
                raise Exception("service is missing")

        subdomain = DEFAULT_SUBDOMAIN
        ical_url_file = DEFAULT_ICAL_URL_FILE

        if (service.split(".")[-1] in APPS_MAP):
            service = service.split(".")[-1]
        if (service in APPS_MAP):
            if ("subdomain" in APPS_MAP[service]):
                subdomain = APPS_MAP[service]["subdomain"]
            if ("ical_url_file" in APPS_MAP[service]):
                ical_url_file = APPS_MAP[service]["ical_url_file"]

            if ("full_service_name" in APPS_MAP[service]):
                service = APPS_MAP[service]["full_service_name"]


        self._service = service
        self._ort = ort
        self._strasse = strasse
        self._hausnummer = hausnummer
        self._base_url = BASE_URL.format(subdomain=subdomain)
        self.ical_url_file = ical_url_file
        self._ics = ICS(regex=r"Abfuhr: (.*)")

    def fetch(self):
        session = requests.session()

        # get session url
        r = session.get(
            f"{self._base_url}/{self._service}/Abfallkalender",
            allow_redirects=False,
        )

        session_id = ""
        if "location" in r.headers:
            session_id = r.headers["location"].split("/")[
                2
            ]  # session_id like "(S(r3bme50igdgsp2lstgxxhvs2))"

        args = {
            "Ort": self._ort,
            "Gemeinde": self._ort,
            "Strasse": self._strasse,
            "Hausnr": self._hausnummer,
            # return all waste types
            "Abfall": "|".join(str(i) for i in range(0, 99)),
        }
        r = session.get(
            f"{self._base_url}/{self._service}/{session_id}/abfallkalender/{self.ical_url_file}", params=args
        )
        r.raise_for_status()

        # parse ics file
        r.encoding = "utf-8-sig"
        dates = self._ics.convert(r.text)

        entries = []
        for d in dates:
            entries.append(Collection(d[0], d[1]))
        return entries
