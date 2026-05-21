from datetime import date, datetime
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup, Tag
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]

TITLE = "Sjöbo kommun"
DESCRIPTION = "Source for Sjöbo kommun waste collection."
URL = "https://www.sjobo.se"
TEST_CASES = {
    "Kommunhuset": {"address": "Gamla torg 10", "city": "Sjöbo"},
}

ICON_MAP = {
    "FF1": Icons.GENERAL_WASTE,
    "FF1-H": Icons.GENERAL_WASTE,
    "FF2": Icons.GENERAL_WASTE,
    "FF2-H": Icons.GENERAL_WASTE,
    "MoR": Icons.GENERAL_WASTE,
    "MoR-H": Icons.GENERAL_WASTE,
    "FG": Icons.GLASS,
    "FG-H": Icons.GLASS,
    "OFG": Icons.GLASS,
    "OFG-H": Icons.GLASS,
    "RST": Icons.GENERAL_WASTE,
    "RST-H": Icons.GENERAL_WASTE,
    "KOM": Icons.BIO_KITCHEN,
    "KOM-H": Icons.BIO_KITCHEN,
    "MAT": Icons.BIO_KITCHEN,
    "MAT-H": Icons.BIO_KITCHEN,
    "MEF": Icons.RECYCLING,
    "MEF-H": Icons.RECYCLING,
    "PAF": Icons.PAPER,
    "PAF-H": Icons.PAPER,
    "PLF": Icons.RECYCLING,
    "PLF-H": Icons.RECYCLING,
    "ToP": Icons.NEWSPAPER,
    "ToP-H": Icons.NEWSPAPER,
    "TRG": Icons.ORGANIC,
    "TRG-H": Icons.ORGANIC,
}

MONTH_MAP = {
    "Januari": 1,
    "Februari": 2,
    "Mars": 3,
    "April": 4,
    "Maj": 5,
    "Juni": 6,
    "Juli": 7,
    "Augusti": 8,
    "September": 9,
    "Oktober": 10,
    "November": 11,
    "December": 12,
}

BIN_TYPE_TO_TEXT = {
    "FF1": "Matavfall, restavfall, metallförpackningar och tidningar",
    "FF1-H": "Matavfall, restavfall, metallförpackningar och tidningar",
    "FF2": "Pappersförpackningar, plastförpackningar (hårda & mjuka), ofärgade och färgade glasförpackningar samt batterier och ljuskällor i batteriboxen",
    "FF2-H": "Pappersförpackningar, plastförpackningar (hårda & mjuka), ofärgade och färgade glasförpackningar samt batterier och ljuskällor i batteriboxen",
    "MoR": "Matavfall och Restavfall",
    "MoR-H": "Matavfall och Restavfall",
    "FG": "Färgade glasförpackningar",
    "FG-H": "Färgade glasförpackningar",
    "OFG": "Ofärgade glasförpackningar",
    "OFG-H": "Ofärgade glasförpackningar",
    "RST": "Restavfall",
    "RST-H": "Restavfall",
    "KOM": "Kompost",
    "KOM-H": "Kompost",
    "MAT": "Matavfall",
    "MAT-H": "Matavfall",
    "MEF": "Metallförpackningar",
    "MEF-H": "Metallförpackningar",
    "PAF": "Pappersförpackningar",
    "PAF-H": "Pappersförpackningar",
    "PLF": "Plastförpackningar (hårda och mjuka)",
    "PLF-H": "Plastförpackningar (hårda och mjuka)",
    "ToP": "Tidningar och Papper",
    "ToP-H": "Tidningar och Papper",
    "TRG": "Trädgårdsavfall",
    "TRG-H": "Trädgårdsavfall",
}


class Source:
    def __init__(self, address: str, city: str) -> None:
        self._address: str = address
        self._city: str = city

    def fetch(self) -> list[Collection]:
        params = urlencode(
            {"hsG": self._address, "hsO": self._city}, encoding="iso-8859-1"
        )
        r = requests.get(
            "https://webbservice.indecta.se/kunder/sjobo/kalender/basfiler/onlinekalender.php",
            params=params,
        )
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        entries = []
        for bin_type, translation in BIN_TYPE_TO_TEXT.items():
            bins = soup.find_all("td", {"class": bin_type})
            for bin_ in bins:
                date_ = self._find_date(bin_)
                icon = ICON_MAP.get(bin_type)
                if bin_type.endswith("-H"):
                    translation = "Varning: helgvecka. " + translation

                entries.append(Collection(date=date_, t=translation, icon=icon))

        return entries

    @staticmethod
    def _find_date(bin: Tag) -> date:
        wrapper = bin.find_parent("table", {"class": "styleMonth"})
        year_month = wrapper.find("td", {"class": "styleMonthName"})
        month, year = year_month.text.split(" - ")

        table = bin.find_parent("table")
        cell = table.find("td", {"class": "styleDayHit"})
        if not cell:
            # workaround for a programmer error
            cell = table.find("td", {"style": "styleDayHit"})
        day = cell.text

        date_str = f"{year} {int(MONTH_MAP[month]):02d} {int(day):02d}"
        return datetime.strptime(date_str, "%Y %m %d").date()
