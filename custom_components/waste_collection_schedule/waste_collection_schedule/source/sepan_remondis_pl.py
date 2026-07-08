import datetime
import xml.etree.ElementTree

from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.Sepan import SepanClient

TITLE = "Koziegłowy/Objezierze/Oborniki"
DESCRIPTION = "Source for Koziegłowy/Objezierze/Oborniki city garbage collection"
URL = "https://sepan.remondis.pl"
COUNTRY = "pl"
TEST_CASES = {
    "Street Name": {
        "city": "Poznań",
        "street_name": "ŚWIĘTY MARCIN",
        "street_number": "2",
    },
}

# Waste-type names and icons by report-table column position. This source's
# report tables don't reliably expose parseable header text (unlike
# zys_harmonogram_pl / alba_com_pl), so - as in the pre-refactor
# implementation - rows are read positionally: row 1 = January ... row 12 =
# December, column 1..7 = the fixed categories below.
NAME_MAP = {
    1: "Zmieszane odpady komunalne",
    2: "Papier",
    3: "Metale i tworzywa sztuczne",
    4: "Szkło",
    5: "Bioodpady",
    6: "Drzewka świąteczne",
    7: "Odpady wystawkowe",
}

ICON_MAP = {
    1: Icons.GENERAL_WASTE,
    2: Icons.PAPER,
    3: Icons.RECYCLING,
    4: Icons.GLASS,
    5: Icons.ORGANIC,
    6: Icons.CHRISTMAS_TREE,
    7: Icons.BULKY,
}


def _base_urls() -> list[str]:
    year = datetime.datetime.now().year
    return [
        f"https://sepan.remondis.pl/harmonogram{year}",
        "https://sepan.remondis.pl/harmonogram",
    ]


class Source:
    def __init__(self, city: str, street_name: str, street_number: str):
        self._client = SepanClient(_base_urls())
        self._address_id = self._client.resolve_address(
            city, street_name, street_number
        )

    def fetch(self) -> list[Collection]:
        html = self._client.fetch_report_html(self._address_id)
        table_html = html[html.find("<table") : html.rfind("</table>") + 8]
        tree = xml.etree.ElementTree.fromstring(table_html)  # nosec B314
        year = datetime.date.today().year

        entries = []
        for row_index, row in enumerate(tree.findall(".//tr")):
            if row_index > 0:
                for cell_index, cell in enumerate(row.findall(".//td")):
                    if cell_index > 0 and isinstance(cell.text, str):
                        for day in cell.text.split(","):
                            entries.append(
                                Collection(
                                    datetime.date(year, row_index - 1, int(day)),
                                    NAME_MAP[cell_index],
                                    ICON_MAP[cell_index],
                                )
                            )

        return entries
