"""Generic ICS (iCalendar) source.

The raw-passthrough ICS engine behind ~178 YAML providers (doc/ics/yaml/*.yaml,
served through config_flow's ICS-YAML mechanism) and usable directly for any
other provider that only publishes an .ics feed. Unlike every other pipeline
source this one has no fixed vocabulary to map onto WasteTypes: the feed's own
VEVENT summary becomes the collection title verbatim (the legacy
``Collection(date, t=...)`` raw-string form), so ``classify()`` builds that
directly instead of declaring a transformer.

Demonstrates: ``config_params.integer``/``boolean``/``raw_object``, the three
widget kinds added alongside this conversion so a source with genuinely
arbitrary numeric/boolean/dict fields (``offset``, ``verify_ssl``, extra POST
``params``, extra ``headers``) needs no config-flow UI compromise.
"""

import datetime
import logging
import re
from os import getcwd
from pathlib import Path
from typing import Any, ClassVar, final

from curl_cffi import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    alternatives,
    boolean,
    dropdown,
    integer,
    raw_object,
    text_field,
)
from waste_collection_schedule.exceptions import (
    SourceArgumentException,
    SourceArgumentExceptionMultiple,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.service.ICS import ICS, IcsEvent

# Kept as module-level constants (rather than moved onto the class) so that
# test_source_components.py's "hasattr(module, name) counts even when falsy"
# rule keeps accepting URL = None: this is a generic engine with no single
# provider site, exactly as under the legacy module-level contract.
TITLE = "ICS"
DESCRIPTION = "Source for ICS based schedules."
URL = None
TEST_CASES = {
    "Esslingen, Bahnhof": {
        "url": "https://api.abfall.io/?kh=DaA02103019b46345f1998698563DaAd&t=ics&s=1a862df26f6943997cef90233877a4fe"
    },
    "Test File": {
        # Path is used here to allow to call the Source from any location.
        # This is not required in a yaml configuration!
        "file": str(Path(__file__).resolve().parents[1].joinpath("test/test.ics"))
    },
    "Test File (recurring)": {
        # Path is used here to allow to call the Source from any location.
        # This is not required in a yaml configuration!
        "file": str(Path(__file__).resolve().parents[1].joinpath("test/recurring.ics"))
    },
    "München, Bahnstr. 11": {
        "url": "https://www.awm-muenchen.de/entsorgen/abfuhrkalender?tx_awmabfuhrkalender_abfuhrkalender%5Bhausnummer%5D=11&tx_awmabfuhrkalender_abfuhrkalender%5Bleerungszyklus%5D%5BB%5D=1%2F2%3BU&tx_awmabfuhrkalender_abfuhrkalender%5Bleerungszyklus%5D%5BP%5D=1%2F2%3BG&tx_awmabfuhrkalender_abfuhrkalender%5Bleerungszyklus%5D%5BR%5D=001%3BU&tx_awmabfuhrkalender_abfuhrkalender%5Bsection%5D=ics&tx_awmabfuhrkalender_abfuhrkalender%5Bsinglestandplatz%5D=false&tx_awmabfuhrkalender_abfuhrkalender%5Bstandplatzwahl%5D=true&tx_awmabfuhrkalender_abfuhrkalender%5Bstellplatz%5D%5Bbio%5D=70024507&tx_awmabfuhrkalender_abfuhrkalender%5Bstellplatz%5D%5Bpapier%5D=70024507&tx_awmabfuhrkalender_abfuhrkalender%5Bstellplatz%5D%5Brestmuell%5D=70024507&tx_awmabfuhrkalender_abfuhrkalender%5Bstrasse%5D=bahnstr.&tx_awmabfuhrkalender_abfuhrkalender%5Byear%5D={%Y}",
        "version": 1,
    },
    #    "Hausmüllinfo: ASR Chemnitz": {
    #        "url": "https://asc.hausmuell.info/ics/ics.php",
    #        "method": "POST",
    #        "params": {
    #            "hidden_id_egebiet": 439087,
    #            "input_ort": "Chemnitz",
    #            "input_str": "Straße der Nationen",
    #            "input_hnr": 2,
    #            "hidden_send_btn": "ics",
    #            # "hiddenYear": 2021,
    #            "hidden_id_ort": 10,
    #            "hidden_id_ortsteil": 0,
    #            "hidden_id_str": 17814,
    #            "hidden_id_hnr": 5538100,
    #            "hidden_kalenderart": "privat",
    #            "showBinsBio": "on",
    #            "showBinsRest": "on",
    #            "showBinsRest_rc": "on",
    #            "showBinsPapier": "on",
    #            "showBinsOrganic": "on",
    #            "showBinsXmas": "on",
    #            "showBinsDsd": "on",
    #            "showBinsProb": "on",
    #        },
    #        "year_field": "hiddenYear",
    #    },
    "Abfall Zollernalbkreis, Ebingen": {
        "url": "https://www.abfallkalender-zak.de",
        "params": {
            "city": "2,3,4",
            "street": "3",
            "types[]": [
                "restmuell",
                "gelbersack",
                "papiertonne",
                "biomuell",
                "gruenabfall",
                "schadstoffsammlung",
                "altpapiersammlung",
                "schrottsammlung",
                "weihnachtsbaeume",
                "elektrosammlung",
            ],
            "go_ics": "Download",
        },
        "year_field": "year",
    },
    "ReCollect, Ottawa": {
        "url": "https://recollect.a.ssl.fastly.net/api/places/BCCDF30E-578B-11E4-AD38-5839C200407A/services/208/events.en.ics",
        "split_at": "\\, (?:and )?|(?: and )",
    },
    "ReCollect, Simcoe County": {
        "url": "https://recollect.a.ssl.fastly.net/api/places/08E862E8-8190-11E2-A8A6-C758AE7205AF/services/226/events.en.ics",
        "split_at": "\\, (?:and )?|(?: and )",
    },
    "Erlensee, Am Haspel": {
        "url": "https://sperrmuell.erlensee.de/?type=reminder",
        "method": "POST",
        "params": {
            "street": 8,
            "eventType[]": [27, 23, 19, 20, 21, 24, 22, 25, 26],
            "timeframe": 23,
            "download": "ical",
        },
    },
    "UTF-8-SIG (UTF-8 with BOM)": {
        "url": "https://servicebetrieb.koblenz.de/abfallwirtschaft/entsorgungstermine-digital/entsorgungstermine-2023-digital/altstadt-2023.ics?cid=2ui7",
    },
}


HEADERS = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
_LOGGER = logging.getLogger(__name__)


def _coerce_int(value: Any) -> "int | None":
    """Coerce a PARAMS-supplied value to int, tolerating None/empty/str/float.

    NumberSelector/YAML/UI callers may hand back a str, float or int; the ICS
    service and the year-field arithmetic below both want a plain int.
    """
    if value is None or value == "":
        return None
    return int(value)


def _flatten_params(params: "dict | None") -> "list[tuple[str, Any]] | None":
    """Flatten a params dict to (key, value) pairs, repeating list-valued keys.

    curl_cffi stringifies list-valued params as Python repr instead of
    repeating the key like ``requests`` does; flatten explicitly so multi-value
    fields like ``types[]`` still round-trip as repeated query/form keys.
    """
    if not params:
        return None
    return [
        (k, item)
        for k, v in params.items()
        for item in (v if isinstance(v, list) else [v])
    ]


def _fetch_url(
    url: str,
    params: "dict | None",
    method: str,
    headers: dict,
    verify_ssl: bool,
    impersonate: Any,
) -> str:
    # impersonate is free-text (any curl_cffi-supported browser string, e.g.
    # "chrome124"); curl_cffi's own type is a closed Literal, which a
    # user-configured value can never statically satisfy, hence Any here.
    flat_params = _flatten_params(params)

    if method == "GET":
        r = requests.get(
            url,
            params=flat_params,
            headers=headers,
            verify=verify_ssl,
            impersonate=impersonate,
        )
    elif method == "POST":
        r = requests.post(
            url,
            data=flat_params,
            headers=headers,
            verify=verify_ssl,
            impersonate=impersonate,
        )
    else:
        raise SourceArgumentNotFoundWithSuggestions("method", method, ["GET", "POST"])

    r.raise_for_status()

    if r.content.startswith(b"\xef\xbb\xbf"):
        r.encoding = "UTF-8-SIG"
    else:
        r.encoding = "utf-8"

    return r.text


def _fetch_file(file: str) -> str:
    try:
        path = Path(file)
        with path.open() as f:
            return f.read()
    except FileNotFoundError as e:
        _LOGGER.error(f"Working directory: '{getcwd()}'")
        raise SourceArgumentException(
            "file", f"File '{path.resolve()}' not found"
        ) from e


@final
class Source(BaseSource):
    TEST_CASES: ClassVar[dict] = TEST_CASES

    PARAMS = (
        alternatives(
            [text_field("url", label="URL", optional=True)],
            [text_field("file", label="File", optional=True)],
        ),
        text_field("year_field", label="Year field", optional=True),
        dropdown("method", ["GET", "POST"], label="Method", optional=True),
        text_field("regex", label="Regular expression", optional=True),
        text_field(
            "title_template", label="Title template", default="{{date.summary}}"
        ),
        text_field("split_at", label="Split at", optional=True),
        text_field(
            "impersonate",
            label="Browser to impersonate (e.g. 'chrome') to pass TLS-fingerprinting WAFs",
            optional=True,
        ),
        integer("offset", label="Offset"),
        boolean("verify_ssl", label="Verify SSL", default=True),
        raw_object("params", label="Parameters"),
        raw_object("headers", label="Headers"),
        # Deprecated, kept only so existing YAML configs (and this source's
        # own "München" TEST_CASE) that still set it don't break: retrieve()
        # logs a warning and otherwise ignores it. Declared as a real PARAM
        # (rather than handled via a custom __init__) so this source keeps
        # relying on BaseSource.__init__ -- overriding __init__ would make
        # test_source_components.py fall back to introspecting the
        # **kwargs-only signature instead of PARAMS for its mandatory-args
        # check, which breaks for every source using this pattern.
        integer(
            "version",
            label="(Deprecated) Version, has no effect anymore",
            optional=True,
        ),
    )

    def retrieve(self, source: "Source") -> "list[str]":
        params = self.params
        if params.get("version") is not None:
            _LOGGER.warning(
                "The 'version' parameter is deprecated and has no effect anymore."
            )

        url = params.get("url")
        file = params.get("file")
        year_field = params.get("year_field")
        method = params.get("method") or "GET"
        verify_ssl = params.get("verify_ssl")
        if verify_ssl is None:
            verify_ssl = True
        impersonate = params.get("impersonate")
        request_params = params.get("params")

        headers = dict(HEADERS)
        headers.update(params.get("headers") or {})

        if url is not None:
            url = re.sub("^webcal", "https", url)

            if "{%Y}" in url or year_field is not None:
                # url contains wildcard or params contains year field
                now = datetime.datetime.now()

                this_year_params = dict(request_params) if request_params else None
                url_this_year = url.replace("{%Y}", str(now.year))
                if year_field is not None:
                    if request_params is None:
                        raise SourceArgumentExceptionMultiple(
                            ("params", "year_field"),
                            "year_field specified without params",
                        )
                    this_year_params = dict(request_params)
                    this_year_params[year_field] = str(now.year)

                texts = [
                    _fetch_url(
                        url_this_year,
                        this_year_params,
                        method,
                        headers,
                        verify_ssl,
                        impersonate,
                    )
                ]

                if now.month == 12:
                    # also get data for next year if we are already in december
                    url_next_year = url.replace("{%Y}", str(now.year + 1))
                    next_year_params = dict(request_params) if request_params else None
                    # year_field implies request_params (checked above for
                    # url_this_year; request_params is never reassigned in
                    # between), so next_year_params is never None here -- the
                    # `is not None` guard just keeps that provable locally
                    # instead of relying on the earlier raise.
                    if year_field is not None and next_year_params is not None:
                        next_year_params[year_field] = str(now.year + 1)

                    try:
                        texts.append(
                            _fetch_url(
                                url_next_year,
                                next_year_params,
                                method,
                                headers,
                                verify_ssl,
                                impersonate,
                            )
                        )
                    except Exception:
                        # ignore if fetch for next year fails
                        pass

                return texts

            return [
                _fetch_url(
                    url, request_params, method, headers, verify_ssl, impersonate
                )
            ]

        # alternatives() above guarantees exactly one of url/file is set.
        assert file is not None
        return [_fetch_file(file)]

    def parse(self, raw: "list[str]", source: "Source") -> "list[IcsEvent]":
        ics = ICS(
            offset=_coerce_int(self.params.get("offset")),
            split_at=self.params.get("split_at"),
            regex=self.params.get("regex"),
            title_template=self.params.get("title_template") or "{{date.summary}}",
        )
        events: list[IcsEvent] = []
        for text in raw:
            events.extend(ics.convert_events(text))
        return events

    def classify(self, record: IcsEvent) -> Collection:
        return Collection(
            date=record.date,
            t=record.title,
            location=record.location,
            description=record.description,
        )
