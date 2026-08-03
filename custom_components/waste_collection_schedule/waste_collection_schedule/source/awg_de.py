"""ZAW Donau-Wald / AWG (awg.de), Germany.

Demonstrates: the two Athos "WasteManagementServlet" traits that
``retrievers.AthosWasteManagementRetriever`` gained for this deployment.

* ``state="rescrape"``. Each step posts the form state scraped from the page
  it just received, rather than the state the wizard started with, so the
  servlet's own ``ApplicationName`` / ``PageName`` / ``IsLastPage`` follow the
  wizard forward. Other deployments hardcode those per step instead.
* ``verify=False``. The servlet's certificate is valid (a GoDaddy-issued leaf)
  but the server sends the leaf alone, omitting the "Go Daddy Secure
  Certificate Authority - G2" intermediate, so no default trust store can
  build a chain to it. Disabling verification is what the legacy source did
  and is kept here unchanged; the narrower fix is to point ``verify`` at a CA
  bundle carrying that intermediate, at the cost of shipping and maintaining
  a certificate in-tree.

Two things the legacy source did are deliberately gone, both verified against
the live servlet and all three recorded cassettes:

* It hand-built ``multipart/form-data`` bodies. The servlet accepts an
  ordinary urlencoded POST and returns a byte-identical calendar.
* It re-ran the whole wizard once per ``Zeitraum`` (period) option. The
  servlet renders no ``Zeitraum`` field at all: the string appears in no
  response, so the fan-out never ran.
"""

from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    city,
    house_number,
    street,
    text_field,
)
from waste_collection_schedule.retrievers import AthosWasteManagementRetriever
from waste_collection_schedule.transformers import ICSTransformer

_API_URL = (
    "https://wastemanagement.awg.de/WasteManagementDonauwald/WasteManagementServlet"
)


def _address(city: str, street: str, hnr: "str | int", addition: str = "", **_) -> dict:
    return {
        "Ort": city,
        "Strasse": street,
        "Hausnummer": str(hnr),
        "Hausnummerzusatz": addition,
    }


@final
class Source(BaseSource):
    TITLE = "ZAW Donau-Wald"
    DESCRIPTION = "Source for ZAW Donau-Wald."
    URL = "https://www.awg.de/"
    COUNTRY = "de"
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.ORGANIC, wt.PAPER]

    TEST_CASES: ClassVar[dict] = {
        "Achslach Aign 1 ": {"city": "Achslach", "street": "Aign", "hnr": "1"},
        "Böbrach Bärnerauweg 10A": {
            "city": "Böbrach",
            "street": "Bärnerauweg",
            "hnr": 10,
            "addition": "A",
        },
        "Am Bäckergütl 1, 94094 Malching": {
            "city": "Malching",
            "street": "Am Bäckergütl",
            "hnr": 1,
            "addition": "",
        },
    }

    PARAMS = (
        city(field="city"),
        street(field="street"),
        house_number(field="hnr"),
        text_field("addition", "Address addition", optional=True),
    )

    retrieve = AthosWasteManagementRetriever(
        url=_API_URL,
        initial_params={
            "SubmitAction": "wasteDisposalServices",
            "InFrameMode": "true",
        },
        state="rescrape",
        verify=False,
        steps=[
            {
                "submit_action": "CITYCHANGED",
                "fields": lambda city, **_: {"Ort": city, "Strasse": ""},
            },
            {"submit_action": "forward", "fields": _address},
            {"submit_action": "filedownload_ICAL", "fields": _address},
        ],
    )
    parse = parsers.IcsParser()
    transform = ICSTransformer(
        type_value_map={
            "Restmuelltonne": wt.GENERAL_WASTE,
            "Restmüllcontainer": wt.GENERAL_WASTE,
            "Papiercontainer": wt.PAPER,
        }
    )

    def __init__(
        self,
        city: str,
        street: str,
        hnr: "str | int",
        addition: str = "",
    ):
        super().__init__(city=city, street=street, hnr=hnr, addition=addition)
