import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from bs4 import BeautifulSoup
import re
import datetime


TITLE = "Rushcliffe Brough Council"
DESCRIPTION = "Source for Rushcliffe Brough Council."
URL = "https://www.rushcliffe.gov.uk/"
TEST_CASES = {
    "NG12 5FE 2 Church Drive, Keyworth, NOTTINGHAM, NG12 5FE": {
        "postcode": "NG12 5FE",
        "address": "2 Church Drive, Keyworth, NOTTINGHAM, NG12 5FE"
    }
}


ICON_MAP = {
    "grey": "mdi:trash-can",
    "garden waste": "mdi:leaf",
    "blue": "mdi:package-variant",
}


API_URL = "https://selfservice.rushcliffe.gov.uk/renderform.aspx?t=1242&k=86BDCD8DE8D868B9E23D10842A7A4FE0F1023CCA"


POST_POST_CODE_KEY = "ctl00$ContentPlaceHolder1$FF3518TB"
POST_POST_UPRN_KEY = "ctl00$ContentPlaceHolder1$FF3518DDL"

POST_ARGS = [
    {
        "ctl00$ScriptManager1": "ctl00$ContentPlaceHolder1$APUP_3518|ctl00$ContentPlaceHolder1$FF3518BTN",
        "__EVENTTARGET": "ctl00$ContentPlaceHolder1$FF3518BTN",
        "__EVENTARGUMENT": "",
        "__VIEWSTATEGENERATOR": "CA57E1E8",
        "ctl00$ContentPlaceHolder1$txtPositionLL": "",
        "ctl00$ContentPlaceHolder1$txtPosition": "",
        "ctl00$ContentPlaceHolder1$FF3518TB": "",  # Will be set later
        "__ASYNCPOST": "true",
        "": "",
    },
    {
        "ctl00$ScriptManager1": "ctl00$ContentPlaceHolder1$APUP_3518|ctl00$ContentPlaceHolder1$FF3518DDL",
        "ctl00$ContentPlaceHolder1$txtPositionLL": "",
        "ctl00$ContentPlaceHolder1$txtPosition": "",
        "ctl00$ContentPlaceHolder1$FF3518DDL": "",  # Will be set later
        "__EVENTTARGET": "ctl00$ContentPlaceHolder1$FF3518DDL",
        "__EVENTARGUMENT": "",
        "__LASTFOCUS": "",
        "__VIEWSTATEGENERATOR": "CA57E1E8",
        "__ASYNCPOST": "true",
        "": "",
    },
    {
        "ctl00$ContentPlaceHolder1$txtPositionLL": "",
        "ctl00$ContentPlaceHolder1$txtPosition": "",
        "__EVENTTARGET": "ctl00$ContentPlaceHolder1$btnSubmit",
        "__EVENTARGUMENT": "",
        "__LASTFOCUS": "",
        "__VIEWSTATEGENERATOR": "CA57E1E8",
    }

]


class Source:
    def __init__(self, postcode: str, address: str):
        self._postcode: str = postcode
        self._address: str = address

    def __compare(self, a: str, b: str) -> bool:
        a = a.strip().replace(" ", "").replace(",", "")
        b = b.strip().replace(" ", "").replace(",", "")
        return a.lower() == b.lower() or a.lower().startswith(b.lower()) or b.lower().startswith(a.lower())

    def __get_viewstate_and_validation(self, text: str) -> tuple[str, str]:
        if "__VIEWSTATE" not in text or "__EVENTVALIDATION" not in text:
            raise Exception("Invalid response")

        text_arr = text.split("|")
        viewstate_index = text_arr.index("__VIEWSTATE")
        event_val_index = text_arr.index("__EVENTVALIDATION")
        return (text_arr[viewstate_index+1], text_arr[event_val_index+1])

    def fetch(self):
        s = requests.Session()
        header = {"User-Agent": "Mozilla/5.0",
                  "Host": "selfservice.rushcliffe.gov.uk"}
        s.headers.update(header)

        r = s.get(API_URL)
        r.raise_for_status()

        args: dict[str, str] = POST_ARGS[0]
        args[POST_POST_CODE_KEY] = self._postcode

        soup = BeautifulSoup(r.text, "html.parser")

        viewstate = soup.find("input", {"name": "__VIEWSTATE"})
        validation = soup.find("input", {"name": "__EVENTVALIDATION"})

        if viewstate == None or not viewstate.get("value") or validation == None or not validation.get("value"):
            raise Exception("Invalid response")

        args["__VIEWSTATE"], args["__EVENTVALIDATION"] = viewstate.get(
            'value'), validation.get('value')

        r = s.post(API_URL, data=args)
        r.raise_for_status()

        args: dict[str, str] = POST_ARGS[1]
        args["__VIEWSTATE"], args["__EVENTVALIDATION"] = self.__get_viewstate_and_validation(
            r.text)

        for update in r.text.split("|"):
            if not update.startswith("<label"):
                continue
            soup = BeautifulSoup(update, "html.parser")
            if len(soup.find_all("option")) < 2:
                raise Exception("postcode not found")

            for option in soup.find_all("option"):
                if option["value"] in ("0", ""):
                    continue
                if self.__compare(option.text, self._address):
                    args[POST_POST_UPRN_KEY] = option["value"]
                    break

        if args[POST_POST_UPRN_KEY] == "":
            raise Exception("Address not found")

        r = s.post(API_URL, data=args)
        r.raise_for_status()

        args = POST_ARGS[2]
        args["__VIEWSTATE"], args["__EVENTVALIDATION"] = self.__get_viewstate_and_validation(
            r.text)

        r = s.post(API_URL, data=args)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        panel = soup.find("div", {"class": "ss_confPanel well well-sm"})
        if not panel:
            raise Exception("No data found")

        lines: str = str(panel).replace("<b>", "").replace("</b>", "")
        entries = []

        for line in lines.split("<br/>"):
            line = line.strip()
            if not line.startswith("Your"):
                continue
            bin_type = line[4:line.find("bin")].strip()
            date = re.search(r"\d{2}/\d{2}/\d{4}", line)
            if not date:
                continue
            date = date.group(0)

            date = datetime.datetime.strptime(date, "%d/%m/%Y").date()
            icon = ICON_MAP.get(bin_type)  # Collection icon
            entries.append(Collection(date=date, t=bin_type, icon=icon))

        return entries
