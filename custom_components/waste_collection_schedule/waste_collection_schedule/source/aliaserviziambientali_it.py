import json
import re
from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Alia Servizi Ambientali S.p.A."
DESCRIPTION = "Source for Alia Servizi Ambientali S.p.A.."
URL = "https://www.aliaserviziambientali.it"

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Visit <https://www.aliaserviziambientali.it/it-it/raccolta-rifiuti> and select your municiaplity, if you see an embedded calendar you can just use the municipality name, and leave the area empty. If you see a list of areas, you need to follow the link to the area calendar, there you can fin the area ID in the URL, for example: `https://differenziata.junker.app/embed/barberino-tavarnelle/area/67333/calendario` the area ID is `67333`.",
    "it": "Visita https://www.aliaserviziambientali.it/it-it/raccolta-rifiuti e seleziona il tuo comune. Se vedi un calendario incorporato, puoi semplicemente utilizzare il nome del comune e lasciare vuoto il campo dell'area. Se invece vedi un elenco di aree, devi seguire il link al calendario dell'area; lì puoi trovare l'ID dell'area nell'URL, ad esempio: https://differenziata.junker.app/embed/barberino-tavarnelle/area/67333/calendario l'ID dell'area è 67333.",
}

TEST_CASES = {
    "Gambassi Terme": {"municipality": "Gambassi Terme"},
    "Barberino Tavarnelle Loc. San Donato": {
        "municipality": "Barberino Tavarnelle",
        "area": 67334,
    },
    "Arrighi, Castello, Lecore, San Mauro (centro storico), San Rocco, San Piero a Ponti e Sant'Angelo a Lecore": {
        "municipality": "Signa",
        "area": 11970,
    },
}


ICON_MAP = {
    "organic": "mdi:leaf",
    "paper": "mdi:package-variant",
    "light": "mdi:package-variant",
    "general": "mdi:trash-can",
}


API_URL = "https://differenziata.junker.app/embed/{municipality}/calendario"
API_URL_WITH_AREA = (
    "https://differenziata.junker.app/embed/{municipality}/area/{area}/calendario"
)

MUNICIPALITIES_WITH_AREA = {
    "Bagno a Ripoli": [12035, 12036],
    "Barberino Tavarnelle": [67333, 67334],
    "Calenzano": [11887, 11886],
    "Carmignano": [11888, 11889],
    "Empoli": [11890, 11926, 11891],
    "Fiesole": [11905, 11906, 11907, 11908],
    "Figline e Incisa Valdarno": [11904, 11903],
    "Firenze": [12089, 12082],
    "Greve in Chianti": [12048, 12049, 12046, 12047],
    "Impruneta": [12054, 12068, 12053, 12055],
    "Marliana": [13016],
    "Montecatini Terme": [12037, 12038],
    "Pescia": [11959, 11963, 11960, 11964, 11961, 11965],
    "Pistoia": [
        12101,
        12729,
        12728,
        12103,
        12730,
        12731,
        13004,
        13005,
        12951,
        12954,
        12952,
        12953,
    ],
    "Poggio a Caiano": [11898, 11899],
    "Prato": [
        12007,
        12008,
        12009,
        12010,
        12011,
        12012,
        12013,
        12014,
        67812,
        12016,
        12030,
        12031,
        12032,
        12033,
        12034,
        12015,
        12025,
        12026,
        12027,
        12028,
        12029,
        12017,
        12018,
        12019,
        12020,
        12022,
        12021,
        12021,
        68415,
        12023,
        12024,
    ],
    "Sambuca Pistoiese": [13018, 13019],
    "San Casciano in Val di Pesa": [12057, 12058],
    "San Marcello Piteglio": [13020, 13021],
    "Scandicci": [
        11909,
        11911,
        11912,
        11913,
        11914,
        11915,
        11916,
        11917,
        11918,
        11919,
        11920,
        11921,
        11922,
    ],
    "Sesto Fiorentino": [11972, 11973],
    "Signa": [11970, 11969, 11971],
    "Vaiano": [11893, 11894],
}

MUNICIPALITIES_WITHOUT_AREA = [
    "Agliana",
    "Barberino di Mugello",
    "Borgo San Lorenzo",
    "Buggiano",
    "Campi Bisenzio",
    "Cantagallo",
    "Capraia e Limite",
    "Castelfiorentino",
    "Cerreto Guidi",
    "Certaldo",
    "Chiesina Uzzanese",
    "Fucecchio",
    "Gambassi Terme",
    "Lamporecchio",
    "Larciano",
    "Lastra a Signa",
    "Massa e Cozzile",
    "Monsummano Terme",
    "Montaione",
    "Montale",
    "Montelupo Fiorentino",
    "Montemurlo",
    "Montespertoli",
    "Pieve a Nievole",
    "Ponte Buggianese",
    "Quarrata",
    "Rignano sull'Arno",
    "Scarperia e San Piero",
    "Serravalle Pistoiese",
    "Uzzano",
    "Vaglia",
    "Vernio",
    "Vicchio",
    "Vinci",
]

MUNICIPALITIES = list(MUNICIPALITIES_WITH_AREA.keys()) + MUNICIPALITIES_WITHOUT_AREA
EXTRA_INFO = [
    {"title": mun, "default_params": {"municipality": mun}} for mun in MUNICIPALITIES
]


EVENTS_REGEX = re.compile(r"var\s+events\s*=\s*(\[.*?\])\s*;")


class Source:
    def __init__(self, municipality: str, area: int | None = None):
        self._municipality: str = municipality
        self._area: int | None = area

    def fetch(self) -> list[Collection]:
        mun_str = self._municipality.lower().strip().replace(" ", "-")
        if self._area:
            url = API_URL_WITH_AREA.format(municipality=mun_str, area=self._area)
        else:
            url = API_URL.format(municipality=mun_str)

        r = requests.get(url)
        r.raise_for_status()

        envents_match = EVENTS_REGEX.search(r.text)
        if not envents_match:
            raise ValueError("No events found")
        events_string = envents_match.group(1)
        data = json.loads(events_string)

        entries = []
        for d in data:
            date = datetime.strptime(d["date"], "%Y-%m-%d").date()
            bin_type = d["vbin_desc"]
            icon = ICON_MAP.get(bin_type.lower().split()[0])  # Collection icon
            entries.append(Collection(date=date, t=bin_type, icon=icon))

        if not entries:
            muns = [
                m
                for m in MUNICIPALITIES_WITH_AREA
                if m.lower().replace(" ", "")
                == self._municipality.lower().replace(" ", "")
            ]
            mun = muns[0] if muns else self._municipality
            if (
                not self._area
                and mun in MUNICIPALITIES_WITH_AREA
                and len(MUNICIPALITIES_WITH_AREA[mun]) == 1
            ):
                # If municipality needs region but only one region is available use it
                self._area = MUNICIPALITIES_WITH_AREA[self._municipality][0]
                return self.fetch()
            raise ValueError("No collections found maybe you need to specify an area")

        return entries


def print_municipalities() -> None:
    from bs4 import BeautifulSoup

    r = requests.get("https://www.aliaserviziambientali.it/it-it/raccolta-rifiuti")
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    mun_options = soup.select_one("script#comuni")
    if not mun_options:
        raise ValueError("No municipalities found")
    muns = json.loads(mun_options.text)

    municipalites_without_area: list[str] = []
    municipalities_with_area: dict[str, list[int]] = {}

    for mun in muns:
        mun_name: str = mun["comune"]
        mun_url: str = mun["url"]
        if mun_url.startswith("/"):
            mun_url = "https://www.aliaserviziambientali.it" + mun_url

        r = requests.get(mun_url)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        iframe = soup.select_one("iframe")
        if iframe:
            iframe_url = iframe["src"]
            if "area" in iframe_url:
                area = int(iframe_url.split("/")[-2])
                municipalities_with_area[mun_name] = [area]
            else:
                municipalites_without_area.append(mun_name)

        junker_links = soup.select("a[href*='differenziata.junker.app']")

        for link in junker_links:
            if "area" in link["href"]:
                area = int(link["href"].split("/")[-2])
                municipalities_with_area[mun_name] = municipalities_with_area.get(
                    mun_name, []
                ) + [area]
            else:
                municipalites_without_area.append(mun_name)

    print(f"MUNICIPALITIES_WITH_AREA = {municipalities_with_area}")
    print(f"MUNICIPALITIES_WITHOUT_AREA = {municipalites_without_area}")


if __name__ == "__main__":
    print_municipalities()
