import html
import random
import re
import string
from datetime import datetime

import requests
from waste_collection_schedule import Collection

TITLE = "meinawb.de"
DESCRIPTION = "Bin collection service from Kreis Ahrweiler/Germany"
URL = "https://extdienste01.koblenz.de/WasteManagementAhrweiler/WasteManagementServlet"

city = "Bad Neuenahr-Ahrweiler"
street = "Hauptstrasse"
houseno = "91"
YEAR = "2023"

ICONS = {
    "RM": {"icon": "mdi:trash-can", "t": "Restabfall"},
    "RG2": {"icon": "mdi:trash-can", "t": "Restabfall Gewerbe / PLUS-Tonne"},
    "BM": {"icon": "mdi:leaf", "t": "Bioabfall"},
    "PA": {"icon": "mdi:package-variant", "t": "Altpapier"},
    "GT": {"icon": "mdi:recycle", "t": "Verpackungen"},
    "GS": {"icon": "mdi:forest", "t": "Grünabfall / Weihnachtsbäume"},
}


class Source:
    def __init__(self, city, street, house_number):
        self._city = city
        self._street = street
        self._house_number = house_number

    @staticmethod
    def parse_data(data, boundary):
        result = ""
        for key, value in data.items():
            result += f'------WebKitFormBoundary{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n'
        result += f"------WebKitFormBoundary{boundary}--\r\n"
        return result.encode()

    @staticmethod
    def parse_response_input(text):
        parsed = re.findall("<INPUT\\sNAME=\"([^\"]+?)\"\\sID=\"[^\"]+?\"(?:\\sVALUE=\"([^\"]*?)\")?", text)
        return {k: v for k, v in parsed}

    def fetch(self):
        session = requests.Session()
        response = session.get(f"{URL}?SubmitAction=wasteDisposalServices&InFrameMode=true", verify=False)
        calendars = re.findall('NAME="Zeitraum" VALUE=\"([^\"]+?)\"', response.text)
        year = next(html.unescape(t) for t in calendars if YEAR in html.unescape(t))
        boundary = "".join(random.sample(string.ascii_letters + string.digits, 16))
        headers = {'Content-Type': f'multipart/form-data; boundary=----WebKitFormBoundary{boundary}'}
        payload = self.parse_response_input(response.text)
        payload.update({"SubmitAction": "CITYCHANGED", "Ort": self._city, "Strasse": "", "Zeitraum": year})
        response = session.post(URL, headers=headers, data=self.parse_data(payload, boundary), verify=False)
        payload = self.parse_response_input(response.text)
        payload.update(
            {"SubmitAction": "forward", "Ort": self._city, "Strasse": self._street, "Hausnummer": self._house_number,
             "Zeitraum": year})
        response = session.post(URL, headers=headers, data=self.parse_data(payload, boundary), verify=False)
        dates = re.findall('<P ID="TermineDatum([0-9A-Z]+)_\\d+">[A-Z][a-z]. ([0-9.]{10}) </P>', response.text)
        return [Collection(datetime.strptime(date, "%d.%m.%Y").date(), **ICONS[bin_type]) for bin_type, date in dates]
