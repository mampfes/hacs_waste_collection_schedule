"""ASR Stadt Chemnitz (asr-chemnitz.de / asc.hausmuell.info).

A hausmüll.info deployment in its "proxy dialect": the address cascade
(Straße -> Hausnummer) runs against one ``proxy.php`` on the operator's
hausmuell.info subdomain, an op-code per level. Where street and house number
alone do not name a disposal area ("Entsorgungsgebiet"), an object number
resolves it in a further level. See ``service/HausmuellInfo.py`` for the
platform.

"Restabfall" and "Bio" already resolve against the standard German aliases.
"Pappe, Papier & Kart." and "Leichtstoffverpackungen" are Chemnitz-specific
phrasings the shared vocabulary doesn't recognise verbatim, and
"Weihnachtsbaum" (Christmas tree collection, not exercised by the live
TEST_CASES) is mapped for parity with the legacy ``ICON_MAP``.
"""

from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, street, text_field
from waste_collection_schedule.parsers import IcsParser
from waste_collection_schedule.service.HausmuellInfo import (
    AREA,
    HausmuellInfoRetriever,
    Lookup,
)
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GARDEN_WASTE,
    GENERAL_WASTE,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_BASE_URL = "https://asc.hausmuell.info/"


def _clean_label(label: str) -> str:
    return label.replace("Entsorgung:", "").strip()


def _lookup_form(house_number: str, **_) -> dict:
    return {
        "input": "",
        "ort_id": 0,
        "str_id": 0,
        "input_hnr": house_number,
        "url": 2,
        "hidden_kalenderart": "privat",
    }


def _calendar_data(
    ids: dict, street: str, house_number: str, object_number: str, **_
) -> dict:
    """The download form this deployment expects, filled from the resolved area."""
    return {
        "input_str": street,
        "input_hnr": house_number,
        "input_objektnr": object_number,
        "input_ort": "Ort",
        "hidden_id_ort": 0,
        "hidden_id_ortsteil": 0,
        "hidden_id_egebiet": ids[AREA],
        "hidden_kalenderart": "privat",
        "hidden_send_btn": "ics",
        "hiddenYear": "",
        "showBinsRest": True,
        "showBinsRest_rc": True,
        "showBinsDsd": True,
        "showBinsBio": True,
        "showBinsProb": True,
        "showBinsPapier": True,
        "showBinsXmas": True,
        "showBinsOrganic": True,
    }


@final
class Source(BaseSource):
    TITLE = "ASR Stadt Chemnitz"
    DESCRIPTION = "Source for ASR Stadt Chemnitz."
    URL = "https://www.asr-chemnitz.de"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [GENERAL_WASTE, ORGANIC, PAPER, RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "Hübschmannstr. 4": {"street": "Hübschmannstr.", "house_number": "4"},
        "Carl-von-Ossietzky-Str 94": {
            "street": "Carl-von-Ossietzky-Str",
            "house_number": 94,
        },
        "Wasserscheide 5 (2204101)": {
            "street": "Wasserscheide",
            "house_number": "5",
            "object_number": "2204101",
        },
        "Wasserscheide 5 (89251)": {
            "street": "Wasserscheide",
            "house_number": "5",
            "object_number": 89251,
        },
        "Damaschkestraße 36": {"street": "Damaschkestr.", "house_number": "36"},
    }

    PARAMS = (
        street(field="street"),
        house_number(field="house_number"),
        text_field("object_number", "Object number", default=""),
    )

    retrieve = HausmuellInfoRetriever(
        base_url=_BASE_URL,
        lookup_url=_BASE_URL + "proxy.php",
        form=_lookup_form,
        steps=(
            Lookup(field="street", opcode=2, assign=("str_id",), skip_if_blank=False),
            Lookup(field="house_number", opcode=3, skip_if_blank=False),
            Lookup(
                field="object_number",
                opcode=7,
                only_if_area_unresolved=True,
                required_message="An object number is required for this address",
            ),
        ),
        calendar_data=_calendar_data,
        encoding="utf-8",
    )
    parse = IcsParser()
    transform = ICSTransformer(
        clean=_clean_label,
        type_value_map={
            "pappe, papier & kart.": PAPER,
            "leichtstoffverpackungen": RECYCLABLES,
            "weihnachtsbaum": GARDEN_WASTE,
        },
    )

    def __init__(
        self, street: str, house_number: "str | int", object_number: "str | int" = ""
    ):
        super().__init__(
            street=street,
            house_number=str(house_number),
            object_number=str(object_number),
        )
