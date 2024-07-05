import logging
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

_LOGGER = logging.getLogger(__name__)

TITLE = "Solihull Council"
DESCRIPTION = "Source for Solihull Council."
URL = "https://www.denbighshire.gov.uk/"
TEST_CASES = {
    "100070994046": {"uprn": 100070994046},
    "200003821723, Predict": {"uprn": 200003821723, "predict": True},
}

ICON_MAP = {
    "garden waste": "mdi:leaf",
    "household waste": "mdi:trash-can",
    "mixed recycling": "mdi:recycle",
}

API_URL = "https://digital.solihull.gov.uk/BinCollectionCalendar/Calendar.aspx"


class Source:
    def __init__(self, uprn: str | int, predict: bool = False):
        self._uprn: str | int = uprn
        self._predict = predict

    def fetch(self) -> list[Collection]:
        params = {"UPRN": self._uprn}
        r = requests.get(API_URL, params=params)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")

        entries = []
        for card in soup.find_all("div", class_="card-title"):
            bin_type_tag = card.find("h5") or card.find("h4")
            bin_type = bin_type_tag.text
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
                        if not (
                            "every other week" in freq_str.text.lower()
                            or "every week" in freq_str.text.lower()
                        ):
                            _LOGGER.info(
                                f"Skipping predikt (unknown frequency) for {freq_str.text}"
                            )
                            continue

                        freq = 2 if "every other week" in freq_str.text.lower() else 1
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
                        pass

        return entries
