"""Kommunalservice Landkreis Börde AöR (ks-boerde.de).

A hausmüll.info deployment in its "proxy dialect": the address cascade
(Ort -> Straße -> Hausnummer) runs against one ``proxy.php``, which this
operator mirrors on its own domain, while the calendar itself is fetched from
the operator's hausmuell.info subdomain. See ``service/HausmuellInfo.py`` for
the platform.
"""

from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, municipality, street
from waste_collection_schedule.parsers import IcsParser
from waste_collection_schedule.service.HausmuellInfo import (
    AREA,
    HausmuellInfoRetriever,
    Lookup,
)
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GENERAL_WASTE,
    HAZARDOUS,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_BASE_URL = "https://boerde.hausmuell.info/"
_PROXY_URL = "https://www.ks-boerde.de/_aturis/eko/proxy.php"


def _calendar_data(ids: dict, **_) -> dict:
    """The download form this deployment expects, filled from the resolved ids."""
    return {
        "input_ort": "",
        "input_ortsteil": "Ortsteil",
        "input_str": "",
        "input_hnr": 0,
        "hidden_id_ort": ids["village"],
        "hidden_id_ortsteil": ids["village"],
        "hidden_id_str": ids["street"],
        "hidden_id_hnr": ids["house_number"],
        "hidden_id_egebiet": ids[AREA],
        "hidden_kalenderart": "privat",
        "hidden_send_btn": "ics",
        "hidden_last_field": "input_zusatz",
        "hidden_checkzusatz": "",
        "hiddenAllOrganicWaste": 0,
        "hiddenCollectablesFraktion": "",
        "hiddenYear": "",
        "hiddenView": "",
    }


@final
class Source(BaseSource):
    TITLE = "Kommunalservice Landkreis Börde AöR"
    DESCRIPTION = "Source for KS Börde."
    URL = "https://ks-boerde.de"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        GENERAL_WASTE,
        HAZARDOUS,
        ORGANIC,
        PAPER,
        RECYCLABLES,
    ]

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

    retrieve = HausmuellInfoRetriever(
        base_url=_BASE_URL,
        lookup_url=_PROXY_URL,
        form={
            "input": "",
            "ort_id": 0,
            "str_id": 0,
            "hidden_kalenderart": "privat",
            "url": 0,
            "server": 0,
        },
        steps=(
            Lookup(field="village", opcode=0, assign=("ort_id",), skip_if_blank=False),
            Lookup(field="street", opcode=2, assign=("str_id",), skip_if_blank=False),
            Lookup(field="house_number", opcode=3, skip_if_blank=False),
        ),
        calendar_data=_calendar_data,
        check_calendar_status=False,
    )
    parse = IcsParser()
    transform = ICSTransformer(type_value_map={"Papier, Pappe, Karton": PAPER})
