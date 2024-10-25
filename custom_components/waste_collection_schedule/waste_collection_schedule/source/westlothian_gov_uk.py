import base64
import json
import re
from urllib.parse import parse_qs, urlparse
import requests
from bs4 import BeautifulSoup
# from dateutil import parser
from datetime import datetime
from waste_collection_schedule.collection import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS # type: ignore[attr-defined]


TITLE = "West Lothian Council"
DESCRIPTION = "Source for services for West Lothian"
URL = "https://www.westlothian.gov.uk"
COLLECTION_PAGE_URL = "https://www.westlothian.gov.uk/bin-collections"

TEST_CASES = {
    "Test_001": {"postcode": "EH48+4DD", "uprn": "135007799"},
    "Test_002": {"postcode": "EH55+8FJ", "uprn": "135051417"},
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
        self._ics = ICS()

    def fetch(self):
        session = requests.Session()
        session.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Sec-Fetch-Dest": "document",
            "Host": "www.westlothian.gov.uk",
            "Sec-Fetch-User": "?1",
            "Accept-Language": "en-GB,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Referer": "westlothian.gov.uk",
            "Cache-Control": "no-cache",
            "DNT": "1"
        }
        address_page = self.__get_address_page(session)
        bin_collection_info_page = self.__get_bin_collection_info_page(
            session, address_page, self._postcode, self._uprn
        )
        bin_collection_info = self.__get_ical_bin_collection_info(bin_collection_info_page)
        if bin_collection_info.get("ICALCONTENT", {}).get("value", {}).get("error", None) is not None:
            # West Lothian have broken their iCal generation again - use the page content
            bin_collection_info = self.__get_immediate_bin_collection_info(bin_collection_info_page)
        return self.__generate_collection_entries(bin_collection_info)

    def __generate_collection_entries(self, bin_collection_info):
        icalContent = bin_collection_info.get("ICALCONTENT")
        webpageContent = bin_collection_info.get("PAGE2_1")
        if icalContent is not None:
            if icalContent['error'] is not None:
             raise Exception(icalContent['error'])
            # iCal data returned isn't compatible with _ics.convert because it's UNTIL values
            # don't specify a timezone, but the ICS module asks for "timezone-aware" parsing.
            # So, change the UNTILs to be Z because they're date only and are UK-based.
            ics_data = re.sub(
                r"UNTIL=([0-9]+)",
                lambda m: "UNTIL=" + m.group(1) + "Z",
                icalContent["value"],
            )
            dates = self._ics.convert(ics_data)
            entries = []
            for d in dates:
                icon = ICON_MAP.get(d[1].split(" ")[0])
                if icon is None:
                    icon = ICON_MAP.get(d[1])
                entries.append(Collection(d[0], d[1], icon=icon))

            return entries
        else:
            if webpageContent is not None:
                collections = json.loads(webpageContent["COLLECTIONS"])
                entries = []
                for d in collections:
                    icon = ICON_MAP.get(d['binName'].split(" ")[0])
                    if icon is None:
                        icon = ICON_MAP.get(d['binType'])
                    entries.append(Collection(datetime.strptime(d['nextCollectionISO'], "%Y-%m-%d").date(), d['binType'], icon=icon))

                return entries
        raise Exception('No entries could be parsed')

    def __get_ical_bin_collection_info(self, bin_collection_info_page):
        serialized_collection_info_pattern = re.compile(
            r'var WLBINCOLLECTIONSerializedVariables = "(.*?)";$',
            re.MULTILINE | re.DOTALL,
        )
        soup = BeautifulSoup(bin_collection_info_page, "html.parser")
        script = soup.find("script", text=serialized_collection_info_pattern)
        if not script:
            raise Exception(
                "no script tag cannot find WLBINCOLLECTIONSerializedVariables"
            )
        match = serialized_collection_info_pattern.search(script.text)
        if not match:
            raise Exception("no match cannot find WLBINCOLLECTIONSerializedVariables")
        serialized_collection_info = match.group(1)
        collection_info = json.loads(base64.b64decode(serialized_collection_info))
        return collection_info

    def __get_immediate_bin_collection_info(self, bin_collection_info_page):
        serialized_collection_info_pattern = re.compile(
            r'var WLBINCOLLECTIONFormData = "(.*?)";$',
            re.MULTILINE | re.DOTALL,
        )
        soup = BeautifulSoup(bin_collection_info_page, "html.parser")
        script = soup.find("script", text=serialized_collection_info_pattern)
        if not script:
            raise Exception(
                "no script tag cannot find WLBINCOLLECTIONFormData"
            )
        match = serialized_collection_info_pattern.search(script.text)
        if not match:
            raise Exception("no match cannot find WLBINCOLLECTIONFormData")
        serialized_collection_info = match.group(1)
        collection_info = json.loads(base64.b64decode(serialized_collection_info))
        return collection_info

    def __get_bin_collection_info_page(self, session, address_page, postcode, uprn):
        soup = BeautifulSoup(address_page, "html.parser")
        form = soup.find(id="WLBINCOLLECTION_FORM")
        goss_ids = self.__get_goss_form_ids(form["action"])
        r = session.post(
            form["action"],
            allow_redirects=True,
            data={
                "WLBINCOLLECTION_PAGESESSIONID": goss_ids["page_session_id"],
                "WLBINCOLLECTION_SESSIONID": goss_ids["session_id"],
                "WLBINCOLLECTION_NONCE": goss_ids["nonce"],
                "WLBINCOLLECTION_VARIABLES": "e30=",
                "WLBINCOLLECTION_PAGENAME": "PAGE1",
                "WLBINCOLLECTION_PAGEINSTANCE": "0",
                "WLBINCOLLECTION_PAGE1_UPRN": uprn,
                "WLBINCOLLECTION_PAGE1_ADDRESSLOOKUPPOSTCODE": postcode,
                "WLBINCOLLECTION_PAGE1_ADDRESSLOOKUPADDRESS": "4",
                "WLBINCOLLECTION_FORMACTION_NEXT": "WLBINCOLLECTION_PAGE1_NAVBUTTONS",
            })
        r.raise_for_status()
        return r.text

    def __get_address_page(self, s):
        r = s.get(COLLECTION_PAGE_URL)
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