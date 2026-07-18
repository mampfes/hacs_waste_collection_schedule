import logging
import re
from datetime import date, datetime, timedelta

import requests
from bs4 import BeautifulSoup, Tag
from dateutil.parser import parse
from dateutil.rrule import WEEKLY, rrule
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

_LOGGER = logging.getLogger(__name__)

TITLE = "City of Wanneroo"
DESCRIPTION = "Source for City of Wanneroo."
URL = "https://www.wanneroo.wa.gov.au/"
TEST_CASES = {
    "23 Bakana LP LANDSDALE": {"address": "23 Bakana LP LANDSDALE"},
    "13/26 Princeton CIR ALEXANDER HEIGHTS": {
        "address": "13/26 Princeton CIR ALEXANDER HEIGHTS"
    },
    "1 Atlanta DR TWO ROCKS": {"address": "1 Atlanta DR TWO ROCKS"},
}

ICON_MAP = {
    "Recycling": Icons.RECYCLING,
    "General Waste": Icons.GENERAL_WASTE,
    "Garden Organics": Icons.GARDEN,
}

API_URL = "https://www.wanneroo.wa.gov.au/bincollections"
MAP_SESSION_URL = (
    "https://wanneroo.spatial.t1cloud.com/spatial/intramaps/ApplicationEngine/Projects/"
)
MAP_INITIALIZE_URL = (
    "https://wanneroo.spatial.t1cloud.com/spatial/intramaps/ApplicationEngine/Modules/"
)
COLLECTION_URL = "https://wanneroo.spatial.t1cloud.com/spatial/intramaps/ApplicationEngine/Integration/set"


API_URL_REGEX = re.compile(r'const\s+API_URL\s*=\s*"(.*?Search/)";')
API_KEY_REGEX = re.compile(r'const\s+API_KEY\s*=\s*"(.*?)";')
FORM_ID_REGEX = re.compile(r'const\s+FORM_ID\s*=\s*"(.*?)";')
CONFIG_ID_REGEX = re.compile(r'const\s+CONFIG_ID\s*=\s*"(.*?)";')
PROJECT_NAME_REGEX = re.compile(r'const\s+PROJECT_NAME\s*=\s*"(.*?)";')

WEEKDAYS = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]

# The council's register stores abbreviated street types ("23 Bakana LP
# LANDSDALE"). Users typically spell them out; expand both sides before
# comparing so "23 Bakana Loop, Landsdale" matches the canonical entry.
STREET_TYPE_ABBREVIATIONS = {
    "ST": "STREET",
    "RD": "ROAD",
    "DR": "DRIVE",
    "DRV": "DRIVE",
    "AVE": "AVENUE",
    "AV": "AVENUE",
    "LP": "LOOP",
    "PL": "PLACE",
    "BVD": "BOULEVARD",
    "BLVD": "BOULEVARD",
    "CL": "CLOSE",
    "CT": "COURT",
    "CRES": "CRESCENT",
    "CR": "CRESCENT",
    "CIR": "CIRCLE",
    "CCT": "CIRCUIT",
    "GTE": "GATE",
    "PDE": "PARADE",
    "TCE": "TERRACE",
    "HWY": "HIGHWAY",
    "GRV": "GROVE",
    "GR": "GROVE",
    "LN": "LANE",
    "SQ": "SQUARE",
    "ESP": "ESPLANADE",
    "PWY": "PARKWAY",
    "PKWY": "PARKWAY",
    "GDNS": "GARDENS",
}


def _normalise_address(address: str) -> str:
    tokens = address.upper().replace(",", " ").split()
    return " ".join(STREET_TYPE_ABBREVIATIONS.get(t, t) for t in tokens)


def _reduced_queries(address: str) -> list[str]:
    """Progressively shorter search terms for a strict register search.

    The register search returns nothing for spelled-out street types or
    appended suburbs, but happily lists candidates for "23 Bakana" — which
    then feed the suggestions flow.
    """
    tokens = address.upper().replace(",", " ").split()
    queries = []
    for cut in range(len(tokens) - 1, 0, -1):
        head = tokens[:cut]
        # Stop shrinking below "<number> <name>".
        if len(head) < 2:
            break
        if head[-1] in STREET_TYPE_ABBREVIATIONS or head[-1] in set(
            STREET_TYPE_ABBREVIATIONS.values()
        ):
            continue
        queries.append(" ".join(head))
    return queries[:2]


def _parse_rythm_description(rythm_description: str, bin_type: str) -> list[date]:
    rythm_description_lower = rythm_description.strip().lower()

    match = re.search(
        r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\s+(this|next)\s+week",
        rythm_description_lower,
    )
    if match:
        weekday_str = match.group(1)
        week_str = match.group(2)

        interval = 1 if "general" in bin_type.lower() else 2

        today = datetime.now().date()
        current_week_start = today - timedelta(days=today.weekday())
        target_weekday_idx = WEEKDAYS.index(weekday_str)
        target_date = current_week_start + timedelta(days=target_weekday_idx)

        if week_str == "next":
            target_date += timedelta(days=7)

        target_datetime = datetime.combine(target_date, datetime.min.time())
        return [
            d.date()
            for d in rrule(WEEKLY, interval=interval, dtstart=target_datetime, count=10)
        ]

    match_week_after_next = re.search(
        r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\s+week\s+after\s+next",
        rythm_description_lower,
    )
    if match_week_after_next:
        weekday_str = match_week_after_next.group(1)

        today = datetime.now().date()
        current_week_start = today - timedelta(days=today.weekday())
        target_weekday_idx = WEEKDAYS.index(weekday_str)
        target_date = (
            current_week_start + timedelta(days=target_weekday_idx) + timedelta(days=14)
        )

        target_datetime = datetime.combine(target_date, datetime.min.time())
        return [
            d.date()
            for d in rrule(WEEKLY, interval=2, dtstart=target_datetime, count=10)
        ]

    if rythm_description_lower in WEEKDAYS:
        return [
            d.date()
            for d in rrule(
                WEEKLY,
                byweekday=WEEKDAYS.index(rythm_description_lower),
                dtstart=datetime.now(),
                count=20,
            )
        ]
    if rythm_description_lower.startswith("fortnightly"):
        next_date_str = rythm_description_lower.split("next collection", 1)[1]
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
        self._session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            }
        )

    def _match_address(self, address: str) -> bool:
        return _normalise_address(self._address) == _normalise_address(address)

    def _fetch_address_values(self) -> str:
        r = self._session.get(API_URL)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        script = soup.find("script", {"src": lambda x: x and "widget.js" in x})
        if not isinstance(script, Tag):
            raise Exception(
                "Failed to find address values - the City may have changed their website layout"
            )

        script_url = script["src"]
        if isinstance(script_url, list):
            script_url = script_url[0]

        if script_url.startswith("//"):
            script_url = "https:" + script_url
        r = self._session.get(script_url)
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

        headers = {
            "Authorization": f"apikey {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        def _search(fields: str) -> list:
            params = {
                "configId": config_id,
                "form": form_id,
                "project": project_name,
                "fields": fields,
            }
            r = self._session.get(api_url, params=params, headers=headers)
            try:
                r.raise_for_status()
            except requests.exceptions.HTTPError as e:
                raise Exception(f"Search API Error ({r.status_code}): {r.text}") from e
            return r.json()

        result = _search(self._address)
        if len(result) == 0:
            # The register search is strict: spelled-out street types,
            # commas or an appended suburb return nothing. Retry with a
            # shortened query ("23 Bakana") — the candidates it returns
            # either match after normalisation or become suggestions.
            for reduced in _reduced_queries(self._address):
                result = _search(reduced)
                if result:
                    break
        if len(result) == 0:
            raise SourceArgumentNotFound("address", self._address)

        addresses = []
        for entry in result:
            address = next(v for v in entry if v["name"] == "Address")["value"]
            addresses.append(address)
            if self._match_address(address):
                self._dbkey = next(v for v in entry if v["name"] == "dbkey")["value"]
                self._mapkey = next(v for v in entry if v["name"] == "mapkey")["value"]
                return self._fetch_map_session(config_id)

        raise SourceArgumentNotFoundWithSuggestions(
            "address",
            self._address,
            addresses,
        )

    def _fetch_map_session(self, config_id: str) -> str:
        project_id = "4c19a56b-7a9e-437b-a3f1-a584aa3184fd"
        module_id = "aae4bf39-9508-4528-9436-5942a23ddd7a"

        params = {
            "configId": config_id,
            "appType": "MapBuilder",
            "project": project_id,
            "datasetCode": "",
        }

        r = self._session.get(MAP_SESSION_URL, params=params)
        if r.status_code != 200:
            raise Exception(
                f"Projects API failed! Status: {r.status_code} | Server Says: {r.text}"
            )

        session = r.headers.get("x-intramaps-session")
        if not session:
            raise Exception("Failed to get intramaps-session id from headers")

        self.initialize_map(session, module_id)
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
        headers = {
            "Content-Type": "application/json",
        }
        r = self._session.post(
            MAP_INITIALIZE_URL, json=data, params=params, headers=headers
        )
        if r.status_code != 200:
            raise Exception(f"Initialize Map API failed! Server Says: {r.text}")

    def fetch(self) -> list[Collection]:
        self._session = requests.Session()
        self._session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            }
        )
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
            "selectionLayer": "Property",
            "useCatalogId": False,
            "zoomTo": "entire",
        }
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Requested-With": "XMLHttpRequest",
        }

        r = self._session.post(
            COLLECTION_URL,
            json=data,
            params={"IntraMapsSession": map_session},
            headers=headers,
        )
        if r.status_code != 200:
            raise Exception(f"Collection Data API failed! Server Says: {r.text}")

        response_data: dict = r.json()
        panel_fields = (
            response_data.get("infoPanels", {})
            .get("info1", {})
            .get("feature", {})
            .get("fields")
        )
        if not panel_fields:
            raise Exception("Invalid response from server - no panel fields found")

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

            if "-" not in field["value"]["value"]:
                continue

            bin_type_raw, rythm_description = field["value"]["value"].split("-", 1)
            rythm_description = rythm_description.strip()
            bin_type_raw = bin_type_raw.strip()

            if "general" in bin_type_raw.lower():
                bin_type = "General Waste"
                icon = "mdi:trash-can"
            elif "recycl" in bin_type_raw.lower():
                bin_type = "Recycling"
                icon = "mdi:recycle"
            elif "green" in bin_type_raw.lower() or "garden" in bin_type_raw.lower():
                bin_type = "Garden Organics"
                icon = "mdi:leaf"
            else:
                bin_type = bin_type_raw
                icon = ICON_MAP.get(bin_type)  # type: ignore[assignment, no-redef]

            try:
                dates = _parse_rythm_description(rythm_description, bin_type)
            except Exception as e:
                _LOGGER.warning(
                    f"Failed to parse rhythm description: {rythm_description}, {e}"
                )
                continue

            for date_ in dates:
                entries.append(Collection(date=date_, t=bin_type, icon=icon))

        return entries
