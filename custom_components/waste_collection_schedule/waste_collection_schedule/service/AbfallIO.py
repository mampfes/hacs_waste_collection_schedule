#!/usr/bin/env python3

import datetime
import re
from typing import TYPE_CHECKING, Any

from bs4 import BeautifulSoup, Tag

from ..parsers import Parser
from ..retrievers import RetrieverFunc

if TYPE_CHECKING:
    from ..base_source import BaseSource


# --------------------------------------------------------------------------- #
# Pipeline components (BaseSource architecture)
#
# The AbfallPlus / abfall.io API is a server-side wizard: POST "init" for a
# token and the form's hidden fields, then walk the kommune -> (bezirk) ->
# strasse -> (house number) cascade, each step POSTing the accumulated state
# back so the server advances, before POSTing "export_ics" for the calendar.
# That stateful acquisition belongs to the platform, so it lives here as a
# retriever rather than in every abfall.io source:
#
#     retrieve = AbfallIoRetriever()
#     parse    = AbfallIoParser()
#
# AbfallIoRetriever runs the wizard on the shared session and returns the final
# export_ics response; AbfallIoParser strips the HTML warning lines some
# providers prepend, decodes UTF-8 explicitly, then hands the feed to the shared
# ICS converter. ``list_choices`` replays the same wizard to enumerate one
# cascade level's options for the config flow (config_params.cascading_select).
# --------------------------------------------------------------------------- #

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


def list_choices(key: str, field: str, selections: dict) -> list[tuple[str, str]]:
    """Walk the abfall.io form and return one level's options as (name, id).

    Replays the wizard up to ``field`` using the ids already in ``selections``
    (the same flow the retriever uses for fetching), following the form's own
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


class AbfallIoRetriever(RetrieverFunc):
    """Walk the abfall.io wizard and return the final ``export_ics`` response.

    Reads the platform's fixed cascade fields from ``source.params``: ``key``,
    ``f_id_kommune``, ``f_id_strasse``, and the optional ``f_id_bezirk`` /
    ``f_id_strasse_hnr`` / ``f_abfallarten``. Runs on the shared session so
    cookies and the server-side wizard state are reused across the steps.
    """

    def __call__(self, source: "BaseSource"):
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


class AbfallIoParser(Parser["list[tuple[datetime.date, str]]"]):
    """Decode the export_ics response into ``(date, summary)`` rows.

    Strips the HTML warning lines some providers prepend (an extra special-waste
    radio list that isn't valid iCalendar), decodes UTF-8 explicitly (the stack
    can misdetect the charset), then hands the feed to the shared ICS converter.
    """

    def __call__(
        self, response, source: "BaseSource | None" = None
    ) -> "list[tuple[datetime.date, str]]":
        from waste_collection_schedule.service.ICS import ICS

        text = response.content.decode("utf-8", errors="replace")
        if "<b" in text:
            text = re.sub(r"<br.*|<b.*", "\r", text)
        return ICS().convert(text)
