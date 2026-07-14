from datetime import datetime

import requests
from bs4 import BeautifulSoup, Tag
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]

TITLE = "Ards and North Down Borough Council"
DESCRIPTION = "Source for Ards and North Down Borough Council."
URL = "https://ardsandnorthdown.gov.uk"
TEST_CASES = {
    "185833845": {"uprn": 185833845},
    "187340776": {"uprn": "185928695"},
    "185180798": {"uprn": 185180798},
}


ICON_MAP = {
    "grey": Icons.GENERAL_WASTE,
    "glass": Icons.GLASS,
    "green": Icons.ORGANIC,
    "blue": Icons.RECYCLING,
}


API_URL = (
    "https://ardsandnorthdownbincalendar.azurewebsites.net/api/calendarhtml/{uprn}"
)


class Source:
    def __init__(self, uprn: str | int):
        self._uprn = str(uprn).strip()

    def fetch(self) -> list[Collection]:
        r = requests.get(API_URL.format(uprn=self._uprn))
        r.raise_for_status()

        html = r.json().get("calendarHTML", "")

        entries: list[Collection] = []

        soup = BeautifulSoup(html, "html.parser")
        # find b/strong tag where text starts with "Key:"

        self._bin_type_translation: dict[str, str] = {}

        keys = soup.find_all(["b", "strong"])

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

                    svg = td.find("svg")
                    if svg:
                        day += 1
                        for p in svg.find_all("path"):
                            if not p.has_attr("fill"):
                                continue
                            fill = p["fill"]
                            if fill.lower() == "#ffffff":
                                continue
                            bin_name = self._bin_type_translation.get(fill)
                            if bin_name:
                                try:
                                    entries.append(
                                        Collection(
                                            date=datetime.strptime(
                                                f"{day} {month_year}", "%d %B %Y"
                                            ).date(),
                                            t=bin_name,
                                            icon=ICON_MAP.get(
                                                bin_name.split()[0].lower()
                                            ),
                                        )
                                    )
                                except ValueError:
                                    continue
        return entries
