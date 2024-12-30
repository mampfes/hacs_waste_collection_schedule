from datetime import datetime
from typing import TypedDict

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "SISMS.pl / BLISKO"
DESCRIPTION = "Source for SISMS.pl / BLISKO."
URL = "https://sisms.pl"
TEST_CASES = {
    "188 Bobrza ul. St. Staszica 3": {
        "owner_id": 188,
        "town": "Bobrza",
        "street": "ul. St. Staszica",
        "street_address": 23,
    },
    "Jeżewo Ciemniki 2a": {
        "owner": "Jeżewo",
        "town": "Ciemniki",
        "town_address": "2a",
    },
}


ICON_MAP = {
    "Trash": "mdi:trash-can",
    "Glass": "mdi:bottle-soda",
    "Bio": "mdi:leaf",
    "Paper": "mdi:package-variant",
    "Recycle": "mdi:recycle",
}


API_URL_LIST = "https://gateway.sisms.pl/akun/api/owners/{owner_id}/{key}/list"
API_URL_GET = "https://gateway.sisms.pl/akun/api/owners/{owner_id}/{key}/get"


class JSONResponseItem(TypedDict):
    id: str
    kind: str


class JSONResponseItemName(JSONResponseItem):
    name: str


class JSONResponseItemNumber(JSONResponseItem):
    number: str


class JSONResponseNumber(TypedDict):
    data: list[JSONResponseItemNumber]


class JSONResponseName(TypedDict):
    data: list[JSONResponseItemName]


class Receptions(TypedDict):
    id: int
    binId: int
    date: str


class TimetableMonth(TypedDict):
    month: str
    receptions: list[Receptions]


class TimedatbleResponse(TypedDict):
    data: list[TimetableMonth]


class Bin(TypedDict):
    id: int
    name: str
    type: str
    color: str


class BinResponse(TypedDict):
    data: list[Bin]


OWNER_IDS = {
    39: "Gmina Topólka",
    40: "Gmina Strzelin",
    42: "Gmina Reda",
    44: "Gmina Rumia",
    # 45: "[TEST] Gmina Kuźnica",
    51: "Gmina Złoty Stok",
    61: "Klient Szablonowy - Karty Usług",
    73: "Gmina Wieluń",
    75: "Gmina Łęczyce",
    77: "Gmina Kolbudy",
    78: "Gmina Polanica-Zdrój",
    81: "Gmina Wisznia Mała",
    82: "Polkowice",
    83: "Gmina Cedry Wielkie",
    84: "Gmina i Miasto Nowe Skalmierzyce",
    85: "Gmina Chojnów",
    86: "Gmina Pajęczno",
    87: "Gospodarka Odpadami - Pelplin",
    89: "Gmina Szczytna",
    # 91: "[TEST] Gmina Ustka",
    # 95: "[TEST] Gmina Moszczenica",
    99: "ZGPD-7",
    100: "Gmina Mysłakowice",
    101: "Gmina Krotoszyce",
    103: "Gmina Sobótka",
    104: "Gmina Wołów",
    109: "Gospodarka Odpadami - Starogard Gdański",
    111: "Gmina Inowrocław",
    112: "Gmina Dobra",
    114: "Gmina Słupno",
    115: "Gmina Mielec",
    116: "Gmina Bardo",
    117: "Gmina Żmigród",
    # 118: "[TEST] Gmina Wołów",
    119: "Gmina Stawiguda",
    120: "Gmina Starogard Gdański",
    121: "Gmina Nowa Ruda",
    122: "Gmina Legnickie Pole",
    123: "Gmina Brzeziny",
    124: "Gmina Zduńska Wola",
    125: "Gmina Międzybórz",
    127: "Gmina Osiecznica",
    128: "Gmina Słupca",
    136: "Gmina Grabów nad Prosną",
    140: "Gmina Mokrsko",
    142: "Strzelce Krajeńskie",
    144: "Gmina i Miasto Dzierzgoń",
    145: "Gmina Brzeg Dolny",
    146: "Gmina Wiązów",
    149: "Przedsiębiorstwo Gospodarki Komunalnej w Wołowie Sp. z o.o.",
    150: "Gmina Staszów",
    153: "Miasto Wałbrzych",
    154: "Miasto Rejowiec Fabryczny",
    # 155: "[TEST] Urząd Miejski Krzeszowice",
    158: "Gmina Grodzisk Mazowiecki",
    159: "Gmina Świecie",
    160: "Gmina Kozy",
    161: "Gmina Gniew",
    162: "Gmina Ostrowiec Świętokrzyski",
    163: "Gmina Skarszewy",
    164: "Gminne Przedsiębiorstwo Komunalne Sp. z o.o. w Skarszewach",
    165: "Gmina Porąbka",
    166: "Gmina Zbrosławice",
    167: "Gmina Szumowo",
    168: "KOMUS",
    169: "Miasto i Gmina Łasin",
    # 170: "Zakład Gospodarki Komunalnej Sp. z o.o.",
    171: "Gmina Kamionka Wielka",
    172: "Gmina Czernichów",
    173: "Gmina Świdnica",
    174: "Klient Szablonowy - Ekostrażnik",
    175: "Gmina Daleszyce",
    # 176: "[TEST] Gmina Szkolenie DU",
    177: "Gmina Nowy Staw",
    178: "Gmina Przeworno",
    179: "Gmina Pruszcz",
    # 180: "[TEST] Gmina Bisztynek",
    181: "Gmina Władysławowo",
    182: "Gmina Czechowice- Dziedzice",
    183: "ABRUKO PLUS",
    184: "Miasto i Gmina Morawica",
    185: "Gmina Wilkowice",
    186: "Gmina Wojcieszków",
    187: "Gmina Gorzyce",
    188: "Gmina Miedziana Góra",
    189: "Gmina Mogilany ",
    190: "Gmina Gościno",
    191: "Gmina Ulan-Majorat",
    192: "Gmina Wąchock ",
    193: "Gmina Wodzisław",
    194: "Miasto Malbork",
    195: "Gmina Grodków",
    196: "Gmina Zaleszany",
    197: "Gmina Gać",
    198: "Gmina Kluczbork",
    199: "Miasto Inowrocław",
    # 200: "Ekologiczny Związek Gmin Dorzecza Koprzywianki",
    201: "Gmina Miejska Kowal",
    202: "Gmina Kruszwica",
    203: "Gmina Przykładowa",
    204: "Gmina Radoszyce",
    205: "Gmina Osiek",
    206: "Gmina Pawłowice",
    # 207: "None",
    208: "Gmina Gaworzyce",
    209: "Gmina Lubrza",
    210: "Parafia św. Wojciecha Biskupa i Męczennika w Nidzicy",
    211: "Gmina Pyskowice",
    212: "Gmina Nowa Słupia",
    # 213: "Stowarzyszenie Centrum Wspierania Organizacji Pozarządowych i Inicjatyw Obywatelskich",
    214: "Gmina Sośno",
    215: "Gmina Dygowo",
    216: "Gmina Bartniczka",
    # 217: "[TEST] Blisko",
    218: "Gmina Jeżewo",
    219: "Gmina Olsztynek",
    220: "Gmina Krzanowice",
    221: "Gmina Wierzchlas",
    222: "Gmina Miejska Hrubieszów",
    223: "Miasto Rydułtowy",
    224: "Gmina Gorlice",
    225: "Gmina Sztum",
}
# https://gospodarkakomunalna.strefamieszkanca.pl/?ownerId=188&colorAccent=%83ef9546&colorButtonBg=%23ef9546&colorButtonBgHover=%53ffaa60

EXTRA_INFO = [
    {
        "title": name.strip(),
        "default_params": {
            "owner": name.strip(),
        },
    }
    for name in OWNER_IDS.values()
]

PARAM_TRANSLATION = {
    "en": {
        "owner": "owner",
        "town": "town (Miejscowość)",
        "street": "street (Ulica)",
        "owner_id": "ownerId",
        "street_address": "Street House Number (Numer domu)",
        "town_address": "Town House Number (Numer domu)",
    }
}


PARAM_DESCRIPTIONS = {
    "en": {
        "owner_id": "Owner of the waste collection service You can see the owner id in the url requested by the search page",
        "street_address": "House number of the street if street is set",
        "town_address": "House number of the town if street is not set",
    }
}


class Source:
    def __init__(
        self,
        town: str,
        street: str | None = None,
        owner: str | None = None,
        owner_id: str | int | None = None,
        street_address: str | int | None = None,
        town_address: str | None = None,
    ):
        self._town: str = town
        self._street: str | None = street
        self._street_address: str | int | None = street_address
        self._town_address: str | None = town_address
        if self._town_address is None and self._street_address is None:
            raise Exception("Either town_address or street_address must be set")
        if street is None and street_address is not None:
            raise Exception("street must be set if street_address is set")
        if owner is None and owner_id is None:
            raise Exception("Either owner or owner_id must be set")
        if owner_id is None:
            assert owner is not None
            for o_id, o_name in OWNER_IDS.items():
                if self.compare(
                    o_name.removeprefix("Gmina").removeprefix("Miasto"), owner
                ):
                    owner_id = o_id
                    break
            if owner_id is None:
                raise SourceArgumentNotFoundWithSuggestions(
                    "owner", owner, [o_name for o_name in OWNER_IDS.values()]
                )
        self._owner_id: str = str(owner_id)

    def get_bins(self, unitId: str) -> BinResponse:
        r = requests.get(
            API_URL_LIST.format(owner_id=self._owner_id, key="bins")
            + f"?unitId={unitId}"  # params=args not working because it encodes : to %3A
        )
        r.raise_for_status()
        return r.json()

    def get_timetable(self, unitId: str) -> TimedatbleResponse:
        r = requests.get(
            API_URL_GET.format(owner_id=self._owner_id, key="timetable")
            + f"?unitId={unitId}"  # params=args not working because it encodes : to %3A
        )
        r.raise_for_status()
        return r.json()

    def get_street_addresses(self, street_id: str) -> JSONResponseNumber:
        r = requests.get(
            API_URL_LIST.format(owner_id=self._owner_id, key="streetAddresses")
            + f"?streetId={street_id}",  # params=args not working because it encodes : to %3A
        )
        r.raise_for_status()
        return r.json()

    def get_town_addresses(self, town_id: str) -> JSONResponseNumber:
        r = requests.get(
            API_URL_LIST.format(owner_id=self._owner_id, key="townAddresses")
            + f"?townId={town_id}"  # params=args not working because it encodes : to %3A
        )
        r.raise_for_status()
        return r.json()

    def get_streets(self, town_id: str) -> JSONResponseName:
        r = requests.get(
            API_URL_LIST.format(owner_id=self._owner_id, key="streets")
            + f"?townId={town_id}"  # params=args not working because it encodes : to %3A
        )
        r.raise_for_status()
        return r.json()

    def get_towns(self) -> JSONResponseName:
        r = requests.get(
            API_URL_LIST.format(owner_id=self._owner_id, key="towns")
            + f"?ownerId={self._owner_id}"  # params=args not working because it encodes : to %3A
        )
        r.raise_for_status()
        return r.json()

    @staticmethod
    def compare(a: str, b: str) -> bool:
        return (
            a.lower()
            .strip()
            .replace(" ", "")
            .replace(",", "")
            .replace(".", "")
            .casefold()
            == b.lower()
            .strip()
            .replace(" ", "")
            .replace(",", "")
            .replace(".", "")
            .casefold()
        )

    def fetch(self) -> list[Collection]:
        towns = self.get_towns()
        town_id: str | None = None
        for town in towns["data"]:
            if self.compare(town["name"], self._town):
                town_id = town["id"]
                break
        if town_id is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "town", self._town, [town["name"] for town in towns["data"]]
            )

        address_id: str | None = None
        if self._town_address is not None:
            town_addresses = self.get_town_addresses(town_id)
            for town_address in town_addresses["data"]:
                if self.compare(town_address["number"], self._town_address):
                    address_id = town_address["id"]
                    break
            if address_id is None:
                raise SourceArgumentNotFoundWithSuggestions(
                    "town_address",
                    self._town_address,
                    [town_address["number"] for town_address in town_addresses["data"]],
                )
        else:
            assert self._street_address is not None
            assert self._street is not None
            streets = self.get_streets(town_id)
            street_id: str | None = None
            for street in streets["data"]:
                if self.compare(street["name"], self._street):
                    street_id = street["id"]
                    break
            if street_id is None:
                raise SourceArgumentNotFoundWithSuggestions(
                    "street",
                    self._street,
                    [street["name"] for street in streets["data"]],
                )

            street_addresses = self.get_street_addresses(street_id)
            for street_address in street_addresses["data"]:
                if self.compare(street_address["number"], str(self._street_address)):
                    address_id = street_address["id"]
                    break
            if address_id is None:
                raise SourceArgumentNotFoundWithSuggestions(
                    "street_address",
                    self._street_address,
                    [
                        street_address["number"]
                        for street_address in street_addresses["data"]
                    ],
                )

        bins = self.get_bins(address_id)

        bins_map = {b["id"]: b["name"] for b in bins["data"]}

        timetable = self.get_timetable(address_id)

        entries = []
        for month in timetable["data"]:
            for reception in month["receptions"]:
                date_ = datetime.strptime(reception["date"], "%Y-%m-%d").date()
                bin_type = bins_map[reception["binId"]]
                icon = ICON_MAP.get(bin_type)
                entries.append(Collection(date=date_, t=bin_type, icon=icon))

        return entries


def get_owner_ids():
    import time

    INFO_URL = "https://gateway.sisms.pl/akun/api/owners/{owner_id}/info"

    for i in range(30, 300):
        r = requests.get(INFO_URL.format(owner_id=i))
        if r.status_code != 404:
            print(i, ":", r.json().get("name"))
        elif i % 50 == 0:
            print(i)
        time.sleep(0.1)
