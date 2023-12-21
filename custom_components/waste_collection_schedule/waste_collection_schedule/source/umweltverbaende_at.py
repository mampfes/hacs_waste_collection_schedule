from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Die NÖ Umweltverbände"
DESCRIPTION = (
    "Consolidated waste collection provider for several districts in Lower Austria"
)
URL = "https://www.umweltverbaende.at/"
EXTRA_INFO = [
    {
        "title": "GDA Amstetten",
        "url": "https://amstetten.umweltverbaende.at/",
        "country": "at",
    },
    {
        "title": "GABL",
        "url": "https://bruck.umweltverbaende.at/",
        "country": "at",
    },
    {
        "title": "GVA Baden",
        "url": "https://baden.umweltverbaende.at/",
        "country": "at",
    },
    {
        "title": "GV Gmünd",
        "url": "https://gmuend.umweltverbaende.at/",
        "country": "at",
    },
    {
        "title": "GVU Bezirk Gänserndorf",
        "url": "https://gaenserndorf.umweltverbaende.at/",
        "country": "at",
    },
    {
        "title": "Abfallverband Hollabrunn",
        "url": "https://hollabrunn.umweltverbaende.at/",
        "country": "at",
    },
    {
        "title": "Gemeindeverband Horn",
        "url": "https://horn.umweltverbaende.at/",
        "country": "at",
    },
    {
        "title": "Klosterneuburg",
        "url": "https://klosterneuburg.umweltverbaende.at/",
        "country": "at",
    },
    {
        "title": "Abfallverband Korneuburg",
        "url": "https://korneuburg.umweltverbaende.at/",
        "country": "at",
    },
    {
        "title": "GV Krems",
        "url": "https://krems.umweltverbaende.at/",
        "country": "at",
    },
    {
        "title": "Abfallwirtschaft Stadt Krems",
        "url": "https://kremsstadt.umweltverbaende.at/",
        "country": "at",
    },
    {
        "title": "GVA Lilienfeld",
        "url": "https://lilienfeld.umweltverbaende.at/",
        "country": "at",
    },
    {
        "title": "GAUL Laa an der Thaya",
        "url": "https://laa.umweltverbaende.at/",
        "country": "at",
    },
    {
        "title": "GVA Mödling",
        "url": "https://moedling.umweltverbaende.at/",
        "country": "at",
    },
    {
        "title": "GVU Melk",
        "url": "https://melk.umweltverbaende.at/",
        "country": "at",
    },
    {
        "title": "GAUM Mistelbach",
        "url": "https://mistelbach.umweltverbaende.at/",
        "country": "at",
    },
    {
        "title": "AWV Neunkirchen",
        "url": "https://neunkirchen.umweltverbaende.at/",
        "country": "at",
    },
    {
        "title": "Abfallwirtschaft Stadt St Pölten",
        "url": "https://stpoelten.umweltverbaende.at/",
        "country": "at",
    },
    {
        "title": "GVU St. Pölten",
        "url": "https://stpoeltenland.umweltverbaende.at/",
        "country": "at",
    },
    {
        "title": "GVU Scheibbs",
        "url": "https://scheibbs.umweltverbaende.at/",
        "country": "at",
    },
    {
        "title": "Abfallverband Schwechat",
        "url": "https://schwechat.umweltverbaende.at/",
        "country": "at",
    },
    {
        "title": "GVA Tulln",
        "url": "https://tulln.umweltverbaende.at/",
        "country": "at",
    },
    {
        "title": "AWV Wr. Neustadt",
        "url": "https://wrneustadt.umweltverbaende.at/",
        "country": "at",
    },
    {
        "title": "GVA Waidhofen/Thaya",
        "url": "https://waidhofen.umweltverbaende.at/",
        "country": "at",
    },
    {
        "title": "GV Zwettl",
        "url": "https://zwettl.umweltverbaende.at/",
        "country": "at",
    },
]

TEST_CASES = {
    "krems Langenlois": {
        "district": "krems",
        "municipal": "Langenlois",
        "calendar": "Gobelsburg, Mittelberg, Reith, Schiltern, Zöbing",
    },
    # "Amstetten": {"district": "amstetten", "municipal": "?"}, # No schedules listed on website
    "Bruck/Leitha": {"district": "bruck", "municipal": "Berg"},
    "Baden": {"district": "baden", "municipal": "Hernstein"},
    "Gmünd": {"district": "gmuend", "municipal": "Weitra"},
    "Gänserndorf": {"district": "gaenserndorf", "municipal": "Marchegg"},
    "Hollabrunn": {"district": "hollabrunn", "municipal": "Retz"},
    "Horn": {"district": "horn", "municipal": "Japons"},
    "Klosterneuburg": {"district": "klosterneuburg", "municipal": "Klosterneuburg"},
    "Korneuburg": {"district": "korneuburg", "municipal": "Bisamberg"},
    "Krems": {"district": "krems", "municipal": "Aggsbach"},
    "Stadt Krems Old Version": {"district": "kremsstadt", "municipal": "Rehberg"},
    "Stadt Krems New Version": {"district": "kremsstadt", "calendar": "Rehberg"},
    "Lilienfeld": {"district": "lilienfeld", "municipal": "Annaberg"},
    # "Laa/Thaya": {"district": "laa", "municipal": "Staatz"}, # schedules use www.gaul-laa.at
    "Mödling": {"district": "moedling", "municipal": "Wienerwald"},
    "Melk": {"district": "melk", "municipal": "Schollach"},
    "Mistelbach": {"district": "mistelbach", "municipal": "Falkenstein"},
    # "Neunkirchen": {"district": "neunkirchen", "municipal": "?"},  # No schedules listed on website
    "St. Pölten": {"district": "stpoeltenland", "municipal": "Pyhra"},
    # "Stadt St. Pölten": {"district": "stpoelten", "municipal": "?"}, # schedules use www.st-poelten.at/gv-buergerservice/bauen-und-wohnen/muell-und-abfall
    "Scheibbs": {"district": "scheibbs", "municipal": "Wolfpassing"},
    "Schwechat": {"district": "schwechat", "municipal": "Ebergassing"},
    "Tulln": {"district": "tulln", "municipal": "Absdorf"},
    # "Wiener Neustadt": {"district": "wrneustadt", "municipal": "?"}, # schedules use www.umweltverbaende.at/verband/vb_wn_sms.asp
    "Waidhofen/Thaya": {"district": "waidhofen", "municipal": "Kautzen"},
    "Zwettl": {"district": "zwettl", "municipal": "Martinsberg"},
}


ICON_MAP = {
    "Restmüll": "mdi:trash-can",
    "Gelber Sack": "mdi:sack",
    "Gelbe Tonne": "mdi:trash-can",
    "Altpapier": "mdi:package-variant",
    "Papier": "mdi:package-variant",
    "Biotonne": "mdi:leaf",
    "Bio": "mdi:leaf",
    "Windeltonne": "mdi:baby",
}


class Source:
    def __init__(self, district, municipal=None, calendar=None):
        self._district = district.lower()
        self._municipal = municipal
        self._calendar = calendar.lower() if calendar else None
        if (
            district == "kremsstadt" and not calendar
        ):  # Keep compatibility with old configs
            self._calendar = self._municipal
            self._municipal = None

    def get_icon(self, waste_text: str) -> str:
        for waste in ICON_MAP:
            if waste in waste_text:
                mdi_icon = ICON_MAP[waste]
        return mdi_icon

    def append_entry(self, ent: list, txt: list):
        ent.append(
            Collection(
                date=datetime.strptime(txt[1].strip(), "%d.%m.%Y").date(),
                t=txt[2].strip(),
                icon=self.get_icon(txt[2].strip()),
            )
        )
        return

    def fetch(self):
        now = datetime.now()
        entries = self.get_data(now.year)
        if now.month != 12:
            return entries
        try:
            entries.extend(self.get_data(now.year + 1))
        except Exception:
            pass
        return entries

    def get_data(self, year):
        s = requests.Session()
        # Select appropriate url, the "." allows stpoelten/stpoeltenland and krems/kremsstadt to be distinguished
        for item in EXTRA_INFO:
            if (self._district.lower() + ".") in item["url"]:
                district_url = item["url"]
        r0 = s.get(f"{district_url}?kat=32&jahr={year}")
        soup = BeautifulSoup(r0.text, "html.parser")

        # Get list of municipalities and weblinks
        # kremsstadt lists collections for all municipals on the main page so skip that district
        if self._municipal:
            table = soup.find_all("div", {"class": "col-sm-9"})
            for item in table:
                weblinks = item.find_all("a", {"class": "weblink"})
                for item in weblinks:
                    # match weblink with municipal to get collection schedule
                    if self._municipal in item.text:
                        r1 = s.get(f"{district_url}{item['href']}")
                        soup = BeautifulSoup(r1.text, "html.parser")

        # Find all the listed collections
        schedule = soup.find_all("div", {"class": "tunterlegt"})

        entries = []
        for day in schedule:
            txt = day.text.strip().split(" \u00a0")
            if self._calendar:  # Filter for calendar if there are multiple calendars
                if self._calendar.upper() in txt[2].upper():
                    txt[2] = txt[2].split(":")[-1].strip()
                    self.append_entry(entries, txt)
            else:  # Process all other municipals
                self.append_entry(entries, txt)

        return entries
