from datetime import datetime
from typing import Any

import requests
from bs4 import BeautifulSoup, Tag
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Windsor and Maidenhead"
DESCRIPTION = "Source for Windsor and Maidenhead."
URL = "https://my.rbwm.gov.uk/"
TEST_CASES = {
    "Windsor 1": {"postcode": "SL4 4EN", "uprn": 100080381393},
    "Windsor 2": {"postcode": "SL4 3NX", "uprn": "100080384194"},
    "Maidenhead 1": {"postcode": "SL6 8EH", "uprn": "100080359672"},
    "Maidenhead 2": {"postcode": "SL6 5HX", "uprn": 100080355442},
}


ICON_MAP = {
    "refuse": "mdi:trash-can",
    "garden waste": "mdi:leaf",
    "recycling": "mdi:recycle",
}


API_URL = "https://forms.rbwm.gov.uk/bincollections"

REQUEST_TEMPLATE = """-----------------------------{rand_id}
Content-Disposition: form-data; name="{name}"

{value}
"""
REQUEST_TEMPLATE_END = """-----------------------------{rand_id}--
"""


HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Content-Type": "multipart/form-data; boundary=---------------------------{rand_id}",
}


def construct_payload(data: dict[str, Any]) -> tuple[str, dict[str, str]]:
    rand_id = datetime.now().strftime("%Y%m%d%H%M%S%f%f%H%m")
    payload = ""
    for key, value in data.items():
        payload += REQUEST_TEMPLATE.format(rand_id=rand_id, name=key, value=value)
    payload += REQUEST_TEMPLATE_END.format(rand_id=rand_id)
    headers = HEADERS.copy()
    headers["Content-Type"] = headers["Content-Type"].format(rand_id=rand_id)
    return payload, headers


class Source:
    def __init__(self, uprn: str | int, postcode: str):
        self._uprn: str = str(uprn).zfill(12)
        self._postcode: str = postcode

    def _get_payload_data(self, form: Tag) -> dict[str, str]:
        form_data = {"next": "next"}
        for i in form.find_all("input"):
            if i.get("name") == "injectedParams":
                continue
            form_data[i.get("name")] = i.get("value")
            if i.get("name").endswith("_0_0"):
                form_data[i.get("name")] = self._postcode
                form_data[i.get("name").replace("_0_0", "_1_0")] = self._uprn
        return form_data

    def fetch(self):
        s = requests.Session()
        r = s.get(API_URL)
        r.raise_for_status()
        URL_BASE = "https://" + r.url.removeprefix("https://").split("/")[0]

        soup = BeautifulSoup(r.text, "html.parser")

        form = soup.find("main").find("form")
        next_url = form.get("action")
        if next_url.startswith("/"):
            next_url = URL_BASE + next_url

        if not isinstance(form, Tag):
            raise Exception("Invalid response from API")
        form_data = self._get_payload_data(form)
        payload, headers = construct_payload(form_data)

        r = s.post(next_url, data=payload, headers=headers)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        table = soup.find("table")

        entries = []
        for tr in table.find_all("tr"):
            tds = tr.find_all("td")
            if len(tds) != 2:
                continue

            bi_type = tds[0].text.split("Collection Service")[0].strip()
            date_string = tds[1].text.strip()
            date = datetime.strptime(date_string, "%d/%m/%Y").date()
            icon = ICON_MAP.get(bi_type.lower())  # Collection icon
            entries.append(Collection(date=date, t=bi_type, icon=icon))

        return entries
