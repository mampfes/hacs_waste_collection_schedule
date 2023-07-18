import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from bs4 import BeautifulSoup, Tag
import re
from datetime import datetime

TITLE = "Ashford Borough Council"
DESCRIPTION = "Source for Ashford Borough Council."
URL = "https://ashford.gov.uk"
TEST_CASES = {
    "100060796052": {
        "uprn": 100060796052,
        "postcode": "TN23 3DY"
    },
    "100060780440": {
        "uprn": "100060780440",
        "postcode": "TN24 9JD"
    },
    "100062558476": {
        "uprn": "100062558476",
        "postcode": "TN233LX"
    },
}


ICON_MAP = {
    "household refuse": "mdi:trash-can",
    "food waste": "mdi:food",
    "garden waste": "mdi:leaf",
    "recycling": "mdi:recycle",
}


API_URL = "https://secure.ashford.gov.uk/wastecollections/collectiondaylookup/"


class Source:
    def __init__(self, postcode: str, uprn: str | int):
        self._uprn = str(uprn).strip()
        self._postcode = str(postcode).strip()

        self._post_code_args = {"CollectionDayLookup2$Button_PostCodeSearch": "Continue+>"}
        self._uprn_args = {"CollectionDayLookup2$Button_SelectAddress": "Continue+>"}
        self._post_code_args["CollectionDayLookup2$TextBox_PostCode"] = self._postcode
        self._uprn_args["CollectionDayLookup2$DropDownList_Addresses"] = self._uprn

    def fetch(self):
        # get json file
        s = requests.Session()
        r = s.get(API_URL)
        r.raise_for_status()

        soup: BeautifulSoup = BeautifulSoup(r.text, "html.parser")

        viewstate = soup.find("input", id="__VIEWSTATE")
        viewstate_generator = soup.find("input", id="__VIEWSTATEGENERATOR")
        
        if not viewstate or type(viewstate) != Tag or not viewstate_generator or type(viewstate_generator) != Tag:
            raise Exception("could not get valid data from ashford.gov.uk")

        self._post_code_args["__VIEWSTATE"] = str(viewstate["value"])

        self._post_code_args["__VIEWSTATEGENERATOR"] = str(viewstate_generator["value"])
        self._uprn_args["__VIEWSTATEGENERATOR"] = str(viewstate_generator["value"])

        r = s.post(API_URL, data=self._post_code_args)
        r.raise_for_status()

        soup: BeautifulSoup = BeautifulSoup(r.text, "html.parser")
        viewstate = soup.find("input", id="__VIEWSTATE")
        if not viewstate or type(viewstate) != Tag:
            raise Exception("could not get valid data from ashford.gov.uk")

        self._uprn_args["__VIEWSTATE"] = str(viewstate["value"])

        r = s.post(API_URL, data=self._uprn_args)
        if r.status_code != 200:
            raise Exception(
                f"could not get correct data for your postcode ({self._postcode}). check {API_URL} to validate your arguments.")

        soup: BeautifulSoup = BeautifulSoup(r.text, "html.parser")

        bin_tables = soup.find_all("table")
        if bin_tables == []:
            raise Exception(
                f"could not get valid data from ashford.gov.uk. is your UPRN ({self._uprn}) correct for postcode ({self._postcode})? check https://uprn.uk/{self._uprn} and {API_URL}")

        entries = []
        for bin_table in bin_tables:
            bin_text = bin_table.find(
                "td", id=re.compile("CollectionDayLookup2_td_"))
            if not bin_text:
                continue

            bin_type_soup = bin_text.find("b")

            if not bin_type_soup:
                continue
            bin_type: str = bin_type_soup.text.strip()

            date_soup = bin_text.find("span", id=re.compile(r"CollectionDayLookup2_Label_\w*_Date"))
            if not date_soup or not " " in date_soup.text.strip():
                continue
            date_str: str = date_soup.text.strip()
            try:
                date = datetime.strptime(
                    date_str.split(" ")[1], "%d/%m/%y").date()

            except ValueError:
                continue

            icon = ICON_MAP.get(bin_type.split("(")[0].strip().lower())
            entries.append(Collection(date=date, t=bin_type, icon=icon))

        return entries
