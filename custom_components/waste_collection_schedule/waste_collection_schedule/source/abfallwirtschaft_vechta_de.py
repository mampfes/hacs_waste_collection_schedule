"""AWB Abfallwirtschaft Vechta, Germany.

Demonstrates: a per-street calendar assembled from *two* independent paper-
collector feeds ("pamo" and "siemer") that must each be resolved (city
search, then street search, threading the previous step's id through a
cookie jar) and fetched separately, then merged and de-duplicated. Near
year-end the provider also publishes the first weeks of the following year,
best-effort (swallowed if not yet published). No configured retriever
expresses "resolve an id twice over, fetch two related but separate feeds,
optionally a third year", hence a source-defined retrieve(); the label
clean-up (stripping a fixed prefix/suffix and the per-district digit
suffix) happens before the record reaches ICSTransformer, since a stripped
digit does not change the record's canonical waste type -- only its
now-superseded display text.
"""

import json
import re
from datetime import datetime
from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, street
from waste_collection_schedule.service.ICS import ICS
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GENERAL_WASTE,
    GLASS,
    HAZARDOUS,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_BASE_URL = "https://www.abfallwirtschaft-vechta.de"
_STADT_SUCHE_URL = f"{_BASE_URL}/CALENDER/inc.suche_stadt.php"
_STRASSE_SUCHE_URL = f"{_BASE_URL}/CALENDER/inc.suche_strasse.php"
_ICS_URL = f"{_BASE_URL}/CALENDER/inc.get_calender_ics.php"

_TITLE_STRIP = ("Abfuhrtermin", "Erinnerung", "für")
_DIGITS_RE = re.compile(r"[0-9]")


def _clean_bin_type(title: str) -> str:
    for phrase in _TITLE_STRIP:
        title = title.replace(phrase, "")
    title = _DIGITS_RE.sub("", title).strip().replace("  ", " ")
    return title


def _fetch_year(session, stadt: str, strasse: str, jahr: int) -> "list[tuple]":
    entries: list = []
    seen: set = set()

    for papier_typ in ("pamo", "siemer"):
        cookies = {"jahr": str(jahr)}

        r = session.get(_STADT_SUCHE_URL, params={"term": stadt}, cookies=cookies)
        r.raise_for_status()
        city_id = r.json()[0]["id"]
        cookies["stadt"] = str(city_id)

        r = session.get(
            _STRASSE_SUCHE_URL,
            params={"stadt": city_id, "term": strasse},
            cookies=cookies,
        )
        r.raise_for_status()
        street_entry = json.loads(r.text[1:-2])["strassen"][0]
        cookies["stadt"] = str(street_entry["id"])
        cookies["abfuhrbezirk"] = str(street_entry["abfuhrbezirk"])
        cookies["abfuhrbezirkpapir"] = str(street_entry[papier_typ])
        cookies["papier"] = papier_typ

        args = {
            "stadt": city_id,
            "strasse": street_entry["id"],
            "abfuhrbezirkpapier": street_entry[papier_typ],
            "jahr": jahr,
            "papier": papier_typ,
            "trigger": "false",
            "triggerday": "false",
            "triggertime": "false",
        }
        r = session.get(_ICS_URL, params=args, cookies=cookies)
        r.raise_for_status()
        r.encoding = "utf-8"

        # Sometimes has a non-ASCII UID, which would raise while converting.
        text = r.text.replace("UID:", "NOTUID: ")
        for date_, title in ICS().convert(text):
            bin_type = _clean_bin_type(title)
            key = (date_, bin_type)
            if key in seen:
                continue
            seen.add(key)
            entries.append(key)

    return entries


@final
class Source(BaseSource):
    TITLE = "AWB Abfallwirtschaft Vechta"
    DESCRIPTION = "Source for AWB Abfallwirtschaft Vechta."
    URL = f"{_BASE_URL}/"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Vechta, An der Hasenweide": {
            "stadt": "Vechta",
            "strasse": "An der Hasenweide",
        },
        "Bakum, Up'n Sande": {"stadt": "Bakum", "strasse": "Up'n Sande"},
        "Neuenkirchen-Vörden, Braunschweiger Straße": {
            "stadt": "Neuenkirchen-Vörden",
            "strasse": "Braunschweiger Straße",
        },
        "Goldenstedt, An der Ellenbäke": {
            "stadt": "Goldenstedt",
            "strasse": "An der Ellenbäke",
        },
    }

    PARAMS = (
        city(field="stadt"),
        street(field="strasse"),
    )

    def retrieve(self, source):
        session = source.session
        stadt = self.params["stadt"]
        strasse = self.params["strasse"]
        now = datetime.now()

        entries = _fetch_year(session, stadt, strasse, now.year)
        if now.month == 12:
            try:
                entries = entries + _fetch_year(session, stadt, strasse, now.year + 1)
            except Exception:
                pass
        return entries

    def parse(self, raw, source):
        return raw

    transform = ICSTransformer(
        type_value_map={
            "Restabfall": GENERAL_WASTE,
            "Glass": GLASS,
            "Glas": GLASS,
            "Bioabfall": ORGANIC,
            "Altpapier": PAPER,
            "Altpapier Siemer": PAPER,
            "Altpapier Pamo": PAPER,
            "Gelbe Tonne": RECYCLABLES,
            "Altkleider": RECYCLABLES,
            "Altkleider (Außer Langförden)": RECYCLABLES,
            "Mobile Schadstoff.": HAZARDOUS,
        }
    )

    def __init__(self, stadt: str, strasse: str):
        super().__init__(stadt=stadt, strasse=strasse)
