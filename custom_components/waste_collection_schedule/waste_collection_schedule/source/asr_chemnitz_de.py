"""ASR Stadt Chemnitz (asr-chemnitz.de / asc.hausmuell.info).

Demonstrates: a genuinely bespoke multi-step retrieve against a shared
"hausmuell.info" backend that resolves state (a street id, then a disposal
area / "Entsorgungsgebiet" id) through the *same* endpoint called with
different ``url`` op-codes, one response threading into the next request's
form data. When the street/house-number pair alone doesn't resolve a disposal
area (``egebiet_id == "0"``), a required ``object_number`` argument drives a
third lookup call before the final POST requests the ICS export. No
configured retriever expresses this "same endpoint, different op-code per
step, conditional extra step" shape, hence a source-defined ``retrieve``
method (the default ``parse = IcsParser()`` handles the single ICS response).

"Restabfall" and "Bio" already resolve against the standard German aliases.
"Pappe, Papier & Kart." and "Leichtstoffverpackungen" are Chemnitz-specific
phrasings the shared vocabulary doesn't recognise verbatim, and
"Weihnachtsbaum" (Christmas tree collection, not exercised by the live
TEST_CASES) is mapped for parity with the legacy ``ICON_MAP``.
"""

from typing import ClassVar, final

from bs4 import BeautifulSoup
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, street, text_field
from waste_collection_schedule.exceptions import SourceArgumentRequired
from waste_collection_schedule.parsers import IcsParser
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import GARDEN_WASTE, PAPER, RECYCLABLES

_PROXY_URL = "https://asc.hausmuell.info/proxy.php"
_API_URL = "https://asc.hausmuell.info/ics/ics.php"


def _clean_label(label: str) -> str:
    return label.replace("Entsorgung:", "").strip()


@final
class Source(BaseSource):
    TITLE = "ASR Stadt Chemnitz"
    DESCRIPTION = "Source for ASR Stadt Chemnitz."
    URL = "https://www.asr-chemnitz.de"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True

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

    def retrieve(self, source):
        session = source.session
        street = source.params["street"]
        house_number = source.params["house_number"]
        object_number = source.params["object_number"]

        args = {
            "input": street,
            "ort_id": 0,
            "str_id": 0,
            "input_hnr": house_number,
            "url": 2,
            "hidden_kalenderart": "privat",
        }
        r = session.post(_PROXY_URL, data=args)
        r.raise_for_status()
        street_id = BeautifulSoup(r.text, "html.parser").find("span").text.strip()

        args["str_id"] = street_id
        args["url"] = 3
        args["input"] = house_number

        r = session.post(_PROXY_URL, data=args)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        egebiet_id = soup.find_all("span")[1].text.strip()

        if egebiet_id == "0":
            if not object_number:
                raise SourceArgumentRequired(
                    "object_number", "An object number is required for this address"
                )
            args["input"] = object_number
            args["url"] = 7
            r = session.post(_PROXY_URL, data=args)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            egebiet_id = soup.find_all("span")[1].text.strip()

        data = {
            "input_str": street,
            "input_hnr": house_number,
            "input_objektnr": object_number,
            "input_ort": "Ort",
            "hidden_id_ort": 0,
            "hidden_id_ortsteil": 0,
            "hidden_id_egebiet": egebiet_id,
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
        r = session.post(_API_URL, data=data)
        r.raise_for_status()
        r.encoding = "utf-8"
        return r
