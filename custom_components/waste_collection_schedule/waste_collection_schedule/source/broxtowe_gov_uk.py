import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from bs4 import BeautifulSoup, NavigableString, Tag
import datetime


TITLE = "Broxtowe Borough Council"
DESCRIPTION = "Source for Broxtowe Borough Council."
URL = "https://www.broxtowe.gov.uk/"
TEST_CASES = {
    "100031343805 NG9 2NL": {"uprn": 100031343805, "postcode": "NG9 2NL"},
    "100031514955 NG9 4DU": {"uprn": " 100031308988", "postcode": "NG9 4DU"},
    "U100031514955 NG9 4DU": {"uprn": "U100031308988 ", "postcode": "NG9 4DU"}

}


ICON_MAP = {
    "BLACK": "mdi:trash-can",
    "GLASS": "mdi:bottle-soda",
    "GREEN": "mdi:leaf",
}


API_URL = "https://selfservice.broxtowe.gov.uk/renderform.aspx?t=217&k=9D2EF214E144EE796430597FB475C3892C43C528"


POSTCODE_ARGS = {
    "ctl00$ScriptManager1": "ctl00$ContentPlaceHolder1$APUP_5683|ctl00$ContentPlaceHolder1$FF5683BTN",
    "__EVENTTARGET": "ctl00$ContentPlaceHolder1$FF5683BTN",
    "__ASYNCPOST": "true",
}

UPRN_ARGS = {
    "ctl00$ScriptManager1": "ctl00$ContentPlaceHolder1$APUP_5683|ctl00$ContentPlaceHolder1$FF5683DDL",
    "__EVENTTARGET": "ctl00$ContentPlaceHolder1$FF5683DDL",
    "__ASYNCPOST": "true",
}

SUBMIT_ARGS = {
    "__EVENTTARGET": "ctl00$ContentPlaceHolder1$btnSubmit",
}


class Source:
    def __init__(self, uprn: str | int, postcode: str):
        self._uprn: str = str(uprn).strip()
        if self._uprn[0].upper() == "U":
            self._uprn = self._uprn[1:].strip()

        self._postcode: str = str(postcode)
        self._uprn_args = UPRN_ARGS.copy()
        self._postcode_args = POSTCODE_ARGS.copy()
        self._submit_args = SUBMIT_ARGS.copy()
        self._uprn_args["ctl00$ContentPlaceHolder1$FF5683DDL"] = f"U{self._uprn}"
        self._postcode_args["ctl00$ContentPlaceHolder1$FF5683TB"] = f"{self._postcode}"

    def __get_hidden_fiels(self, response: requests.Response, to_update: dict[str, str]):
        response.raise_for_status()
        r_list = response.text.split("|")

        if r_list[1] == "error":
            raise Exception("could not get valid data from ashford.gov.uk")

        indexes = [index for index, value in enumerate(
            r_list) if value == "hiddenField"]

        for index in indexes:
            key = r_list[index+1]
            value = r_list[index+2]
            to_update[key] = value

    def fetch(self):
        s = requests.Session()
        headers = {"User-Agent": "Mozilla/5.0"}
        s.headers.update(headers)

        r = s.get(API_URL)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        for key in ["__VIEWSTATE", "__VIEWSTATEGENERATOR", "__EVENTVALIDATION"]:
            search = soup.find(id=key)
            if not search or not isinstance(search, Tag):
                continue

            self._postcode_args[key] = search.attrs["value"]

        r = s.post(API_URL, data=self._postcode_args)
        r.raise_for_status()

        if "No addresses were found for the post code you entered." in r.text:
            raise Exception(
                "No addresses were found for the post code you entered.")

        self.__get_hidden_fiels(r, self._uprn_args)

        r = s.post(API_URL, data=self._uprn_args)
        r.raise_for_status()

        self.__get_hidden_fiels(r, self._submit_args)

        self._submit_args["ctl00$ContentPlaceHolder1$btnSubmit"] = "ctl00$ContentPlaceHolder1$btnSubmit"
        r = s.post(API_URL, data=self._submit_args)
        r.raise_for_status()

        if "No collection calendars are available for the selected property." in r.text:
            raise Exception(
                f"No collection calendars are available for the selected property. Make sure your address returns entries on the council website ({API_URL}).")

        soup = BeautifulSoup(r.text, "html.parser")

        table = soup.find("table", class_="bartec")

        if table == None or isinstance(table, NavigableString):
            raise Exception("could not get valid data from ashford.gov.uk")

        entries = []
        trs = table.find_all("tr")

        if not trs or len(trs) < 2:
            raise Exception("could not get valid data from ashford.gov.uk")

        for row in trs[1:]:
            bint_type = row.find("td")
            if not bint_type:
                continue

            bint_type = bint_type.text

            collections = row.find_all("td")
            if not collections or len(collections) < 2:
                continue
            collections = collections[2:]

            for collection in collections:
                date = datetime.datetime.strptime(
                    collection.text, "%A, %d %B %Y").date()
                icon = ICON_MAP.get(bint_type.split(" ")[0])  # Collection icon

                entries.append(Collection(date=date, t=bint_type, icon=icon))

        return entries
