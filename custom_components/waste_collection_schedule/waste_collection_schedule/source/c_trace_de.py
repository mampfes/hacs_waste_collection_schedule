import datetime
import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS


TITLE = "C-Trace.de"
DESCRIPTION = "Source for C-Trace.de."
URL = "https://c-trace.de/"
TEST_CASES = {"Bremen": {"ort": "Bremen", "strasse": "Abbentorstraße", "hausnummer": 5},
                "AugsburgLand": {"ort": "Königsbrunn", "strasse": "Marktplatz", "hausnummer": 7,"abfall":"2|3", "jahr": datetime.datetime.now().year, "service":"augsburglandkreis"}}


BASE_URL = "https://web.c-trace.de"
SERVICE_MAP = {"Bremen": "bremenabfallkalender"}



class Source:
    def __init__(self, ort, strasse, hausnummer,abfall,gemeinde = None, service = None)  :
        self._ort = gemeinde if ort is None else ort # keep in sync in case only one value is set
        self._gemeinde = ort if gemeinde is None else gemeinde  # keep in sync in case only one value is set
        self._strasse = strasse 
        self._hausnummer = hausnummer
        self._service =  SERVICE_MAP.get(self._ort) if service is None else service  # set value from Service_Map if service is not set. 
        self._abfall= abfall
        self._ics = ICS(regex=r"Abfuhr: (.*)")


    def fetch(self):
        service = self._service 
        if service is None:
            raise Exception(f"no service for {self._ort}")

        session = requests.session()

        # get session url
        r = session.get(f"{BASE_URL}/{service}/Abfallkalender", allow_redirects=False,)
        session_id = r.headers["location"].split("/")[
            2
        ]  # session_id like "(S(r3bme50igdgsp2lstgxxhvs2))"

        args = {
            "Gemeinde": self._gemeinde,
            "Ort": self._ort,
            "Strasse": self._strasse,
            "Hausnr": self._hausnummer,
            "Abfall":self._abfall,
        }
        r = session.get(
            f"{BASE_URL}/{service}/{session_id}/abfallkalender/cal", params=args
        )
        r.raise_for_status()

        # parse ics file
        r.encoding = "utf-8"
        dates = self._ics.convert(r.text)

        entries = []
        for d in dates:
            entries.append(Collection(d[0], d[1]))
        return entries
