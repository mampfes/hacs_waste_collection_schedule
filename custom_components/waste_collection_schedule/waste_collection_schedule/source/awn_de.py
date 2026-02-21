from html.parser import HTMLParser

import requests
import urllib3
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

# With verify=True the POST fails due to a SSLCertVerificationError.
# Using verify=False works, but is not ideal. The following links may provide a better way of dealing with this:
# https://urllib3.readthedocs.io/en/1.26.x/advanced-usage.html#ssl-warnings
# https://urllib3.readthedocs.io/en/1.26.x/user-guide.html#ssl
# This line suppresses the InsecureRequestWarning when using verify=False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


TITLE = "Abfallwirtschaft Neckar-Odenwald-Kreis"
DESCRIPTION = "Source for AWN (Abfallwirtschaft Neckar-Odenwald-Kreis)."
URL = "https://www.awn-online.de"
TEST_CASES = {
    "Adelsheim": {
        "city": "Adelsheim",
        "street": "Badstr.",
        "house_number": 1,
    },
    "Mosbach": {
        "city": "Mosbach",
        "street": "Hauptstr.",
        "house_number": 53,
        "address_suffix": "/1",
    },
    "Billigheim": {
        "city": "Billigheim",
        "street": "Marienhöhe",
        "house_number": 5,
        "address_suffix": "A",
    },
}
SERVLET = (
    "https://athos.awn-online.de/WasteManagementNeckarOdenwald/WasteManagementServlet"
)

PARAM_TRANSLATIONS = {
    "de": {
        "city": "Ort",
        "street": "Straße",
        "house_number": "Hausnummer",
        "address_suffix": "Hausnummerzusatz",
    }
}


# Parser for HTML input (hidden) text
class HiddenInputParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self._args = {}

    @property
    def args(self):
        return self._args

    def handle_starttag(self, tag, attrs):
        if tag == "input":
            d = dict(attrs)
            if str(d["type"]).lower() == "hidden":
                self._args[d["name"]] = d["value"] if "value" in d else ""


class Source:
    def __init__(
        self,
        city: str,
        street: str,
        house_number: int,
        address_suffix: str = "",
        restmuell: bool = True,
        bioenergietonne: bool = True,
        altpapier_papiertonne: bool = True,
        altpapier_buendelsammlung: bool = True,
        verpackungstonne: bool = True,
        altkleider_schuhe: bool = True,
        schadstoffe: bool = True,
    ):
        self._city = city
        self._street = street
        self._hnr = house_number
        self._suffix = address_suffix
        self._ics = ICS()
        self._container_selection = {
            1: restmuell,
            2: bioenergietonne,
            3: altpapier_papiertonne,
            4: altpapier_buendelsammlung,
            5: verpackungstonne,
            6: altkleider_schuhe,
            7: schadstoffe,
        }

    def fetch(self):
        session = requests.session()

        r = session.get(
            SERVLET,
            params={"SubmitAction": "wasteDisposalServices", "InFrameMode": "TRUE"},
            verify=False,
        )
        r.raise_for_status()
        r.encoding = "utf-8"

        parser = HiddenInputParser()
        parser.feed(r.text)

        args = parser.args
        args["Ort"] = self._city
        args["Strasse"] = self._street
        args["Hausnummer"] = str(self._hnr)
        args["Hausnummerzusatz"] = self._suffix
        args["SubmitAction"] = "CITYCHANGED"
        r = session.post(
            SERVLET,
            data=args,
            verify=False,
        )
        r.raise_for_status()

        args["SubmitAction"] = "forward"

        for idx, selected in self._container_selection.items():
            if selected:
                args[f"ContainerGewaehlt_{idx}"] = "on"

        r = session.post(
            SERVLET,
            data=args,
            verify=False,
        )
        r.raise_for_status()

        args["ApplicationName"] = "com.athos.kd.neckarodenwald.abfuhrtermine.AbfuhrTerminModel"
        args["SubmitAction"] = "filedownload_ICAL"
        r = session.post(
            SERVLET,
            data=args,
            verify=False,
        )
        r.raise_for_status()

        dates = self._ics.convert(r.text)

        entries = []
        for d in dates:
            entries.append(Collection(d[0], d[1]))

        return entries
