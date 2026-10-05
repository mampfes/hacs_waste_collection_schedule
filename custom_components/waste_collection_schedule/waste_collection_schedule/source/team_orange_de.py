"""Team Orange (Landkreis Würzburg).

Reverse-engineered from the athos WasteManagementServlet behind the Regiogate
CMS wrapper (https://www.team-orange.info/muellabfuhr/abfallkalender/); the
calendar app is an iframe into the classic servlet, so no browser automation is
needed.

Demonstrates ``IcsSessionRetriever``'s cascading form selects on an Athos
deployment whose every response carries a fresh ``SessionId`` and
``ApplicationName`` that the next request must echo back: the first three steps
each read the options their own response offers and resolve one address field
against them (municipality, then its streets, then that street's house
numbers), so the next step submits a spelling the servlet will accept, and each
step's ``extract`` carries the session state forward. The last step's response
is the ICS download, so ``feed_url`` stays ``None``.
"""

from typing import Any, ClassVar, final

from bs4 import BeautifulSoup
from waste_collection_schedule import parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, municipality, street
from waste_collection_schedule.preprocessors import SortRows
from waste_collection_schedule.response_shape import ResponseShapeError
from waste_collection_schedule.service.ICS import IcsFeedsParser, IcsSessionRetriever
from waste_collection_schedule.transformers import ICSTransformer

_API_URL = (
    "https://athosweb.team-orange.info/WasteManagementWuerzburg/WasteManagementServlet"
)
_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64)"}

# Waste types read like "Restmüll 02-wöchentl." or
# "Problemmüll 13-16 Uhr Wertstoffhof Klingholz": matched by substring.
_TYPE_VALUE_MAP = {
    "Restmüll": wt.GENERAL_WASTE,
    "Papier": wt.PAPER,
    "Bioabfall": wt.ORGANIC,
    "Gelbe Tonne": wt.RECYCLABLES,
    "LVP": wt.RECYCLABLES,
    "Problemmüll": wt.HAZARDOUS,
    "Elektro": wt.ELECTRONICS,
    "Schrott": wt.OTHER,
}


def _bin(label: str) -> str:
    # The servlet pads names with trailing/duplicated whitespace, e.g.
    # "Gelbe Tonne " or "Problemmüll  9-12 Uhr ...".
    label = " ".join(label.split())
    for key in _TYPE_VALUE_MAP:
        if key in label:
            return key
    return label


def _session_state(response: Any, context: "dict[str, Any]") -> "dict[str, str]":
    """The SessionId/ApplicationName the servlet wants echoed back next."""
    soup = BeautifulSoup(response.text, "html.parser")
    state: dict[str, str] = {}
    for name, key in (("SessionId", "session_id"), ("ApplicationName", "app")):
        field = soup.find("input", {"name": name})
        value = field.get("value") if field is not None else None
        if not value:
            raise ResponseShapeError(
                "team_orange_de",
                f"the servlet response carries no {name} token",
            )
        state[key] = str(value)
    return state


def _form(
    action: str,
    session_id: str,
    app: str,
    ort: str,
    strasse: str = "",
    hausnummer: str = "",
    **extra: str,
) -> "dict[str, str]":
    return {
        "ApplicationName": app,
        "SessionId": session_id,
        "SubmitAction": action,
        "Ort": ort,
        "Strasse": strasse,
        "Hausnummer": hausnummer,
        "InFrameMode": "TRUE",
        **extra,
    }


@final
class Source(BaseSource):
    TITLE = "Team Orange (Landkreis Würzburg)"
    DESCRIPTION = "Source for team orange waste collection in Landkreis Würzburg."
    URL = "https://www.team-orange.info"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True
    SOURCE_CODEOWNERS: ClassVar[list[str]] = ["@ChrisKoh83"]

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.PAPER,
        wt.ORGANIC,
        wt.RECYCLABLES,
        wt.HAZARDOUS,
        wt.ELECTRONICS,
        wt.OTHER,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Altertheim": {"ort": "Altertheim", "strasse": "Am Berg", "hausnummer": 1},
        "Reichenberg (Rathaus)": {
            "ort": "Reichenberg",
            "strasse": "Kirchgasse",
            "hausnummer": 5,
        },
    }

    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unknown municipality": {
            "ort": "Nirgendwo",
            "strasse": "Am Berg",
            "hausnummer": 1,
        },
    }

    HOWTO: ClassVar[dict[str, str]] = {
        "de": (
            "Ort, Straße und Hausnummer entnehmen Sie bitte dem Abfallkalender "
            "auf https://www.team-orange.info/muellabfuhr/abfallkalender/."
        ),
        "en": (
            "Please take Ort (municipality), Strasse (street) and Hausnummer "
            "(street number) from the calendar at "
            "https://www.team-orange.info/muellabfuhr/abfallkalender/."
        ),
    }

    PARAMS = (
        municipality(field="ort"),
        street(field="strasse"),
        house_number(field="hausnummer"),
    )

    retrieve = IcsSessionRetriever(
        headers=_HEADERS,
        steps=[
            # The first three steps each read the options their own response
            # offers and resolve one address field against them.
            {
                "url": _API_URL,
                "params": {
                    "SubmitAction": "wasteDisposalServices",
                    "InFrameMode": "TRUE",
                },
                "encoding": "utf-8",
                "select": {"Ort": "ort"},
                "extract": _session_state,
            },
            {
                "method": "POST",
                "url": _API_URL,
                "data": lambda session_id, app, ort, **_: _form(
                    "CITYCHANGED", session_id, app, ort
                ),
                "encoding": "utf-8",
                "select": {"Strasse": "strasse"},
                "extract": _session_state,
            },
            {
                "method": "POST",
                "url": _API_URL,
                "data": lambda session_id, app, ort, strasse, **_: _form(
                    "STREETCHANGED", session_id, app, ort, strasse
                ),
                "encoding": "utf-8",
                "select": {"Hausnummer": "hausnummer"},
                "extract": _session_state,
            },
            # Forward to the appointment list, which offers the download.
            {
                "method": "POST",
                "url": _API_URL,
                "data": lambda session_id, app, ort, strasse, hausnummer, **_: _form(
                    "forward", session_id, app, ort, strasse, hausnummer
                ),
                "encoding": "utf-8",
                "extract": _session_state,
            },
            # No feed_url: this step's own response is the ICS download.
            {
                "method": "POST",
                "url": _API_URL,
                "data": lambda session_id, app, ort, strasse, hausnummer, **_: _form(
                    "filedownload_ICAL",
                    session_id,
                    app,
                    ort,
                    strasse,
                    hausnummer,
                    ICalErinnerung="keine Erinnerung",
                ),
            },
        ],
        lookahead_month=None,
    )

    parse = IcsFeedsParser(parsers.IcsParser())

    # The raw label keeps what the canonical type drops: the rhythm
    # ("02-wöchentl.") and, for Problemmüll, the drop-off site and hours.
    transform = ICSTransformer(
        clean=_bin, type_value_map=_TYPE_VALUE_MAP, carry_raw_label=True
    )

    # The servlet returns the events in varying order across requests.
    preprocess = SortRows()
