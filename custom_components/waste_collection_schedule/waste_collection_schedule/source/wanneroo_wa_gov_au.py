import logging
import re
from datetime import date, datetime

import requests
from bs4 import BeautifulSoup, Tag
from dateutil.parser import parse
from dateutil.rrule import WEEKLY, rrule
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

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
MAP_SESSION_URL = [
    "https://wanneroo.spatial.t1cloud.com/spatial/IntraMaps/ApplicationEngine/Configuration/PublicLite/Config/{liteConfigId}",
    "https://wanneroo.spatial.t1cloud.com/spatial/IntraMaps/ApplicationEngine/Projects/",
]
MAP_INITIALIZE_URL = (
    "https://wanneroo.spatial.t1cloud.com/spatial/IntraMaps/ApplicationEngine/Modules/"
)
COLLECTION_URL = "https://wanneroo.spatial.t1cloud.com/spatial/IntraMaps/ApplicationEngine/Integration/set"


# const API_URL = "https://enterprise.mapimage.net/IntraMaps22B/ApplicationEngine/Integration/api/search/";
API_URL_REGEX = re.compile(r'const\s+API_URL\s*=\s*"(.*?Search/)";')
API_KEY_REGEX = re.compile(r'const\s+API_KEY\s*=\s*"(.*?)";')
FORM_ID_REGEX = re.compile(r'const\s+FORM_ID\s*=\s*"(.*?)";')
CONFIG_ID_REGEX = re.compile(r'const\s+CONFIG_ID\s*=\s*"(.*?)";')
LITE_CONGI_ID_REGEX = re.compile(r"liteConfigId=([0-9a-f-]+)&")
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
        self._session = requests.Session()

    def _match_address(self, address: str) -> bool:
        return self._address.lower().replace(" ", "").replace(
            ",", ""
        ) == address.lower().replace(" ", "").replace(",", "")

    def _fetch_address_values(self) -> str:
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

        lite_config_id_search = LITE_CONGI_ID_REGEX.search(r.text)
        if not lite_config_id_search:
            raise Exception("Failed to find lite config ID")

        lite_config_id = lite_config_id_search.group(1)

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
            raise SourceArgumentNotFound("address", self._address)

        addresses = []
        for entry in result:
            address = [v for v in entry if v["name"] == "Address"][0]["value"]
            addresses.append(address)
            if self._match_address(address):
                self._dbkey = [v for v in entry if v["name"] == "dbkey"][0]["value"]
                self._mapkey = [v for v in entry if v["name"] == "mapkey"][0]["value"]
                return self._fetch_map_session(config_id, lite_config_id)

        raise SourceArgumentNotFoundWithSuggestions(
            "address",
            self._address,
            addresses,
        )

    def _fetch_map_session(self, config_id: str, lite_config_id) -> str:
        params = {
            "configId": config_id,
        }
        r = self._session.get(
            MAP_SESSION_URL[0].format(liteConfigId=lite_config_id), params=params
        )
        r.raise_for_status()
        data = r.json()
        if (
            "intraMapsSettings" not in data
            or "project" not in data["intraMapsSettings"]
            or "module" not in data["intraMapsSettings"]
        ):
            raise Exception("Failed to get project id")

        project_id = data["intraMapsSettings"]["project"]
        module_id = data["intraMapsSettings"]["module"]

        params = {
            "configId": config_id,
            "appType": "MapBuilder",
            "project": project_id,
            "datasetCode": "",
        }
        r = self._session.get(MAP_SESSION_URL[1], params=params)
        r.raise_for_status()

        session = r.headers.get("x-intramaps-session")
        if not session:
            raise Exception("Failed to get intramaps-session id")

        self.initialize_map(session, module_id)
        if not session:
            raise Exception("Failed to get intramaps-session id")
        return session

    def initialize_map(self, map_session_id: str, module_id: str) -> None:
        params = {
            "IntraMapsSession": map_session_id,
        }
        data = {
            "module": module_id,
            "includeBasemaps": False,
            "includeWktInSelection": True,
        }

        r = self._session.post(MAP_INITIALIZE_URL, json=data, params=params)
        r.raise_for_status()

    def fetch(self) -> list[Collection]:
        self._session = requests.Session()
        map_session_id = self._fetch_address_values()
        return self._get_collections(map_session_id)

    def _get_collections(self, map_session: str) -> list[Collection]:
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

        r = self._session.post(
            COLLECTION_URL,
            json=data,
            params={"IntraMapsSession": map_session},
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
