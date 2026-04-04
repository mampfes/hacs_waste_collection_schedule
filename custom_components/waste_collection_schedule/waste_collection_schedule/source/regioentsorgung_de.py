from datetime import datetime
from html.parser import HTMLParser

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.service.ICS import ICS

TITLE = "RegioEntsorgung Städteregion Aachen"
DESCRIPTION = "RegioEntsorgung Städteregion Aachen"
URL = "https://regioentsorgung.de"
TEST_CASES = {
    "Merzbrück": {"city": "Würselen", "street": "Merzbrück", "house_number": 200},
}

API_URL = "https://tonnen.regioentsorgung.de/WasteManagementRegioentsorgung/WasteManagementServlet"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64)",
}


PARAM_TRANSLATIONS = {
    "de": {
        "city": "Ort",
        "street": "Straße",
        "house_number": "Hausnummer",
    },
}


class FormStateParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.select_options = {}
        self._current_select = None
        self._current_option_value = None
        self._current_option_text = []

    def _finalize_option(self):
        if self._current_select is None or self._current_option_value is None:
            return

        text = " ".join(part.strip() for part in self._current_option_text).strip()
        self.select_options[self._current_select].append(
            (self._current_option_value or "", text)
        )
        self._current_option_value = None
        self._current_option_text = []

    def finalize(self):
        self._finalize_option()

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "select" and "name" in attributes:
            self._finalize_option()
            self._current_select = attributes["name"]
            self.select_options.setdefault(self._current_select, [])
        elif tag == "option" and self._current_select is not None:
            self._finalize_option()
            self._current_option_value = attributes.get("value", "")
            self._current_option_text = []

    def handle_data(self, data):
        if self._current_option_value is not None:
            self._current_option_text.append(data)

    def handle_endtag(self, tag):
        if tag == "option":
            self._finalize_option()
        elif tag == "select":
            self._finalize_option()
            self._current_select = None

    def get_options(self, field_name):
        return [
            text or value
            for value, text in self.select_options.get(field_name, [])
            if (text or value)
        ]


def parse_form_state(content):
    parser = FormStateParser()
    parser.feed(content)
    parser.finalize()
    parser.close()
    return parser


def validate_option(field_name, value, options):
    if value in options:
        return
    if options:
        raise SourceArgumentNotFoundWithSuggestions(field_name, value, options)
    raise SourceArgumentNotFound(
        field_name,
        value,
        "please check the other address arguments and try again.",
    )


class Source:
    def __init__(self, city, street, house_number):
        self.city = city
        self.street = street
        self.house_number = house_number
        self._ics = ICS()

    def fetch(self):
        now = datetime.now()
        year = now.year
        entries = self.get_collection(year)
        if now.month == 12:
            entries += self.get_collection(year + 1)
        return entries

    def get_collection(self, year):
        # Use a session to keep cookies
        session = requests.Session()

        payload = {
            "SubmitAction": "wasteDisposalServices",
        }
        r = session.get(API_URL, headers=HEADERS, params=payload)
        r.raise_for_status()
        r.encoding = "utf-8"

        form_state = parse_form_state(r.text)
        validate_option("city", self.city, form_state.get_options("Ort"))

        payload = {
            "ApplicationName": "com.athos.kd.regioentsorgung.CheckAbfuhrtermineModel",
            "SubmitAction": "CITYCHANGED",
            "Ort": self.city,
            "Strasse": "",
            "Hausnummer": "",
        }
        r = session.post(API_URL, headers=HEADERS, data=payload)
        r.raise_for_status()
        r.encoding = "utf-8"

        form_state = parse_form_state(r.text)
        validate_option("street", self.street, form_state.get_options("Strasse"))

        payload = {
            "ApplicationName": "com.athos.kd.regioentsorgung.CheckAbfuhrtermineModel",
            "SubmitAction": "STREETCHANGED",
            "Ort": self.city,
            "Strasse": self.street,
            "Hausnummer": "",
        }
        r = session.post(API_URL, headers=HEADERS, data=payload)
        r.raise_for_status()
        r.encoding = "utf-8"

        form_state = parse_form_state(r.text)
        validate_option(
            "house_number", str(self.house_number), form_state.get_options("Hausnummer")
        )

        payload = {
            "ApplicationName": "com.athos.kd.regioentsorgung.CheckAbfuhrtermineModel",
            "SubmitAction": "forward",
            "Ort": self.city,
            "Strasse": self.street,
            "Hausnummer": self.house_number,
            "Zeitraum": f"Jahresübersicht {year}",
        }
        r = session.post(API_URL, headers=HEADERS, data=payload)
        r.raise_for_status()

        payload = {
            "ApplicationName": "com.athos.kd.regioentsorgung.AbfuhrTerminModel",
            "SubmitAction": "forward",
        }
        r = session.post(API_URL, headers=HEADERS, data=payload)
        r.raise_for_status()

        payload = {
            "ApplicationName": "com.athos.kd.regioentsorgung.AbfuhrTerminDownloadModel",
            "ContainerGewaehlt_1": "on",
            "ContainerGewaehlt_2": "on",
            "ContainerGewaehlt_3": "on",
            "ContainerGewaehlt_4": "on",
            "ContainerGewaehlt_5": "on",
            "ContainerGewaehlt_6": "on",
            "ContainerGewaehlt_7": "on",
            "ContainerGewaehlt_8": "on",
            "ContainerGewaehlt_9": "on",
            "ICalErinnerung": "keine Erinnerung",
            "ICalZeit": "06:00 Uhr",
            "SubmitAction": "filedownload_ICAL",
        }
        r = session.post(API_URL, headers=HEADERS, data=payload)
        r.raise_for_status()

        # Parse ics file
        dates = self._ics.convert(r.text)

        entries = []
        for d in dates:
            entries.append(Collection(d[0], d[1]))
        return entries
