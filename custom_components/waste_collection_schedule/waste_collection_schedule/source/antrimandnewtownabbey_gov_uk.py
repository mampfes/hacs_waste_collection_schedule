import logging
import re
from datetime import date, datetime, timedelta

import requests
from bs4 import BeautifulSoup, Tag
from dateutil.parser import parse
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

_LOGGER = logging.getLogger(__name__)

TITLE = "Antrim and Newtownabbey"
DESCRIPTION = "Source for Antrim and Newtownabbey."
URL = "https://antrimandnewtownabbey.gov.uk"
TEST_CASES = {
    "uprn + id": {"id": 1456, "uprn": 185354344},
    "uprn": {"uprn": "185405500"},
    "id_str": {"id": "1145"},
}


ICON_MAP = {
    "Black bins": "mdi:trash-can",
    "Brown bins": "mdi:leaf",
    "Kerbside Recycling": "mdi:recycle",
}


REGULAR_API_URL = (
    "https://antrimandnewtownabbey.gov.uk/residents/bins-recycling/bins-schedule/"
)
RECYCLING_API_URL = "https://www.brysonrecycling.org/northern-ireland/kerbside-collections/collection-day"
RECYCLING_HOLYDAY_API_URL = "https://www.brysonrecycling.org/northern-ireland/kerbside-collections/bank-holidays/"

REGEX_REMOVE_TH_ND_RD_ST = r"(?<=\d)(st|nd|rd|th)"


FREQUENCY_MAP = {
    "every week": 7,
    "every fortnight": 14,
    "fortnightly": 14,
}


class Source:
    def __init__(self, id: int | None = None, uprn: str | int | None = None):
        self._id: int | None = id
        self._uprn: str | int | None = uprn
        if id is None and uprn is None:
            raise ValueError("This source cannot do anything without an id or uprn")

        self._bank_holday_move: dict[date, date] | None = None

    def fetch(self) -> list[Collection]:
        entries = []
        if self._id is not None:
            entries = self.fetch_regular()
        if self._uprn is not None:
            entries += self.fetch_recycling()
        return entries

    def fetch_bank_holidays(self):
        r = requests.get(RECYCLING_HOLYDAY_API_URL)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        table = soup.select_one("table#bank-holidays")
        if not table:
            raise ValueError("No bank holidays table found")
        rows = table.select("tr")
        councils = rows[0].select("th")[1:]
        council_idx = None
        for id, council in enumerate(councils):
            if council.text.lower().strip().startswith("antrim and newtownabbey"):
                council_idx = id
                break
        if council_idx is None:
            raise ValueError("No council found")

        bank_holidays = {}
        for row in rows[1:]:
            cols = row.select("td")
            date_td = cols[0]
            date_ = None
            for p in date_td.select("p"):
                date_text = p.text.strip()
                date_text = re.sub(REGEX_REMOVE_TH_ND_RD_ST, "", date_text)
                try:
                    date_ = parse(date_text, default=datetime.now()).date()
                    if date_ < datetime.now().date():
                        date_.replace(year=date_.year + 1)
                    break
                except ValueError:
                    pass
            if date_ is None:
                raise ValueError("No date found")

            replace_date_td = cols[1 + council_idx]
            if "No Collection" not in replace_date_td.text:
                continue
            raplace_date_str = replace_date_td.text.strip().split(
                "Alternative collection"
            )[1]

            try:
                raplace_date = parse(raplace_date_str, default=datetime.now()).date()
                if raplace_date < datetime.now().date():
                    raplace_date.replace(year=raplace_date.year + 1)
                bank_holidays[date_] = raplace_date
            except ValueError:
                raise
        self._bank_holday_move = bank_holidays

    def fetch_recycling(self) -> list[Collection]:
        if self._uprn is None:
            raise ValueError("No uprn provided")

        if self._bank_holday_move is None:
            try:
                self.fetch_bank_holidays()
            except Exception:
                pass
        params = {
            "uprn": f"NI{self._uprn}",
            "district": "newtownabbey",
            "submit": "",
        }
        r = requests.get(RECYCLING_API_URL, params=params)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        divs = soup.select("div.recyling-food")
        entries: list[Collection] = []
        for div in divs:
            bin_type_tag = div.select_one("h2")
            if not bin_type_tag:
                continue
            bin_type = bin_type_tag.text.strip()
            icon = ICON_MAP.get(bin_type)

            frequency_p = div.select_one("p")
            frequency_days: int | None = None
            if not frequency_p:
                continue
            frequency_strong = frequency_p.select_one("strong")
            frequency = frequency_strong.text.strip() if frequency_strong else None

            if frequency and frequency.lower() in FREQUENCY_MAP:
                frequency_days = FREQUENCY_MAP[frequency.lower()]
            else:
                if frequency:
                    _LOGGER.warning(f"Unknown frequency: {frequency}")

            next_date_p = frequency_p.find_next_sibling("p")
            if not isinstance(next_date_p, Tag):
                continue
            next_date_strong = next_date_p.select_one("strong")
            if not next_date_strong:
                continue
            next_date_str = next_date_strong.text.strip()
            # Tuesday 13th August 2024
            next_date_str = re.sub(REGEX_REMOVE_TH_ND_RD_ST, "", next_date_str)
            # Tuesday 13 August 2024
            next_date = datetime.strptime(next_date_str, "%A %d %B %Y").date()
            moved_date = (self._bank_holday_move or {}).get(next_date, next_date)

            entries.append(Collection(date=moved_date, t=bin_type, icon=icon))
            if frequency_days:
                for i in range(1, 20):
                    d = next_date + timedelta(days=frequency_days * i)
                    moved = (self._bank_holday_move or {}).get(d, d)
                    entries.append(Collection(date=moved, t=bin_type, icon=icon))
        return entries

    def fetch_regular(self) -> list[Collection]:
        if self._id is None:
            raise ValueError("No id provided")

        args = {
            "Id": self._id,
            "size": 20,
        }

        r = requests.get(REGULAR_API_URL, params=args)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")

        collection_divs = soup.select("div.feature-box.bins")
        if not collection_divs:
            raise Exception("No collections found")

        entries = []
        for collection_div in collection_divs:
            date_p = collection_div.select_one("p.date")
            if not date_p:
                continue

            # Thu 22 Aug, 2024
            date_ = datetime.strptime(date_p.text.strip(), "%a %d %b, %Y").date()
            bins = collection_div.select("li")
            if not bins:
                continue
            for bin in bins:
                if not bin.text.strip():
                    continue
                bin_type = bin.text.strip()
                icon = ICON_MAP.get(bin_type)
                entries.append(Collection(date=date_, t=bin_type, icon=icon))
        return entries
