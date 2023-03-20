import html
import logging
import random
import re
import string
from datetime import datetime

import requests
from waste_collection_schedule import Collection

_LOGGER = logging.getLogger(__name__)

TITLE = "Abfallwirtschaftsbetrieb Landkreis Ahrweiler"
URL = "https://www.meinawb.de"
DESCRIPTION = "Bin collection service from Kreis Ahrweiler/Germany"
API_URL = (
    "https://extdienste01.koblenz.de/WasteManagementAhrweiler/WasteManagementServlet"
)

ICON_MAP = {
    "Restabfall": "mdi:trash-can",
    "Restabfall Plus": "mdi:trash-can",
    "Bioabfall": "mdi:leaf",
    "Altpapier": "mdi:package-variant",
    "Verpackungen": "mdi:recycle",
    "Grünabfall / Weihnachtsbäume": "mdi:forest",
}
TYPES = {
    "RM": "Restabfall",
    "RG": "Restabfall Plus",
    "BM": "Bioabfall",
    "PA": "Altpapier",
    "GT": "Verpackungen",
    "GS": "Grünabfall / Weihnachtsbäume",
}

TEST_CASES = {
    "Oberzissen": {
        "city": "Oberzissen",
        "street": "Lindenstrasse",
        "house_number": "1",
    },
    "Niederzissen": {
        "city": "Niederzissen",
        "street": "Brohltalstrasse",
        "house_number": "189",
    },
    "Bad Neuenahr": {
        "city": "Bad Neuenahr-Ahrweiler",
        "street": "Hauptstrasse",
        "house_number": "91",
        "address_suffix": "A",
    },
}


class Source:
    def __init__(self, city, street, house_number, address_suffix=""):
        self._city = city
        self._street = street
        self._house_number = house_number
        self._address_suffix = address_suffix
        self._boundary = "WebKitFormBoundary" + "".join(
            random.sample(string.ascii_letters + string.digits, 16)
        )

    def __str__(self):
        return (
            f"{self._city} {self._street} {self._house_number} {self._address_suffix}"
        )

    @staticmethod
    def _parse_data(data, boundary):
        result = ""
        for key, value in data.items():
            result += f'------{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n'
        result += f"------{boundary}--\r\n"
        return result.encode()

    @staticmethod
    def _parse_response_input(text):
        parsed = re.findall(
            '<INPUT\\sNAME="([^"]+?)"\\sID="[^"]+?"(?:\\sVALUE="([^"]*?)")?', text
        )
        return {k: v for k, v in parsed}

    def _address(self):
        return {
            "Ort": self._city,
            "Strasse": self._street,
            "Hausnummer": self._house_number,
            "Hausnummerzusatz": self._address_suffix,
        }

    def _headers(self):
        return {"Content-Type": f"multipart/form-data; boundary=----{self._boundary}"}

    def _payload(self, last_request, action="", period="", **kwargs):
        payload = self._parse_response_input(last_request)
        payload.update({"SubmitAction": action, **kwargs})
        if period:
            payload.update({"Zeitraum": html.unescape(period)})
        return self._parse_data(payload, self._boundary)

    def _get_dates(self, session, init_request, calendar=""):
        kwargs = {"Ort": self._city, "Strasse": ""}
        payload = self._payload(
            init_request, action="CITYCHANGED", period=calendar, **kwargs
        )
        city_response = session.post(API_URL, headers=self._headers(), data=payload)
        payload = self._payload(
            city_response.text, action="forward", period=calendar, **self._address()
        )
        final_response = session.post(API_URL, headers=self._headers(), data=payload)
        if error := re.findall(
            'informationItemsText_1">([^<]+?)<', final_response.text
        ):
            _LOGGER.warning(f"{self} - {html.unescape(error[0])}")
            return []
        return re.findall(
            '<P ID="TermineDatum([0-9A-Z]+)_\\d+">[A-Z][a-z]. ([0-9.]{10}) ?\\** </P>',
            final_response.text,
        )

    def fetch(self):
        session = requests.Session()
        init_request = session.get(
            f"{API_URL}?SubmitAction=wasteDisposalServices&InFrameMode=true"
        ).text
        if calendars := re.findall('NAME="Zeitraum" VALUE="([^"]+?)"', init_request):
            dates = [
                date
                for calendar in calendars
                for date in self._get_dates(session, init_request, calendar)
            ]
        else:
            dates = self._get_dates(session, init_request)
        entries = []
        for bin_type, date in dates:
            name = TYPES[next(x for x in list(TYPES) if x in bin_type)]
            entries.append(
                Collection(
                    datetime.strptime(date, "%d.%m.%Y").date(), name, ICON_MAP.get(name)
                )
            )
        return entries
