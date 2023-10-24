import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from bs4 import BeautifulSoup, Tag
import datetime

TITLE = "Highland"
DESCRIPTION = "Source for Highland."
URL = "https://www.highland.gov.uk/"
TEST_CASES = {
    "Allangrange Mains Road, Black Isle": {"record_id": 2004443},
    "Kishorn, Wester Ross": {"record_id": "2005124"},
    "Quarry Lane, Tain": {"record_id": "2005420"},
}


ICON_MAP = {
    "refuse": "mdi:trash-can",
    "recycling": "mdi:recycle",
    "garden waste": "mdi:leaf",
}


API_URL = "https://www.highland.gov.uk/directory_record"


class Source:
    def __init__(self, record_id: str | int):
        self._record_id: str = str(record_id)

    def fetch(self):
        today = datetime.datetime.now().date()
        
        r = requests.get(f"{API_URL}/{self._record_id}/")
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        table = soup.find("ul", {"class": "data-table"})
        if table is None or isinstance(table, str):
            raise Exception(f"Content of the webpage seems to be invalid check {API_URL}/{self._record_id}/")
        rows:list[Tag] = table.find_all("li")

        entries = []
        for row in rows:
            if not "bin days" in row.text.lower():
                continue
            bin_type_heading = row.find("h2")
            if bin_type_heading is None:
                continue
            bin_type_text = bin_type_heading.text.lower().strip()
            
            if "bin days" == bin_type_text:
                bin_type = "Refuse"
            else:
                bin_type = bin_type_text.replace(
                    "bin days", "").strip().capitalize()

            dates = row.find("div")
            if dates is None:
                continue

            for date in dates.text.split(","):
                # Remove suffixes from date string
                date = date.replace("th", "").replace("st", "").replace(
                    "nd", "").replace("rd", "").strip()

                # Convert date string to datetime object
                try:
                    date_obj = datetime.datetime.strptime(date, "%A %d %B").date()
                    date_obj = date_obj.replace(year=today.year)
                    if date_obj < today:
                        date_obj = date_obj.replace(year=today.year + 1)
                    
                except ValueError:
                    continue

                # Create Collection object and append to entries list
                icon = ICON_MAP.get(bin_type.lower())
                entries.append(
                    Collection(
                        date=date_obj,
                        t=bin_type,
                        icon=icon
                    )
                )

        return entries
