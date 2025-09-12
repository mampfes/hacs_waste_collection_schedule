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
            
            # Process the calendar grid row by row
            rows = table.find_all("tr")
            for row_idx, tr in enumerate(rows):
                cells = tr.find_all("td")
                
                # Skip header rows (day names like Mo, Tu, etc.)
                if any(cell.text.strip() in ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su'] for cell in cells):
                    continue
                
                for col_idx, td in enumerate(cells):
                    svgs = td.find_all("svg")
                    for svg in svgs:
                        # For SVG cells, we need to determine the day from calendar position
                        # A standard calendar has 7 columns (days of week)
                        # We need to find what day this position represents
                        
                        # Look for day numbers in nearby cells or previous rows to establish the pattern
                        day = None
                        
                        # Check current row for any day numbers
                        for check_cell in cells:
                            if check_cell.text.strip().isdigit():
                                # Found a day number in this row, calculate offset
                                found_day = int(check_cell.text.strip())
                                found_col = cells.index(check_cell)
                                day = found_day + (col_idx - found_col)
                                break
                        
                        # If no day found in current row, check previous rows
                        if day is None:
                            for prev_row_idx in range(row_idx - 1, -1, -1):
                                prev_row = rows[prev_row_idx]
                                prev_cells = prev_row.find_all("td")
                                if len(prev_cells) > col_idx:
                                    if prev_cells[col_idx].text.strip().isdigit():
                                        base_day = int(prev_cells[col_idx].text.strip())
                                        day = base_day + 7 * (row_idx - prev_row_idx)
                                        break
                        
                        if day and day > 0:
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
                                    try:
                                        entries.append(
                                            Collection(
                                                date=datetime.strptime(f"{day} {month_year}", "%d %B %Y").date(),
                                                t=bin_name,
                                                icon=ICON_MAP.get(bin_name.split()[0].lower()),
                                            )
                                        )
                                    except ValueError:
                                        # Invalid date, skip
                                        continue
        return entries


