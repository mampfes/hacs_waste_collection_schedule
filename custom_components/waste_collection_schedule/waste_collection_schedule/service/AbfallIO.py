#!/usr/bin/env python3

import datetime
import re
from typing import TYPE_CHECKING, Any

from bs4 import BeautifulSoup, Tag

from ..parsers import Parser
from ..retrievers import RetrieverFunc

if TYPE_CHECKING:
    from ..base_source import BaseSource


SERVICE_MAP = [
    {
        "title": "EGST Steinfurt",
        "url": "https://www.egst.de/",
        "service_id": "e21758b9c711463552fb9c70ac7d4273",
    },
    {
        "title": "ALBA Berlin",
        "url": "https://berlin.alba.info/",
        "service_id": "9583a2fa1df97ed95363382c73b41b1b",
    },
    {
        "title": "ASO Abfall-Service Osterholz",
        "url": "https://www.aso-ohz.de/",
        "service_id": "040b38fe83f026f161f30f282b2748c0",
    },
    {
        "title": "Landkreis Bayreuth",
        "url": "https://www.landkreis-bayreuth.de/",
        "service_id": "951da001077dc651a3bf437bc829964e",
    },
    {
        "title": "Landkreis Calw",
        "url": "https://www.kreis-calw.de/",
        "service_id": "690a3ae4906c52b232c1322e2f88550c",
    },
    {
        "title": "Entsorgungsbetriebe Essen",
        "url": "https://www.ebe-essen.de/",
        "service_id": "9b5390f095c779b9128a51db35092c9c",
    },
    {
        "title": "Abfallwirtschaft Landkreis Freudenstadt",
        "url": "https://www.awb-fds.de/",
        "service_id": "595f903540a36fe8610ec39aa3a06f6a",
    },
    {
        "title": "Göttinger Entsorgungsbetriebe",
        "url": "https://www.geb-goettingen.de/",
        "service_id": "7dd0d724cbbd008f597d18fcb1f474cb",
    },
    {
        "title": "Landkreis Heilbronn",
        "url": "https://www.landkreis-heilbronn.de/",
        "service_id": "1a1e7b200165683738adddc4bd0199a2",
    },
    {
        "title": "Abfallwirtschaft Landkreis Kitzingen",
        "url": "https://www.abfallwelt.de/",
        "service_id": "594f805eb33677ad5bc645aeeeaf2623",
    },
    {
        "title": "Abfallwirtschaft Landkreis Landsberg am Lech",
        "url": "https://www.abfallberatung-landsberg.de/",
        "service_id": "7df877d4f0e63decfb4d11686c54c5d6",
    },
    {
        "title": "Stadt Landshut",
        "url": "https://www.landshut.de/",
        "service_id": "bd0c2d0177a0849a905cded5cb734a6f",
    },
    {
        "title": "Ludwigshafen am Rhein",
        "url": "https://www.ludwigshafen.de/",
        "service_id": "6efba91e69a5b454ac0ae3497978fe1d",
    },
    {
        "title": "MüllALARM / Schönmackers",
        "url": "https://www.schoenmackers.de/",
        "service_id": "e5543a3e190cb8d91c645660ad60965f",
    },
    {
        "title": "Abfallbewirtschaftung Ostalbkreis",
        "url": "https://www.goa-online.de/",
        "service_id": "3ca331fb42d25e25f95014693ebcf855",
    },
    {
        "title": "Landkreis Oldenburg",
        "url": "https://www.oldenburg-kreis.de/",
        "service_id": "27708a019a2e35de7eb4bbe7c851609f",
    },
    {
        "title": "Landkreis Ostallgäu",
        "url": "https://www.buerger-ostallgaeu.de/",
        "service_id": "342cedd68ca114560ed4ca4b7c4e5ab6",
    },
    {
        "title": "Rhein-Neckar-Kreis",
        "url": "https://www.rhein-neckar-kreis.de/",
        "service_id": "914fb9d000a9a05af4fd54cfba478860",
    },
    {
        "title": "Landkreis Rotenburg (Wümme)",
        "url": "https://lk-awr.de/",
        "service_id": "645adb3c27370a61f7eabbb2039de4f1",
    },
    {
        "title": "Landkreis Sigmaringen",
        "url": "https://www.landkreis-sigmaringen.de/",
        "service_id": "39886c5699d14e040063c0142cd0740b",
    },
    {
        "title": "Landratsamt Traunstein",
        "url": "https://www.traunstein.com/",
        "service_id": "279cc5db4db838d1cfbf42f6f0176a90",
    },
    {
        "title": "Landratsamt Unterallgäu",
        "url": "https://www.landratsamt-unterallgaeu.de/",
        "service_id": "c22b850ea4eff207a273e46847e417c5",
    },
    {
        "title": "AWB Westerwaldkreis",
        "url": "https://wab.rlp.de/",
        "service_id": "248deacbb49b06e868d29cb53c8ef034",
    },
    {
        "title": "Landkreis Limburg-Weilburg",
        "url": "https://www.awb-lm.de/",
        "service_id": "0ff491ffdf614d6f34870659c0c8d917",
    },
    {
        "title": "Landkreis Weißenburg-Gunzenhausen",
        "url": "https://www.landkreis-wug.de",
        "service_id": "31fb9c7d783a030bf9e4e1994c7d2a91",
    },
    {
        "title": "VIVO Landkreis Miesbach",
        "url": "https://www.vivowarngau.de/",
        "service_id": "4e33d4f09348fdcc924341bf2f27ec86",
    },
    {
        "title": "Abfallzweckverband Rhein-Mosel-Eifel (Landkreis Mayen-Koblenz)",
        "url": "https://www.azv-rme.de/",
        "service_id": "8303df78b822c30ff2c2f98e405f86e6",
    },
    {
        "title": "Team Orange (Landkreis Würzburg)",
        "url": "https://www.team-orange.info/",
        "service_id": "3701fd1ff111f63996ab46a448669ea3",
    },
    {
        "title": "Landkreis Cuxhaven",
        "url": "https://www.landkreis-cuxhaven.de/",
        "service_id": "49fe8a63a056adbfc43f051f61dd4a44",
    },
    {
        "title": "Landkreis Rottweil",
        "url": "https://landkreis-rottweil.de",
        "service_id": "d287412901d68d66825e588a60c94641",
    },
    {
        "title": "ASG Nordsachsen",
        "url": "https://www.asg-nordsachsen.de/",
        "service_id": "1d78841c5d7fc43ebe52b9dc01f6b962",
    },
    {
        "title": "AVR Kommunal, Rhein-Neckar-Kreis",
        "url": "https://www.avr-kommunal.de/",
        "service_id": "914fb9d000a9a05af4fd54cfba478860",
    },
    {
        "title": "AWG Abfallwirtschaft Landkreis Calw",
        "url": "https://www.awg-info.de/",
        "service_id": "0813ea99f520c462373386564a99a51e",
    },
    {
        "title": "Amt Bad Wilsnack/Weisen (Landkreis Prignitz)",
        "url": "https://www.landkreis-prignitz.de/",
        "service_id": "1e9592418582666e2a5d1c62b2683435",
    },
    {
        "title": "Gemeinde Groß Pankow (Landkreis Prignitz)",
        "url": "https://www.landkreis-prignitz.de/",
        "service_id": "af91b65d2753a219309072837d8ea4e1",
    },
    {
        "title": "Gemeinde Gumtow (Landkreis Prignitz)",
        "url": "https://www.landkreis-prignitz.de/",
        "service_id": "3cefa45ab357d231891bb497253c630f",
    },
    {
        "title": "Gemeinde Karstädt (Landkreis Prignitz)",
        "url": "https://www.landkreis-prignitz.de/",
        "service_id": "798f59a75627f5d7686dab0c7226c877",
    },
    {
        "title": "Amt Lenzen-Elbtalaue (Landkreis Prignitz)",
        "url": "https://www.landkreis-prignitz.de/",
        "service_id": "bb937857acd951dfc8de5be8b8a49f6d",
    },
    {
        "title": "Amt Meyenburg (Landkreis Prignitz)",
        "url": "https://www.landkreis-prignitz.de/",
        "service_id": "4638881e7bebe6869e2e86de5f8aa09e",
    },
    {
        "title": "Stadt Perleberg (Landkreis Prignitz)",
        "url": "https://www.landkreis-prignitz.de/",
        "service_id": "9fb3e2e5498e825250105ee272102a7b",
    },
    {
        "title": "Gemeinde Plattenburg (Landkreis Prignitz)",
        "url": "https://www.landkreis-prignitz.de/",
        "service_id": "a0461612534502273c518e28d4f6f1e4",
    },
    {
        "title": "Stadt Pritzwalk (Landkreis Prignitz)",
        "url": "https://www.landkreis-prignitz.de/",
        "service_id": "d92f59ef4066ae6d299478996d1d8430",
    },
    {
        "title": "Amt Putlitz/Berge (Landkreis Prignitz)",
        "url": "https://www.landkreis-prignitz.de/",
        "service_id": "4f06df48f154246415e57ce12b26abe5",
    },
    {
        "title": "Stadt Wittenberge (Landkreis Prignitz)",
        "url": "https://www.landkreis-prignitz.de/",
        "service_id": "b870ecfa6e1f882680758d374ba3fa2d",
    },
]


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
