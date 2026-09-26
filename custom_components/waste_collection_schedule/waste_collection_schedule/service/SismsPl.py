"""SISMS / BLISKO (gateway.sisms.pl): collection calendars of Polish gminas.

Each gmina (an "owner") exposes the same API under its numeric owner id::

    /akun/api/owners/{owner}/towns/list?ownerId=...
    /akun/api/owners/{owner}/townAddresses/list?townId=...        (house in a town)
    /akun/api/owners/{owner}/streets/list?townId=...
    /akun/api/owners/{owner}/streetAddresses/list?streetId=...    (house on a street)
    /akun/api/owners/{owner}/bins/list?unitId=...                 (binId -> name)
    /akun/api/owners/{owner}/timetable/get?unitId=...             (receptions)

The ids contain ``:``, which the API only accepts unencoded, so query strings
are built by hand rather than through ``params=``.

    retrieve  = SismsRetriever()
    parse     = SismsParser()
    transform = JsonTransformer(date_key="date", type_key="type", ...)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.exceptions import (
    SourceArgumentExceptionMultiple,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource

API_URL = "https://gateway.sisms.pl/akun/api/owners/{owner_id}/{key}/{verb}"

#: Gminas on the platform, by owner id. Read while fetching (a configuration
#: stores the gmina's name), so it stays in Python.
#: Found by probing https://gateway.sisms.pl/akun/api/owners/{id}/info.
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


def _norm(value: object) -> str:
    """The platform's loose comparison: case, spaces, commas and dots ignored."""
    return (
        str(value).strip().casefold().replace(" ", "").replace(",", "").replace(".", "")
    )


def _short(name: str) -> str:
    return name.removeprefix("Gmina").removeprefix("Miasto")


def owner_id(owner: str) -> int:
    """The owner id for a gmina's name, with or without "Gmina"/"Miasto"."""
    wanted = _norm(owner)
    for o_id, name in OWNER_IDS.items():
        if wanted in (_norm(name), _norm(_short(name))):
            return o_id
    raise SourceArgumentNotFoundWithSuggestions(
        "owner", owner, list(OWNER_IDS.values())
    )


class SismsRetriever(RetrieverFunc):
    """Resolve owner, town and house to a unit id; fetch its bins and timetable.

    Returns ``{"bins": <bins/list JSON>, "timetable": <timetable/get JSON>}``,
    since the timetable names each bin only by id.

    Reads ``source.params``: ``owner`` or ``owner_id``; ``town``; and either
    ``town_address`` (a house in the town) or ``street`` plus
    ``street_address``.
    """

    def __init__(self, *, timeout: int = 30):
        self.timeout = timeout

    def _get(self, source: BaseSource, owner: str, key: str, verb: str, query: str):
        url = API_URL.format(owner_id=owner, key=key, verb=verb) + "?" + query
        response = source.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _pick(rows: list[dict], field: str, wanted: object, argument: str) -> str:
        for row in rows:
            if _norm(row[field]) == _norm(wanted):
                return row["id"]
        raise SourceArgumentNotFoundWithSuggestions(
            argument, wanted, [row[field] for row in rows]
        )

    def _unit(self, source: BaseSource, owner: str) -> str:
        params = source.params
        towns = self._get(source, owner, "towns", "list", f"ownerId={owner}")["data"]
        town = self._pick(towns, "name", params["town"], "town")
        if params.get("town_address") not in (None, ""):
            houses = self._get(
                source, owner, "townAddresses", "list", f"townId={town}"
            )["data"]
            return self._pick(houses, "number", params["town_address"], "town_address")
        streets = self._get(source, owner, "streets", "list", f"townId={town}")["data"]
        street = self._pick(streets, "name", params["street"], "street")
        houses = self._get(
            source, owner, "streetAddresses", "list", f"streetId={street}"
        )["data"]
        return self._pick(houses, "number", params["street_address"], "street_address")

    def __call__(self, source: BaseSource) -> dict[str, Any]:
        params = source.params
        if params.get("owner_id") in (None, "") and not params.get("owner"):
            raise SourceArgumentExceptionMultiple(
                ["owner", "owner_id"], "Either owner or owner_id must be set"
            )
        if params.get("town_address") in (None, "") and (
            params.get("street_address") in (None, "") or not params.get("street")
        ):
            raise SourceArgumentExceptionMultiple(
                ["town_address", "street", "street_address"],
                "Set town_address, or street and street_address",
            )
        owner = str(
            params["owner_id"]
            if params.get("owner_id") not in (None, "")
            else owner_id(params["owner"])
        )
        unit = self._unit(source, owner)
        return {
            "bins": self._get(source, owner, "bins", "list", f"unitId={unit}"),
            "timetable": self._get(source, owner, "timetable", "get", f"unitId={unit}"),
        }


class SismsParser(Parser["list[dict[str, str]]"]):
    """One ``{"date", "type"}`` record per reception, named by its bin."""

    def __call__(
        self, response: dict[str, Any], source: BaseSource | None = None
    ) -> list[dict[str, str]]:
        bins = {row["id"]: row["name"] for row in response["bins"]["data"]}
        return [
            {"date": reception["date"], "type": bins[reception["binId"]]}
            for month in response["timetable"]["data"]
            for reception in month["receptions"]
        ]


#: The platform's bin names. Polish is not in the shared vocabulary, so they are
#: mapped here once for every gmina rather than in each source.
TYPE_VALUE_MAP = {
    "Zmieszane odpady komunalne": wt.GENERAL_WASTE,
    "Odpady biodegradowalne": wt.ORGANIC,
    "Papier i tektura": wt.PAPER,
    "Szkło": wt.GLASS,
    "Tworzywa sztuczne i metale": wt.RECYCLABLES,
    "Popiół": wt.OTHER,
    # The platform's own spelling, and the correct one.
    "Zbióra tekstyliów": wt.TEXTILES,
    "Zbiórka tekstyliów": wt.TEXTILES,
}
