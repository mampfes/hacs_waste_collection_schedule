import datetime
import re

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "VEVG Vorpommern-Greifswald"
DESCRIPTION = "Source for Ver- und Entsorgungsgesellschaft des Landkreises Vorpommern-Greifswald mbH (VEVG), Germany."
URL = "https://www.vevg-karlsburg.de"
COUNTRY = "de"
TEST_CASES = {
    "Wusterhusen (OVP/G)": {"ort": 722, "kreis": "G"},
    "Jarmen (JTPL/L)": {"ort": 823, "kreis": "L"},
    "Greifswald Aalbruch (UHGW/H)": {"ort": 1, "kreis": "H"},
    "Ahlbeck UER": {"ort": 1001, "kreis": "U"},
}

ICON_MAP = {
    "restmüll": Icons.GENERAL_WASTE,
    "gelbe": Icons.PLASTIC_PACKAGING,
    "papiertonne": Icons.PAPER,
    "schadstoff": Icons.HAZARDOUS,
}

PARAM_TRANSLATIONS = {
    "en": {
        "ort": "Location ID",
        "kreis": "District code",
    },
    "de": {
        "ort": "Orts-ID",
        "kreis": "Kreis-Kennung",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "ort": "Numeric location ID from the VEVG online calendar dropdown (e.g. 722 for Wusterhusen). See 'How to get the source arguments'.",
        "kreis": "Single-letter district code from the same dropdown (e.g. 'G' for Greifswald-Land, 'A' for Anklam, 'W' for Wolgast, 'L' for JTPL, 'H' for Stadt Greifswald, 'U' for Uecker-Randow).",
    },
    "de": {
        "ort": "Numerische Orts-ID aus der Auswahlliste des VEVG Online-Abfallkalenders (z.B. 722 für Wusterhusen).",
        "kreis": "Einbuchstabige Kreis-Kennung aus derselben Auswahlliste (z.B. 'G' für Greifswald-Land, 'A' für Anklam, 'W' für Wolgast, 'L' für JTPL, 'H' für Stadt Greifswald, 'U' für Uecker-Randow).",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": """
1. Go to the VEVG online calendar:
   - OVP (Anklam/Wolgast/Greifswald-Land): https://vevg-karlsburg.de/online-abfallkalender-ovp.html
   - JTPL (Jarmen/Tutow/Peenetal-Loitz): https://vevg-karlsburg.de/online-abfallkalender-jtpl.html
   - UHGW (Stadt Greifswald streets): https://vevg-karlsburg.de/online-abfallkalender-uhgw.html
   - UER (Uecker-Randow): https://vevg-karlsburg.de/online-abfallkalender-uer.html
2. Select your location from the dropdown and click "Auswählen".
3. The `ort` and `kreis` values appear in the page URL as `key={ort}#{name}#{kreis}#`.
   - Example: Wusterhusen shows `key=722#Wusterhusen#G#`, so `ort=722` and `kreis="G"`.
4. For locations marked with "lesen" (street-level lookup): select your street first, then read ort/kreis from the resulting URL.
""",
    "de": """
1. Öffnen Sie den VEVG Online-Abfallkalender:
   - OVP (Anklam/Wolgast/Greifswald-Land): https://vevg-karlsburg.de/online-abfallkalender-ovp.html
   - JTPL (Jarmen/Tutow/Peenetal-Loitz): https://vevg-karlsburg.de/online-abfallkalender-jtpl.html
   - UHGW (Straßen der Stadt Greifswald): https://vevg-karlsburg.de/online-abfallkalender-uhgw.html
   - UER (Uecker-Randow): https://vevg-karlsburg.de/online-abfallkalender-uer.html
2. Wählen Sie Ihren Ort aus der Liste und klicken Sie auf "Auswählen".
3. Die Werte für `ort` und `kreis` stehen in der URL als `key={ort}#{name}#{kreis}#`.
   - Beispiel: Wusterhusen hat `key=722#Wusterhusen#G#`, also `ort=722` und `kreis="G"`.
4. Bei Orten mit "lesen" (straßengenaue Abfrage): zuerst die Straße auswählen, dann ort/kreis aus der URL ablesen.
""",
}

# Endpoint for UHGW (Stadt Greifswald streets, kreis="H")
_ICAL_UHGW_URL = "https://vevg-karlsburg.de/abfallkalender/ical_uhgw_get_utf8.php"
# Endpoint for all other districts
_ICAL_REST_URL = "https://vevg-karlsburg.de/abfallkalender/ical_rest_get_utf8.php"

# Provider uses non-standard durations: -P10H (invalid) instead of -PT10H
_FIX_TRIGGER = re.compile(r"TRIGGER:-P(\d+)H")
# Provider sometimes emits malformed DTEND such as "20260204T 1.000" or "20260408T.300"
_FIX_DTEND = re.compile(r"DTEND[^\r\n]*T[ .][^\r\n]*")
# Strip the "Leerung der " prefix from waste type summaries
_LEERUNG_RE = re.compile(r"Leerung der (.*)")


def _fix_ics(text: str) -> str:
    """Apply provider-specific ICS fixes before parsing."""
    text = _FIX_TRIGGER.sub(r"TRIGGER:-PT\1H", text)
    text = _FIX_DTEND.sub("", text)
    return text


def _waste_type(summary: str) -> str:
    """Strip the 'Leerung der ' prefix and trailing whitespace from a summary."""
    m = _LEERUNG_RE.match(summary)
    if m:
        return m.group(1).strip()
    return summary.strip()


class Source:
    def __init__(self, ort: int, kreis: str) -> None:
        self._ort = int(ort)
        self._kreis = str(kreis).upper()
        self._ics = ICS()

    def _ical_url(self) -> str:
        if self._kreis == "H":
            return _ICAL_UHGW_URL
        return _ICAL_REST_URL

    def _fetch_year(self, year: int) -> list[Collection]:
        params: dict = {
            "ical_1": "1",
            "ical_2": "1",
            "ical_3": "1",
            "ical_4": "1",
            "ical_5": "1",
            "ical_12": "1",
            "ical_ort": str(self._ort),
            "ical_kreis": self._kreis,
            "ical_monat": "1",
            "ical_year": str(year),
            "gesendet": "Termine herunterladen",
        }

        r = requests.get(self._ical_url(), params=params, timeout=30)
        r.raise_for_status()

        ics_text = _fix_ics(r.text)

        dates = self._ics.convert(ics_text)
        entries: list[Collection] = []
        for date, summary in dates:
            waste = _waste_type(summary)
            icon = None
            for key, ico in ICON_MAP.items():
                if key in waste.lower():
                    icon = ico
                    break
            entries.append(Collection(date, waste, icon))
        return entries

    def fetch(self) -> list[Collection]:
        now = datetime.date.today()
        entries = self._fetch_year(now.year)
        if now.month >= 11:
            try:
                entries += self._fetch_year(now.year + 1)
            except Exception:
                pass
        return entries
