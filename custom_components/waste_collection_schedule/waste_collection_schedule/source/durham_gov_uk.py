import json
import re
from datetime import date, datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Durham County Council"
DESCRIPTION = "Source for Durham County Council, UK."
URL = "https://durham.gov.uk"
TEST_CASES = {
    "Test_001": {"uprn": "100110414978"},
    "Test_002": {"uprn": 100110427200},
}

API_URL = "https://www.durham.gov.uk/apiserver/ajaxlibrary/"
ICON_MAP = {
    "Rubbish bin": "mdi:trash-can",
    "Recycle bin": "mdi:recycle",
    "Garden waste bin": "mdi:leaf",
    "Food waste bin": "mdi:food-apple",
    "Clinical Waste": "mdi:medical-bag",
}

NAME_MAP = {
    "Empty Bin Refuse": "Rubbish bin",
    "Empty Bin Recycling": "Recycle bin",
    "Empty Bin Organic": "Garden waste bin",
    "Empty Bin Food": "Food waste bin",
    "Empty Bin Clinical": "Clinical Waste",
}


def _map_bin_name(name: str) -> str:
    for prefix, display in NAME_MAP.items():
        if name.startswith(prefix):
            return display
    return name


class Source:
    def __init__(self, uprn: str | int):
        self._uprn = str(uprn)

    def fetch(self) -> list[Collection]:
        s = requests.Session()
        s.headers.update(
            {
                "Content-Type": "application/json",
                "Referer": f"https://www.durham.gov.uk/bincollections?uprn={self._uprn}",
            }
        )

        payload = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "durham.Localities.GetBartecCalendar",
                "params": {"uprn": self._uprn},
                "id": "21",
                "name": "V2 AJAX End Point Library Worker",
            }
        )
        r = s.post(API_URL, data=payload)
        r.raise_for_status()

        result = r.json()
        xml_str = result.get("result", "")

        today = date.today()
        entries = []

        for match in re.finditer(r"<Job>(.*?)</Job>", xml_str, re.DOTALL):
            job_xml = match.group(1)

            name_match = re.search(r"<Name[^>]*>([^<]+)</Name>", job_xml)
            sched_match = re.search(
                r"<ScheduledStart>([^<]+)</ScheduledStart>", job_xml
            )

            if not name_match or not sched_match:
                continue

            name = name_match.group(1).strip()
            sched_str = sched_match.group(1).strip()

            try:
                collection_date = datetime.fromisoformat(sched_str).date()
            except ValueError:
                continue

            if collection_date < today:
                continue

            waste_type = _map_bin_name(name)
            entries.append(
                Collection(
                    date=collection_date,
                    t=waste_type,
                    icon=ICON_MAP.get(waste_type),
                )
            )

        return entries
