from waste_collection_schedule import Collection
from waste_collection_schedule.service.A_region_ch import A_region_ch

TITLE = "Köniz"
DESCRIPTION = "Source for Köniz"
URL = "https://koeniz.citymobile.ch"

def EXTRA_INFO():
    return [{"title": m, "default_params": {"municipality": m}} for m in MUNICIPALITIES]

TEST_CASES = {
    "Wabern": {"municipality": "Wabern"},
    "Spiegel": {"municipality": "Spiegel"},
    "Liebefeld": {"municipality": "Liebefeld"},
    "Köniz": {"municipality": "Köniz"},
}

ICON_MAP = {
    "Kehricht": "mdi:trash-can",
    "Grünabfuhr": "mdi:leaf",
    "Papier/Karton": "mdi:newspaper",
    "Metall": "mdi:screw-flat-top",
    "Schredderdienst": "mdi:shredder",
    "Christbaum": "mdi:pine-tree"
}

MUNICIPALITIES = {
    "Wabern": "/index.php?apid=2248967&apparentid=6297623",
    "Spiegel": "/index.php?apid=6520219&apparentid=6297623",
    "Liebefeld": "/index.php?apid=6134271&apparentid=6297623",
    "Schliern": "/index.php?apid=9960784&apparentid=6297623",
    "Köniz": "/index.php?apid=6275384&apparentid=6297623",
    "Gasel": "/index.php?apid=7837203&apparentid=6297623",
    "Nieder-/Oberscherli": "/index.php?apid=1169618&apparentid=6297623",
    "Mittelhäusern": "/index.php?apid=15691286&apparentid=6297623",
    "Niederwangen": "/index.php?apid=3535226&apparentid=6297623",
    "Oberwangen": "/index.php?apid=3880894&apparentid=6297623",
    "Thörishaus": "/index.php?apid=16358162&apparentid=6297623"
}

class Source:
    def __init__(self, municipality, district=None):
        self._municipality = municipality
        self._district = district
        if municipality not in MUNICIPALITIES:
            raise Exception(f"municipality '{municipality}' not found")
        self._municipality_url = MUNICIPALITIES[municipality]

        self._ics_sources = []

    def _get_ics_sources(self):
        self._ics_sources = A_region_ch(
            "a_region", self._municipality_url, self._district
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