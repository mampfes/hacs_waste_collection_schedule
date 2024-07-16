import logging
import re
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup, Tag
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

_LOGGER = logging.getLogger(__name__)

TITLE = "Stroud District Council"
DESCRIPTION = "Source for Stroud District Council."
URL = "https://stroud.gov.uk"
TEST_CASES = {"GL6+9BW 100120517945": {"postcode": "GL6 9BW", "uprn": 100120517945}}


ICON_MAP = {
    "rubbish": "mdi:trash-can",
    "food": "mdi:food",
    "recycling": "mdi:recycle",
    "garden": "mdi:leaf",
}


API_URL = "https://www.stroud.gov.uk/my-house"

# Wednesday 24 July 2024
DATE_REGEX = r"(\w+day) (\d{1,2}) (\w+) (\d{4})"


def make_bin_type_string(bin_type: str) -> str:
    return (
        bin_type.lower()
        .replace("next", "")
        .replace("collection date", "")
        .replace("collection", "")
        .strip()
        .capitalize()
    )


def get_icon(bin_type: str) -> str | None:
    return ICON_MAP.get(bin_type.split()[0].lower())


class Source:
    def __init__(self, postcode: str, uprn: str | int):
        self._postcode: str = postcode.strip()
        self._uprn: str = str(uprn).replace("+", " ")

    def _parse_date_in_title(self, bin_type: str) -> Collection:
        # Trash collection date
        match = re.match(DATE_REGEX, bin_type)
        if not match:
            raise ValueError(f"Could not parse bin type: {bin_type}")

        d = datetime.strptime(
            f"{match.group(4)}-{match.group(3)}-{match.group(2)}", "%Y-%B-%d"
        ).date()
        bin_type = bin_type.replace(match.group(0), "").strip()
        return Collection(date=d, t=bin_type, icon=get_icon(bin_type))

    def _parse_every(self, date_string: str, bin_type: str) -> list[Collection]:
        """Parse the date string for a bin type that is collected every week on a specific day.

        Args:
            date_string (str): should be in the format "every WEEKDAY"
            bin_type (str): the type of bin that is collected

        Raises:
            ValueError: if date_string has an invalid format
            ValueError: if the weekday is not a valid weekday

        Returns:
            list[Collection]
        """
        match = re.match(r"every (\w+)", date_string.lower())
        if not match:
            raise ValueError(
                f"Could not parse bin type: {bin_type} with date string: {date_string}"
            )
        weekday = match.group(1)

        next_date = datetime.now().date()
        found = False
        for _ in range(7):
            if next_date.strftime("%A").lower() == weekday.lower():
                found = True
                break
            next_date += timedelta(days=1)

        if not found:
            raise ValueError(f"Could not find weekday: {weekday} in next 7 days")

        entries = []
        for i in range(10):
            entries.append(
                Collection(
                    date=next_date + timedelta(weeks=i),
                    t=bin_type,
                    icon=get_icon(bin_type),
                )
            )
        return entries

    def _parse_entry(self, date_string: str, bin_type: str) -> list[Collection]:
        entries = []
        if date_string.lower().startswith("every"):
            entries += self._parse_every(date_string, bin_type)
            return entries

        # Wednesday 24 July 2024
        try:
            d = datetime.strptime(date_string, "%A %d %B %Y").date()
            entries.append(Collection(date=d, t=bin_type, icon=get_icon(bin_type)))
        except ValueError:
            try:
                entries += self._parse_date_in_title(bin_type)
            except ValueError:
                _LOGGER.warning(
                    f"Could not parse date: {date_string} for bin type: {bin_type}"
                )
        return entries

    def fetch(self) -> list[Collection]:
        params = {"postcode": self._postcode, "uprn": self._uprn}

        r = requests.get(API_URL, params=params)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        rubbish_panel = soup.select("section.panel-rubbish")
        if len(rubbish_panel) == 0:
            raise Exception(
                "No data found for this postcode and uprn (could not find panel-rubbish)"
            )

        lis = rubbish_panel[0].select("li")
        if len(lis) == 0:
            raise Exception(
                "No data found for this postcode and uprn (could not find any collection entries)"
            )

        entries = []
        for li in lis:
            bin_type_tag = li.find("h3")
            if not isinstance(bin_type_tag, Tag):
                strongs = li.select("strong")
                if len(strongs) < 2:
                    continue
                try:
                    entries += self._parse_entry(
                        strongs[1].text, make_bin_type_string(strongs[0].text)
                    )
                except ValueError:
                    pass
                continue

            bin_type = make_bin_type_string(bin_type_tag.text)
            date_string_tag = li.find("p")

            if not isinstance(date_string_tag, Tag):
                try:
                    entries += self._parse_date_in_title(bin_type)
                except ValueError:
                    _LOGGER.warning(
                        f"Could not parse bin type: {bin_type} did not find date string"
                    )
                continue

            date_string = date_string_tag.text
            entries += self._parse_entry(date_string, bin_type)

        return entries
