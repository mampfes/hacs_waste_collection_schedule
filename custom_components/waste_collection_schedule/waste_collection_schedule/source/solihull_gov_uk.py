import logging
import re
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]

_LOGGER = logging.getLogger(__name__)

TITLE = "Solihull Council"
DESCRIPTION = "Source for Solihull Council."
URL = "https://www.solihull.gov.uk/"
TEST_CASES = {
    "100070994046": {"uprn": 100070994046},
    "200003821723, Predict": {"uprn": 200003821723, "predict": True},
    "New Garden Waste Subscription Service": {"uprn": 100071011936},
}

ICON_MAP = {
    "food waste": Icons.BIO_KITCHEN,
    "garden waste": Icons.GARDEN,
    "garden waste - subscribed": Icons.GARDEN,
    "household waste": Icons.GENERAL_WASTE,
    "mixed recycling": Icons.RECYCLING,
}

API_URL = "https://digital.solihull.gov.uk/BinCollectionCalendar/Calendar.aspx"

# The site answers requests without a browser user agent with 404.
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
}


class Source:
    def __init__(self, uprn: str | int, predict: bool = False):
        self._uprn: str | int = uprn
        self._predict = predict

    def fetch(self) -> list[Collection]:
        params = {"UPRN": self._uprn}
        r = requests.get(API_URL, params=params, headers=HEADERS)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")

        entries = []
        for card in soup.find_all("div", class_="card-title"):
            bin_type_tag = card.find("h5") or card.find("h4")
            # "Household Waste", "Mixed Recycling", "Garden Waste" & "Garden Waste - Subscribed"
            bin_type = bin_type_tag.text
            # "Household Waste", "Mixed Recycling" & "Garden Waste"
            # bin_type = bin_type_tag.text.split(" - ")[0]
            icon = ICON_MAP.get(bin_type.lower())

            siblings = card.find_next_siblings("div", class_="mt-1")
            for sibling in siblings:
                date_tag = sibling.find("strong")
                if not date_tag:
                    continue
                date_str = date_tag.text
                # Wednesday, 19 June 2024
                try:
                    date = datetime.strptime(date_str, "%A, %d %B %Y").date()
                except ValueError:
                    _LOGGER.warning(f"Could not parse date {date_str}")
                    continue
                entries.append(Collection(date=date, t=bin_type, icon=icon))

                if "next" in sibling.text and self._predict:
                    try:
                        # card sibling with no class
                        freq_str = card.find_next_sibling()
                        freq_text = freq_str.text.strip().lower()
                        # "Collected on a Monday fortnightly." / "Collected on a Monday."
                        if (
                            "every other week" in freq_text
                            or "fortnightly" in freq_text
                        ):
                            freq = 2
                        elif "every week" in freq_text or re.fullmatch(
                            r"collected on an? \w+day\.?", freq_text
                        ):
                            freq = 1
                        else:
                            _LOGGER.info(
                                f"Skipping predict (unknown frequency) for {freq_str.text}"
                            )
                            continue

                        for i in range(1, 10 // freq):
                            entries.append(
                                Collection(
                                    date=date + timedelta(weeks=i * freq),
                                    t=bin_type,
                                    icon=icon,
                                )
                            )
                    except Exception as e:
                        _LOGGER.warning(f"Error predicting next collection: {e}")

        return entries
