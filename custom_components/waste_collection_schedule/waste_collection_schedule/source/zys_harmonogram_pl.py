# Mod by SEMATpl - semat.pl - based on sepan_remondis_pl
import datetime

from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.Sepan import SepanClient

TITLE = "Kleszczewo/Kostrzyn"
DESCRIPTION = "Source for Kleszczewo/Kostrzyn commune garbage collection"
URL = "https://www.puk-zys.pl/index.php"  # Only Kleszczewo and Kostrzyn
COUNTRY = "pl"
TEST_CASES = {
    "Street Name": {
        "city": "Komorniki",
        "street_name": "Komorniki",
        "street_number": "93/2",
        "commune_name": "Kleszczewo",
    },
}

ICON_MAP = {
    "Zmieszane odpady komunalne": Icons.GENERAL_WASTE,
    "Papier": Icons.PAPER,
    "Metale i tworzywa sztuczne": Icons.RECYCLING,
    "Szkło": Icons.GLASS,
    "Bioodpady": Icons.ORGANIC,
}


def _base_urls(commune_name: str) -> list[str]:
    year = datetime.datetime.now().year
    commune = commune_name.lower()
    return [
        f"https://zys-harmonogram.smok.net.pl/{commune}/{year}",
        "https://zys-harmonogram.smok.net.pl//",
    ]


class Source:
    def __init__(
        self, city: str, street_name: str, street_number: str, commune_name: str
    ):
        self._client = SepanClient(_base_urls(commune_name))
        self._address_id = self._client.resolve_address(
            city, street_name, street_number
        )

    def fetch(self) -> list[Collection]:
        entries = self._client.fetch_schedule(self._address_id)
        return [
            Collection(date=date, t=waste_type, icon=ICON_MAP.get(waste_type))
            for date, waste_type in entries
        ]
