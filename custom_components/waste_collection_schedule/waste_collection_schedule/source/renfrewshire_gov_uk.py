from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup
from dateutil import parser
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Renfrewshire Council"
DESCRIPTION = "Source for renfrewshire.gov.uk services for Renfrewshire"
URL = "https://renfrewshire.gov.uk/"
API_URL = "https://www.renfrewshire.gov.uk/article/2320/Check-your-bin-collection-day"

TEST_CASES = {
    "Test_001": {"postcode": "PA12 4JU", "uprn": 123033059},
    "Test_002": {"postcode": "PA12 4AJ", "uprn": "123034174"},
    "Test_003": {"postcode": "PA12 4EW", "uprn": "123033042"},
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
        self._uprn = str(uprn)

    def fetch(self):
        session = requests.Session()
        bin_collection_info_page = self.__get_bin_collection_info_page(
            session, self._uprn, self._postcode
        )
        return self.__get_bin_collection_info(bin_collection_info_page)

    def __get_goss_form_ids(self, url):
        parsed_form_url = urlparse(url)
        form_url_values = parse_qs(parsed_form_url.query)
        return {
            "page_session_id": form_url_values["pageSessionId"][0],
            "session_id": form_url_values["fsid"][0],
            "nonce": form_url_values["fsn"][0],
        }

    def __get_bin_collection_info_page(self, session, uprn, postcode):
        r = session.get(API_URL)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        form = soup.find(id="RENFREWSHIREBINCOLLECTIONS_FORM")
        goss_ids = self.__get_goss_form_ids(form["action"])
        r = session.post(
            form["action"],
            data={
                "RENFREWSHIREBINCOLLECTIONS_PAGESESSIONID": goss_ids["page_session_id"],
                "RENFREWSHIREBINCOLLECTIONS_SESSIONID": goss_ids["session_id"],
                "RENFREWSHIREBINCOLLECTIONS_NONCE": goss_ids["nonce"],
                "RENFREWSHIREBINCOLLECTIONS_VARIABLES": "",
                "RENFREWSHIREBINCOLLECTIONS_PAGENAME": "PAGE1",
                "RENFREWSHIREBINCOLLECTIONS_PAGEINSTANCE": "0",
                "RENFREWSHIREBINCOLLECTIONS_PAGE1_ADDRESSSTRING": "",
                "RENFREWSHIREBINCOLLECTIONS_PAGE1_UPRN": uprn,
                "RENFREWSHIREBINCOLLECTIONS_PAGE1_ADDRESSLOOKUPPOSTCODE": postcode,
                "RENFREWSHIREBINCOLLECTIONS_PAGE1_NAVBUTTONS_NEXT": "Load Address",
            },
        )
        r.raise_for_status()
        return r.text

    def __get_bin_collection_info(self, binformation):
        soup = BeautifulSoup(binformation, "html.parser")
        all_collections = soup.select(
            "#RENFREWSHIREBINCOLLECTIONS_PAGE1_COLLECTIONDETAILS"
        )
        for collection in all_collections:
            dates = collection.select("p.collection__date")
            date_list = []
            bin_list = []
            for individualdate in dates:
                date_list.append(parser.parse(individualdate.get_text()).date())
            bins = collection.select("p.bins__name")
            for individualbin in bins:
                bin_list.append(individualbin.get_text().strip())

        schedule = list(zip(date_list, bin_list))

        entries = []
        for sched_entry in schedule:
            entries.append(
                Collection(
                    date=sched_entry[0],
                    t=sched_entry[1],
                    icon=ICON_MAP.get(sched_entry[1]),
                )
            )
        return entries
