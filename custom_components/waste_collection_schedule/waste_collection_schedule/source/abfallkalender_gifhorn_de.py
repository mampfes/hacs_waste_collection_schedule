import json
import re
from typing import TypedDict

import requests
from bs4 import BeautifulSoup, Tag
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "Landkreis Gifhorn"
DESCRIPTION = "Source for Landkreis Gifhorn."
URL = "https://www.abfallkalender-gifhorn.de"
TEST_CASES = {
    "Wittingen Glüsingen": {"territory": "Wittingen", "street": "Glüsingen"},
    "Gifhorn, Ackerstraße": {"territory": "Gifhorn", "street": "Ackerstraße"},
}


ICON_MAP = {
    "Trash": "mdi:trash-can",
    "Glass": "mdi:bottle-soda",
    "Bio": "mdi:leaf",
    "Paper": "mdi:package-variant",
    "Recycle": "mdi:recycle",
}
# const street_array = [
STREET_ARRAY_REGEX = re.compile(r"const\s*street_array\s*=\s*\[(.*?)\];")


API_URL = "https://www.abfallkalender-gifhorn.de"


class Terretory(TypedDict):
    id: str
    streets: list[str]


class Source:
    def __init__(self, territory: str, street: str):
        self._territory: str = territory
        self._street: str = street
        self._ics = ICS(split_at=" und ")

    @staticmethod
    def _get_street_dict(html: str) -> list[Terretory]:
        street_array = STREET_ARRAY_REGEX.search(html)
        if not street_array:
            raise RuntimeError("No street array found")

        array_str = "[" + street_array.group(1) + "]"
        array_str = array_str.replace('"', '\\"').replace("'", '"').replace(",]", "]")
        return json.loads(array_str)

    def _validate_params(self, terretories: list[Terretory]):
        matching_terretory: None | Terretory = None
        for terretory in terretories:
            if terretory["id"].lower().replace(
                " ", ""
            ) == self._territory.lower().replace(" ", ""):
                matching_terretory = terretory
                self._territory = terretory["id"]
                break

        if matching_terretory is None:
            raise ValueError(
                f"Territory {self._territory} not found use one of {[t['id'] for t in terretories]}"
            )

        street_match = False
        for street in matching_terretory["streets"]:
            if street.lower().replace(" ", "").replace("str.", "straße").replace(
                "ß", "ss"
            ).replace(".", "") == self._street.lower().replace(" ", "").replace(
                "str.", "straße"
            ).replace(
                "ß", "ss"
            ).replace(
                ".", ""
            ):
                street_match = True
                self._street = street
                break
        if not street_match:
            raise ValueError(
                f"Street {self._street} not found use one of {matching_terretory['streets']}"
            )

    def fetch(self) -> list[Collection]:
        s = requests.Session()
        r = s.get(API_URL)
        r.encoding = "utf-8"
        terretories = self._get_street_dict(r.text)
        self._validate_params(terretories)

        url = r.url

        args = {
            "territory": self._territory,
            "street": self._street,
            "act": "get_ics",
            "act2": "",
            "cur_month": "1",
            "view": "calendar",
            "show_rm14": "on",
            "show_bt": "on",
            "show_ap": "on",
            "show_gs": "on",
            "show_sm": "on",
            "show_gr": "on",
            "show_we": "on",
            "email-notification": "",
            "email-notification_verify": "",
        }

        r = s.post(url, data=args)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        ics_link = soup.find("a", {"href": lambda link: link and link.endswith(".ics")})
        if not isinstance(ics_link, Tag):
            raise RuntimeError("No ics link found")
        ics_url = ics_link["href"]
        if not isinstance(ics_url, str):
            raise RuntimeError("Invalid ics link found")
        if ics_url.startswith("/"):
            ics_url = API_URL + ics_url

        r = s.get(ics_url)
        r.encoding = "utf-8"
        dates = self._ics.convert(r.text)
        entries = []
        for d in dates:
            entries.append(Collection(d[0], d[1], ICON_MAP.get(d[1])))

        return entries
