import re
from datetime import datetime
from typing import TypedDict

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequiredWithSuggestions,
)
from waste_collection_schedule.source.ics import Source as ICSSource

TITLE = "Die NÖ Umweltverbände"
DESCRIPTION = (
    "Consolidated waste collection provider for several districts in Lower Austria"
)
URL = "https://www.umweltverbaende.at/"


class E_I_TYPE(TypedDict):
    title: str
    url: str
    country: str
    default_params: dict[str, str]


EXTRA_INFO: list[E_I_TYPE] = [
    # { --> Schedules supported via generic ICS source [GDA Amstetten](/doc/ics/gda_gv_at.md)
    #     "title": "GDA Amstetten",
    #     "url": "https://gda.gv.at/",
    #     "country": "at",
    # },
    # { # Not supported anymore as they only provide a PDFs now
    #     "title": "GABL",
    #     "url": "https://bruck.umweltverbaende.at/",
    #     "country": "at",
    #     "default_params": {
    #         "district": "bruck",
    #     },
    # },
    {
        "title": "GVA Baden",
        "url": "https://baden.umweltverbaende.at/",
        "country": "at",
        "default_params": {
            "district": "baden",
        },
    },
    {
        "title": "GV Gmünd",
        "url": "https://gmuend.umweltverbaende.at/",
        "country": "at",
        "default_params": {
            "district": "gmuend",
        },
    },
    {
        "title": "GVU Bezirk Gänserndorf",
        "url": "https://gaenserndorf.umweltverbaende.at/",
        "country": "at",
        "default_params": {
            "district": "gaenserndorf",
        },
    },
    {
        "title": "Abfallverband Hollabrunn",
        "url": "https://hollabrunn.umweltverbaende.at/",
        "country": "at",
        "default_params": {
            "district": "hollabrunn",
        },
    },
    {
        "title": "Gemeindeverband Horn",
        "url": "https://horn.umweltverbaende.at/",
        "country": "at",
        "default_params": {
            "district": "horn",
        },
    },
    # {
    #     "title": "Klosterneuburg",
    #     "url": "https://klosterneuburg.umweltverbaende.at/",
    #     "country": "at",
    #     "default_params": {
    #         "district": "klosterneuburg",
    #     },
    # }, The site still exists but does not offer any schedules anymore they now have a own page not yet supported by this integration: https://www.klosterneuburg.at/Natur_Umwelt/Recycling/Muellabfuhr/Muellabfuhrkalender
    {
        "title": "Abfallverband Korneuburg",
        "url": "https://korneuburg.umweltverbaende.at/",
        "country": "at",
        "default_params": {
            "district": "korneuburg",
        },
    },
    {
        "title": "GV Krems",
        "url": "https://krems.umweltverbaende.at/",
        "country": "at",
        "default_params": {
            "district": "krems",
        },
    },
    # { # Does not offer same schedule but is supported via generic ICS kremsstadt_umweltverbaende_at
    #     "title": "Abfallwirtschaft Stadt Krems",
    #     "url": "https://kremsstadt.umweltverbaende.at/",
    #     "country": "at",
    #     "default_params": {
    #         "district": "kremsstadt",
    #     },
    # },
    {
        "title": "GVA Lilienfeld",
        "url": "https://lilienfeld.umweltverbaende.at/",
        "country": "at",
        "default_params": {
            "district": "lilienfeld",
        },
    },
    {
        "title": "GAUL Laa an der Thaya",
        "url": "https://laa.umweltverbaende.at/",
        "country": "at",
        "default_params": {
            "district": "laa",
        },
    },
    {
        "title": "GVA Mödling",
        "url": "https://moedling.umweltverbaende.at/",
        "country": "at",
        "default_params": {
            "district": "moedling",
        },
    },
    {
        "title": "GVU Melk",
        "url": "https://melk.umweltverbaende.at/",
        "country": "at",
        "default_params": {
            "district": "melk",
        },
    },
    {
        "title": "GAUM Mistelbach",
        "url": "https://mistelbach.umweltverbaende.at/",
        "country": "at",
        "default_params": {
            "district": "mistelbach",
        },
    },
    # { # No schedules listed on website
    #     "title": "AWV Neunkirchen",
    #     "url": "https://neunkirchen.umweltverbaende.at/",
    #     "country": "at",
    #     "default_params": {
    #         "district": "neunkirchen",
    #     },
    # },
    # { --> Schedules supported via generic ICS source [Abfallwirtschaft der Stadt St. Pölten](/doc/ics/st-poelten_at.md)
    #     "title": "Abfallwirtschaft Stadt St Pölten",
    #     "url": "https://stpoelten.umweltverbaende.at/",
    #     "country": "at",
    # },
    {
        "title": "GVU St. Pölten",
        "url": "https://stpoeltenland.umweltverbaende.at/",
        "country": "at",
        "default_params": {
            "district": "stpoeltenland",
        },
    },
    {
        "title": "GVU Scheibbs",
        "url": "https://scheibbs.umweltverbaende.at/",
        "country": "at",
        "default_params": {
            "district": "scheibbs",
        },
    },
    {
        "title": "Abfallverband Schwechat",
        "url": "https://schwechat.umweltverbaende.at/",
        "country": "at",
        "default_params": {
            "district": "schwechat",
        },
    },
    # { No ICAL or API available anymore
    #     "title": "GVA Tulln",
    #     "url": "https://tulln.umweltverbaende.at/",
    #     "country": "at",
    #     "default_params": {
    #         "district": "tulln",
    #     },
    # },
    {
        "title": "GVA Waidhofen/Thaya",
        "url": "https://waidhofen.umweltverbaende.at/",
        "country": "at",
        "default_params": {
            "district": "waidhofen",
        },
    },
    {
        "title": "GV Zwettl",
        "url": "https://zwettl.umweltverbaende.at/",
        "country": "at",
        "default_params": {
            "district": "zwettl",
        },
    },
]

PARAM_TRANSLATIONS = {
    "de": {
        "district": "Gebiet/Service provider id",
        "municipal": "Gemeinde",
        "town": "Ort",
        "plz": "Postleitzahl",
        "street": "Straße",
        "hnr": "Hausnummer",
        "zusatz": "Zusatz",
        "calendar": "Kalender",
        "calendar_title_separator": "Kalendertitel Seperator",
        "calendar_splitter": "Kalendereintrag-Trenner",
    },
    "en": {
        "district": "District/Service provider id",
        "municipal": "Municipal",
        "town": "Town",
        "plz": "Postal code",
        "street": "Street",
        "hnr": "House number",
        "zusatz": "Addition",
        "calendar": "Calendar",
        "calendar_title_separator": "Calendar title separator",
        "calendar_splitter": "Calendar entry splitter",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "There are two kinds of websites supported: The old one: Light blue header with green buttons. And a new one Dark blue header with only Blue accent elements. Follow the descriptions of the attributes according to your website type.",
    "de": "Es werden zwei Arten von Websites unterstützt: Die alte: Hellblaue Kopfzeile mit grünen Schaltflächen. Und eine neue: Dunkelblaue Kopfzeile mit nur blauen Akzentelementen. Befolgen Sie die Beschreibungen der Attribute entsprechend Ihrem Website-Typ.",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "district": "subdomain of the waste collection provider it is one of"
        + "`"
        + "`, `".join([item["default_params"]["district"] for item in EXTRA_INFO])
        + "`",
        "municipal": "Municipal name",
        "town": "(New Website only) Not needed in most cases leave empty and only use if you get an error without it",
        "plz": "(New Website only) Not needed in most cases leave empty and only use if you get an error without it",
        "street": "(New Website only) Not needed in most cases leave empty and only use if you get an error without it",
        "hnr": "(New Website only) Not needed in most cases leave empty and only use if you get an error without it",
        "addition": "(New Website only) Not needed in most cases leave empty and only use if you get an error without it",
        "calendar": "(Old website only) If you see multiple collection calendars for your municipal (different streets or Rayons), you can specify the calendar name here. The calendar name should be spelt as it appears on the Abholtermine page below `Kalenderansicht`.",
        "calendar_title_separator": "(Old website only) rarely needed, only works if `calendar` is set. This is the character that separates the calendar title from the collection dates. Like `Tour 1: Restmüll` (`:` is the separator which is the default value) or `Bisamberg Zone B, Restmüll 14-tägig` (`,` is the separator). You can see the text, the integration will use, at the Abholtermine page below `Kalenderansicht`",
        "calendar_splitter": "(Old website only) rarely needed, only works if `calendar` is set. Only needed if multiple collections are shown in one line. This is the character that separates the collection times, that are listed in one line. Like `Bisamberg Zone B, Restmüll 14-tägig: Gelber Sack` (`:` is the separator) You can see the text, the integration will use, at the Abholtermine page below `Kalenderansicht`",
    },
    "de": {
        "district": "Subdomain des Abfallwirtschaftsverbandes, einer der folgenden"
        + "`"
        + "`, `".join([item["default_params"]["district"] for item in EXTRA_INFO])
        + "`",
        "municipal": "Gemeindename",
        "town": "(Neue Website) In den meisten Fällen nicht notwendig, nur verwenden, wenn ein Fehler ohne diese Angabe auftritt",
        "plz": "(Neue Website) In den meisten Fällen nicht notwendig, nur verwenden, wenn ein Fehler ohne diese Angabe auftritt",
        "street": "(Neue Website) In den meisten Fällen nicht notwendig, nur verwenden, wenn ein Fehler ohne diese Angabe auftritt",
        "hnr": "(Neue Website) In den meisten Fällen nicht notwendig, nur verwenden, wenn ein Fehler ohne diese Angabe auftritt",
        "addition": "(Neue Website) In den meisten Fällen nicht notwendig, nur verwenden, wenn ein Fehler ohne diese Angabe auftritt",
        "calendar": "(Alte Website) Wenn mehrere Abfallkalender für Ihre Gemeinde angezeigt werden (unterschiedliche Straßen oder Rayons), können Sie hier den Kalendernamen angeben. Der Kalendername sollte so geschrieben sein, wie er auf der Abholtermine-Seite unter `Kalenderansicht` erscheint.",
        "calendar_title_separator": "(Alte Website) selten benötigt, nur wenn `calendar` gesetzt ist. Dies ist das Zeichen, das den Kalendertitel von den Abholterminen trennt. Wie `Tour 1: Restmüll` (`:` ist der Trenner, der Standardwert) oder `Bisamberg Zone B, Restmüll 14-tägig` (`,` ist der Trenner). Sie können den Text, den die Integration verwendet, auf der Abholtermine-Seite unter `Kalenderansicht` sehen",
        "calendar_splitter": "(Alte Website) selten benötigt, nur wenn `calendar` gesetzt ist. Nur erforderlich, wenn mehrere Sammlungen in einer Zeile angezeigt werden. Dies ist das Zeichen, das die Sammelzeiten trennt, die in einer Zeile aufgeführt sind. Wie `Bisamberg Zone B, Restmüll 14-tägig: Gelber Sack` (`:` ist der Trenner) Sie können den Text, den die Integration verwendet, auf der Abholtermine-Seite unter `Kalenderansicht` sehen",
    },
}


TEST_CASES = {
    # "Bruck/Leitha": {"district": "bruck", "municipal": "Berg"}, # Not supported anymore as they only provide a PDFs now
    "Baden": {
        "district": "baden",
        "municipal": "Hernstein",
        "calendar": "ICS Hernstein",
    },  # old version (as of 29.12.2024)
    "Gmünd": {
        "district": "gmuend",
        "municipal": "Weitra",
    },  # old version (as of 29.12.2024)
    "Gänserndorf": {"district": "gaenserndorf", "municipal": "Auersthal"},
    "Hollabrunn": {
        "district": "hollabrunn",
        "municipal": "Retz",
        "town": "Obernalb",
        "street": "Zum weissen Engel",
    },
    "Horn": {
        "district": "horn",
        "municipal": "Japons",
    },  # old version (as of 29.12.2024)
    # "Klosterneuburg": {
    #     "district": "klosterneuburg",
    #     "municipal": "Klosterneuburg",
    # },  # Not supported anymore
    "Korneuburg": {  # old version (as of 29.12.2024)
        "district": "korneuburg",
        "municipal": "Bisamberg",
        "calendar": "Bisamberg B",
        "calendar_title_separator": ",",
        "calendar_splitter": ":",
    },
    "Krems - Langenlois Land": {
        "district": "krems",
        "municipal": "Langenlois Land",
        "calendar": "Gobelsburg, Mittelberg, Reith, Schiltern, Zöbing",
    },
    # "Krems": {"district": "krems", "municipal": "Aggsbach"}, # 0 results with this config
    # "Stadt Krems Old Version": {"district": "kremsstadt", "municipal": "Rehberg"}, # Does not offer same schedule but is supported via generic ICS kremsstadt_umweltverbaende_at
    # "Lilienfeld": {
    #    "district": "lilienfeld",
    #    "municipal": "Annaberg",
    # },  # No ICAL or API available anymore - only redirects to the local municipal websites
    "Laa/Thaya": {
        "district": "laa",
        "municipal": "Staatz",
        "town": "kautendorf",
    },  # schedules use www.gaul-laa.at
    # "Mödling": {
    #     "district": "moedling",
    #     "municipal": "Wienerwald",
    # },  # Not supported anymore as they only provide a PDFs now
    "Melk": {"district": "melk", "municipal": "Schollach"},
    "Mistelbach": {"district": "mistelbach", "municipal": "Falkenstein"},
    # "Neunkirchen": {"district": "neunkirchen", "municipal": "?"},  # No schedules listed on website
    "St. Pölten": {"district": "stpoeltenland", "municipal": "Pyhra"},
    "Scheibbs": {"district": "scheibbs", "municipal": "Wolfpassing"},
    "Schwechat": {
        "district": "schwechat",
        "municipal": "Schwechat",
        "town": "Kledering Einfamilienhaus",
    },
    # "Tulln": {
    #    "district": "tulln",
    #    "municipal": "Absdorf",
    # },  # No ICAL or API available anymore
    "Waidhofen/Thaya": {"district": "waidhofen", "municipal": "Kautzen"},
    "Zwettl": {
        "district": "zwettl",
        "municipal": "Martinsberg",
    },  # old version (as of 29.12.2024)
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
    "Christbaum": "mdi:pine-tree",
    "Problemstoff": "mdi:chemical-weapon",
    "Strauchschnitt": "mdi:tree",
    "Verpackung": "mdi:package-variant",
    "LVP": "mdi:package-variant",
}

PARAM_TRANSLATIONS = {
    "de": {
        "district": "Gebiet",
        "municipal": "Gemeinde",
        "calendar": "Kalender",
        "calendar_title_separator": "Kalendertitel Seperator",
        "calendar_splitter": "Kalendereintrag-Trenner",
    }
}

POSSIBLE_COLLECTION_PATHS = (
    "abholtermine-preview/", # Hollabrunn
    "fuer-die-bevoelkerung/abholtermine/",
    "abfall-entsorgung/abfuhrtermine/",
    "fuer-die-bevoelkerung/abfuhrterminkalender/",
    "entsorgung-und-termine/abholtermine/",  # Scheibbs
    f"fuer-die-bevoelkerung/abholtermine-{datetime.now().year + 1}/", # Zwettl
    f"fuer-die-bevoelkerung/abholtermine-{datetime.now().year}/", # Zwettl
)


class Source:
    def __init__(
        self,
        district: str,
        municipal: str | None = None,
        town: str | None = None,
        plz: str | None = None,
        street: str | None = None,
        hnr: str | None = None,
        addition: str | None = None,
        calendar: list[str] | str | None = None,
        calendar_title_separator: str = ":",
        calendar_splitter: str | None = None,
    ):
        self._district = district.lower()
        self._municipal = municipal

        # ## arguments for new version
        self._town = town
        self._plz = plz
        self._street = street
        self._hnr = hnr
        self._addition = addition

        # ##  END arguments for new version

        if isinstance(calendar, list):
            self._calendars: list[str] | str | None = [x.lower() for x in calendar]
        elif calendar:
            self._calendars = [calendar.lower()]
        else:
            self._calendars = None

        self.calendar_title_separator = calendar_title_separator
        self.calendar_splitter = calendar_splitter

        if district == "kremsstadt":  # Keep compatibility with old configs
            raise Exception(
                "kremstadt is no longer supported by this source follow the documentation on the City of Krems ICS source"
            )

        district_url: str | None = None
        for item in EXTRA_INFO:
            if (self._district.lower() + ".") in item["url"]:
                district_url = item["url"]

        if not district_url:
            raise SourceArgumentNotFoundWithSuggestions(
                "district",
                self._district,
                [item["url"].split(".")[0].split("://")[1] for item in EXTRA_INFO],
            )
        self._district_url: str = district_url

        self._district_collection_url: str | None = None
        self.use_new = False

        # Scheibbs special case: use specific path directly (redirects cause issues)
        if "scheibbs" in self._district_url.lower():
            scheibbs_path = "entsorgung-und-termine/abholtermine/"
            r = requests.get(f"{self._district_url}{scheibbs_path}")
            if r.status_code == 200:
                self._district_collection_url = r.url
                self._district_url = self._district_collection_url.split(scheibbs_path)[
                    0
                ]
                self.use_new = True

        if not self.use_new:
            for col_path in POSSIBLE_COLLECTION_PATHS:
                if (
                    r := requests.get(f"{self._district_url}{col_path}")
                ).status_code == 200:
                    self._district_collection_url = r.url
                    self._district_url = self._district_collection_url.split(col_path)[
                        0
                    ]
                    self.use_new = True
                    break

    def get_icon(self, waste_text: str) -> str | None:
        mdi_icon = None
        for waste in ICON_MAP:
            if waste in waste_text:
                mdi_icon = ICON_MAP[waste]
        return mdi_icon

    def append_entry(self, ent: list, txt: list):
        ent.append(
            Collection(
                date=datetime.strptime(txt[1].strip().strip(",:"), "%d.%m.%Y").date(),
                t=txt[2].strip(),
                icon=self.get_icon(txt[2].strip()),
            )
        )
        return

    def fetch(self) -> list[Collection]:
        if self.use_new:
            try:
                now = datetime.now()
                entries = self.fetch_new(year=now.year)
                if now.month == 12:
                    try:
                        entries += self.fetch_new(year=now.year + 1)
                    except Exception:
                        pass
                # If new method returns no entries, try old method as fallback
                if not entries:
                    return self.fetch_old()
                return entries
            except Exception as e:
                # If new method fails, fallback to old method
                try:
                    return self.fetch_old()
                except Exception:
                    # If both methods fail, raise the original error from new method
                    raise e
        return self.fetch_old()

    def fetch_old(self) -> list[Collection]:
        now = datetime.now()
        entries = self.get_data_old(now.year)
        if now.month != 12:
            return entries
        try:
            entries2 = self.get_data_old(now.year + 1)
            entries.extend(entries2)
        except Exception:
            pass
        return entries

    def get_data_old(self, year: int) -> list[Collection]:
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
            table = soup.select("div.col-sm-9")
            for col in table:
                weblinks = col.select("a.weblink")
                for col in weblinks:
                    # match weblink with municipal to get collection schedule
                    if self._municipal in col.text:
                        r1 = s.get(f"{district_url}{col['href']}")
                        soup = BeautifulSoup(r1.text, "html.parser")

        # Find all the listed collections
        schedule = soup.select("div.tunterlegt")

        entries: list[Collection] = []
        for day in schedule:
            txt = day.text.strip().split(" \u00a0")
            if len(txt) == 1:
                txt = day.text.strip().split(" ")
                txt = [
                    txt[0].strip(","),
                    txt[1].strip(","),
                    (" ".join([t.strip() for t in txt[2:]])).strip(","),
                ]
            if self._calendars:  # Filter for calendar if there are multiple calendars
                if any(cal.upper() in txt[2].upper() for cal in self._calendars):
                    for entry_text in (
                        [txt[2]]
                        if self.calendar_splitter is None
                        else txt[2].split(self.calendar_splitter)
                    ):
                        new_txt = txt.copy()
                        new_txt[2] = entry_text.split(self.calendar_title_separator)[
                            -1
                        ].strip()
                        self.append_entry(entries, new_txt)
            else:  # Process all other municipals
                self.append_entry(entries, txt)

        return entries

    @staticmethod
    def compare(a: str, b: str) -> bool:
        return (
            a.strip().lower().replace(" ", "").replace(",", "").casefold()
            == b.strip().lower().replace(" ", "").replace(",", "").casefold()
        )

    def get_genereic(
        self,
        s: requests.Session,
        data: dict[str, str],
        arg_name: str,
        arg_value: str | None,
        element_name: str,
        newxt_stage,
    ) -> dict[str, str]:
        data["element"] = element_name
        r = s.post(f"{self._district_url}wp-admin/admin-ajax.php", data=data)
        r.raise_for_status()
        if values := r.json()["options"].strip():
            soup = BeautifulSoup(values, "html.parser")
            options = soup.select("option")
            if len(options) == 1:
                data[f"search[{element_name}]"] = options[0]["value"]
                return self.get_hnr(s, data)
            value: str | None = None
            for option in options:
                if arg_value and self.compare(arg_value, option.text):
                    value = option["value"]
                    break
            if not arg_value:
                raise SourceArgumentRequiredWithSuggestions(
                    arg_name,
                    arg_value,
                    [option.text.strip() for option in options],
                )
            if not value:
                raise SourceArgumentNotFoundWithSuggestions(
                    arg_name,
                    arg_value,
                    [option.text.strip() for option in options],
                )
            data[f"search[{element_name}]"] = value
            return newxt_stage(s, data)
        return data

    def get_addition(self, s: requests.Session, data: dict[str, str]) -> dict[str, str]:
        def do_nothing(s: requests.Session, data: dict[str, str]):
            return data

        return self.get_genereic(
            s, data, "addition", self._addition, "zusatz", do_nothing
        )

    def get_hnr(self, s: requests.Session, data: dict[str, str]) -> dict[str, str]:
        return self.get_genereic(
            s, data, "hnr", self._hnr, "hausnummer", self.get_addition
        )

    def get_street(self, s: requests.Session, data: dict[str, str]) -> dict[str, str]:
        return self.get_genereic(
            s, data, "street", self._street, "strasse", self.get_hnr
        )

    def get_plz(self, s: requests.Session, data: dict[str, str]) -> dict[str, str]:
        return self.get_genereic(
            s, data, "plz", self._plz, "postleitzahl", self.get_street
        )

    def get_ort(self, s: requests.Session, data: dict[str, str]) -> dict[str, str]:
        return self.get_genereic(s, data, "town", self._town, "ort", self.get_plz)

    def _fetch_new_from_list(self, soup: BeautifulSoup) -> list[Collection]:
        """Fetch ICS links directly from the page, e.g. for Korneuburg."""
        # Find all <a>-Tags with .ics-Links
        ics_links = {}
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.endswith(".ics"):
                # Calendarname from Linktext
                cal_name = a.text.strip()
                # build full URL
                if href.startswith("/"):
                    url = self._district_url.rstrip("/") + href
                elif href.startswith("http"):
                    url = href
                else:
                    url = self._district_url.rstrip("/") + "/" + href
                ics_links[cal_name] = url

        if not ics_links:
            raise Exception("Could not find any ics links on the page")

        matched_links = []
        # If calendar(s) are specified, filter for them
        if self._calendars and any(self._calendars):
            for cal in self._calendars:
                for name, url in ics_links.items():
                    # More tolerant: substring match
                    if cal.lower() in name.lower():
                        matched_links.append(url)
            # If no match, but only one ICS link exists, use that one
            if not matched_links and len(ics_links) == 1:
                matched_links = list(ics_links.values())
        else:
            # No calendar specified
            if len(ics_links) == 1:
                matched_links = list(ics_links.values())
            else:
                # Multiple ICS links, but no calendar specified: raise required argument exception with suggestions
                raise SourceArgumentRequiredWithSuggestions(
                    "calendar",
                    None,
                    list(ics_links.keys()),
                )

        if not matched_links:
            raise SourceArgumentNotFoundWithSuggestions(
                "calendar",
                self._calendars,
                list(ics_links.keys()),
            )

        entries = []
        for link in matched_links:
            entries += ICSSource(url=link).fetch()
        return entries

    def fetch_new(self, year: int | None = None) -> list[Collection]:
        assert self._district_collection_url is not None
        s = requests.Session()

        if year is None:
            year = datetime.now().year

        r0 = s.get(self._district_collection_url)
        soup = BeautifulSoup(r0.text, "html.parser")

        # NEW: If ICS links are directly on the page, use them!
        try:
            entries_ = self._fetch_new_from_list(soup)
            if entries_:
                return entries_
        except SourceArgumentNotFoundWithSuggestions as e:
            # If ICS links exist but no calendar is matched, raise exception with suggestions
            raise e
        except Exception as e:
            # Only fallback if really no ICS links were found
            if str(e).startswith("Could not find any ics links"):
                pass
            else:
                raise

        # OLD: Fallback to previous behavior
        NONCE_REGEX = r'"nonce":"([a-zA-Z0-9]+)"'
        nonce_match = re.search(NONCE_REGEX, r0.text)
        if (
            not nonce_match
            or not (nonce := nonce_match.group(1))
            or not isinstance(nonce, str)
        ):
            raise Exception(
                f"Could not find nonce for page {self._district_collection_url}"
            )

        mun_select = soup.select_one("select#gemeinde")
        if not mun_select:
            raise Exception(
                f"Could not find list of municipalities for page {self._district_url}fuer-die-bevoelkerung/abholtermine/"
            )

        mun_options = mun_select.select("option")
        mun_value: str | None = None
        for city_option in mun_options:
            if not city_option["value"]:
                continue
            if self._municipal and self.compare(self._municipal, city_option.text):
                mun_value = city_option["value"]
                break
        if not mun_value:
            raise SourceArgumentNotFoundWithSuggestions(
                "municipal",
                self._municipal,
                [
                    city_option.text.strip()
                    for city_option in mun_options
                    if city_option["value"]
                ],
            )

        # Build the data dict for get_zone_and_abfuhrtermine
        # Based on HAR analysis: use jahr parameter (not search[jahr])
        data: dict[str, str] = {
            "action": "get_zone_and_abfuhrtermine",
            "nonce": nonce,
            "element": "",
            "jahr": str(year),
            "search[gemeinde]": mun_value,
        }

        # Try to get ort/postleitzahl/strasse if available from get_ort
        try:
            ort_data = self.get_ort(
                s,
                {
                    "action": "get_dropdown_data",
                    "nonce": nonce,
                    "element": "ort",
                    "search[gemeinde]": mun_value,
                    "jahr": str(year),
                },
            )
            # Add additional parameters if they exist
            for key in ["search[ort]", "search[postleitzahl]", "search[strasse]"]:
                if key in ort_data:
                    data[key] = ort_data[key]
        except Exception:
            # Continue with just gemeinde
            pass

        # Try direct API call first (works for St. Pölten, newer districts)
        r = s.post(f"{self._district_url}wp-admin/admin-ajax.php", data=data)
        r.raise_for_status()

        response_json = r.json()

        zones = []
        # If direct call succeeds, get zones
        if response_json.get("success"):
            zones = response_json.get("zones", [])
            # Fix TypeError: zones might be string "error" or "no dates found" instead of list
            if not isinstance(zones, list):
                zones = []

        # If no zones returned (or success=false), try old method with fraktionen (for Scheibbs, older districts)
        if not zones or len(zones) == 0:
            # Try to get fraktionen from API
            fraktionen_data = {
                "action": "get_fraktionen",
                "nonce": nonce,
                "element": "",
                "jahr": str(year),
                "search[gemeinde]": mun_value,
            }
            # Add location data if we have it
            for key in ["search[ort]", "search[postleitzahl]", "search[strasse]"]:
                if key in data:
                    fraktionen_data[key] = data[key]

            r_frak = s.post(
                f"{self._district_url}wp-admin/admin-ajax.php", data=fraktionen_data
            )
            r_frak.raise_for_status()
            frak_response = r_frak.json()

            # Parse fraktionen even if success=false, as long as HTML is present (Scheibbs case)
            if frak_response.get("html"):
                # Parse checkboxes from HTML
                soup_frak = BeautifulSoup(frak_response["html"], "html.parser")
                checkboxes = soup_frak.select(
                    "input[type=checkbox][name='fraktionen[]']"
                )
                # Only use checkboxes that have the "checked" attribute (regardless of disabled)
                fraktionen = [
                    cb["value"] for cb in checkboxes if cb.has_attr("checked")
                ]

                if fraktionen:
                    # Call API again with fraktionen - use list of tuples for multiple values with same key
                    post_data = [
                        ("action", "get_zone_and_abfuhrtermine"),
                        ("nonce", nonce),
                        ("element", ""),
                        ("jahr", str(year)),
                        ("search[gemeinde]", mun_value),
                    ]
                    # Add location data if we have it
                    for key in [
                        "search[ort]",
                        "search[postleitzahl]",
                        "search[strasse]",
                    ]:
                        if key in data:
                            post_data.append((key, data[key]))
                    # Add all fraktionen
                    for frak in fraktionen:
                        post_data.append(("fraktionen[]", frak))

                    r2 = s.post(
                        f"{self._district_url}wp-admin/admin-ajax.php", data=post_data
                    )
                    r2.raise_for_status()
                    response_json = r2.json()

                    if response_json.get("success"):
                        zones = response_json.get("zones", [])
                        if not isinstance(zones, list):
                            return []

        entries: list[Collection] = []
        for zone in zones:
            bin_type = zone["fraktion"]
            for date_dict in zone["dates"]:
                date_str = date_dict["date"]
                date_ = datetime.strptime(date_str, "%Y-%m-%d").date()
                entries.append(
                    Collection(
                        date=date_,
                        t=bin_type,
                        icon=self.get_icon(bin_type),
                    )
                )
        return entries
