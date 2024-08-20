from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.A_region_ch import (
    get_region_url_by_street,
)

TITLE = "Winterthur"
DESCRIPTION = "Source for Winterthur."
URL = "https://winterthur.ch/"
TEST_CASES = {"Am Iberghang": {"street": "Am Iberghang"}}


ICON_MAP = {
    "Trash": "mdi:trash-can",
    "Glass": "mdi:bottle-soda",
    "Bio": "mdi:leaf",
    "Paper": "mdi:package-variant",
    "Recycle": "mdi:recycle",
}


API_URL = "https://m.winterthur.ch/index.php?apid=1066394"


class Source:
    def __init__(self, street: str):
        self._street: str = street
        self._ics_sources: list[Source] = []

    def _get_ics_sources(self):
        self._ics_sources = get_region_url_by_street(
            "winterthur",
            self._street,
            "https://m.winterthur.ch/appl/ajax/index.php?id=street&usid=9749&do=lookupStreet&container=737670",
            regex=r"(?:Tour \d{1,2} )?(.*?)(?=\s*ganze Stadt|$)",
        ).fetch()
        for source in self._ics_sources:
            r"(\d{2}\.\d{2}\.\d{4})"

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
