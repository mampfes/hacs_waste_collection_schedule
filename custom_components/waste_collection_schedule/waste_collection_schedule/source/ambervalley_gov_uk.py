import json
from datetime import date, datetime, timedelta

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Amber Valley Borough Council"
DESCRIPTION = (
    "Source for ambervalley.gov.uk services for Amber Valley Borough Council, UK."
)
URL = "https://ambervalley.gov.uk"
TEST_CASES = {
    "Test_001": {"uprn": "100030011612", "predict": True},
    "Test_002": {"uprn": "100030011654"},
    "test_003": {"uprn": 100030041980, "predict": True},
}

ICON_MAP = {
    "REFUSE": "mdi:trash-can",
    "RECYCLING": "mdi:recycle",
    "GREEN": "mdi:leaf",
    "COMMUNAL REFUSE": "mdi:trash-can",
    "COMMUNAL RECYCLING": "mdi:recycle",
}

WASTE_TYPES_DATE_KEY = {
    "REFUSE": "refuseNextDate",
    "RECYCLING": "recyclingNextDate",
    "GREEN": "greenNextDate",
    "COMMUNAL REFUSE": "communalRefNextDate",
    "COMMUNAL RECYCLING": "communalRycNextDate",
}

WASTE_TYPE_FREQUENCY_KEY = {
    "REFUSE": "weeklyCollection",
    "RECYCLING": "weeklyCollection",
    "GREEN": "weeklyCollection",
    "COMMUNAL REFUSE": "communalRefWeekly",
    "COMMUNAL RECYCLING": "communalRycWeekly",
}


def _get_date(date_string: str) -> date:
    return datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S").date()


class Source:
    def __init__(self, uprn: str | int, predict: bool = False):
        self._uprn = str(uprn)
        self._predict = predict

    @staticmethod
    def _construct_waste_dict(data: dict, predict: bool) -> dict[str, list[date]]:
        to_return = {}
        for bin, datge_key in WASTE_TYPES_DATE_KEY.items():
            date_ = _get_date(data[datge_key])
            if date_ == date(1900, 1, 1):
                continue
            to_return[bin] = [date_]
            if predict:
                weekly: bool = data[WASTE_TYPE_FREQUENCY_KEY[bin]]
                day_offset = 7 if weekly else 14
                for i in range(1, 365 // day_offset):
                    to_return[bin].append(date_ + timedelta(days=day_offset * i))

        return to_return

    def fetch(self) -> list[Collection]:
        # get json file
        r = requests.get(
            f"https://info.ambervalley.gov.uk/WebServices/AVBCFeeds/WasteCollectionJSON.asmx/GetCollectionDetailsByUPRN?uprn={self._uprn}"
        )

        # extract data from json
        data = json.loads(r.text)
        wasteDict = self._construct_waste_dict(data, self._predict)

        entries = []

        for bin_type, dates in wasteDict.items():
            for date_ in dates:
                if date_ != "1900-01-01T00:00:00":
                    entries.append(
                        Collection(
                            date=date_,
                            t=bin_type,
                            icon=ICON_MAP.get(bin_type),
                        )
                    )

        return entries
