import datetime
import json
from html.parser import HTMLParser

import requests
from waste_collection_schedule import Collection, Icons

TITLE = "Ipswich City Council"
DESCRIPTION = "Source for Ipswich City Council rubbish collection."
URL = "https://www.ipswich.qld.gov.au"
TEST_CASES = {
    "Camira State School": {"street": "184-202 Old Logan Rd", "suburb": "Camira"},
    "Random": {"street": "50 Brisbane Road", "suburb": "Redbank"},
}


ICON_MAP = {
    "Waste Bin": Icons.GENERAL_WASTE,
    "Recycle Bin": Icons.RECYCLING,
    "FOGO Bin": Icons.BIO_KITCHEN,
    "GO Bin": Icons.BIO_KITCHEN,
}


def toDate(dateStr: str):
    items = dateStr.split("-")
    return datetime.date(int(items[1]), int(items[2]), int(items[3]))


class IpswichGovAuParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self._entries = []
        self._state = None
        self._level = 0
        self._class = ""
        self._li_level = 0
        self._li_valid = False
        self._span_level = 0
        self._load_date = False
        self._load_bin = False
        self._loaded_date = None

    @property
    def entries(self):
        return self._entries

    def handle_endtag(self, tag):

        if tag == "li":
            self._li_level -= 1
            self._loaded_date = None

        if tag == "span":
            self._span_level -= 1

    def handle_starttag(self, tag, attrs):

        d = dict(attrs)
        cls = d.get("class", "")

        if tag == "li":
            self._li_level += 1
            if self._li_level == 1 and cls == "WBD-result-item":
                self._li_valid = True
            else:
                self._li_valid = False
                self._loaded_date = None

        if tag == "span":
            self._span_level += 1
            if self._li_valid and self._span_level == 1 and cls == "WBD-event-date":
                self._load_date = True

            if self._li_valid and self._span_level == 3 and cls == "WBD-bin-text":
                self._load_bin = True

    def handle_data(self, data):
        if not self._li_valid:
            return

        if self._load_date:
            self._load_date = False

            value = data.strip()

            try:
                self._loaded_date = datetime.datetime.strptime(value, "%Y-%m-%d").date()
            except ValueError:
                self._loaded_date = datetime.datetime.strptime(
                    value, "%A+%d+%b+%Y"
                ).date()

        if self._load_bin:
            self._load_bin = False

            self._entries.append(
                Collection(self._loaded_date, data, icon=ICON_MAP.get(data))
            )


class Source:
    def __init__(self, street, suburb):
        self._street = street
        self._suburb = suburb

    def fetch(self):
        geocode_params = {
            "SingleLine": f"{self._street}, {self._suburb}, QLD Australia",
            "outSR": '{"wkid":4326}',
            "maxLocations": 1,
            "outFields": "*",
            "f": "json",
        }

        geocode_response = requests.get(
            "https://geocode.arcgis.com/arcgis/rest/services/"
            "World/GeocodeServer/findAddressCandidates",
            params=geocode_params,
            timeout=20,
        )
        geocode_response.raise_for_status()

        candidates = geocode_response.json().get("candidates", [])
        if not candidates:
            return []

        candidate = candidates[0]
        attributes = candidate.get("attributes", {})
        postcode = attributes.get("Postal")

        if not postcode:
            return []

        street_number, _, street_name = self._street.partition(" ")

        route = (
            " ".join(
                part
                for part in (
                    attributes.get("StPreDir"),
                    attributes.get("StPreType"),
                    attributes.get("StName"),
                    attributes.get("StType"),
                    attributes.get("StDir"),
                )
                if part
            )
            or street_name
        )

        locality = attributes.get("Nbrhd") or self._suburb
        state = attributes.get("Region") or "Queensland"

        address_data = {
            "address": {
                "street_number": street_number,
                "route": route,
                "locality": locality,
                "administrative_area_level_1": state,
                "postal_code": postcode,
                "part": "",
                "subpremise": "",
                "formatted_address": (
                    f"{self._street}, {locality} {state} {postcode}, Australia"
                ),
            },
            "geometry": {
                "location": {
                    "lat": candidate["location"]["y"],
                    "lng": candidate["location"]["x"],
                }
            },
        }

        params = {
            "apiKey": "b8dbca0c-ad9c-4f8a-8b9c-080fd435c5e7",
            "agendaResultLimit": "3",
            "dateFormat": "yyyy-MM-dd",
            "displayFormat": "agenda",
            "address": json.dumps(address_data, separators=(",", ":")),
        }

        response = requests.post(
            "https://console.whatbinday.com/api/search",
            data=params,
            timeout=20,
        )
        response.raise_for_status()

        parser = IpswichGovAuParser()
        parser.feed(response.text)
        return parser.entries
