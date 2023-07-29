# Credit where it's due:
# This is predominantly a refactoring of the Somerset Council script from the UKBinCollectionData repo
# https://github.com/robbrad/UKBinCollectionData

import json
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection

TITLE = "iTouchVision"
URL = "https://iweb.itouchvision.com/"
COUNTRY = "uk"
EXTRA_INFO = [
    {
        "title": "Somerset Council",
        "url": "https://www.somerset.gov.uk/",
        "country": "uk",
    },
    {
        "title": "South Somerset District Council",
        "url": "https://www.somerset.gov.uk/",
        "country": "uk",
    },
    {
        "title": "Mendip District Council",
        "url": "https://www.somerset.gov.uk/",
        "country": "uk",
    },
    {
        "title": "Sedgemoor District Council",
        "url": "https://www.somerset.gov.uk/",
        "country": "uk",
    },
    {
        "title": "Somerset West & Taunton District Council",
        "url": "https://www.somerset.gov.uk/",
        "country": "uk",
    },
    {
        "title": "Somerset County Council",
        "url": "https://www.somerset.gov.uk/",
        "country": "uk",
    },
    {
        "title": "Test Valley Borough Council",
        "url": "https://www.testvalley.gov.uk/",
        "country": "uk",
    },
]
DESCRIPTION = """Consolidated source for waste collection services from:
        Somerset Council, comprising four former District Councils (Mendip, Sedgemoor, Somerset West & Taunton, South Somerset) and Somerset County Council
        Test Valley Borough Council
        """
HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36",
}
URLS = {
    "TEST_VALLEY": "https://iweb.itouchvision.com/portal/f?p=customer:BIN_DAYS:::NO:RP:UID:13353F039C4B1454827EE05536414091A8C058F4",
    "SOMERSET": "https://iweb.itouchvision.com/portal/f?p=customer:BIN_DAYS:::NO:RP:UID:625C791B4D9301137723E9095361401AE8C03934",
    "FLOW.ACCEPT": "https://iweb.itouchvision.com/portal/wwv_flow.accept",
    "BIN_DAYS": "https://iweb.itouchvision.com/portal/itouchvision/r/customer/bin_days",
}
KEYLISTS = {
    "POSTCODE_1": [
        "P153_UPRN",
        "P153_TEMP",
        "P153_SYSDATE",
        "P0_LANGUAGE",
        "P153_POST_CODE",
    ],
    "POSTCODE_2": [
        "p_flow_id",
        "p_flow_step_id",
        "p_instance",
        "p_page_submission_id",
        "p_request",
        "p_reload_on_submit",
    ],
    "ADDRESS_1": ["P153_UPRN", "P153_TEMP", "P153_SYSDATE", "P0_LANGUAGE"],
    "ADDRESS_2": [
        "p_flow_id",
        "p_flow_step_id",
        "p_instance",
        "p_page_submission_id",
        "p_request",
        "p_reload_on_submit",
    ],
}
TEST_CASES = {
    "Somerset #1": {"postcode": "TA20 2JG", "uprn": "30071283", "council": "SOMERSET"},
    "Somerset #2": {"postcode": "BA9 9NF", "uprn": "30002380", "council": "SOMERSET"},
    "Somerset #3": {"postcode": "TA24 7JE", "uprn": 10023837109, "council": "SOMERSET"},
    "Test Valley #1": {
        "postcode": "SP10 3JB",
        "uprn": "100060559598",
        "council": "TEST_VALLEY",
    },
    "Test Valley #2": {
        "postcode": "SO20 6EJ",
        "uprn": "100060583697",
        "council": "TEST_VALLEY",
    },
    "Test Valley #3": {
        "postcode": "SO51 5BE",
        "uprn": 100060571645,
        "council": "TEST_VALLEY",
    },
}
ICON_MAP = {
    "GARDEN": "mdi:leaf",
    "RECYCLING": "mdi:recycle",
    "REFUSE": "mdi:trash-can",
    "HOUSEHOLD WASTE": "mdi:trash-can",
    "GARDEN WASTE": "mdi:leaf",
}


class Source:
    def __init__(self, council, postcode, uprn):
        self._postcode = postcode.upper().strip()
        self._uprn = str(uprn)
        self._council = council.upper()

    def get_payloads(self, s):
        p1 = {i["name"]: i.get("value", "") for i in s.select("input[name]")}
        p2 = {i["data-for"]: i.get("value", "") for i in s.select("input[data-for]")}
        ps = s.select_one('input[id="pSalt"]').get("value")
        pp = s.select_one('input[id="pPageItemsProtected"]').get("value")
        return p1, p2, ps, pp

    def fetch(self):
        s = requests.Session()
        s.headers.update(HEADERS)

        # Get postcode search page
        r0 = s.get(URLS[self._council])
        # Extract values needed for the postcode search
        soup = BeautifulSoup(r0.text, "html.parser")
        payload1, payload2, payload_salt, payload_protected = self.get_payloads(soup)
        payload1["p_request"] = "SEARCH"
        payload1["P153_POST_CODE"] = self._postcode

        # Build JSON for postcode search
        merged_list = {**payload1, **payload2}
        new_list = []
        other_list = {}
        for key in merged_list.keys():
            temp_list = {}
            val = merged_list[key]
            if key in KEYLISTS["POSTCODE_1"]:
                temp_list = {"n": key, "v": val}
                new_list.append(temp_list)
            elif key in KEYLISTS["POSTCODE_2"]:
                other_list[key] = val
            else:
                temp_list = {"n": key, "v": "", "ck": val}
                new_list.append(temp_list)
        json_builder = {
            "pageItems": {
                "itemsToSubmit": new_list,
                "protected": payload_protected,
                "rowVersion": "",
                "formRegionChecksums": [],
            },
            "salt": payload_salt,
        }
        json_object = json.dumps(json_builder, separators=(",", ":"))
        other_list["p_json"] = json_object

        # Update header and submit postcode search
        s.headers.update(
            {
                "referer": URLS[self._council],
            }
        )
        s.post(URLS["FLOW.ACCEPT"], data=other_list)

        # Get address selection page
        r2 = s.get(URLS["BIN_DAYS"])
        # Extract values needed for address selection
        soup = BeautifulSoup(r2.text, "html.parser")
        payload1, payload2, payload_salt, payload_protected = self.get_payloads(soup)
        payload1["p_request"] = "SUBMIT"
        payload1["P153_UPRN"] = self._uprn

        # Build JSON for address selection
        merged_list = {**payload1, **payload2}
        new_list = []
        other_list = {}
        for key in merged_list.keys():
            temp_list = {}
            val = merged_list[key]
            if key in KEYLISTS["ADDRESS_1"]:
                temp_list = {"n": key, "v": val}
                new_list.append(temp_list)
            elif key in ["P153_ZABY"]:
                temp_list = {"n": key, "v": "1", "ck": val}
                new_list.append(temp_list)
            elif key in ["P153_POST_CODE"]:
                temp_list = {"n": key, "v": self._postcode, "ck": val}
                new_list.append(temp_list)
            elif key in KEYLISTS["ADDRESS_2"]:
                other_list[key] = val
            else:
                temp_list = {"n": key, "v": "", "ck": val}
                new_list.append(temp_list)
        json_builder = {
            "pageItems": {
                "itemsToSubmit": new_list,
                "protected": payload_protected,
                "rowVersion": "",
                "formRegionChecksums": [],
            },
            "salt": payload_salt,
        }
        json_object = json.dumps(json_builder, separators=(",", ":"))
        other_list["p_json"] = json_object

        # Submit address selection
        s.post(URLS["FLOW.ACCEPT"], data=other_list)

        # Finally, get the collection schedule page
        r4 = s.get(URLS["BIN_DAYS"])
        soup = BeautifulSoup(r4.text, "html.parser")
        entries = []
        for item in soup.select(".t-MediaList-item"):
            for value in item.select(".t-MediaList-body"):
                waste_type = value.select("span")[1].get_text(strip=True).title()
                waste_date = datetime.strptime(
                    value.select(".t-MediaList-desc")[0].get_text(strip=True),
                    "%A, %d %B, %Y",
                ).date()
                entries.append(
                    Collection(
                        date=waste_date,
                        t=waste_type,
                        icon=ICON_MAP.get(waste_type.upper()),
                    )
                )

        return entries
