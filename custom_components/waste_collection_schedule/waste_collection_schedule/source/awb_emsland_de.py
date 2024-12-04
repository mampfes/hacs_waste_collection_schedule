# Nearly direct copy of source awn_de

from html.parser import HTMLParser

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "Abfallwirtschaftsbetrieb Emsland"
DESCRIPTION = "Source for AWB Emsland."
URL = "https://www.awb-emsland.de"
TEST_CASES = {
    "Andervenne Am Gallenberg": {
        "city": "Andervenne",
        "street": "Am Gallenberg",
        "house_number": "1",
    },
    "Neubörger Aschendorfer Straße 1 A": {
        "city": "Neubörger",
        "street": "Aschendorfer Straße",
        "house_number": 1,
        "address_suffix": "A",
    },
    "Lähden Ahornweg 15": {
        "city": "Lähden",
        "street": "Ahornweg",
        "house_number": 15,
    },
}
SERVLET = "https://portal.awb-emsland.de/WasteManagementEmsland/WasteManagementServlet"

ICON_MAP = {
    "Restabfallbehaelter": "mdi:trash-can",
    "Papierbehaelter": "mdi:package-variant",
    "Wertstoffbehaelter": "mdi:recycle",
    "Bioabfallbehaelter": "mdi:leaf",
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


PARAM_TRANSLATIONS = {
    "de": {
        "city": "Ort",
        "street": "Straße",
        "house_number": "Hausnummer",
        "address_suffix": "Hausnummerzusatz",
    }
}


class Source:
    def __init__(
        self, city: str, street: str, house_number: int, address_suffix: str = ""
    ):
        self._city = city
        self._street = street
        self._hnr = house_number
        self._suffix = address_suffix
        self._ics = ICS()


    def get_zeitraum_values(self):
        try:
            session = requests.session()

            response = session.get(
                SERVLET,
                params={"SubmitAction": "wasteDisposalServices"},
            )
            response.raise_for_status()

            # Parse the HTML content
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find all input elements with the name "Zeitraum"
            input_elements = soup.find_all('input', {'name': 'Zeitraum'})

            # Extract values
            values = [input_elem.get('value') for input_elem in input_elements if input_elem.get('value')]
            return values

        except requests.exceptions.RequestException as e:
            return []
    

    def fetch(self):
        available_years = self.get_zeitraum_values()

        if available_years:
            values = []

            for year in available_years:
                result = self.fetch_year(year)
                values.extend(result)

            return values
        
        else:
            return self.fetch_year()


    def fetch_year(self, year=None):    
        session = requests.session()

        r = session.get(
            SERVLET,
            params={"SubmitAction": "wasteDisposalServices", "InFrameMode": "TRUE"},
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

        if year:
            args["Zeitraum"] = year

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

        args["ApplicationName"] = "com.athos.kd.emsland.AbfuhrTerminModel"
        args["SubmitAction"] = "filedownload_ICAL"
        r = session.post(
            SERVLET,
            data=args,
        )
        r.raise_for_status()

        dates = self._ics.convert(r.text)

        entries = []
        for d in dates:
            bin_type = d[1].strip()
            entries.append(Collection(d[0], bin_type, icon=ICON_MAP.get(bin_type)))

        return entries

