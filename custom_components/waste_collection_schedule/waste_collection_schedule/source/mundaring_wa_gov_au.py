from datetime import datetime
from bs4 import BeautifulSoup
from dateutil.rrule import FR, MO, SA, SU, TH, TU, WE, DAILY, WEEKLY, YEARLY, rrule

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Shire of Mundaring"
DESCRIPTION = (
    "Source for mundaring.wa.gov.au services for teh Shire of Mundaring, Western Australia"
)
URL = "https://wwwhttps://www.mundaring.wa.gov.au/"
TEST_CASES = {
    "Test_001": {"parcel_number": 103239, "suburb": "Helena Valley"},
    # "Test_002": {"uprn": "100050188326"},
    # "Test_003": {"uprn": 100050199446},
}
ICON_MAP = {
    "FOGO Bin": "mdi:leaf",
    "Recycle Bin": "mdi:recycle",
    "General Waste": "mdi:trash-can",
    "Bulk Verge Collection": "mdi:sofa",
}
HEADERS = {
    "user-agent": "Mozilla/5.0",
}
DAYS = {
    "Monday": MO,
    "Tuesday": TU,
    "Wednesday": WE,
    "Thursday": TH,
    "Friday": FR,
    "Saturday": SA,
    "Sunday": SU,
}

class Source:
    def __init__(self, parcel_number: str | int, suburb:str):
        self._parcel_number = str(parcel_number)
        self._suburb = str(suburb).upper()

    def tidytext(self, lst:list) -> list:
        temp_list = [txt.replace("\r\n            ", "").replace("\r\n", "").strip() for txt in lst]
        return temp_list

    # def get_waste_type(txt:str) -> str:
    #     for waste in ICON_MAP:
    #         if waste in txt:
    #             temp_waste = waste
    #     return temp_waste


    def fetch(self):

        s = requests.Session()

        params = {
            "parcelNumber": self._parcel_number,
            "suburb": self._suburb
        }
        r = s.get("https://my.mundaring.wa.gov.au/BinLocationInfo/Info?", headers=HEADERS, params=params)
        r.raise_for_status()

        soup = BeautifulSoup(r.content.decode("utf-8"), "html.parser")
        pickups = soup.find_all("div", {"class": "form-group mb-3"})

        today = datetime.now()
        entries = []
        for pickup in pickups[1:]:
            details: list = self.tidytext(pickup.text.split(":"))
            for detail in details:
                # print(details, waste)
                if "FOGO Bin" in details[0]:
                    dt = list(rrule(WEEKLY, byweekday=DAYS[details[1]], dtstart=today,count=1))[0]
                    waste = "FOGO Bin"
                elif "Bulk" in details[0]:
                    dt = datetime.strptime(details[1], "%d %B %Y")
                    waste = "Bulk Verge Collection"
                else:
                    dt = datetime.strptime(details[1], "%d/%m/%Y")
                    if "Recycle" in details[0]:
                        waste = "Recycle Bin"
                    else:
                        waste = "General Waste"
            entries.append(
                Collection(
                    date=dt.date(),
                    t=waste,
                    icon=ICON_MAP.get(waste),
                )
            )
        
        return entries
