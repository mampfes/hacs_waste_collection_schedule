from datetime import date, datetime

import requests
from bs4 import BeautifulSoup, Tag
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Ards and North Down Borough Council"
DESCRIPTION = "Source for Ards and North Down Borough Council."
URL = "https://ardsandnorthdown.gov.uk"
TEST_CASES = {
    "185833845": {"uprn": 185833845},
    "187340776": {"uprn": "185928695"},
    "185180798": {"uprn": 185180798},
}


ICON_MAP = {
    "grey": "mdi:trash-can",
    "glass": "mdi:bottle-soda",
    "green": "mdi:leaf",
    "blue": "mdi:recycle",
}


API_URL = "https://collections-ardsandnorthdown.azurewebsites.net/WSCollExternal.asmx"

# council seems to always be ARD no matter what the old council was
PAYLOAD = """<?xml version="1.0" encoding="utf-8" ?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:xsd="http://www.w3.org/2001/XMLSchema"
    xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Body>
        <getRoundCalendarForUPRN  xmlns="http://webaspx-collections.azurewebsites.net/">
            <council>ARD</council>
            <UPRN>{uprn}</UPRN>
            <from>Chtml</from>
        </getRoundCalendarForUPRN >
    </soap:Body>
</soap:Envelope>
"""


class Source:
    def __init__(self, uprn: str | int):
        self._payload = PAYLOAD.format(uprn=str(uprn).strip())

    def fetch(self) -> list[Collection]:
        # get json file
        r = requests.post(
            API_URL,
            data=self._payload,
            headers={"Content-Type": "text/xml; charset=utf-8"},
        )
        r.raise_for_status()

        # xml parser
        entries: list[Collection] = []
        # html unescape text
        text = (
            (r.text.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&"))
            .split("<getRoundCalendarForUPRNResult>")[-1]
            .split("</getRoundCalendarForUPRNResult>")[0]
        )

        soup = BeautifulSoup(text, "html.parser")
        # find b where text start with Key:

        self._bin_type_translation: dict[str, str] = {}

        keys = soup.find_all("b")

        for k in keys:
            if k.text.strip().startswith("Key:"):
                key = k
                break

        for k in key:
            if not isinstance(k, Tag) or k.name != "img":
                continue

            if k.attrs["src"].endswith(".png"):
                id = k.attrs["src"].split("-")[-1].split(".")[0]
                self._bin_type_translation[id] = k.attrs["alt"]

        calendar = soup.find("div", {"id": "NewCalendar"})
        if not isinstance(calendar, Tag):
            raise Exception("No calendar found")

        for table in calendar.find_all("table"):
            month_year = table.find("th").text
            day = 0
            for tr in table.find_all("tr"):
                for td in tr.find_all("td"):
                    if td.text.strip().isdigit():
                        day = int(td.text.strip())
                        continue

                    if img := td.find("img"):
                        day += 1
                        entries.extend(
                            self._get_collections_by_id(
                                img.attrs.get("alt"),
                                datetime.strptime(
                                    f"{day} {month_year}", "%d %B %Y"
                                ).date(),
                            )
                        )

        return entries

    def _get_collections_by_id(self, id: str, date: date) -> list[Collection]:
        id_int = int(id, 2)
        collections = []
        for k, v in self._bin_type_translation.items():
            if id_int & int(k, 2) != 0:
                collections.append(
                    Collection(date=date, t=v, icon=ICON_MAP.get(v.split()[0].lower()))
                )
        return collections
