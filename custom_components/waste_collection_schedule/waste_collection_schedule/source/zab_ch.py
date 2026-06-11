from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.service.A_region_ch import A_region_ch

TITLE = "ZAB Bazenheid"
DESCRIPTION = "Source for Zweckverband Abfallverwertung Bazenheid (ZAB)"
URL = "https://zab.citymobile.ch"


def EXTRA_INFO():
    return [{"title": m, "default_params": {"municipality": m}} for m in MUNICIPALITIES]


TEST_CASES = {
    "Wängi": {"municipality": "Wängi"},
    "Sirnach": {"municipality": "Sirnach", "district": "Papier und Karton Sirnach"},
    "Eschlikon": {
        "municipality": "Eschlikon",
        "district": "Kehrichtsammlung Eschlikon",
    },
}

ICON_MAP = {
    "Kehricht": Icons.GENERAL_WASTE,
    "Grünabfuhr": Icons.ORGANIC,
    "Grüngut": Icons.ORGANIC,
    "Papier": Icons.PAPER,
    "Papier/Karton": Icons.PAPER,
    "Karton": Icons.PAPER,
    "Metall": Icons.METAL,
    "Altmetall": Icons.METAL,
    "Schredderdienst": Icons.GARDEN,
    "Häckseldienst": Icons.GARDEN,
    "Christbaum": Icons.CHRISTMAS_TREE,
    "Christbäume": Icons.CHRISTMAS_TREE,
    "Sperrgut": Icons.BULKY,
}

MUNICIPALITIES = {
    "Aadorf": "/index.php?apid=9726871&apparentid=2326631",
    "Bettwiesen": "/index.php?apid=12085057&apparentid=2326631",
    "Bichelsee-Balterswil": "/index.php?apid=11535568&apparentid=2326631",
    "Braunau": "/index.php?apid=12198875&apparentid=2326631",
    "Bütschwil-Ganterschwil": "/index.php?apid=8392002&apparentid=2326631",
    "Degersheim": "/index.php?apid=16588818&apparentid=2326631",
    "Ebnat-Kappel": "/index.php?apid=6034813&apparentid=2326631",
    "Eschlikon": "/index.php?apid=4813431&apparentid=2326631",
    "Fischingen": "/index.php?apid=9382046&apparentid=2326631",
    "Flawil": "/index.php?apid=8527584&apparentid=2326631",
    "Gossau": "/index.php?apid=3414158&apparentid=2326631",
    "Jonschwil": "/index.php?apid=5841810&apparentid=2326631",
    "Kirchberg": "/index.php?apid=13015555&apparentid=2326631",
    "Lichtensteig": "/index.php?apid=6846579&apparentid=2326631",
    "Lütisburg": "/index.php?apid=13024565&apparentid=2326631",
    "Mosnang": "/index.php?apid=782123&apparentid=2326631",
    "Münchwilen": "/index.php?apid=312606&apparentid=2326631",
    "Neckertal": "/index.php?apid=2949770&apparentid=2326631",
    "Nesslau": "/index.php?apid=15203333&apparentid=2326631",
    "Niederbüren": "/index.php?apid=9191724&apparentid=2326631",
    "Niederhelfenschwil": "/index.php?apid=10484022&apparentid=2326631",
    "Oberbüren": "/index.php?apid=3972728&apparentid=2326631",
    "Oberuzwil": "/index.php?apid=4440141&apparentid=2326631",
    "Rickenbach": "/index.php?apid=5878077&apparentid=2326631",
    "Sirnach": "/index.php?apid=10773272&apparentid=2326631",
    "Tobel-Tägerschen": "/index.php?apid=13036162&apparentid=2326631",
    "Uzwil": "/index.php?apid=6575733&apparentid=2326631",
    "Wängi": "/index.php?apid=1811155&apparentid=2326631",
    "Wattwil": "/index.php?apid=6490334&apparentid=2326631",
    "Wil": "/index.php?apid=9385302&apparentid=2326631",
    "Wilen": "/index.php?apid=9820263&apparentid=2326631",
    "Wuppenau": "/index.php?apid=9826075&apparentid=2326631",
    "Zuzwil": "/index.php?apid=215802&apparentid=2326631",
}


class Source:
    def __init__(self, municipality, district=None):
        self._municipality = municipality
        self._district = district
        if municipality not in MUNICIPALITIES:
            raise SourceArgumentNotFoundWithSuggestions(
                "municipality", municipality, MUNICIPALITIES.keys()
            )
        self._municipality_url = MUNICIPALITIES[municipality]

        self._ics_sources = []

    def _get_ics_sources(self):
        self._ics_sources = A_region_ch(
            "zab", self._municipality_url, self._district
        ).fetch()

    def fetch(self) -> list[Collection]:
        fresh_sources = False
        if not self._ics_sources:
            fresh_sources = True
            self._get_ics_sources()

        entries = []
        for source in self._ics_sources:
            fresh_sources, e = self._get_dates(source, fresh_sources)
            entries += e
        return entries

    def _get_dates(self, source, fresh=False) -> tuple[bool, list[Collection]]:
        exception = None
        try:
            entries = source.fetch()
        except Exception as e:
            exception = e

        if exception or not entries:
            if fresh:
                if exception:
                    raise exception
                return fresh, []

            self._get_ics_sources()
            return self._get_dates(source, fresh=True)

        return fresh, entries
