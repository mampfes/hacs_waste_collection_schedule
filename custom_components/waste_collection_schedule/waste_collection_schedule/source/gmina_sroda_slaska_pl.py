import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequired,
)

TITLE = "Gmina Środa Śląska"
DESCRIPTION = "Source for Gmina Środa Śląska, Poland"
URL = "https://srodowisko.srodaslaska.pl/gospodarka-odpadami/harmonogram-odbioru-odpadow-komunalnych/"
COUNTRY = "pl"

BASE_URL = "https://www.com-d.pl"
SCHEDULE_URL = f"{BASE_URL}/komunalne/harm/sroda-slaska"

TEST_CASES = {
    "Szczepanów": {"location": "szczepanow"},
    "Środa Śląska I rejon": {"location": "sroda-slaska-i-rejon"},
    "Ciechów": {"location": "ciechow"},
}

ICON_MAP = {
    "1xmc-odpady-szklo": Icons.GLASS,
    "inne-odpady-rozne": Icons.TEXTILE,
    "inne-odpady-zbiorki": Icons.BULKY,
    "inne-odpady-papier": Icons.PAPER,
    "t-odpady-biodegradowalne": Icons.ORGANIC,
    "t-odpady-zmieszane": Icons.GENERAL_WASTE,
    "tp-odpady-metaletworzywa": Icons.RECYCLING,
}

TYPE_MAP = {
    "1xmc-odpady-szklo": "Szkło",
    "inne-odpady-rozne": "Tekstylia i odzież",
    "inne-odpady-zbiorki": "Odpady wielkogabarytowe",
    "inne-odpady-papier": "Papier",
    "t-odpady-biodegradowalne": "Odpady biodegradowalne",
    "t-odpady-zmieszane": "Zmieszane odpady komunalne",
    "tp-odpady-metaletworzywa": "Metale i tworzywa sztuczne",
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Visit https://www.com-d.pl/komunalne/harm/sroda-slaska, select your locality or Środa Śląska district, and enter the final part of its URL.",
}

PARAM_TRANSLATIONS = {
    "en": {
        "location": "Location",
        "location_id": "Location ID (obsolete)",
    },
    "de": {
        "location": "Ort",
        "location_id": "Orts-ID (veraltet)",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "location": "Locality or district URL slug from the COM-D schedule page",
        "location_id": "No longer supported, use 'location' instead",
    },
    "de": {
        "location": "URL-Kürzel des Ortes bzw. Stadtteils von der COM-D Abfuhrplan-Seite",
        "location_id": "Wird nicht mehr unterstützt, bitte stattdessen 'location' verwenden",
    },
}

HOW_TO_GET_LOCATION = (
    f"open {SCHEDULE_URL}, select your locality or Środa Śląska district and use the "
    "last part of its URL"
)
LEGACY_ARGUMENT_REASON = (
    "the waste collection provider changed, so the old 'location_id' groups no longer "
    f"exist; {HOW_TO_GET_LOCATION}"
)


def _get_locations(session: requests.Session) -> list[str]:
    """Return all locality/district slugs published by COM-D."""
    response = session.get(SCHEDULE_URL, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    return sorted(
        {
            link["href"].rsplit("/", 1)[-1]
            for link in soup.find_all("a", href=True)
            if "sroda-slaska/" in link["href"]
        }
    )


class Source:
    def __init__(
        self, location: str | None = None, location_id: str | int | None = None
    ):
        # location_id was used by the previous provider. Its values grouped several
        # localities together and cannot be mapped to a COM-D location automatically,
        # so existing configurations get a helpful message instead of a TypeError.
        if not location:
            raise SourceArgumentRequired(
                "location",
                LEGACY_ARGUMENT_REASON
                if location_id is not None
                else HOW_TO_GET_LOCATION,
            )
        self._location: str = location

    def fetch(self) -> list[Collection]:
        session = requests.Session()

        response = session.get(f"{SCHEDULE_URL}/{self._location}", timeout=30)
        if response.status_code == 404:
            raise SourceArgumentNotFoundWithSuggestions(
                "location", self._location, _get_locations(session)
            )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        schedule_table = next(
            (
                table
                for table in soup.find_all("table")
                if table.find("th", string="Frakcja")
            ),
            None,
        )
        if schedule_table is None:
            raise ValueError(
                "Could not find a collection schedule for the location "
                f"'{self._location}' at {SCHEDULE_URL}/{self._location}. "
                "The website layout may have changed."
            )

        category_urls = {
            link["href"] for link in schedule_table.select('a[href*="/sroda-slaska/"]')
        }

        entries: list[Collection] = []
        seen = set()

        for category_url in sorted(category_urls):
            category = category_url.rsplit("/", 1)[-1]
            category_response = session.get(f"{BASE_URL}{category_url}", timeout=30)
            category_response.raise_for_status()
            category_soup = BeautifulSoup(category_response.text, "html.parser")

            for collection_day in category_soup.select("td.highlighted[data-date]"):
                collection_date = datetime.datetime.strptime(
                    collection_day["data-date"], "%Y-%m-%d"
                ).date()
                entry = (collection_date, category)
                if entry in seen:
                    continue
                seen.add(entry)
                entries.append(
                    Collection(
                        date=collection_date,
                        t=TYPE_MAP.get(category, category.capitalize()),
                        icon=ICON_MAP.get(category),
                    )
                )

        return entries
