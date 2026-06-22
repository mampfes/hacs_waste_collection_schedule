import datetime
import re
from typing import Any, final

from bs4 import BeautifulSoup, Tag
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import cascading_select, text_field
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
# The 4-level config wizard (kommune -> bezirk -> strasse -> house number, each
# fetched from the previous choice) is expressed with config_params.cascading_
# select: get_choices(field, selections) walks the same form to list one level's
# options as (name, id) pairs, so the config flow shows names while storing the
# ids the fetch already uses (TEST_CASES and fetch unchanged).

MODUS_KEY = "d6c5855a62cf32a4dadbc2831f0f295f"
API_URL = "https://api.abfall.io"

# The form's onchange handler names the waction to submit for the next step.
_WACTION_RE = re.compile(r'(?<=awk-data-onchange-submit-waction=")[^\n\r"]+')
_CASCADE_FIELDS = ("f_id_kommune", "f_id_bezirk", "f_id_strasse", "f_id_strasse_hnr")


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


def _select_options(soup: BeautifulSoup, field: str) -> list[tuple[str, str]]:
    """The ``<select name=field>`` options as (visible name, stored id) pairs."""
    select = soup.find("select", attrs={"name": field})
    if not isinstance(select, Tag):
        return []
    pairs: list[tuple[str, str]] = []
    for option in select.find_all("option"):
        if not isinstance(option, Tag):
            continue
        value = option.get("value")
        name = option.get_text(strip=True)
        if isinstance(value, str) and value and value != "-1" and name:
            pairs.append((name, value))
    return pairs


def _list_choices(key: str, field: str, selections: dict) -> list[tuple[str, str]]:
    """Walk the abfall.io form and return one level's options as (name, id).

    Replays the wizard up to ``field`` using the ids already in ``selections``
    (the same flow ``retrieve`` uses for fetching), following the form's own
    onchange waction at each step. Returns ``[]`` if the level is not applicable
    for the given selections (e.g. a kommune with no bezirk).
    """
    from curl_cffi import requests as cffi_requests

    session = cffi_requests.Session(impersonate="chrome")

    def post(waction: str, data: dict | None = None):
        return session.post(
            API_URL,
            params={"key": key, "modus": MODUS_KEY, "waction": waction},
            data=data,
        )

    response = post("init")
    if response.status_code != 200:
        return []
    data = response.text
    args: dict[str, Any] = {}
    # Advance one cascade level per step; bounded so a malformed flow can't loop.
    for _ in range(len(_CASCADE_FIELDS) + 1):
        soup = BeautifulSoup(data, "html.parser")
        options = _select_options(soup, field)
        if options:
            return options
        # The page presents exactly one cascade select at a time. To advance we
        # must be able to fill the one shown; if it is the target or we have no
        # value for it, the target level is not applicable for these selections.
        current = next(
            (
                level
                for level in _CASCADE_FIELDS
                if isinstance(soup.find("select", attrs={"name": level}), Tag)
            ),
            None,
        )
        value = selections.get(current) if current else None
        if current is None or current == field or value in (None, ""):
            return []
        args.update(_hidden_inputs(data))
        args[current] = value
        wactions = _WACTION_RE.findall(data)
        if not wactions:
            return []
        response = post(wactions[0], args)
        if response.status_code != 200:
            return []
        data = response.text
    return []


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
        cascading_select(
            ("f_id_kommune", "Kommune"),
            ("f_id_bezirk", "Bezirk"),
            ("f_id_strasse", "Straße"),
            ("f_id_strasse_hnr", "Hausnummer"),
        ),
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

    @classmethod
    def get_choices(cls, field: str, selections: dict) -> list[tuple[str, str]]:
        """Options for one cascade level given the levels chosen so far.

        Implements the config_params.cascading_select contract. Returns
        (visible name, stored id) pairs walked live from the abfall.io form, or
        [] when this level does not apply to the current selections.
        """
        key = selections.get("key")
        if not key:
            return []
        return _list_choices(str(key), field, selections)

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
