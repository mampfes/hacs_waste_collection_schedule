import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "C-Trace"
DESCRIPTION = "Source for C-Trace.de."
URL = "https://c-trace.de/"


def EXTRA_INFO():
    return [{"title": s["title"], "url": s["url"]} for s in SERVICE_MAP.values()]


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
}

DEFAULT_SUBDOMAIN = "web"
DEFAULT_ICAL_URL_FILE = "cal"

# Do not support Ical Download:
# lekarowarschau-abfallkalender
# web.torgauoschatz2015


SERVICE_MAP = {
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
    "overathabfallkalender": {
        "title": "Stadt Overath",
        "url": "https://www.overath.de/",
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
    #    "lekarowarschau-abfallkalender": {
    #        "title": "Lekaro Warszawa",
    #        "url": "https:lekaro.pl",
    #        "subdomain": "apps",
    #        "full_service_name": "web.lekarowarschau-abfallkalender",
    #    },
    "oberursel": {
        "title": "Bau & Service Oberursel",
        "url": "https://www.bso-oberursel.de/",
        "subdomain": "apps",
        "full_service_name": "web.oberursel",
    },
}

BASE_URL = "https://{subdomain}.c-trace.de"


class Source:
    def __init__(
        self, strasse, hausnummer, gemeinde="", ort="", ortsteil="", service=None
    ):
        # Compatibility handling for Bremen which was the first supported
        # district and didn't require to set a service name.
        if service is None:
            if ort == "Bremen":
                service = "bremenabfallkalender"
            else:
                raise Exception("service is missing")

        subdomain = DEFAULT_SUBDOMAIN
        ical_url_file = DEFAULT_ICAL_URL_FILE

        if service in SERVICE_MAP:
            if "subdomain" in SERVICE_MAP[service]:
                subdomain = SERVICE_MAP[service]["subdomain"]
            if "ical_url_file" in SERVICE_MAP[service]:
                ical_url_file = SERVICE_MAP[service]["ical_url_file"]
            if "full_service_name" in SERVICE_MAP[service]:
                service = SERVICE_MAP[service]["full_service_name"]

        self._service = service
        self._ort = ort
        if not gemeinde:
            gemeinde = ort
        self._gemeinde = gemeinde
        self._ortsteil = ortsteil
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
            "Gemeinde": self._gemeinde,
            "Strasse": self._strasse,
            "Hausnr": self._hausnummer,
            "Abfall": "|".join(str(i) for i in range(0, 99)),  # return all waste types
        }
        if self._ortsteil:
            args["Ortsteil"] = self._ortsteil
        r = session.get(
            f"{self._base_url}/{self._service}/{session_id}/abfallkalender/{self.ical_url_file}",
            params=args,
        )
        r.raise_for_status()

        # parse ics file
        r.encoding = "utf-8-sig"
        dates = self._ics.convert(r.text)

        entries = []
        for d in dates:
            entries.append(Collection(d[0], d[1]))
        return entries
