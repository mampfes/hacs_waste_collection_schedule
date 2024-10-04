import requests
from bs4 import BeautifulSoup
from dateutil.parser import parse
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Rochdale Borough Council"
DESCRIPTION = "Source for Rochdale Borough Council."
URL = "https://www.rochdale.gov.uk/"
TEST_CASES = {
    "144 Claybank Street, Heywood": {"postcode": "OL104TJ", "uprn": 10094359340},
    "OL12 7TX 23030658": {"postcode": "OL12 7TX", "uprn": "23030658"},
}


ICON_MAP = {
    "Food": "mdi:leaf",
    "Paper": "mdi:package-variant",
    "Rubbish": "mdi:trash-can",
    "Cans": "mdi:bottle-soda",
}


API_URL = "https://webforms.rochdale.gov.uk/BinCalendar"


class Source:
    def __init__(self, postcode: str, uprn: str | int):
        self._postcode: str = postcode.replace(" ", "").upper()
        self._uprn: str | int = uprn

    def fetch(self) -> list[Collection]:
        data = {
            "FormTypeId": "2",
            "Step": "2",
            "PostCode": self._postcode,
            "SelectedUprn": self._uprn,
        }

        r = requests.post(API_URL, data=data)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        table = soup.select_one("table#tblCollectionDetails")
        if not table:
            # ERROR STATE: Check if the postcode or UPRN is invalid
            uprn_options = list(soup.select("select#SelectedUprn > option"))
            uprn_options = list(
                filter(
                    lambda option: option.attrs.get("value")
                    and option.attrs["value"].isdigit(),
                    uprn_options,
                )
            )
            if not uprn_options:
                raise SourceArgumentNotFound("postcode", self._postcode)
            uprns = [option.attrs["value"] for option in uprn_options]
            raise SourceArgumentNotFoundWithSuggestions("uprn", self._uprn, uprns)

        body = table.select_one("tbody")
        if not body:
            raise Exception("Could not find Collection table body")

        entries = []
        for row in body.select("tr"):
            date = None
            for idx, cell in enumerate(row.select("th, td")):
                if idx == 0:  # Date Column
                    date = parse(cell.text, dayfirst=True).date()
                coll_type_div = cell.select_one("div")
                if not coll_type_div or date is None:
                    continue
                coll_type = coll_type_div.attrs.get("data-label")
                if not isinstance(coll_type, str):
                    continue
                icon = ICON_MAP.get(coll_type.split()[0])

                entries.append(Collection(date=date, t=coll_type, icon=icon))

        return entries
