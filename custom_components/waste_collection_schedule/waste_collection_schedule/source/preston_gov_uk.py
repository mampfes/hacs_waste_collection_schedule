from datetime import datetime,date
from typing import Optional
from requests import Session
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Preston City Council"
DESCRIPTION = "Source for preston.gov.uk services for Preston City Council, UK."
URL = "https://preston.gov.uk"
SRV_URL = "https://selfservice.preston.gov.uk/service/Forms/FindMyNearest.aspx?Service=bins"

TEST_CASES = {
    "Test_001": {"street": "town hall, lancaster road"},
    "Test_002": {"street": "", "uprn": "10002220003"},
}

ICON_MAP = {
    "Commercial -  general waste:": "mdi:trash-can",
    "Commercial -  cardboard and paper:": "mdi:note-text",
    "Commercial - plastic cans and glass:": "mdi:recycle",
    "Black/grey bin (general waste):": "mdi:trash-can",
    "Yellow lidded recycling container (glass/cans/plastics):": "mdi:recycle",
    "Red lidded recycling container (paper/card):": "mdi:note-text",
    "Brown bin (garden waste):": "mdi:leaf",
}

HEADER_MAP = {
    "Commercial -  general waste:": "General Waste (Commercial)",
    "Commercial -  cardboard and paper:": "Cardboard (Commercial)",
    "Commercial - plastic cans and glass:": "Plastic (Commercial)",
    "Black/grey bin (general waste):": "General Waste (Black/Grey bin)",
    "Yellow lidded recycling container (glass/cans/plastics):": "Glass/Cans/Plastics (Yellow bin)",
    "Red lidded recycling container (paper/card):": "Cardboard/Paper (Red bin)",
    "Brown bin (garden waste):": "Garden/Green Waste (Brown bin)",
}

PARAMS = {
    "__VIEWSTATE": "",
    "__VIEWSTATEGENERATOR": "",
    "__EVENTVALIDATION": "",
    "__EVENTTARGET": "ctl00$MainContent$btnSearch",
    "__EVENTARGUMENT": "",
    "__LASTFOCUS": "",
    "__SCROLLPOSITIONX": "0",
    "__SCROLLPOSITIONY": "0",

    "ctl00$MainContent$hdnService": "bins",
    "ctl00$MainContent$hdnActivityId": "",
    "ctl00$MainContent$hdnPropertyEntityAddress": "",
    "ctl00$MainContent$hdnPropertyEntityValue": "",
    "ctl00$MainContent$txtAddress": "",
    "ctl00$MainContent$hdnUPRN": "",
}

class Source:
    def __init__(self, street = "", uprn = ""):
        self._street = street
        self._uprn = str(uprn)

    def _update_params(self, soup: BeautifulSoup) -> None:
        self._params = {k: v for k, v in PARAMS.items()}

        for k, v in PARAMS.items():
            try:
                self._params[k] = (soup.find("input", {"name": k})['value'])
            except KeyError:
                self._params[k] = ""
            except TypeError:
                self._params[k] = ""

        self._params["__EVENTTARGET"] = "ctl00$MainContent$btnSearch"
        self._params["ctl00$MainContent$hdnService"] = "bins"
        self._params["ctl00$MainContent$txtAddress"] = self._street
        self._params["ctl00$MainContent$hdnUPRN"] = self._uprn

    def fetch(self):
        return self._get()

    def _get(self):
        #
        # Initial fetch to get session information
        #
        session = Session()

        r0 = session.get(SRV_URL)
        r0.raise_for_status()
        r0_bs4 = BeautifulSoup(r0.text, features="html.parser")
        self._update_params(r0_bs4)

        #
        # Post with Street
        #
        r1 = session.post(SRV_URL, data=self._params)
        r1.raise_for_status()
        bs = BeautifulSoup(r1.text, features="html.parser")

        return self._parse(bs)

    @staticmethod
    def _entries(entries, header: str, date_obj: date, ico: Optional[str]):
        entries.append(Collection(t=header, date=date_obj, icon=ico))
        return entries

    @staticmethod
    def _date(date_string: str) -> Optional[date]:
        try:
            return datetime.strptime(date_string, "%A %d/%m/%Y").date()
        except ValueError:
            return None

    @staticmethod
    def _parse(bs):
        entries = []

        cnt = bs.select_one("span#MainContent_lblMoreCollectionDates")
        if not cnt:  # no tables in HTML means the address lookup failed
            raise Exception("Address lookup failed")

        for blk in cnt.find_all("div", {"id" : "container"}):
            headerSel = blk.select_one("ul > b")
            headerTxt = headerSel.text

            hdr = HEADER_MAP.get(headerTxt) or headerTxt
            ico = ICON_MAP.get(headerTxt)

            itms = blk.select("ul > li")
            for itm in itms:
                dateTxt = itm.select_one("span")
                dateObj = Source._date(dateTxt.text),
                if dateObj is None:
                    continue

                entries = Source._entries(entries, hdr, dateObj[0], ico)

        return entries
