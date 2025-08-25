import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "North Herts Council"
DESCRIPTION = "Source for www.north-herts.gov.uk services for North Herts Council."
URL = "https://www.north-herts.gov.uk/"
TEST_CASES = {
    "Example": {
        "address_postcode": "SG4 9QY",
        "address_name_numer": "26",
        "address_street": "BENSLOW RISE",
    },
    "Example No Postcode Space": {
        "address_postcode": "SG49QY",
        "address_name_numer": "26",
        "address_street": "BENSLOW RISE",
    },
}
ICON_MAP = {
    "Refuse Collection": "mdi:trash-can",
    "Mixed Recycling Collection": "mdi:recycle",
    "Garden Collection": "mdi:leaf",
    "Food Collection": "mdi:food-apple",
    "Paper/Card Collection": "mdi:package-variant",
}
#
API_URLS = {
    "BASE": "https://waste.nc.north-herts.gov.uk",
    "CSRF": "/w/webpage/find-bin-collection-day-input-address",
    # https://waste.nc.north-herts.gov.uk/
    "KEYPREP": "/w/webpage/find-bin-collection-day-input-address",
    "SCHEDULE": "/w/webpage/find-bin-collection-day-input-address?webpage_subpage_id=PAG0000778GBNLM1&webpage_token=81bf109be5477ba63904dc10c69c37000417bf78a9e0d2b21585ec15ef05088d",
}
HEADER_COMPONENTS = {
    "BASE": {
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Origin": "https://waste.nc.north-herts.gov.uk",
        "Host": "waste.nc.north-herts.gov.uk",
        "sec-ch-ua": '"Not_A Brand";v="99", "Google Chrome";v="109", "Chromium";v="109"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "Windows",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-User": "?1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
    },
    "GET": {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Sec-Fetch-Mode": "none",
    },
    "POST": {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Sec-Fetch-Mode": "cors",
        "X-Requested-With": "XMLHttpRequest",
    },
}


def _parse_custom_date(date_string):
    # Remove ordinal suffixes (st, nd, rd, th) from the day number
    cleaned_date = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", date_string)

    try:
        # Parse the cleaned date string
        return datetime.strptime(cleaned_date, "%A %d %B %Y")
    except ValueError as e:
        raise ValueError(f"Could not parse date string '{date_string}': {str(e)}")


class Source:
    def __init__(
        self,
        address_name_numer=None,
        address_street=None,
        street_town=None,
        address_postcode=None,
    ):
        self._address_name_numer = address_name_numer
        self._address_street = address_street
        self._street_town = street_town
        self._address_postcode = address_postcode

    def fetch(self):
        s = requests.Session()

        # Get CSRF token
        headers = {**HEADER_COMPONENTS["BASE"], **HEADER_COMPONENTS["GET"]}
        r0 = s.get(API_URLS["BASE"] + API_URLS["CSRF"], headers=headers)

        soup = BeautifulSoup(r0.text, features="html.parser")
        app_body = soup.find("div", {"class": "app-body"})
        script = app_body.find("script", {"type": "text/javascript"}).string
        p = re.compile("var CSRF = ('|\")(.*?)('|\");")
        m = p.search(script)
        csrf_token = m.groups()[1]

        # Get form tokens
        form_data = {
            "_dummy": "1",
            "_session_storage": '{"_global":{}}',
            "_update_page_content_request": "1",
            "form_check_ajax": csrf_token,
        }
        headers = {
            **HEADER_COMPONENTS["BASE"],
            **HEADER_COMPONENTS["POST"],
        }

        r1 = s.post(
            API_URLS["BASE"] + API_URLS["KEYPREP"],
            headers=headers,
            data=form_data,
        )
        r1.raise_for_status()

        page_data = r1.json()["data"]
        key = (
            re.findall(r"data-unique_key=\"C_[a-f0-9]+\"", page_data)[-1]
            .replace('data-unique_key="', "")
            .replace('"', "")
        )
        soup = BeautifulSoup(page_data, features="html.parser")
        submitted_widget_group_id = soup.findAll(
            "input", {"name": "submitted_widget_group_id"}
        )[-1].attrs["value"]
        submission_token = soup.find("input", {"name": "submission_token"}).attrs[
            "value"
        ]
        submitted_page_id = soup.find("input", {"name": "submitted_page_id"}).attrs[
            "value"
        ]

        # Fetch collection data
        headers = {
            **HEADER_COMPONENTS["BASE"],
            **HEADER_COMPONENTS["POST"],
        }
        address_str = f"{self._address_name_numer} {self._address_street}"
        form_data = {
            "submitted_page_storage_key": "/w/webpage/find-bin-collection-day-input-address",
            "submitted_page_id": submitted_page_id,
            "submitted_widget_group_id": submitted_widget_group_id,
            "submitted_widget_group_type": "search",
            "submission_token": submission_token,
            f"payload[{submitted_page_id}][{submitted_widget_group_id}][PCL0006978GBNLM1][search][{key}][PCF0023743GBNLM1]": address_str,
            f"payload[{submitted_page_id}][{submitted_widget_group_id}][PCL0006978GBNLM1][search][{key}][PCF0023721GBNLM1]": "Find bin collection dates",
            "submit_fragment_id": "PCF0023721GBNLM1",
            "_session_storage": '{"_global":{"destination_stack":["w/webpage/find-bin-collection-day-input-address"]}}',
            "_update_page_content_request": "1",
            "form_check_ajax": csrf_token,
            "form_check": csrf_token,
        }
        params = {
            "webpage_subpage_id": submitted_page_id,
            "webpage_token": "81bf109be5477ba63904dc10c69c37000417bf78a9e0d2b21585ec15ef05088d",
        }
        r2 = s.post(
            API_URLS["BASE"] + API_URLS["SCHEDULE"],
            headers=headers,
            data=form_data,
            params=params,
        )
        json_res = r2.json()
        soup = BeautifulSoup(json_res["data"], features="html.parser")
        schedule = soup.find_all(
            "div", {"class": "page_fragment_collection form-group block"}
        )

        # Parse outputs
        entries = []
        for pickup in schedule:
            row_data = pickup.find_all("span", {"class": "value-as-text"})
            if row_data:
                address = row_data[0].text.strip()
                # Filter out mismatches (e.g. on duplicate street names)
                if address_str.lower() not in address.lower():
                    continue
                if self._address_postcode is not None:
                    # Postcodes can have spaces or without; UK format always splits at last 3 letters
                    postcode_with_space = (
                        self._address_postcode
                        if " " in self._address_postcode
                        else self._address_postcode[:-3]
                        + " "
                        + self._address_postcode[-3:]
                    )
                    postcode_without_space = self._address_postcode.replace(" ", "")
                    if not (
                        postcode_with_space.lower() in address.lower()
                        or postcode_without_space.lower() in address.lower()
                    ):
                        continue
                if (
                    self._street_town
                    and self._street_town.lower() not in address.lower()
                ):
                    continue
                collection_type = row_data[1].text.strip()
                collection_date_str = row_data[2].text.strip()
                entries.append(
                    Collection(
                        date=_parse_custom_date(collection_date_str).date(),
                        t=collection_type.replace(
                            " Collection", ""
                        ),  # No need for verbosity
                        icon=ICON_MAP.get(collection_type),
                    )
                )

        return entries
