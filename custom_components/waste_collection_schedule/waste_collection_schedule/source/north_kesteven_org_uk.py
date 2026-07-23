from datetime import datetime

from bs4 import BeautifulSoup
from curl_cffi import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]

TITLE = "North Kesteven District Council"
DESCRIPTION = (
    "Source for n-kesteven.org.uk services for North Kesteven District Council, UK."
)
URL = "https://n-kesteven.org.uk"
TEST_CASES = {
    "Test_001": {"uprn": "100030860713"},
    "Test_002": {"uprn": "10006514327"},
    "Test_003": {"uprn": "100030857039"},
    "Test_004": {"uprn": 100030864449},
    "Test_005": {"uprn": 10006507163},
}
ICON_MAP = {
    "BLACK": Icons.GENERAL_WASTE,
    "GREEN": Icons.RECYCLING,
    "PURPLE": Icons.NEWSPAPER,
    "BROWN": Icons.ORGANIC,
    "ORANGE": Icons.BIO_KITCHEN,
}


def _icon_for(bin_type: str):
    # The council has changed the wording of bin type names over time
    # (e.g. "Purple (Paper/Card)" -> "Purple Lidded", "Orange Lidded Caddy"),
    # so match on the leading colour keyword rather than the full string.
    for keyword, icon in ICON_MAP.items():
        if keyword in bin_type:
            return icon
    return None


class Source:
    def __init__(self, uprn):
        self._uprn = str(uprn)

    def fetch(self):
        # North Kesteven District Council intermittently enables Cloudflare's
        # bot-check on this endpoint, which blocks plain "requests" sessions.
        # Impersonating a real browser via curl_cffi avoids that in most cases.
        s = requests.Session(impersonate="chrome")
        r = s.get(f"https://www.n-kesteven.org.uk/bins/display?uprn={self._uprn}")
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        bin_type = soup.find_all("span", {"class": "font-weight-bold"})
        bin_dates = soup.find_all("strong")

        entries = []
        for idx in range(len(bin_type)):
            bin_type_upper = bin_type[idx].text.upper()
            entries.append(
                Collection(
                    date=datetime.strptime(
                        bin_dates[idx].text.split(", ")[1], "%d %B %Y"
                    ).date(),
                    t=bin_type_upper,
                    icon=_icon_for(bin_type_upper),
                )
            )

        return entries
