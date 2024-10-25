import logging
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup, Tag
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

_LOGGER = logging.getLogger(__name__)

TITLE = "High Peak Borough Council"
DESCRIPTION = "Source for High Peak Borough Council."
URL = "https://www.highpeak.gov.uk/"
TEST_CASES = {
    "SK23 6BQ 10010724045": {"postcode": "SK23 6BQ", "uprn": 10010724045},
    "S33 7ZA, 10010747174": {"postcode": "S33 7ZA", "uprn": "10010747174"},
    " SK13 2AD, 10010734345": {"postcode": "SK13 2AD", "uprn": "10010734345"},
}
BIN_TYPE_SPLIT_REGEX = re.compile(r"\b and \b|\b with \b|\b \& \b")

ICON_MAP = {
    "Rubbish": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Food": "mdi:food",
    "Garden": "mdi:leaf",
}


API_URL = "https://www.highpeak.gov.uk/article/6348/Find-your-bin-day"


class Source:
    def __init__(self, postcode: str, uprn: str | int):
        self._postcode: str = postcode
        self._uprn: str = str(uprn)

    def _extract_all_form_data(self, soup: BeautifulSoup) -> tuple[dict[str, str], str]:
        form_data = {}
        inputs = soup.select("input") + soup.select("select")
        for input in inputs:
            if input.get("name"):
                name = input["name"]
                if not isinstance(name, str) or name == "go":
                    continue
                if name is not None:
                    form_data[name] = input.get("value", "")
                if name.lower().endswith("postcode"):
                    form_data[name] = self._postcode
                if name.lower().endswith("address"):
                    form_data[name] = ["", self._uprn]
                if name.lower().endswith("_variables"):
                    form_data[name] = "e30="
        form_url_tag = soup.find("form", id="FINDBINDAYSHIGHPEAK_FORM")
        form_url = form_url_tag.get("action") if isinstance(form_url_tag, Tag) else None

        return form_data, form_url

    def fetch(self) -> list[Collection]:
        s = requests.Session()

        r = s.get(API_URL)
        r.raise_for_status()
        s.headers.update(
            {
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }
        )

        BASE_URL = "https://" + r.url.replace("https://", "").split("/")[0]

        soup = BeautifulSoup(r.text, "html.parser")

        form_data, next_url = self._extract_all_form_data(soup)
        if next_url.startswith("/"):
            next_url = BASE_URL + next_url

        r = s.post(next_url, data=form_data)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        form_data, next_url = self._extract_all_form_data(soup)
        if next_url.startswith("/"):
            next_url = BASE_URL + next_url
        r = s.post(next_url, data=form_data)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        entries = []
        for month_heading in soup.select("h3.bin-collection__title--month"):
            month = month_heading.text.strip()
            collections_panel = month_heading.find_next(
                "ol", class_="bin-collection__list"
            )
            if not isinstance(collections_panel, Tag):
                _LOGGER.warning(
                    "Could not find collections panel for month %s, skipping", month
                )
                continue
            for day_tag in collections_panel.find_all(
                "span", class_="bin-collection__number"
            ):
                day = day_tag.text.strip()
                bin_type_tag = day_tag.find_next("span", class_="bin-collection__type")
                bin_type = bin_type_tag.text.strip()
                try:
                    date_ = datetime.strptime(f"{day} {month}", "%d %B %Y").date()
                except ValueError:
                    _LOGGER.warning("Could not parse date %s %s", day, month)
                    continue

                for bin_type_split in re.split(BIN_TYPE_SPLIT_REGEX, bin_type):
                    bin_type_split = bin_type_split.strip().capitalize()
                    icon = ICON_MAP.get(bin_type_split)
                    entries.append(Collection(date=date_, t=bin_type_split, icon=icon))

        return entries
