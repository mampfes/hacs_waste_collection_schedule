from datetime import date, datetime, timedelta

import requests
from bs4 import BeautifulSoup
from dateutil.parser import ParserError
from dateutil.parser import parse as dateutil_parse
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.icons import Icons  # type: ignore[attr-defined]

TITLE = "Birmingham City Council"
DESCRIPTION = "Source for birmingham.gov.uk services for Birmingham, UK."
URL = "https://birmingham.gov.uk"
TEST_CASES = {
    "Cherry Tree Croft": {"uprn": 100070321799, "postcode": "B27 6TF"},
    "Victoria Road": {"uprn": 100070548572, "postcode": "B17 0AH"},
    "Windermere Road": {"uprn": "100070566109", "postcode": "B13 9JP"},
    "Park Hill": {"uprn": "100070475114", "postcode": "B13 8DS"},
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
}

API_URL = "https://www.birmingham.gov.uk/info/50388/check_your_collection_day"

ICON_MAP = {
    "Rubbish": Icons.GENERAL_WASTE,
    "Food": Icons.BIO_KITCHEN,
    "Mixed recycling": Icons.RECYCLING,
}


def _parse_collection_date(raw_date: str, today: datetime) -> date:
    """
    Parse a 'Weekday DD Month' table entry (year omitted).

    If we are in the last quarter of the year and the parsed month is in the first quarter, assume the date is in the next year.
    if we are in the first quarter of the year and the parsed month is in the last quarter, assume the date is in the previous year.
    """
    try:
        parsed = dateutil_parse(raw_date, default=today, fuzzy=True)
    except (ParserError, ValueError, OverflowError) as exc:
        raise ValueError(f"Could not parse collection date '{raw_date}'") from exc

    # handle year crossover
    if today.month >= 10 and parsed.month <= 3:
        parsed = parsed.replace(year=parsed.year + 1)
    elif today.month <= 3 and parsed.month >= 10:
        parsed = parsed.replace(year=parsed.year - 1)

    return parsed.date()


class Source:
    def __init__(self, uprn: str, postcode: str):
        self._uprn = uprn
        self._postcode = postcode

    def fetch(self):
        entries: list[Collection] = []

        params = {
            "postcode": self._postcode,
            "uprn": self._uprn,
            "next": "Next",
        }
        response = requests.get(API_URL, headers=HEADERS, params=params, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        if not (table := soup.find("table", class_="data-table")) or not table.tbody:
            raise ValueError(
                "Could not find collection schedule table - check UPRN/postcode "
                "or whether the council page structure has changed."
            )

        today = datetime.now()
        cutoff = today - timedelta(days=1)  # drop the just-completed row

        for table_row in table.tbody.find_all("tr"):
            cells = table_row.find_all(["th", "td"])
            if len(cells) < 2:
                continue

            raw_date = cells[0].text.strip()
            collection_type = cells[1].text.strip()

            collection_date = _parse_collection_date(raw_date, today)
            if collection_date < cutoff.date():
                continue

            entries.append(
                Collection(
                    date=collection_date,
                    t=collection_type,
                    icon=ICON_MAP.get(collection_type, Icons.GENERAL_WASTE),
                )
            )

        if not entries:
            raise ValueError(
                "Could not get collections for the given combination of UPRN and Postcode."
            )

        return entries
