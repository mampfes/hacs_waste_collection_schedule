import datetime
import logging
import re
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup, Tag
from waste_collection_schedule import Collection

TITLE = "Ashfield District Council"
DESCRIPTION = "Source for ashfield.gov.uk, Ashfield District Council, UK"
URL = "https://www.ashfield.gov.uk"
TEST_CASES = {
    "1 Acacia Avenue, Annesley Woodhouse, Nottingham, NG17 9BH": {
        "address": "1 Acacia Avenue, Annesley Woodhouse, Nottingham, NG17 9BH"
    },
    "101 Main Street, Huthwaite, Sutton In Ashfield, NG17 2LQ": {
        "address": "101 Main Street, Huthwaite, Sutton In Ashfield, NG17 2LQ"
    },
}
_LOGGER = logging.getLogger(__name__)

API_URLS = {
    "address_search": "https://www.ashfield.gov.uk/api/powersuite/getaddresses/{postcode}",
    "collection": "https://www.ashfield.gov.uk/api/powersuite/GetCollectionByUprnAndDate/{uprn}",
}

ICON_MAP = {
    "Residual Waste Collection Service": "mdi:trash-can",
    "Domestic Recycling Collection Service": "mdi:recycle",
    "Domestic Glass Collection Service": "mdi:glass-fragile",
    "Garden Waste Collection Service": "mdi:leaf",
}

NAMES = {
    "Residual Waste Collection Service": "Red (rubbish)",
    "Domestic Recycling Collection Service": "Green (recycling)",
    "Domestic Glass Collection Service": "Blue (glass)",
    "Garden Waste Collection Service": "Brown (garden)",
}


CSRF_REGEX = r"var\s+CSRF\s*=\s*'(\w+)';"
WEBPAGE_TOKEN_REGEX = r"webpage_token\s*=\s*([a-f0-9]+)"
DATA_CELL_ID_REGEX = r'data-cell_id\s*=\s*"(\w+)"'
DATA_PAGE_ID_REGEX = r'data-page_id\s*=\s*"(\w+)"'
DATA_WIDGET_GROUP_ID_REGEX = r'data-widget_group_id\s*=\s*"(\w+)"'
DATA_UNIQUE_KEY_REGEX = r'data-unique_key\s*=\s*"(\w+)"'
DATA_PARENT_FRAGMENT_ID_REGEX = r'data-parent_fragment_id\s*=\s*"(\w+)"'
SYSTEM_ADDRESS_REGEX = r"var\s+SYSTEM_ADDRESS\s*=\s*'(.+?)';"
AJAX_URL_REGEX = r'"AJAX_URL"\s*:\s*"(.+?)"'
LEVEL_REGEX = r'(?:"|&quot;)levels(?:"|&quot;)\s*:\s*(?:"|&quot;)(.+?)(?:"|&quot;)'

WEBPAGE_HASH_REGEX = r"webpage_hash=([a-f0-9]+)(&amp;)?"
REQUEST_URI_REGEX = r"var\s+REQUEST_URI\s*=\s*'(.+?)';"

BASE_URL = "https://portal.digital.ashfield.gov.uk/w/webpage/raise-case"
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
}

POST_HEADERS = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest",
}

DEFAULT_DATA_1 = {
    "_dummy": "1",
    "_session_storage": '{"_global":{}}',
    "_update_page_content_request": "1",
    "form_check_ajax": "",  # This will be filled in later
}

DEFAULT_DATA_2 = {
    "code_action": "call_api",
    "code_params": "{}",
    "_session_storage": '{"/w/webpage/raise-case":{},"_global":{}}',
    "action_cell_id": "",  # This will be filled in later
    "action_page_id": "",  # This will be filled in later
    "form_check_ajax": "",  # This will be filled in later
}

SEARCH_DATA = {
    "context_page_id": "",  # This will be filled in later
    "form_check_ajax": "",  # This will be filled in later
    "levels": "",  # This will be filled in later
    "search_string": "",  # This will be filled in later,
    "display_limit": "15",
    "presenter_settings[records_limit]": "15",
    "presenter_settings[load_more_records_label]": "Load+more+results",
    "presenter_settings[min_characters]": "1",
}


@dataclass
class RequestData:
    levels: str
    system_address: str
    ajax_url: str
    full_ajax_url: str
    webpage_subpage_id: str
    webpage_hash: str
    data_widget_group_id: str
    data_cell_id: str
    data_unique_key: str
    data_parent_fragment_id: str
    request_uri: str
    page_data: str


class Invalid:
    def __init__(self) -> None:
        raise ValueError("Something went wrong")

    def group(self, i: int) -> str:
        return ""


class Source:
    def __init__(self, address: str):
        self._address = address

    def __get_csrf(self, session: requests.Session) -> str:
        session.get(
            "https://www.ashfield.gov.uk/environment-health/bins-waste-recycling/bin-calendar/"
        )

        r = session.get(BASE_URL, params={"service": "bin_calendar"})
        r.raise_for_status()
        return (re.search(CSRF_REGEX, r.text) or Invalid()).group(1)

    def __get_request_data(
        self, session: requests.Session, csrf: str
    ) -> tuple[str, str, str, str]:
        """Get data required for further requests.

        Args:
            csrf (str): csrf token

        Returns:
            tuple[str, str, str, str]: webpage_subpage_id, webpage_token, data_cell_id, data_page_id
        """
        data = DEFAULT_DATA_1.copy()
        data["form_check_ajax"] = csrf
        r = session.post(
            BASE_URL,
            data=data,
            params={"service": "bin_calendar"},
            headers=POST_HEADERS,
        )
        r.raise_for_status()
        resone_json = r.json()
        webpage_subpage_id = resone_json["page"]["id"]
        webpage_token = (
            re.search(WEBPAGE_TOKEN_REGEX, resone_json["data"]) or Invalid()
        ).group(1)
        data_cell_id = (
            re.search(DATA_CELL_ID_REGEX, resone_json["data"]) or Invalid()
        ).group(1)
        data_page_id = (
            re.search(DATA_PAGE_ID_REGEX, resone_json["data"]) or Invalid()
        ).group(1)

        return webpage_subpage_id, webpage_token, data_cell_id, data_page_id

    def __get_next_url(
        self,
        session: requests.Session,
        csrf: str,
        data_cell_id: str,
        data_page_id: str,
        webpage_subpage_id: str,
        webpage_token: str,
    ) -> tuple[str, str]:
        """Get data required for further requests.

        Returns:
            tuple[str, str]: next_url, context_record_id
        """
        data = DEFAULT_DATA_2.copy()
        data.update(
            {
                "action_cell_id": data_cell_id,
                "action_page_id": data_page_id,
                "form_check_ajax": csrf,
            }
        )
        params = {
            "service": "bin_calendar",
            "webpage_subpage_id": webpage_subpage_id,
            "webpage_token": webpage_token,
            "widget_action": "handle_event",
        }
        r = session.post(BASE_URL, data=data, params=params, headers=POST_HEADERS)
        r.raise_for_status()
        resone_json = r.json()
        next_url = resone_json["response"]["url"]
        context_record_id = resone_json["response"]["id"]

        return next_url, context_record_id

    def __get_next_csrf(self, session: requests.Session, next_url: str) -> str:
        r = session.get(next_url)
        csrf = (re.search(CSRF_REGEX, r.text) or Invalid()).group(1)
        return csrf

    def __get_relevant_data(
        self, session: requests.Session, next_url: str, csrf: str
    ) -> RequestData:
        data = DEFAULT_DATA_1.copy()
        data["form_check_ajax"] = csrf
        r = session.post(next_url, data=data, headers=POST_HEADERS)
        r.raise_for_status()
        resone_json = r.json()

        system_address_match = re.search(SYSTEM_ADDRESS_REGEX, resone_json["data"])
        if not system_address_match:
            raise ValueError("Could not find system address")
        system_address = system_address_match.group(1)

        ajax_url = (re.search(AJAX_URL_REGEX, resone_json["data"]) or Invalid()).group(
            1
        )

        return RequestData(
            levels=(re.search(LEVEL_REGEX, resone_json["data"]) or Invalid()).group(1),
            system_address=system_address,
            ajax_url=ajax_url,
            full_ajax_url=system_address.rstrip("/")
            + "/"
            + ajax_url.replace(r"\/", "/").lstrip("/"),
            webpage_subpage_id=resone_json["page"]["id"],
            webpage_hash=(
                re.search(WEBPAGE_HASH_REGEX, resone_json["data"]) or Invalid()
            ).group(1),
            data_widget_group_id=(
                re.search(DATA_WIDGET_GROUP_ID_REGEX, resone_json["data"]) or Invalid()
            ).group(1),
            data_cell_id=(
                re.search(DATA_CELL_ID_REGEX, resone_json["data"]) or Invalid()
            ).group(1),
            data_unique_key=(
                re.search(DATA_UNIQUE_KEY_REGEX, resone_json["data"]) or Invalid()
            ).group(1),
            data_parent_fragment_id=(
                re.search(DATA_PARENT_FRAGMENT_ID_REGEX, resone_json["data"])
                or Invalid()
            ).group(1),
            request_uri=(
                re.search(REQUEST_URI_REGEX, resone_json["data"]) or Invalid()
            ).group(1),
            page_data=resone_json["data"],
        )

    def __search_address(
        self,
        session: requests.Session,
        csrf: str,
        data_page_id: str,
        levels: str,
        full_ajax_url: str,
    ) -> requests.Response:
        data = SEARCH_DATA.copy()
        data.update(
            {
                "context_page_id": data_page_id,
                "form_check_ajax": csrf,
                "levels": levels,
                "search_string": self._address,
            }
        )

        params = {"ajax_action": "html_get_type_ahead_results"}
        r = session.post(full_ajax_url, data=data, params=params)
        r.raise_for_status()
        return r

    def __get_address_id(self, response: requests.Response) -> str:
        soup = BeautifulSoup(response.text, "html.parser")
        address_id: str | None = None
        address_match = self._address.lower().replace(" ", "")

        lis = soup.find_all("li")
        if len(lis) == 0:
            raise ValueError(
                "Address not found searched for address: "
                + self._address
                + " did not return any results, please check the address is correct and spelled exactly as it is on the council website"
            )
        for li in lis:
            if li.text.lower().replace(" ", "") == address_match:
                address_id = li["data-id"]
                break

        if address_id is None:
            raise ValueError(
                "Address not found searched for address: "
                + self._address
                + " did not return a perfect match. Please use on of: "
                + str([element.text for element in lis])
            )
        return address_id

    def __get_submit_data(
        self, page_data: str, address_id: str, request_uri: str, context_record_id: str
    ) -> tuple[str, dict[str, str]]:
        """Get the data to submit to the server.

        Returns:
            str, dict[str, str]: submit_url, submit_data
        """
        submit_data: dict[str, str] = {}
        submit_fragment_id: str | None = None
        soup = BeautifulSoup(page_data, "html.parser")

        form = soup.find("form")
        if not isinstance(form, Tag):
            raise ValueError("Could not find form")
        submit_url = form.attrs["data-submit_destination"]
        if submit_url.startswith("/"):
            submit_url = "https://host02.digital.ashfield.gov.uk" + submit_url

        for input_t in soup.find_all("input"):
            if input_t.get("name") is not None:
                submit_data[input_t["name"]] = input_t["value"]
                if input_t["value"] == "Search":
                    submit_fragment_id = input_t["name"].split("[")[-1].split("]")[0]

        if submit_fragment_id is None:
            raise ValueError("Could not find submit fragment id")
        submit_data["submit_fragment_id"] = submit_fragment_id
        submit_data["_update_page_content_request"] = "1"
        submit_data["form_check_ajax"] = submit_data["form_check"]

        for key in submit_data:
            if key.startswith("payload"):
                if submit_data[key] == "":
                    submit_data[key] = address_id

        submit_data["_session_storage"] = (
            '{"_global":{"destination_stack":["'
            + request_uri
            + '"],"last_context_record_id":"'
            + context_record_id
            + '"}}'
        )

        return submit_url, submit_data

    def __request_collection(
        self,
        session: requests.Session,
        webpage_subpage_id: str,
        request_data: RequestData,
        data_cell_id: str,
        context_record_id: str,
        address_id: str,
        domain: str,
    ) -> requests.Response:
        submit_url, submit_data = self.__get_submit_data(
            request_data.page_data,
            address_id,
            request_data.request_uri,
            context_record_id,
        )
        params = {
            "webpage_subpage_id": webpage_subpage_id,
            "webpage_hash": request_data.webpage_hash,
        }

        paramless_url = submit_url.split("?")[0]
        if paramless_url.startswith("/"):
            paramless_url = domain + paramless_url

        params_s = submit_url.split("?")[1].split("&")
        for p in params_s:
            k, v = p.split("=")
            params[k] = v

        r = session.post(
            paramless_url, data=submit_data, params=params, headers=POST_HEADERS
        )
        r.raise_for_status()
        return r

    def __parse_collection(self, response: requests.Response) -> list[Collection]:
        json_data = response.json()
        soup = BeautifulSoup(json_data["data"], "html.parser")
        collections = []
        trs = soup.select("tr.page_fragment_collection")
        for tr in trs:
            if not isinstance(tr, Tag):
                continue
            tds = tr.find_all("td")
            if len(tds) != 3:
                continue
            bin_type = tds[0].text.strip()
            date_str = tds[2].text.strip()
            # Tue, 09 Jul 2024
            try:
                date = datetime.datetime.strptime(date_str, "%a, %d %b %Y").date()
            except ValueError:
                _LOGGER.warning("Could not parse date: %s", date_str)
                continue
            collections.append(
                Collection(date, NAMES.get(bin_type, bin_type), ICON_MAP.get(bin_type))
            )
        return collections

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        session.headers.update(DEFAULT_HEADERS)
        csrf = self.__get_csrf(session)
        (
            webpage_subpage_id,
            webpage_token,
            data_cell_id,
            data_page_id,
        ) = self.__get_request_data(session, csrf)

        next_url, context_record_id = self.__get_next_url(
            session, csrf, data_cell_id, data_page_id, webpage_subpage_id, webpage_token
        )
        csrf = self.__get_next_csrf(session, next_url)
        request_data = self.__get_relevant_data(session, next_url, csrf)

        address_id = self.__get_address_id(
            self.__search_address(
                session,
                csrf,
                data_page_id,
                request_data.levels,
                request_data.full_ajax_url,
            )
        )

        domain = request_data.full_ajax_url.split("/w/")[0]
        r = self.__request_collection(
            session,
            request_data.webpage_subpage_id,
            request_data,
            request_data.data_cell_id,
            context_record_id,
            address_id,
            domain,
        )
        return self.__parse_collection(r)
