from datetime import date, datetime

import requests
from bs4 import BeautifulSoup, Tag
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Mid and East Antrim"
DESCRIPTION = "Source for Mid and East Antrim Borough Council."
URL = "https://www.midandeastantrim.gov.uk"
TEST_CASES = {
    "185438838": {"uprn": 185438838},
    "185448385": {"uprn": "185448385"},
    "187262293": {"uprn": 187262293},
}


ICON_MAP = {
    "refuse": "mdi:trash-can",
    "garden": "mdi:leaf",
    "recycling": "mdi:recycle",
}


API_URL = "https://collections-midandeastantrim.azurewebsites.net/WSCollExternal.asmx"

PAYLOAD = """<?xml version="1.0" encoding="utf-8" ?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:xsd="http://www.w3.org/2001/XMLSchema"
    xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Body>
        <getRoundCalendarForUPRN  xmlns="http://webaspx-collections.azurewebsites.net/">
            <council>MidAndEastAntrim</council>
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
        r = requests.post(
            API_URL,
            data=self._payload,
            headers={"Content-Type": "text/xml; charset=utf-8"},
        )
        r.raise_for_status()

        entries: list[Collection] = []
        text = (
            r.text.replace("&lt;", "<").replace("&gt;", ">" ).replace("&amp;", "&")
            .split("<getRoundCalendarForUPRNResult>")[-1]
            .split("</getRoundCalendarForUPRNResult>")[0]
        )
        soup = BeautifulSoup(text, "html.parser")

        # Parse bin type translation from Key section (SVG icons)
        self._bin_type_translation: dict[str, str] = {}
        key_div = None
        for b in soup.find_all("b"):
            if b.text.strip().startswith("Key:"):
                key_div = b.parent
                break
        if key_div:
            for span in key_div.find_all("span"):
                svg = span.find("svg")
                if svg:
                    title = svg.find("title")
                    if title and title.text.strip():
                        # Use lowercased bin type as key
                        self._bin_type_translation[title.text.strip().lower()] = title.text.strip()

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

                    # Look for SVG icon in cell
                    svg = td.find("svg")
                    if svg:
                        title = svg.find("title")
                        if title and title.text.strip():
                            bin_type = title.text.strip().lower()
                            date_obj = datetime.strptime(f"{day} {month_year}", "%d %B %Y").date()
                            entries.append(
                                Collection(
                                    date=date_obj,
                                    t=self._bin_type_translation.get(bin_type, bin_type.title()),
                                    icon=ICON_MAP.get(bin_type)
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
