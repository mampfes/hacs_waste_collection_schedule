import logging
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentExceptionMultiple,
)

TITLE = "Derby City Council"
DESCRIPTION = "Source for Derby.gov.uk services for Derby City Council, UK."
URL = "https://derby.gov.uk"
TEST_CASES = {
    # Derby City council wants specific addresses, and they can't
    # be business addresses. Hopefully these are suitably generic..
    "22A Wood Road, Chaddesden, Derby, DE21 4LU": {
        # The flat above Bargain Hut on Wood Road
        "premises_id": "10010688168"
    },
    "Allestree Home Improvements, 512 Duffield Road, Derby, DE22 2DL": {
        "premises_id": "100030310335"
    },
}

ICON_MAP = {
    "Black bin": "mdi:trash-can",
    "Blue bin": "mdi:recycle",
    "Brown bin": "mdi:leaf",
}

_LOGGER = logging.getLogger(__name__)


PARAM_TRANSLATIONS = {
    "en": {
        "premises_id": "premises_id",
        "post_code": "DEPRECATED: post_code",
        "house_number": "DEPRECATED: house_number",
    }
}

PARAM_DESCRIPTIONS = {
    "en": {
        "post_code": "LEAVE EMPTY is not used anymore.",
        "house_number": "LEAVE EMPTY is not used anymore.",
    }
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Search your address on <https://secure.derby.gov.uk/binday>. The url will contain your premises ID, e.g. `https://secure.derby.gov.uk/binday/BinDays/10010688168?...` where `10010688168` is the premises ID.",
}


class Source:
    def __init__(
        self,
        premises_id: int | None = None,
        post_code: str | None = None,
        house_number: str | None = None,
    ):
        self._premises_id = premises_id
        if not self._premises_id:
            raise SourceArgumentExceptionMultiple(
                ["premises_id"],
                "premises_id must be provided in config",
            )
        self._session = requests.Session()

    def fetch(self):
        entries = []
        r = self._session.get(
            f"https://secure.derby.gov.uk/binday/Bindays/{self._premises_id}"
        )
        r.raise_for_status()
        soup = BeautifulSoup(r.text, features="html.parser")
        results = soup.find_all("div", {"class": "binresult"})

        for result in results:
            date = result.find("strong")
            try:
                date = datetime.strptime(date.text, "%A, %d %B %Y:").date()
            except ValueError:
                _LOGGER.info(f"Skipped {date} as it does not match time format")
                continue
            img_tag = result.find("img")
            collection_type = img_tag["alt"]
            entries.append(
                Collection(
                    date=date,
                    t=collection_type,
                    icon=ICON_MAP.get(collection_type),
                )
            )
        return entries
