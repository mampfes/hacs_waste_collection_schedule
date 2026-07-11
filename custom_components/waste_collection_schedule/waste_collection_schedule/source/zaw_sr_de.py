"""ZAW-SR Straubing (zaw-sr.de).

Athos "WasteManagementServlet" wizard: CITYCHANGED, STREETCHANGED, a
combined address+download ``forward``, then download.

The legacy source builds its own multipart/form-data POST body, disables
TLS verification, and re-parses every ``<INPUT>``/``<SELECT>`` field from
each response (the address form renders as dropdowns rather than plain
inputs). None of that turned out to be required: a live comparison found
the servlet accepts the retriever's plain url-encoded POSTs over a
verified TLS connection identically, so the extra machinery is dropped
here (confirmed live: 12/56 collections, matching the legacy source's two
TEST_CASES exactly).

Known gap (documented, not reproduced here): the legacy source scrapes
``NAME="Zeitraum" VALUE="..."`` radio alternatives off the initial page and
re-runs the whole wizard once per alternative found (a Bielefeld-style
multi-run). Neither TEST_CASE address ever exposed more than the single
default period (confirmed live), so this always takes the common,
single-run path; an address that genuinely offered multiple periods would
need that fan-out reintroduced. Like the legacy source, ``ApplicationName``
also changes once the address is accepted (from the wizard's own model to
``com.athos.kd.straubing.AbfuhrTerminModel``); the retriever never
re-scrapes mid-flow, so that value is hardcoded on the download step
instead of picked up dynamically.
"""

from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    city,
    house_number,
    street,
    text_field,
)
from waste_collection_schedule.retrievers import AthosWasteManagementRetriever
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GENERAL_WASTE,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_SERVLET = "https://straubing.zaw-sr.de/WasteManagementStraubing/WasteManagementServlet"


@final
class Source(BaseSource):
    TITLE = "ZAW-SR Straubing"
    DESCRIPTION = (
        "Source for ZAW-SR (Zweckverband Abfallwirtschaft Straubing Stadt und Land)."
    )
    URL = "https://www.zaw-sr.de"
    COUNTRY = "de"

    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Straubing Theresienplatz 1": {
            "city": "Straubing",
            "street": "Theresienplatz",
            "hnr": "1",
        },
        "Straubing Stadtgraben 1": {
            "city": "Straubing",
            "street": "Stadtgraben",
            "hnr": "1",
        },
    }

    PARAMS = (
        city(field="city"),
        street(field="street"),
        house_number(field="hnr"),
        text_field("addition", "House number suffix", default=""),
    )

    retrieve = AthosWasteManagementRetriever(
        url=_SERVLET,
        initial_params={"SubmitAction": "wasteDisposalServices", "InFrameMode": "TRUE"},
        steps=[
            {
                "submit_action": "CITYCHANGED",
                "fields": lambda city, **_: {
                    "Ort": city,
                    "Strasse": "",
                    "Hausnummer": "",
                },
            },
            {
                "submit_action": "STREETCHANGED",
                "fields": lambda city, street, **_: {
                    "Ort": city,
                    "Strasse": street,
                    "Hausnummer": "",
                },
            },
            {
                "submit_action": "forward",
                "fields": lambda city, street, hnr, addition="", **_: {
                    "Ort": city,
                    "Strasse": street,
                    "Hausnummer": str(hnr),
                    "Hausnummerzusatz": addition,
                },
            },
            {
                "submit_action": "filedownload_ICAL",
                "fields": lambda **_: {
                    "ApplicationName": "com.athos.kd.straubing.AbfuhrTerminModel",
                },
            },
        ],
    )
    parse = parsers.IcsParser()
    transform = ICSTransformer(
        clean=lambda label: label.split()[0],
        type_value_map={
            "restmuell": GENERAL_WASTE,
            "restmüll": GENERAL_WASTE,
            "restmülltonne": GENERAL_WASTE,
            "bio": ORGANIC,
            "biotonne": ORGANIC,
            "bioabfall": ORGANIC,
            "papier": PAPER,
            "papiertonne": PAPER,
            "gelbe": RECYCLABLES,
            "gelber": RECYCLABLES,
            "wertstofftonne": RECYCLABLES,
        },
    )

    def __init__(self, city: str, street: str, hnr: str, addition: str = ""):
        super().__init__(city=city, street=street, hnr=hnr, addition=addition)
