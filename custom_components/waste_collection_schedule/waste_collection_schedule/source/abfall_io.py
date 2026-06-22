import datetime
import re
from typing import Any, final

from bs4 import BeautifulSoup, Tag
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.regions import Region, region
from waste_collection_schedule.service.AbfallIO import SERVICE_MAP
from waste_collection_schedule.service.ICS import ICS
from waste_collection_schedule.transformers import ICSTransformer

# Demonstrates: a second deep stateful flow (a method retrieve()), plus a method
# parse() that cleans the response before the shared ICS parser. The AbfallPlus /
# abfall.io API is a server-side wizard: POST "init" for a token and the form's
# hidden fields, then walk the kommune -> (bezirk) -> strasse -> (house number)
# cascade, each step POSTing the accumulated state back so the server advances,
# before POSTing "export_ics" for the calendar. Some providers wrap the ICS in
# HTML warning lines (an extra special-waste radio list); parse() strips those,
# decodes UTF-8 explicitly, then hands the feed to ICS().convert, with the German
# bin names resolved by the shared multilingual vocabulary.
#
# Note: the real config UI is a 4-level cascading wizard (kommune/bezirk/strasse/
# house number, each fetched from the previous choice), which is deeper than the
# two-level config_params.dependent_select. PARAMS here declare the resolved IDs
# the fetch needs; capturing the full cascade in the config flow is a separate
# concern (the legacy wizard module), out of scope for this pipeline migration.

MODUS_KEY = "d6c5855a62cf32a4dadbc2831f0f295f"
API_URL = "https://api.abfall.io"


def _hidden_inputs(text: str) -> dict[str, str]:
    """All hidden form fields (incl. the token and accumulated server state)."""
    args: dict[str, str] = {}
    for inp in BeautifulSoup(text, "html.parser").find_all("input"):
        if not isinstance(inp, Tag) or inp.get("type") != "hidden":
            continue
        name = inp.get("name")
        if isinstance(name, str):
            value = inp.get("value")
            args[name] = value if isinstance(value, str) else ""
    return args


@final
class Source(BaseSource):
    TITLE = "Abfall.IO / AbfallPlus"
    DESCRIPTION = (
        "Source for AbfallPlus.de waste collection. Service is hosted on abfall.io."
    )
    URL = "https://www.abfallplus.de"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True

    TEST_CASES = {
        "Landshut": {
            "key": "bd0c2d0177a0849a905cded5cb734a6f",
            "f_id_kommune": 2655,
            "f_id_bezirk": 2655,
            "f_id_strasse": 763,
        },
        "Schoenmackers": {
            "key": "e5543a3e190cb8d91c645660ad60965f",
            "f_id_kommune": 3682,
            "f_id_strasse": "3682adenauerplatz",
            "f_id_strasse_hnr": "20417",
        },
        "Ludwigshafen am Rhein": {
            "key": "6efba91e69a5b454ac0ae3497978fe1d",
            "f_id_kommune": "5916",
            "f_id_strasse": "5916abteistrasse",
            "f_id_strasse_hnr": 33,
        },
        "AWB Limburg-Weilburg": {
            "key": "0ff491ffdf614d6f34870659c0c8d917",
            "f_id_kommune": 6031,
            "f_id_strasse": 621,
            "f_id_strasse_hnr": 872,
            "f_abfallarten": [27, 28, 17, 67],
        },
        "Landkreis Prignitz, Gemeinde Karstädt, Blüthen": {
            "key": "798f59a75627f5d7686dab0c7226c877",
            "f_id_kommune": 3229,
            "f_id_bezirk": 31,
            "f_id_strasse": 322,
            "f_id_strasse_hnr": 323,
        },
        "Landkreis Prignitz, Gemeinde Karstädt, restliche Straßen": {
            "key": "798f59a75627f5d7686dab0c7226c877",
            "f_id_kommune": 3229,
            "f_id_bezirk": 41,
            "f_id_strasse": 333,
            "f_id_strasse_hnr": 333,
        },
    }

    PARAMS = [
        text_field("key", "Key"),
        text_field("f_id_kommune", "Kommune ID"),
        text_field("f_id_strasse", "Straße ID"),
        text_field("f_id_bezirk", "Bezirk ID", optional=True),
        text_field("f_id_strasse_hnr", "Hausnummer ID", optional=True),
        text_field("f_abfallarten", "Abfallarten", optional=True),
    ]

    transform = ICSTransformer()

    def __init__(
        self,
        key: str,
        f_id_kommune: int | str,
        f_id_strasse: int | str,
        f_id_bezirk: int | str | None = None,
        f_id_strasse_hnr: int | str | None = None,
        f_abfallarten: list[int] | None = None,
    ):
        super().__init__(
            key=key,
            f_id_kommune=f_id_kommune,
            f_id_strasse=f_id_strasse,
            f_id_bezirk=f_id_bezirk,
            f_id_strasse_hnr=f_id_strasse_hnr,
            f_abfallarten=f_abfallarten,
        )

    @staticmethod
    def REGIONS() -> list[Region]:
        return [
            region(s["title"], url=s["url"], key=s["service_id"]) for s in SERVICE_MAP
        ]

    def retrieve(self, source):
        key = source.params["key"]
        session = source.session

        def post(waction: str, data: dict | None = None):
            return session.post(
                API_URL,
                params={"key": key, "modus": MODUS_KEY, "waction": waction},
                data=data,
            )

        r = post("init")
        if r.status_code == 401:
            raise ValueError(
                f"API key '{key}' is no longer valid for the legacy abfall.io API. "
                "This provider may have migrated to the new abfall.io v3 API, which "
                "is not yet supported. See "
                "https://github.com/mampfes/hacs_waste_collection_schedule/issues/3788"
            )
        r.raise_for_status()
        # Holds hidden form fields (str) plus the int/str IDs we inject; all are
        # form-encoded to strings on POST, so the value type is intentionally Any.
        args: dict[str, Any] = _hidden_inputs(r.text)
        args["f_id_kommune"] = source.params["f_id_kommune"]

        def step(waction: str) -> None:
            response = post(waction, args)
            response.raise_for_status()
            args.update(_hidden_inputs(response.text))

        bezirk = source.params.get("f_id_bezirk")
        strasse = source.params["f_id_strasse"]
        hnr = source.params.get("f_id_strasse_hnr")

        # A bezirk (district) selection needs the intermediate steps so the
        # server accumulates the correct per-step state before the export.
        if bezirk is not None:
            args["f_id_bezirk"] = bezirk
            step("auswahl_bezirk_set")
            args["f_id_strasse"] = strasse
            step("auswahl_strasse_set")
            if hnr is not None:
                args["f_id_strasse_hnr"] = hnr
                step("auswahl_hnr_set")
        else:
            args["f_id_strasse"] = strasse
            if hnr is not None:
                args["f_id_strasse_hnr"] = hnr

        abfallarten = source.params.get("f_abfallarten") or []
        for i, abfalltyp in enumerate(abfallarten):
            args[f"f_id_abfalltyp_{i}"] = abfalltyp
        args["f_abfallarten_index_max"] = len(abfallarten)
        args["f_abfallarten"] = ",".join(str(a) for a in abfallarten)

        today = datetime.date.today()
        end = today + datetime.timedelta(days=365)
        args["f_zeitraum"] = f"{today:%Y%m%d}-{end:%Y%m%d}"

        return post("export_ics", args)

    def parse(self, response, source=None):
        # requests/curl_cffi can misdetect the charset; the feed is UTF-8.
        text = response.content.decode("utf-8", errors="replace")
        # Some providers prepend HTML warning lines (an extra special-waste radio
        # list) that aren't valid iCalendar; drop them before parsing.
        if "<b" in text:
            text = re.sub(r"<br.*|<b.*", "\r", text)
        return ICS().convert(text)
