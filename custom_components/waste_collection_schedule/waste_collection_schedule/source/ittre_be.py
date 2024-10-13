import re
from datetime import date, datetime

import requests
from bs4 import BeautifulSoup
from dateutil.rrule import FR, MO, SA, SU, TH, TU, WE, WEEKLY, rrule
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Ittre"
DESCRIPTION = "Source for Ittre."
URL = "https://www.ittre.be/"
TEST_CASES: dict[str, dict] = {"Ittre": {}}


ICON_MAP = {
    "Trash": "mdi:trash-can",
    "Glass": "mdi:bottle-soda",
    "Bio": "mdi:leaf",
    "Paper": "mdi:package-variant",
    "Recycle": "mdi:recycle",
}


FRENSH_DAYS = {
    "lundi": MO,
    "mardi": TU,
    "mercredi": WE,
    "jeudi": TH,
    "vendredi": FR,
    "samedi": SA,
    "dimanche": SU,
}


API_URL = "https://www.ittre.be/ma-commune/services-communaux/environnement/gestion-des-dechets/collecte-des-dechets-menagers"


def clean_string(text: str) -> str:
    text = text.replace("\n", " ")
    # Replace multiple spaces with a single space
    text = re.sub(r"\s+", " ", text)
    text = text.strip()
    return text


class Source:
    def __init__(self):
        ...

    def fetch(self) -> list[Collection]:
        r = requests.get(API_URL)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")

        table = soup.select_one("table")
        if not table:
            raise Exception("Could not find collection dates table")

        table_body = table.find("tbody")
        if not table_body:
            raise Exception("Could not find collection dates table body")

        trs = table_body.select("tr")

        entries = []
        for tr in trs:
            tds = tr.select("th, td")
            if len(tds) < 2:
                continue
            bin_type = clean_string(tds[0].text.strip())
            month = 1
            while month < 13:
                td = tds[month]
                brs = td.select("br")
                for br in brs:
                    br.replace_with(" ")
                start_month = month
                days = [
                    int(day.strip())
                    for day in td.text.replace("-", " ").split()
                    if day.strip() and day.strip().isdigit()
                ]
                dates = [date(datetime.now().year, month, day) for day in days]

                if "colspan" in td.attrs:
                    month += int(td.attrs["colspan"])
                else:
                    month += 1
                if td.text.strip().lower().startswith("tous"):
                    # Parse every WEEKDAY
                    for word in td.text.strip().lower().split():
                        if word in FRENSH_DAYS:
                            rrule_rule = rrule(
                                WEEKLY,
                                byweekday=FRENSH_DAYS[word],
                                dtstart=date(datetime.now().year, start_month, 1),
                                until=date(datetime.now().year, month - 1, 31),
                            )
                            dates += [d.date() for d in rrule_rule]
                            break

                for date_ in dates:
                    entries.append(
                        Collection(date=date_, t=bin_type, icon=ICON_MAP.get(bin_type))
                    )

        return entries
