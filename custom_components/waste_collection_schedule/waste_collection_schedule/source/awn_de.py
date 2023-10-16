from html.parser import HTMLParser

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

# With verify=True the POST fails due to a SSLCertVerificationError.
# Using verify=False works, but is not ideal. The following links may provide a better way of dealing with this:
# https://urllib3.readthedocs.io/en/1.26.x/advanced-usage.html#ssl-warnings
# https://urllib3.readthedocs.io/en/1.26.x/user-guide.html#ssl
# These two lines areused to suppress the InsecureRequestWarning when using verify=False
import urllib3
urllib3.disable_warnings()


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
        self, city: str, street: str, house_number: int, address_suffix: str = ""
    ):
        self._city = city
        self._street = street
        self._hnr = house_number
        self._suffix = address_suffix
        self._ics = ICS()

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
        )
        r.raise_for_status()

        args["SubmitAction"] = "forward"
        args["ContainerGewaehlt_1"] = "on"
        args["ContainerGewaehlt_2"] = "on"
        args["ContainerGewaehlt_3"] = "on"
        args["ContainerGewaehlt_4"] = "on"
        args["ContainerGewaehlt_5"] = "on"
        args["ContainerGewaehlt_6"] = "on"
        args["ContainerGewaehlt_7"] = "on"
        args["ContainerGewaehlt_8"] = "on"
        args["ContainerGewaehlt_9"] = "on"
        args["ContainerGewaehlt_10"] = "on"
        r = session.post(
            SERVLET,
            data=args,
        )
        r.raise_for_status()

        args["ApplicationName"] = "com.athos.nl.mvc.abfterm.AbfuhrTerminModel"
        args["SubmitAction"] = "filedownload_ICAL"
        r = session.post(
            SERVLET,
            data=args,
        )
        r.raise_for_status()

        dates = self._ics.convert(r.text)

        entries = []
        for d in dates:
            entries.append(Collection(d[0], d[1]))

        return entries
