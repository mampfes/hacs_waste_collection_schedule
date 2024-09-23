import logging
import re
from datetime import date, datetime

import requests
from bs4 import BeautifulSoup, Tag
from dateutil.parser import parse
from dateutil.rrule import WEEKLY, rrule
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

_LOGGER = logging.getLogger(__name__)

TITLE = "City of Wanneroo"
DESCRIPTION = "Source for City of Wanneroo."
URL = "https://www.wanneroo.wa.gov.au/"
TEST_CASES = {
    "23 Bakana Loop LANDSDALE": {"address": "23 Bakana Loop LANDSDALE"},
    "13/26 Princeton Circle ALEXANDER HEIGHTS": {
        "address": "13/26 Princeton Circle ALEXANDER HEIGHTS"
    },
}


ICON_MAP = {
    "Recycling": "mdi:recycle",
    "General Waste": "mdi:trash-can",
    "Garden Organics": "mdi:leaf",
}


API_URL = "https://www.wanneroo.wa.gov.au/info/20008/waste_services"
COLLECTION_URL = "https://wanneroo.spatial.t1cloud.com/spatial/IntraMaps/ApplicationEngine/Integration/set"


# const API_URL = "https://enterprise.mapimage.net/IntraMaps22B/ApplicationEngine/Integration/api/search/";
API_URL_REGEX = re.compile(r'const\s+API_URL\s*=\s*"(.*?Search/)";')
API_KEY_REGEX = re.compile(r'const\s+API_KEY\s*=\s*"(.*?)";')
FORM_ID_REGEX = re.compile(r'const\s+FORM_ID\s*=\s*"(.*?)";')
CONFIG_ID_REGEX = re.compile(r'const\s+CONFIG_ID\s*=\s*"(.*?)";')
PROJECT_NAME_REGEX = re.compile(r'const\s+PROJECT_NAME\s*=\s*"(.*?)";')

# "Authorization": "apikey f49dd048-a442-4810-a567-544a1e0d32bc",
AUTHORIZATION_REGEX = re.compile(r'"Authorization": "(.*?)"')


WEEKDAYS = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]


def _parse_rythm_description(rythm_description: str) -> list[date]:
    if rythm_description.strip().lower() in WEEKDAYS:
        return [
            d.date()
            for d in rrule(
                WEEKLY,
                byweekday=WEEKDAYS.index(rythm_description.strip().lower()),
                dtstart=datetime.now(),
                count=20,
            )
        ]
    if rythm_description.strip().lower().startswith("fortnightly"):
        next_date_str = rythm_description.strip().lower().split("next collection", 1)[1]
        next_date = parse(next_date_str, dayfirst=True).date()
        return [
            d.date() for d in rrule(WEEKLY, interval=2, dtstart=next_date, count=10)
        ]

    raise Exception(f"Could not parse rhythm description: {rythm_description}")


class Source:
    def __init__(self, address: str):
        self._address: str = address
        self._dbkey: str | None = None
        self._mapkey: str | None = None

    def _match_address(self, address: str) -> bool:
        return self._address.lower().replace(" ", "").replace(
            ",", ""
        ) in address.lower().replace(" ", "").replace(",", "")

    def _fetch_address_values(self) -> None:
        session = requests.Session()

        r = session.get(API_URL)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        script = soup.find("script", {"src": lambda x: x and "widget.js" in x})
        if not isinstance(script, Tag):
            raise Exception("Failed to find address values")

        script_url = script["src"]
        if isinstance(script_url, list):
            script_url = script_url[0]

        if script_url.startswith("//"):
            script_url = "https:" + script_url
        r = session.get(script_url)
        r.raise_for_status()

        api_url_search = API_URL_REGEX.search(r.text)
        if not api_url_search:
            raise Exception("Failed to find API URL")
        api_url = api_url_search.group(1)

        api_key_search = API_KEY_REGEX.search(r.text)
        if not api_key_search:
            raise Exception("Failed to find API key")
        api_key = api_key_search.group(1)

        form_id_search = FORM_ID_REGEX.search(r.text)
        if not form_id_search:
            raise Exception("Failed to find form ID")
        form_id = form_id_search.group(1)

        config_id_search = CONFIG_ID_REGEX.search(r.text)
        if not config_id_search:
            raise Exception("Failed to find config ID")
        config_id = config_id_search.group(1)

        project_name_search = PROJECT_NAME_REGEX.search(r.text)
        if not project_name_search:
            raise Exception("Failed to find project name")
        project_name = project_name_search.group(1)

        params = {
            "configId": config_id,
            "form": form_id,
            "project": project_name,
            "fields": self._address,
        }

        headers = {
            "Authorization": f"apikey {api_key}",
            "Content-Type": "application/json",
        }

        # get json file
        r = session.get(api_url, params=params, headers=headers)
        r.raise_for_status()

        result = r.json()

        if len(result) == 0:
            raise Exception("Could not find any matching addresses")

        addresses = []
        for entry in result:
            address = [v for v in entry if v["name"] == "Address"][0]["value"]
            addresses.append(address)
            if self._match_address(address):
                self._dbkey = [v for v in entry if v["name"] == "dbkey"][0]["value"]
                self._mapkey = [v for v in entry if v["name"] == "mapkey"][0]["value"]
                return

        raise Exception(
            "Could not find matching address, using one of: " + ", ".join(addresses)
        )

    def fetch(self) -> list[Collection]:
        fresh_keys = False
        if not self._dbkey or not self._mapkey:
            fresh_keys = True
            self._fetch_address_values()

        try:
            return self._get_collections()
        except Exception as e:
            if fresh_keys:
                raise e
            self._fetch_address_values()
            return self._get_collections()

    def _get_collections(self) -> list[Collection]:
        if not self._dbkey or not self._mapkey:
            raise Exception("No address keys found")

        data = {
            "dbKey": self._dbkey,
            "infoPanelWidth": 0,
            "mapKeys": [self._mapkey],
            "multiLayer": False,
            "selectionLayer": "Parcels",
            "useCatalogId": False,
            "zoomTo": "entire",
        }
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0",
            "X-Requested-With": "XMLHttpRequest",
        }

        r = requests.post(
            COLLECTION_URL,
            json=data,
            params={"IntraMapsSession": "78a2138f-1941-4070-baf4-e8ff5da5cfba"},
            headers=headers,
        )

        r.raise_for_status()

        respone_data: dict = r.json()
        panel_fields = (
            respone_data.get("infoPanels", {})
            .get("info1", {})
            .get("feature", {})
            .get("fields")
        )
        if not panel_fields:
            raise Exception("Invalid response from server")

        entries = []
        for field in panel_fields:
            if "value" not in field:
                continue
            if "column" not in field["value"]:
                continue
            if not field["value"]["column"].lower().endswith("day"):
                continue
            if "value" not in field["value"]:
                continue

            bin_type, rythm_description = field["value"]["value"].split("-", 1)
            rythm_description = rythm_description.strip()
            bin_type = bin_type.strip()
            icon = ICON_MAP.get(bin_type)  # Collection icon

            try:
                dates = _parse_rythm_description(rythm_description)
            except Exception as e:
                _LOGGER.warning(
                    f"Failed to parse rhythm description: {rythm_description}, {e}"
                )
                continue

            for date_ in dates:
                entries.append(Collection(date=date_, t=bin_type, icon=icon))

        return entries
