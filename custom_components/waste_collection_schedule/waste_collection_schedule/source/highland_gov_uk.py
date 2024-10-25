import datetime
import time

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Highland"
DESCRIPTION = "Source for Highland."
URL = "https://www.highland.gov.uk/"
TEST_CASES = {
    "Allangrange Mains Road, Black Isle": {"uprn": 130108578, "predict": True},
    "Kishorn, Wester Ross": {"uprn": "130066519", "predict": True},
    "Quarry Lane, Tain": {"uprn": "130007199"},
    "130143631": {"uprn": 130072429, "predict": True},
}


ICON_MAP = {
    "refuse": "mdi:trash-can",
    "recycle": "mdi:recycle",
    "garden": "mdi:leaf",
    "food": "mdi:food",
    "containers": "mdi:package",
}


SESSION_URL = "https://highland-self.achieveservice.com/authapi/isauthenticated?uri=https%3A%2F%2Fhighland-self.achieveservice.com%2Fen%2Fservice%2FCheck_your_household_bin_collection_days&hostname=highland-self.achieveservice.com&withCredentials=true"

API_URL = "https://highland-self.achieveservice.com/apibroker/runLookup"


class Source:
    def __init__(self, uprn: str | int, predict: bool = False):
        self._uprn: str = str(uprn)
        self._predict: bool = predict

    def fetch(self) -> list[Collection]:
        data = {
            "formValues": {"Your address": {"propertyuprn": {"value": self._uprn}}},
        }
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://highland-self.achieveservice.com/fillform/?iframe_id=fillform-frame-1&db_id=",
        }
        s = requests.session()
        r = s.get(SESSION_URL)
        r.raise_for_status()
        session_data = r.json()
        sid = session_data["auth-session"]
        params = {
            "id": "660d44a698632",
            "repeat_against": "",
            "noRetry": "false",
            "getOnlyTokens": "undefined",
            "log_id": "",
            "app_name": "AF-Renderer::Self",
            # unix_timestamp
            "_": str(int(time.time() * 1000)),
            "sid": sid,
        }

        r = s.post(API_URL, json=data, headers=headers, params=params)
        r.raise_for_status()

        data = r.json()
        rows_data = data["integration"]["transformed"]["rows_data"]["0"]
        if not isinstance(rows_data, dict):
            raise ValueError("Invalid data returned from API")

        use_new = any(k.endswith("New") and v for k, v in rows_data.items())
        next_date_key = "NextDateNew" if use_new else "NextDateOld"

        entries = []
        for key, value in rows_data.items():
            if not (key.endswith("NextDate") or key.endswith(next_date_key)):
                continue

            bin_type = key.split("NextDate")[0]
            try:
                date = datetime.datetime.fromisoformat(value).date()
            except ValueError:
                continue
            entries.append(
                Collection(
                    date=date,
                    t=bin_type,
                    icon=ICON_MAP.get(bin_type.lower()),
                )
            )
            freq_key = key.replace("NextDate", "Frequency")
            if not self._predict or freq_key not in rows_data:
                continue
            week_freq = rows_data[freq_key]
            if not week_freq or not isinstance(week_freq, str):
                continue
            week_freq = week_freq.lower().replace("every week", "every 1 weeks")
            week_freq = week_freq.replace("every ", "").replace(" weeks", "")
            # if week_freq is integer string
            if not week_freq.isdigit():
                continue
            week_freq_int = int(week_freq)

            # add 10 weeks of entries
            for i in range(int(10 * (1 / week_freq_int))):
                entries.append(
                    Collection(
                        date=date + datetime.timedelta(weeks=i * week_freq_int),
                        t=bin_type,
                        icon=ICON_MAP.get(bin_type.lower()),
                    )
                )
        return entries
