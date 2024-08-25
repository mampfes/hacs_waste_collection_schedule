import datetime

from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.SSLError import get_legacy_session

# Include work around for SSL UNSAFE_LEGACY_RENEGOTIATION_DISABLED error

TITLE = "Auckland Council"
DESCRIPTION = "Source for Auckland council."
URL = "https://aucklandcouncil.govt.nz"
TEST_CASES = {
    "429 Sea View Road": {"area_number": "12342453293"},  # Monday
    "8 Dickson Road": {"area_number": 12342306525},  # Thursday
    "with Food Scraps": {"area_number": 12341998652},
    "3 Andrew Road": {"area_number": "12345375455"},  # friday with foodscraps
}

MONTH = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12,
}


def toDate(formattedDate):
    items = formattedDate.split()
    return datetime.date(int(items[3]), MONTH[items[2]], int(items[1]))


HEADER = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
}


class Source:
    def __init__(
        self,
        area_number,
    ):
        self._area_number = area_number

    def fetch(self):
        # get token
        params = {"an": self._area_number}

        # Updated request using SSL code snippet
        r = get_legacy_session().get(
            "https://www.aucklandcouncil.govt.nz/rubbish-recycling/rubbish-recycling-collections/Pages/collection-day-detail.aspx",
            params=params,
            headers=HEADER,
            # verify=False,
        )

        soup = BeautifulSoup(r.text, features="html.parser")

        # find the household block - top section which has a title of "Household collection"

        household = soup.find("div", id=lambda x: x and x.endswith("HouseholdBlock2"))

        # grab all the date blocks
        collections = household.find_all("h5", class_="collectionDayDate")

        entries = []

        for item in collections:
            # find the type - its on the icon
            rubbishType = None
            for rubbishTypeSpan in item.find_all("span"):
                if rubbishTypeSpan.has_attr("class"):
                    spanType = rubbishTypeSpan["class"][0]
                    if spanType.startswith("icon-"):
                        rubbishType = spanType[5:]

            # the date is a bold tag in the same block
            foundDate = item.find("strong").text

            todays_date = datetime.date.today()
            # use current year, unless Jan is in data, and we are still in Dec
            year = todays_date.year
            if "January" in foundDate and todays_date.month == 12:
                # then add 1
                year = year + 1
            fullDate = foundDate + " " + f"{year}"

            entries.append(Collection(toDate(fullDate), rubbishType))

        return entries
