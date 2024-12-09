import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from bs4 import BeautifulSoup
import re
import datetime
import json


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
ADDRESS_LOOKUP = "https://selfservice.rushcliffe.gov.uk/core/addresslookup"
FORM = "https://selfservice.rushcliffe.gov.uk/renderform/Form"

POST_POST_UPRN_KEY="FF3518"

POST_ARGS = {
        "FormGuid":"aaa360e6-240e-46e9-b651-bd7fb8091354",
        "ObjectTemplateID":"1242",
        "Trigger":"submit",
        "CurrentSectionID":1397,
        "TriggerCtl":""
            }



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

        args: dict[str, str] = POST_ARGS

        soup = BeautifulSoup(r.text, "html.parser")

        RequestVerificationToken = soup.find("input", {"name": "__RequestVerificationToken"})

        if RequestVerificationToken == None or not RequestVerificationToken.get("value"):
            raise Exception("Invalid response")

        args["__RequestVerificationToken"] = RequestVerificationToken.get('value')

        r = s.post(ADDRESS_LOOKUP,data=dict(query=self._postcode,searchNlpg="True",
classification=""))

        adddresses=json.loads(r.text)

        args[POST_POST_UPRN_KEY] = next((key for key, value in adddresses.items() if value == self._address), None)
        
        if args[POST_POST_UPRN_KEY] == "":
            raise Exception("Address not found")

        args[POST_POST_UPRN_KEY+"lbltxt"]=self._address
        args[POST_POST_UPRN_KEY+"FF3518-text"]=self._postcode

        r = s.post(FORM, data=args)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        panel = soup.find("div", {"class": "ss_confPanel"})
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
