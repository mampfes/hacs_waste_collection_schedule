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

        key = None
        for k in keys:
            if k.text.strip().startswith("Key:"):
                key = k
                break



        # Map all unique non-background fill colors to their bin names
        if key:
            svg_titles = key.find_all("svg")
            for svg in svg_titles:
                title_tag = svg.find("title")
                if not (title_tag and title_tag.text):
                    continue
                bin_name = title_tag.text.strip()
                fills = set()
                for path in svg.find_all("path"):
                    fill = path.get("fill")
                    if fill and fill.lower() not in ("#ffffff", "#000000"):
                        fills.add(fill)
                for fill in fills:
                    self._bin_type_translation[fill] = bin_name

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

                    # Look for svg in the cell (new style)
                    svg = td.find("svg")
                    if svg:
                        # Find the first path with a fill attribute that is not #FFFFFF (background)
                        path = None
                        for p in svg.find_all("path"):
                            if p.has_attr("fill") and p["fill"].lower() != "#ffffff":
                                path = p
                                break
                        if path and path.has_attr("fill"):
                            fill = path["fill"]
                            bin_name = self._bin_type_translation.get(fill)
                            if bin_name:
                                day += 1
                                entries.append(
                                    Collection(
                                        date=datetime.strptime(f"{day} {month_year}", "%d %B %Y").date(),
                                        t=bin_name,
                                        icon=ICON_MAP.get(bin_name.split()[0].lower()),
                                    )
                                )
        return entries


