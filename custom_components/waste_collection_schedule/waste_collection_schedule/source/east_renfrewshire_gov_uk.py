import base64
import json
import re
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup
from dateutil import parser
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "East Renfrewshire Council"
DESCRIPTION = "Source for eastrenfrewshire.gov.uk services for East Renfrewshire"
URL = "https://www.eastrenfrewshire.gov.uk"

TEST_CASES = {
    "Test_001": {"postcode": "G78 2TJ", "uprn": "131016859"},
    "Test_002": {"postcode": "g775ar", "uprn": 131019331},
    "Test_003": {"postcode": "g78 3er", "uprn": "000131020112"},
}

ICON_MAP = {
    "Grey": "mdi:trash-can",
    "Brown": "mdi:leaf",
    "Green": "mdi:glass-fragile",
    "Blue": "mdi:note",
}


class Source:
    def __init__(self, postcode, uprn):
        self._postcode = postcode
        self._uprn = str(uprn).zfill(12)

    def fetch(self):
        session = requests.Session()
        address_page = self.__get_address_page(session, self._postcode)
        bin_collection_info_page = self.__get_bin_collection_info_page(
            session, address_page, self._uprn
        )
        bin_collection_info = self.__get_bin_collection_info(bin_collection_info_page)
        return self.__generate_collection_entries(bin_collection_info)

    def __generate_collection_entries(self, bin_collection_info):
        collection_results = bin_collection_info["residualWasteResponse"]["value"][
            "collectionResults"
        ]
        entries = []
        for collection in collection_results["binsOrderingArray"]:
            for collection_date in collection["collectionDates"]:
                entries.append(
                    Collection(
                        date=parser.parse(collection_date).date(),
                        t=collection["color"],
                        icon=ICON_MAP.get(collection["color"]),
                    )
                )
        return entries

    def __get_bin_collection_info(self, bin_collection_info_page):
        serialized_collection_info_pattern = re.compile(
            r'var RESIDUALWASTEV2SerializedVariables = "(.*?)";$',
            re.MULTILINE | re.DOTALL,
        )
        soup = BeautifulSoup(bin_collection_info_page, "html.parser")
        script = soup.find("script", text=serialized_collection_info_pattern)
        if not script:
            raise Exception(
                "no script tag cannot find RESIDUALWASTEV2SerializedVariables"
            )
        match = serialized_collection_info_pattern.search(script.text)
        if not match:
            raise Exception("no match cannot find RESIDUALWASTEV2SerializedVariables")
        serialized_collection_info = match.group(1)
        collection_info = json.loads(base64.b64decode(serialized_collection_info))
        return collection_info

    def __get_bin_collection_info_page(self, session, address_page, uprn):
        soup = BeautifulSoup(address_page, "html.parser")
        form = soup.find(id="RESIDUALWASTEV2_FORM")
        goss_ids = self.__get_goss_form_ids(form["action"])
        r = session.post(
            form["action"],
            data={
                "RESIDUALWASTEV2_PAGESESSIONID": goss_ids["page_session_id"],
                "RESIDUALWASTEV2_SESSIONID": goss_ids["session_id"],
                "RESIDUALWASTEV2_NONCE": goss_ids["nonce"],
                "RESIDUALWASTEV2_VARIABLES": "e30=",
                "RESIDUALWASTEV2_PAGENAME": "PAGE2",
                "RESIDUALWASTEV2_PAGEINSTANCE": "1",
                "RESIDUALWASTEV2_PAGE2_FIELD201": "true",
                "RESIDUALWASTEV2_PAGE2_UPRN": uprn,
                "RESIDUALWASTEV2_FORMACTION_NEXT": "RESIDUALWASTEV2_PAGE2_FIELD206",
                "RESIDUALWASTEV2_PAGE2_FIELD202": "false",
                "RESIDUALWASTEV2_PAGE2_FIELD203": "false",
            },
        )
        r.raise_for_status()
        return r.text

    def __get_address_page(self, s, postcode):
        r = s.get("https://www.eastrenfrewshire.gov.uk/bin-days")
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        form = soup.find(id="RESIDUALWASTEV2_FORM")
        goss_ids = self.__get_goss_form_ids(form["action"])
        r = s.post(
            form["action"],
            data={
                "RESIDUALWASTEV2_PAGESESSIONID": goss_ids["page_session_id"],
                "RESIDUALWASTEV2_SESSIONID": goss_ids["session_id"],
                "RESIDUALWASTEV2_NONCE": goss_ids["nonce"],
                "RESIDUALWASTEV2_VARIABLES": "e30=",
                "RESIDUALWASTEV2_PAGENAME": "PAGE1",
                "RESIDUALWASTEV2_PAGEINSTANCE": "0",
                "RESIDUALWASTEV2_PAGE1_POSTCODE": postcode,
                "RESIDUALWASTEV2_FORMACTION_NEXT": "RESIDUALWASTEV2_PAGE1_FIELD199",
            },
        )
        r.raise_for_status()
        return r.text

    def __get_goss_form_ids(self, url):
        parsed_form_url = urlparse(url)
        form_url_values = parse_qs(parsed_form_url.query)
        return {
            "page_session_id": form_url_values["pageSessionId"][0],
            "session_id": form_url_values["fsid"][0],
            "nonce": form_url_values["fsn"][0],
        }
