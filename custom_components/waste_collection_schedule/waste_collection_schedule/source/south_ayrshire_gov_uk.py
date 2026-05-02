import base64
import json
import re
from datetime import date, datetime, timedelta, timezone
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup
from curl_cffi import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "South Ayrshire Council"
DESCRIPTION = "Source for south-ayrshire.gov.uk services for South Ayrshire."
URL = "https://www.south-ayrshire.gov.uk"
COLLECTION_PAGE_URL = f"{URL}/article/23931/Bin-collection-days"

TEST_CASES = {
    "4 Thistle Walk, Ayr, KA7 3XH": {"postcode": "KA7 3XH", "uprn": "141030966"},
}

ICON_MAP = {
    "Blue": "mdi:recycle",
    "Brown": "mdi:leaf",
    "Green": "mdi:trash-can",
    "Grey": "mdi:package-variant",
    "Purple": "mdi:glass-fragile",
    "Food": "mdi:food-apple",
}


class Source:
    def __init__(self, postcode: str, uprn: str | int) -> None:
        self._postcode = postcode
        self._uprn = str(uprn)

    def fetch(self) -> list[Collection]:
        session = requests.Session(impersonate="chrome")

        r = session.get(COLLECTION_PAGE_URL, timeout=30)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        form = soup.find("form", action=lambda a: a and "processsubmission" in a)
        action = form["action"]
        ids = _goss_ids(action)

        r2 = session.post(
            action,
            data={
                "BINDAYS_PAGESESSIONID": ids["page_session_id"],
                "BINDAYS_SESSIONID": ids["session_id"],
                "BINDAYS_NONCE": ids["nonce"],
                "BINDAYS_VARIABLES": "",
                "BINDAYS_PAGENAME": "PAGE1",
                "BINDAYS_PAGEINSTANCE": "0",
                "BINDAYS_PAGE1_POSTCODE": self._postcode,
                "BINDAYS_FORMACTION_NEXT": "BINDAYS_PAGE1_WIZBUTTON",
            },
            headers={"Referer": COLLECTION_PAGE_URL, "Origin": URL},
            timeout=30,
        )
        r2.raise_for_status()

        soup2 = BeautifulSoup(r2.text, "html.parser")
        form2 = soup2.find("form", action=lambda a: a and "processsubmission" in a)
        if not form2:
            raise ValueError(
                f"No address found for postcode {self._postcode!r}. Check the postcode is correct."
            )
        action2 = form2["action"]
        ids2 = _goss_ids(action2)

        r3 = session.post(
            action2,
            data={
                "BINDAYS_PAGESESSIONID": ids2["page_session_id"],
                "BINDAYS_SESSIONID": ids2["session_id"],
                "BINDAYS_NONCE": ids2["nonce"],
                "BINDAYS_VARIABLES": "",
                "BINDAYS_PAGENAME": "PAGE2",
                "BINDAYS_PAGEINSTANCE": "0",
                "BINDAYS_PAGE2_ADDRESSDROPDOWN": self._uprn,
                "BINDAYS_FORMACTION_NEXT": "BINDAYS_PAGE2_FIELD7",
            },
            headers={"Referer": COLLECTION_PAGE_URL, "Origin": URL},
            timeout=30,
        )
        r3.raise_for_status()

        return _parse_collections(r3.text)


def _goss_ids(url: str) -> dict:
    qs = parse_qs(urlparse(url).query)
    return {
        "page_session_id": qs["pageSessionId"][0],
        "session_id": qs["fsid"][0],
        "nonce": qs["fsn"][0],
    }


def _parse_collections(html: str) -> list[Collection]:
    match = re.search(r'var BINDAYSFormData = "([^"]+)";', html)
    if not match:
        raise ValueError("Could not find BINDAYSFormData in response")

    raw = match.group(1)
    raw += "=" * (-len(raw) % 4)
    data = json.loads(base64.b64decode(raw))

    field15 = data.get("PAGE3_1", {}).get("FIELD15", {})
    if not field15.get("success"):
        errors = field15.get("errors", [])
        raise ValueError(f"Collection lookup failed: {errors}")

    today = date.today()
    entries = []

    for item in field15.get("calArray", []):
        bin_name = item["bin"]
        frequency = timedelta(days=item["frequency"])
        start_dt = (
            datetime.fromisoformat(item["binDate"].replace("Z", "+00:00"))
            .astimezone(timezone.utc)
            .date()
        )
        end_dt = datetime.strptime(item["dtend"], "%Y%m%d").date()

        icon = ICON_MAP.get(bin_name.split("/")[0].split()[0])

        d = start_dt
        while d <= end_dt:
            if d >= today:
                entries.append(Collection(date=d, t=bin_name, icon=icon))
            d += frequency

    return entries
