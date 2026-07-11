"""Kommunalservice Landkreis Börde AöR (ks-boerde.de).

Demonstrates: a resolve-through-a-proxy-then-POST-for-ICS shape built on the
"aturis eko" address cascade (also used by hausmuell.info's own subdomains,
one of which is this same provider). Three sequential POSTs to a proxy
endpoint narrow village -> street -> house number (each response an HTML
``<li onClick='get_value("id", areaId)'>`` fragment scraped by regex), then a
final POST against a different host (boerde.hausmuell.info) with the resolved
ids downloads the ICS calendar itself. No configured retriever expresses this
three-step id cascade across two hosts, hence a source-defined ``retrieve()``.
"""

import re
from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, municipality, street
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import IcsParser
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import PAPER

_DATA_URL = "https://www.ks-boerde.de/_aturis/eko/proxy.php"
_CALENDAR_URL = "https://boerde.hausmuell.info/ics/ics.php"

_OPTION_RE = re.compile(
    r"<li id = '.*?_\d+'onClick='get_value\(\".*?\",\d+,\d+\)'>"
    r"<span style = 'display:none;'>(\d+)</span>"
    r"<span style = 'display:none;'>(\d+)</span>"
    r"<span>(.*?)</span>"
    r"</li>"
)


def _proxy_lookup(
    session, field: str, value: str, village: int = 0, street: int = 0
) -> tuple[str, str]:
    """Resolve one field of the address cascade via the "aturis eko" proxy.

    Returns the matched (id, area_or_extra_id) pair for the first result --
    the proxy always returns the input's own match first, mirroring the
    original ``get_from_proxy``. Raises with the field's own candidates as
    suggestions when nothing is found.
    """
    post_data = {
        "input": value,
        "ort_id": village,
        "str_id": street,
        "hidden_kalenderart": "privat",
        "url": 0 if village == 0 else 2 if street == 0 else 3,
        "server": 0,
    }
    r = session.post(_DATA_URL, data=post_data)
    r.raise_for_status()
    matches = _OPTION_RE.findall(r.text)
    if not matches:
        raise SourceArgumentNotFoundWithSuggestions(field, value, [])
    return matches[0][0], matches[0][1]


@final
class Source(BaseSource):
    TITLE = "Kommunalservice Landkreis Börde AöR"
    DESCRIPTION = "Source for KS Börde."
    URL = "https://ks-boerde.de"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Rathaus": {
            "village": "Irxleben",
            "street": "Bördestraße",
            "house_number": "8",
        },
        "Grundschule": {
            "village": "Bebertal (Eiche/Hüsig)",
            "street": "Am Drei",
            "house_number": 11,
        },
        "KS Börde": {
            "village": "Wolmirstedt",
            "street": "Schwimmbadstraße",
            "house_number": "2a",
        },
    }

    PARAMS = (
        municipality(field="village"),
        street(field="street"),
        house_number(field="house_number"),
    )

    parse = IcsParser()
    transform = ICSTransformer(type_value_map={"Papier, Pappe, Karton": PAPER})

    def __init__(self, village: str, street: str, house_number: "str | int"):
        super().__init__(village=village, street=street, house_number=house_number)

    def retrieve(self, source):
        session = source.session
        village = self.params["village"]
        street_name = self.params["street"]
        house_no = str(self.params["house_number"])

        village_id, _ = _proxy_lookup(session, "village", village)
        street_id, _ = _proxy_lookup(session, "street", street_name, village=village_id)
        house_number_id, area_id = _proxy_lookup(
            session, "house_number", house_no, village=village_id, street=street_id
        )

        post_data = {
            "input_ort": "",
            "input_ortsteil": "Ortsteil",
            "input_str": "",
            "input_hnr": 0,
            "hidden_id_ort": village_id,
            "hidden_id_ortsteil": village_id,
            "hidden_id_str": street_id,
            "hidden_id_hnr": house_number_id,
            "hidden_id_egebiet": area_id,
            "hidden_kalenderart": "privat",
            "hidden_send_btn": "ics",
            "hidden_last_field": "input_zusatz",
            "hidden_checkzusatz": "",
            "hiddenAllOrganicWaste": 0,
            "hiddenCollectablesFraktion": "",
            "hiddenYear": "",
            "hiddenView": "",
        }
        return session.post(_CALENDAR_URL, data=post_data)
