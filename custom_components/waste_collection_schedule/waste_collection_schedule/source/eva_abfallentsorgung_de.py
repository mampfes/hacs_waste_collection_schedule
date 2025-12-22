import logging
import requests
from datetime import datetime
from waste_collection_schedule import Collection

TITLE = "EVA Abfallentsorgung"
DESCRIPTION = "Source for EVA Abfallentsorgung (Landkreis Weilheim-Schongau)"
URL = "https://www.eva-abfallentsorgung.de/"
TEST_CASES = {
    "Böbing": {"ort": "Böbing", "strasse": "Böbing"},
    "Peißenberg": {"ort": "Peißenberg", "strasse": "Hauptstraße"},
}

_LOGGER = logging.getLogger(__name__)

ICON_MAP = {
    "Bio": "mdi:leaf",
    "Rest": "mdi:trash-can",
    "Gelb": "mdi:recycle",
    "Papier": "mdi:package-variant",
    "Gift": "mdi:biohazard",
    "Giftmobil": "mdi:biohazard",
    "Zeitung": "mdi:newspaper",
}


class Source:
    def __init__(self, ort, strasse):
        self.ort = ort
        self.strasse = strasse

    def fetch_json(self, url):
        r = requests.get(url)
        r.raise_for_status()
        return r.json()

    def fetch(self):
        now = datetime.now()
        years = [now.year]

        # Folgejahr erst ab Dezember laden
        if now.month == 12:
            years.append(now.year + 1)

        entries = []

        for year in years:
            try:
                e = self._fetch_year(year)
                entries.extend(e)
            except Exception as ex:
                _LOGGER.error(f"EVA fetch error in year {year}: {ex}")
                continue

        return entries

    def _fetch_year(self, year):
        base = f"https://www.eva-abfallentsorgung.de/json_export/{year}"

        # Orte laden
        main = self.fetch_json(f"{base}/main.json")

        if self.ort not in main:
            raise Exception(f"Ort '{self.ort}' nicht gefunden.")

        ort_id = main[self.ort]["id"]

        # Straßen laden
        ort_json = self.fetch_json(f"{base}/ort_{ort_id}.json")

        if "strassen" not in ort_json or self.strasse not in ort_json["strassen"]:
            raise Exception(
                f"Straße '{self.strasse}' nicht in Ort '{self.ort}' gefunden."
            )

        strasse_id = ort_json["strassen"][self.strasse]

        # Termindaten laden
        data = self.fetch_json(f"{base}/strasse_{strasse_id}.json")

        # Nur "all" verwenden, hier sind alle Tonnen drin
        if "all" not in data:
            return []

        terminedaten = data["all"]
        entries = []

        for d, value in terminedaten.items():

            # Datum parsen
            try:
                date = datetime.strptime(d, "%Y-%m-%d").date()
            except Exception:
                continue

            # Fall 1: einfacher String ("Bio")
            if isinstance(value, str):
                entries.append(
                    Collection(date, value, ICON_MAP.get(value))
                )
                continue

            # Fall 2: Liste (["Rest", "Gelb"])
            if isinstance(value, list):
                for typ in value:
                    if isinstance(typ, str):
                        entries.append(
                            Collection(date, typ, ICON_MAP.get(typ))
                        )
                continue

            # Fall 3: Dictionary → Sonderfall Giftmobil
            if isinstance(value, dict) and len(value.keys()) == 1:

                typ_key = list(value.keys())[0]
                data_gift = value[typ_key]

                # Giftmobil-Aufbereitung
                if typ_key.lower() == "gift":

                    begin1 = data_gift.get("beginn_1")
                    end1 = data_gift.get("end_1")
                    begin2 = data_gift.get("beginn_2")
                    end2 = data_gift.get("end_2")
                    location = data_gift.get("location") or ""
                    note = data_gift.get("note") or ""

                    times = []

                    if begin1 and begin1 != "00:00":
                        times.append(f"{begin1}-{end1}")

                    if begin2 and begin2 != "00:00":
                        times.append(f"{begin2}-{end2}")

                    time_text = ", ".join(times)

                    # Typstring zusammensetzen
                    parts = ["Giftmobil"]

                    if location:
                        parts.append(location)

                    if time_text:
                        parts.append(f"({time_text})")

                    if note:
                        parts.append(f"[{note}]")

                    typ_text = " – ".join(parts)

                    entries.append(
                        Collection(
                            date,
                            typ_text,
                            ICON_MAP.get("Giftmobil")
                        )
                    )
                    continue

                # Falls etwas anderes drinsteht → ignorieren
                continue

            # Rest ignorieren (None, {}, [], komische Werte)
            continue

        return entries
