from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "St Albans City & District Council"
DESCRIPTION = "Source for St Albans City & District Council."
URL = "https://stalbans.gov.uk"
TEST_CASES = {
    "55 St John's Ct": {"uprn": 100081132201},
    "9 Tyttenhanger Grn": {"uprn": "100080869141"},
}


ICON_MAP = {
    "refuse": "mdi:trash-can",
    "food": "mdi:food",
    "garden": "mdi:leaf",
    "recycling": "mdi:recycle",
}


API_URL = "https://gis.stalbans.gov.uk/NoticeBoard9/VeoliaProxy.NoticeBoard.asmx/GetServicesByUprnAndNoticeBoard"


class Source:
    def __init__(self, uprn: str | int):
        self._uprn: str | int = uprn

    def fetch(self) -> list[Collection]:
        data = {"noticeBoard": "default", "uprn": self._uprn}
        s = requests.Session()
        r = s.post(API_URL, json=data)
        r.raise_for_status()

        data = r.json()
        if (
            not data
            or not isinstance(data, dict)
            or "d" not in data
            or not isinstance(data["d"], list)
        ):
            raise ValueError("Got invalid response from API")

        entries = []
        for entry in data["d"]:
            if not isinstance(entry, dict):
                continue

            if not "ServiceHeaders" or not isinstance(entry["ServiceHeaders"], list):
                continue

            for header in entry["ServiceHeaders"]:
                if not isinstance(header, dict):
                    continue

                bin_type = header.get("TaskType")
                if not bin_type or not isinstance(bin_type, str):
                    continue
                bin_type = bin_type.removeprefix("Collect ")
                icon = ICON_MAP.get(
                    bin_type.lower()
                    .replace("domestic", "")
                    .replace("communal", "")
                    .replace("paid", "")
                    .strip()
                )
                for date_key in ("Last", "Next"):
                    date_str = header.get(date_key)
                    if not date_str or not isinstance(date_str, str):
                        continue
                    date_str = date_str.split("T")[0]
                    d = datetime.strptime(date_str, "%Y-%m-%d").date()
                    entries.append(Collection(d, bin_type, icon))
        return entries
