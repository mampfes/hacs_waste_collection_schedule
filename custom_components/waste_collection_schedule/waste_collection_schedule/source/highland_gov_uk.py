import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.AchieveForms import init_session, run_lookup

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

BASE_URL = "https://highland-self.achieveservice.com"
INITIAL_URL = f"{BASE_URL}/en/service/Check_your_household_bin_collection_days"
AUTH_URL = f"{BASE_URL}/authapi/isauthenticated"
API_URL = f"{BASE_URL}/apibroker/runLookup"
HOSTNAME = "highland-self.achieveservice.com"
LOOKUP_ID = "660d44a698632"


class Source:
    def __init__(self, uprn: str | int, predict: bool = False):
        self._uprn: str = str(uprn)
        self._predict: bool = predict

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        sid = init_session(session, INITIAL_URL, AUTH_URL, HOSTNAME)

        result = run_lookup(
            session,
            API_URL,
            sid,
            LOOKUP_ID,
            {"Your address": {"propertyuprn": {"value": self._uprn}}},
        )

        rows_data = result["integration"]["transformed"]["rows_data"]["0"]
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
