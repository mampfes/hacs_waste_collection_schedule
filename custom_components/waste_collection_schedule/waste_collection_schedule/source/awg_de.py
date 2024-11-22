# This is a nearly 1:1 copy of the original file waste_collection_schedule/waste_collection_schedule/source/meinawb_de.py

import html
import logging
import random
import re
import string

from waste_collection_schedule import Collection
from waste_collection_schedule.service.ICS import ICS
from waste_collection_schedule.service.SSLError import get_legacy_session

_LOGGER = logging.getLogger(__name__)


TITLE = "ZAW Donau-Wald"
DESCRIPTION = "Source for ZAW Donau-Wald."
URL = "https://www.awg.de/"
TEST_CASES = {
    "Achslach Aign 1 ": {"city": "Achslach", "street": "Aign", "hnr": "1"},
    "Böbrach Bärnerauweg 10A": {
        "city": "Böbrach",
        "street": "Bärnerauweg",
        "hnr": 10,
        "addition": "A",
    },
    "Am Bäckergütl 1, 94094 Malching": {
        "city": "Malching",
        "street": "Am Bäckergütl",
        "hnr": 1,
        "addition": "",
    },
}


ICON_MAP = {
    "Biotonne": "mdi:leaf",
    "Papiertonne": "mdi:package-variant",
    "Restmuelltonne": "mdi:trash-can",
    "Restmüllcontainer": "mdi:trash-can",
    "Papiercontainer": "mdi:package-variant",
}


API_URL = (
    "https://wastemanagement.awg.de/WasteManagementDonauwald/WasteManagementServlet"
)


class Source:
    def __init__(self, city, street, hnr, addition=""):
        self._city = city
        self._street = street
        self._house_number = hnr
        self._address_suffix = addition
        self._boundary = "WebKitFormBoundary" + "".join(
            random.sample(string.ascii_letters + string.digits, 16)
        )
        self._ics = ICS()

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

        payload = self._payload(
            final_response.text,
            action="filedownload_ICAL",
            period=calendar,
            **self._address(),
        )

        ics_response = session.post(API_URL, headers=self._headers(), data=payload)
        return self._ics.convert(ics_response.text)

    def fetch(self):
        session = get_legacy_session()

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
        for date, bin_type in dates:
            entries.append(
                Collection(date, bin_type.strip(), ICON_MAP.get(bin_type.strip()))
            )
        return entries
