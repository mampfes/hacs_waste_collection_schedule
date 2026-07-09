# Modelled on awg_de.py — mirrors the Athos WasteManagementServlet multipart-form flow.
# ZAW-SR uses SELECT dropdowns for Ort/Strasse/Hausnummer and requires an extra
# STREETCHANGED step between CITYCHANGED and forward, so the standard parse_response_input
# helper is extended to also capture SELECT field values.

import html
import logging
import random
import re
import string

import requests
import urllib3
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.service.ICS import ICS

# With verify=True the POST fails due to a SSLCertVerificationError.
# Using verify=False works, but is not ideal.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_LOGGER = logging.getLogger(__name__)

TITLE = "ZAW-SR Straubing"
DESCRIPTION = (
    "Source for ZAW-SR (Zweckverband Abfallwirtschaft Straubing Stadt und Land)."
)
URL = "https://www.zaw-sr.de"
COUNTRY = "de"

TEST_CASES = {
    "Straubing Theresienplatz 1": {
        "city": "Straubing",
        "street": "Theresienplatz",
        "hnr": "1",
    },
    "Straubing Stadtgraben 1": {
        "city": "Straubing",
        "street": "Stadtgraben",
        "hnr": "1",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "city": "City",
        "street": "Street",
        "hnr": "House number",
        "addition": "House number suffix",
    },
    "de": {
        "city": "Ort",
        "street": "Strasse",
        "hnr": "Hausnummer",
        "addition": "Hausnummerzusatz",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "city": "Name of your city or town exactly as shown in the dropdown at https://www.zaw-sr.de/abfuhrkalender (e.g. 'Straubing').",
        "street": "Your street name exactly as shown in the dropdown (e.g. 'Theresienplatz').",
        "hnr": "Your house number.",
        "addition": "Optional house number suffix (e.g. 'A').",
    },
    "de": {
        "city": "Name Ihrer Stadt oder Gemeinde genau wie in der Auswahl auf https://www.zaw-sr.de/abfuhrkalender (z.B. 'Straubing').",
        "street": "Ihr Straßenname genau wie in der Auswahl (z.B. 'Theresienplatz').",
        "hnr": "Ihre Hausnummer.",
        "addition": "Optionaler Hausnummernzusatz (z.B. 'A').",
    },
}

ICON_MAP = {
    "Biotonne": Icons.BIO_KITCHEN,
    "Bioabfall": Icons.BIO_KITCHEN,
    "Papiertonne": Icons.PAPER,
    "Papier": Icons.PAPER,
    "Restmülltonne": Icons.GENERAL_WASTE,
    "Restmüll": Icons.GENERAL_WASTE,
    "Restmuelltonne": Icons.GENERAL_WASTE,
    "Gelber Sack": Icons.RECYCLING,
    "Gelbe Tonne": Icons.RECYCLING,
    "Wertstofftonne": Icons.RECYCLING,
}

API_URL = "https://straubing.zaw-sr.de/WasteManagementStraubing/WasteManagementServlet"


class Source:
    def __init__(self, city: str, street: str, hnr: str, addition: str = ""):
        self._city = city
        self._street = street
        self._house_number = str(hnr)
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
    def _parse_response_fields(text):
        """Parse all INPUT and SELECT fields from the response HTML."""
        parsed = re.findall(
            '<INPUT\\sNAME="([^"]+?)"\\sID="[^"]+?"(?:\\sVALUE="([^"]*?)")?', text
        )
        result = dict(parsed)
        for sel_block in re.finditer(
            r'<SELECT\sNAME="([^"]+?)".*?</SELECT>', text, re.DOTALL
        ):
            name = re.search(r'NAME="([^"]+?)"', sel_block.group(0)).group(1)
            selected = re.search(
                r'<OPTION VALUE="([^"]+?)"[^>]*SELECTED', sel_block.group(0)
            )
            result[name] = selected.group(1) if selected else ""
        return result

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
        payload = self._parse_response_fields(last_request)
        payload.update({"SubmitAction": action, **kwargs})
        if period:
            payload.update({"Zeitraum": html.unescape(period)})
        return self._parse_data(payload, self._boundary)

    def _get_dates(self, session, init_request, calendar=""):
        # Step 1: CITYCHANGED — select the city and get the street list
        payload = self._payload(
            init_request,
            action="CITYCHANGED",
            period=calendar,
            Ort=self._city,
            Strasse="",
            Hausnummer="",
        )
        city_response = session.post(
            API_URL, headers=self._headers(), data=payload, verify=False
        )

        # Step 2: STREETCHANGED — select the street and get the house-number list
        payload = self._payload(
            city_response.text,
            action="STREETCHANGED",
            period=calendar,
            Ort=self._city,
            Strasse=self._street,
            Hausnummer="",
        )
        street_response = session.post(
            API_URL, headers=self._headers(), data=payload, verify=False
        )

        # Step 3: forward — submit the full address
        payload = self._payload(
            street_response.text,
            action="forward",
            period=calendar,
            **self._address(),
        )
        final_response = session.post(
            API_URL, headers=self._headers(), data=payload, verify=False
        )

        # Step 4: download ICS
        payload = self._payload(
            final_response.text,
            action="filedownload_ICAL",
            period=calendar,
            **self._address(),
        )
        ics_response = session.post(
            API_URL, headers=self._headers(), data=payload, verify=False
        )
        return self._ics.convert(ics_response.text)

    def fetch(self) -> list[Collection]:
        session = requests.session()

        init_request = session.get(
            f"{API_URL}?SubmitAction=wasteDisposalServices&InFrameMode=true",
            verify=False,
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
