import json
import logging
from datetime import datetime, timedelta

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Manchester City Council"
DESCRIPTION = "Source for bin collection services for Manchester City Council, UK."
URL = "https://www.manchester.gov.uk"
TEST_CASES = {
    "domestic #1": {"uprn": "77065560"},
    "domestic #2": {"uprn": "77121299"},
    "domestic #3": {"uprn": "10093076834"},
    "domestic #4": {"uprn": "77100451"},
    "domestic #5": {"uprn": "77141200"},
}

API_URL = "https://manchester.form.uk.empro.verintcloudservices.com/api/custom?action=bin_checker-get_bin_col_info&actionedby=_KDF_custom&loadform=true&access=citizen&locale=en"
AUTH_URL = "https://manchester.form.uk.empro.verintcloudservices.com/api/citizen?archived=Y&preview=false&locale=en"
AUTH_KEY = "Authorization"

ICON_MAP = {
    "ahtm_dates_black_bin": "mdi:trash-can",
    "ahtm_dates_blue_pulpable_bin": "package-variant",
    "ahtm_dates_brown_commingled_bin": "mdi:recycle",
    "ahtm_dates_green_organic_bin": "mdi:leaf",
}

COLLECTION_MAP = {
    "ahtm_dates_black_bin": "Black bin",
    "ahtm_dates_brown_commingled_bin": "Brown bin",
    "ahtm_dates_blue_pulpable_bin": "Blue bin",
    "ahtm_dates_green_organic_bin": "Green Bin",
}


_LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(self, uprn: int):
        self._uprn = str(uprn)  # str(uprn).zfill(12)
        self._session = requests.session()

    def fetch(self):
        entries = []

        r = self._session.get(AUTH_URL)
        r.raise_for_status()
        auth_token = r.headers[AUTH_KEY]

        post_data = {
            "name": "sr_bin_coll_day_checker",
            "data": {
                "uprn": self._uprn,
                "nextCollectionFromDate": (datetime.now() - timedelta(days=1)).strftime(
                    "%Y-%m-%d"
                ),
                "nextCollectionToDate": (datetime.now() + timedelta(days=365)).strftime(
                    "%Y-%m-%d"
                ),
            },
            "email": "",
            "caseid": "",
            "xref": "",
            "xref1": "",
            "xref2": "",
        }

        headers = {
            "referer": "https://manchester.portal.uk.empro.verintcloudservices.com/",
            "accept": "application/json",
            "content-type": "application/json",
            AUTH_KEY: auth_token,
        }

        r = self._session.post(API_URL, data=json.dumps(post_data), headers=headers)
        r.raise_for_status()

        result = r.json()

        for key, value in result["data"].items():
            if key.startswith("ahtm_dates_"):
                if key not in COLLECTION_MAP:
                    _LOGGER.warning(
                        "Unknow bin type: %s found. Please report back to the creator of this custom_component."
                    )

                dates_list = [
                    datetime.strptime(date.strip(), "%d/%m/%Y %H:%M:%S").date()
                    for date in value.split(";")
                    if date.strip()
                ]

                for current_date in dates_list:
                    entries.append(
                        Collection(
                            date=current_date,
                            t=COLLECTION_MAP.get(key),
                            icon=ICON_MAP.get(key),
                        )
                    )

        return entries
