import datetime
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.SSLError import get_legacy_session

TITLE = "Auckland Council"
DESCRIPTION = "Source for Auckland council."
URL = "https://new.aucklandcouncil.govt.nz"

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


def toDate(formattedDate, year=None):
    # formattedDate looks like "Wednesday, 8 October"
    parts = formattedDate.replace(",", "").split()
    # ["Wednesday", "8", "October"]
    day = int(parts[1])
    month = MONTH[parts[2]]
    if year is None:
        today = datetime.date.today()
        year = today.year
        # Handle December rollover into January
        if month == 1 and today.month == 12:
            year += 1
    return datetime.date(year, month, day)


HEADER = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
}


class Source:
    def __init__(self, area_number):
        self._area_number = str(area_number)

    def fetch(self):
        url = f"https://new.aucklandcouncil.govt.nz/en/rubbish-recycling/rubbish-recycling-collections/rubbish-recycling-collection-days/{self._area_number}.html"
        r = get_legacy_session().get(url, headers=HEADER)

        soup = BeautifulSoup(r.text, "html.parser")
        entries = []

        # Each collection line looks like:
        # <p class="mb-0 lead"><span ...><i class="acpl-icon rubbish"></i>...<b>Wednesday, 8 October</b></span></p>
        for p in soup.find_all("p", class_="mb-0 lead"):
            icon = p.find("i", class_=lambda x: x and x.startswith("acpl-icon"))
            date_tag = p.find("b")

            if not icon or not date_tag:
                continue

            # Extract type (e.g. "rubbish", "recycle", "food-waste")
            classes = icon.get("class", [])
            rubbish_type = None
            for c in classes:
                if c != "acpl-icon":
                    rubbish_type = c
                    break

            # Extract date
            date_str = date_tag.text.strip()
            collection_date = toDate(date_str)

            entries.append(Collection(collection_date, rubbish_type))

        return entries
