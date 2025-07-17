import logging
import re
from datetime import datetime

import certifi
import requests
import urllib3
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Ashford Borough Council"
DESCRIPTION = "Source for Ashford Borough Council."
URL = "https://ashford.gov.uk"
TEST_CASES = {
    "100060796052": {"uprn": 100060796052, "postcode": "TN23 3DY"},
    "100060780440": {"uprn": "100060780440", "postcode": "TN24 9JD"},
    "100062558476": {"uprn": "100062558476", "postcode": "TN233LX"},
}


ICON_MAP = {
    "household refuse": "mdi:trash-can",
    "food waste": "mdi:food",
    "garden waste": "mdi:leaf",
    "recycling": "mdi:recycle",
}


API_URL = "https://secure.ashford.gov.uk/waste/collectiondaylookup/"

_LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(self, postcode: str, uprn: str | int):
        self._uprn = str(uprn).strip()
        self._postcode = str(postcode).strip()

    def fetch(self):

        _LOGGER.warning(
            f"requests: {requests.__version__}, urllib3: {urllib3.__version__}, certifi: {certifi.__version__}"
        )

        s = requests.Session()
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Application": "application/x-www-form-urlencoded",
        }
        s.headers.update(headers)
        r = s.get(API_URL)
        r.raise_for_status()
        soup: BeautifulSoup = BeautifulSoup(r.text, "html.parser")

        args = {}
        for input_tag in soup.find_all("input"):
            if not input_tag.get("name"):
                continue
            args[input_tag["name"]] = input_tag.get("value")
        args["ctl00$ContentPlaceHolder1$CollectionDayLookup2$HiddenField_UPRN"] = ""
        args["ctl00$ContentPlaceHolder1$CollectionDayLookup2$TextBox_PostCode"] = (
            self._postcode
        )
        args["ctl00$ContentPlaceHolder1$CollectionDayLookup2$Button_PostCodeSearch"] = (
            "Continue+>"
        )
        args["__EVENTTARGET"] = ""
        args["__EVENTARGUMENT"] = ""

        r = s.post(API_URL, data=args)
        r.raise_for_status()

        soup: BeautifulSoup = BeautifulSoup(r.text, "html.parser")
        args = {}
        for input_tag in soup.find_all("input"):
            if not input_tag.get("name"):
                continue
            args[input_tag["name"]] = input_tag.get("value")
        args[
            "ctl00$ContentPlaceHolder1$CollectionDayLookup2$DropDownList_Addresses"
        ] = self._uprn

        args["ctl00$ContentPlaceHolder1$CollectionDayLookup2$Button_PostCodeSearch"] = (
            "Continue+>"
        )
        del args["ctl00$ContentPlaceHolder1$CollectionDayLookup2$Button_SelectAddress"]
        del args["ctl00$ContentPlaceHolder1$CollectionDayLookup2$Button_PostCodeSearch"]
        args["ctl00$ContentPlaceHolder1$CollectionDayLookup2$Button_SelectAddress"] = (
            "Continue+>"
        )

        r = s.post(API_URL, data=args)
        if r.status_code != 200:
            raise Exception(
                f"could not get correct data for your postcode ({self._postcode}). check {API_URL} to validate your arguments."
            )

        soup: BeautifulSoup = BeautifulSoup(r.text, "html.parser")
        bin_tables = soup.find_all("table")
        if bin_tables == []:
            raise Exception(
                f"could not get valid data from ashford.gov.uk. is your UPRN ({self._uprn}) correct for postcode ({self._postcode})? check https://uprn.uk/{self._uprn} and {API_URL}"
            )

        entries = []
        for bin_table in bin_tables:
            bin_text = bin_table.find("td", id=re.compile("CollectionDayLookup2_td_"))
            if not bin_text:
                continue

            bin_type_soup = bin_text.find("b")

            if not bin_type_soup:
                continue
            bin_type: str = bin_type_soup.text.strip()

            date_soup = bin_text.find(
                "span", id=re.compile(r"CollectionDayLookup2_Label_\w*_Date")
            )
            if not date_soup or (
                " " not in date_soup.text.strip()
                and date_soup.text.strip().lower() != "today"
            ):
                continue
            date_str: str = date_soup.text.strip()
            try:
                if date_soup.text.strip().lower() == "today":
                    date = datetime.now().date()
                else:
                    date = datetime.strptime(date_str.split(" ")[1], "%d/%m/%Y").date()

            except ValueError:
                continue

            icon = ICON_MAP.get(bin_type.split("(")[0].strip().lower())
            entries.append(Collection(date=date, t=bin_type, icon=icon))

        return entries
