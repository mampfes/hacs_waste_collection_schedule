"""VEVG Vorpommern-Greifswald (vevg-karlsburg.de).

Demonstrates: a static, param-built ICS GET across two endpoints (one for
Stadt Greifswald streets, ``kreis="H"``; one for every other district) whose
raw feed needs pre-parse text fixes ``parsers.IcsParser`` has no hook for
(non-standard ``TRIGGER:-P10H`` durations instead of ``-PT10H``, and
malformed ``DTEND`` values such as "20260204T 1.000"), and whose calendar is
generated one year at a time -- so this also fetches the following year once
the season turns (best-effort: swallowed if it isn't published yet). Label
tidying (stripping the "Leerung der " prefix, and folding every operator's
"Papiertonne <extra>" variant down to a plain "Papiertonne") is expressed as
the transformer's ``clean=`` rather than a custom parse of the label itself.
"""

import datetime
import re
from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.service.ICS import ICS
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GENERAL_WASTE,
    HAZARDOUS,
    PAPER,
    RECYCLABLES,
)

# Endpoint for UHGW (Stadt Greifswald streets, kreis="H")
_ICAL_UHGW_URL = "https://vevg-karlsburg.de/abfallkalender/ical_uhgw_get_utf8.php"
# Endpoint for all other districts
_ICAL_REST_URL = "https://vevg-karlsburg.de/abfallkalender/ical_rest_get_utf8.php"

# Provider uses non-standard durations: -P10H (invalid) instead of -PT10H
_FIX_TRIGGER = re.compile(r"TRIGGER:-P(\d+)H")
# Provider sometimes emits malformed DTEND such as "20260204T 1.000" or "20260408T.300"
_FIX_DTEND = re.compile(r"DTEND[^\r\n]*T[ .][^\r\n]*")

_LEERUNG_RE = re.compile(r"Leerung der (.*)", re.IGNORECASE)


def _fix_ics(text: str) -> str:
    """Apply provider-specific ICS fixes before parsing."""
    text = _FIX_TRIGGER.sub(r"TRIGGER:-PT\1H", text)
    text = _FIX_DTEND.sub("", text)
    return text


def _clean_label(label: str) -> str:
    """Strip the "Leerung der " prefix and fold every Papiertonne variant."""
    match = _LEERUNG_RE.match(label)
    text = (match.group(1) if match else label).strip()
    if text.lower().startswith("papiertonne"):
        return "Papiertonne"
    return text


def _ical_url(kreis: str) -> str:
    return _ICAL_UHGW_URL if kreis.upper() == "H" else _ICAL_REST_URL


def _year_params(ort: int, kreis: str, year: int) -> dict:
    return {
        "ical_1": "1",
        "ical_2": "1",
        "ical_3": "1",
        "ical_4": "1",
        "ical_5": "1",
        "ical_12": "1",
        "ical_ort": str(ort),
        "ical_kreis": kreis.upper(),
        "ical_monat": "1",
        "ical_year": str(year),
        "gesendet": "Termine herunterladen",
    }


@final
class Source(BaseSource):
    TITLE = "VEVG Vorpommern-Greifswald"
    DESCRIPTION = "Source for Ver- und Entsorgungsgesellschaft des Landkreises Vorpommern-Greifswald mbH (VEVG), Germany."
    URL = "https://www.vevg-karlsburg.de"
    COUNTRY = "de"

    TEST_CASES: ClassVar[dict] = {
        "Wusterhusen (OVP/G)": {"ort": 722, "kreis": "G"},
        "Jarmen (JTPL/L)": {"ort": 823, "kreis": "L"},
        "Greifswald Aalbruch (UHGW/H)": {"ort": 1, "kreis": "H"},
        "Ahlbeck UER": {"ort": 1001, "kreis": "U"},
    }

    PARAMS = (
        text_field("ort", "Location ID"),
        text_field("kreis", "District code"),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "1. Go to the VEVG online calendar:\n"
            "   - OVP (Anklam/Wolgast/Greifswald-Land): "
            "https://vevg-karlsburg.de/online-abfallkalender-ovp.html\n"
            "   - JTPL (Jarmen/Tutow/Peenetal-Loitz): "
            "https://vevg-karlsburg.de/online-abfallkalender-jtpl.html\n"
            "   - UHGW (Stadt Greifswald streets): "
            "https://vevg-karlsburg.de/online-abfallkalender-uhgw.html\n"
            "   - UER (Uecker-Randow): "
            "https://vevg-karlsburg.de/online-abfallkalender-uer.html\n"
            "2. Select your location from the dropdown and click 'Auswählen'.\n"
            "3. The `ort` and `kreis` values appear in the page URL as "
            "`key={ort}#{name}#{kreis}#`.\n"
            "   - Example: Wusterhusen shows `key=722#Wusterhusen#G#`, so "
            '`ort=722` and `kreis="G"`.\n'
            "4. For locations marked with 'lesen' (street-level lookup): select "
            "your street first, then read ort/kreis from the resulting URL."
        ),
        "de": (
            "1. Öffnen Sie den VEVG Online-Abfallkalender:\n"
            "   - OVP (Anklam/Wolgast/Greifswald-Land): "
            "https://vevg-karlsburg.de/online-abfallkalender-ovp.html\n"
            "   - JTPL (Jarmen/Tutow/Peenetal-Loitz): "
            "https://vevg-karlsburg.de/online-abfallkalender-jtpl.html\n"
            "   - UHGW (Straßen der Stadt Greifswald): "
            "https://vevg-karlsburg.de/online-abfallkalender-uhgw.html\n"
            "   - UER (Uecker-Randow): "
            "https://vevg-karlsburg.de/online-abfallkalender-uer.html\n"
            "2. Wählen Sie Ihren Ort aus der Liste und klicken Sie auf "
            "'Auswählen'.\n"
            "3. Die Werte für `ort` und `kreis` stehen in der URL als "
            "`key={ort}#{name}#{kreis}#`.\n"
            "   - Beispiel: Wusterhusen hat `key=722#Wusterhusen#G#`, also "
            '`ort=722` und `kreis="G"`.\n'
            "4. Bei Orten mit 'lesen' (straßengenaue Abfrage): zuerst die "
            "Straße auswählen, dann ort/kreis aus der URL ablesen."
        ),
    }

    def retrieve(self, source):
        ort = source.params["ort"]
        kreis = str(source.params["kreis"])
        url = _ical_url(kreis)
        now = datetime.date.today()

        responses = [
            source.session.get(
                url, params=_year_params(ort, kreis, now.year), timeout=30
            )
        ]
        if now.month >= 11:
            try:
                extra = source.session.get(
                    url, params=_year_params(ort, kreis, now.year + 1), timeout=30
                )
                extra.raise_for_status()
                responses.append(extra)
            except Exception:
                pass
        return responses

    def parse(self, raw, source):
        entries = []
        for response in raw:
            response.raise_for_status()
            entries.extend(ICS().convert(_fix_ics(response.text)))
        return entries

    transform = ICSTransformer(
        clean=_clean_label,
        type_value_map={
            "restmülltonne": GENERAL_WASTE,
            "gelben säcke": RECYCLABLES,
            "papiertonne": PAPER,
            "mobile schadstoffsammlung": HAZARDOUS,
        },
    )

    def __init__(self, ort: int, kreis: str) -> None:
        super().__init__(ort=int(ort), kreis=str(kreis).upper())
