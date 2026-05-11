from datetime import date, timedelta

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Rueil-Malmaison"
DESCRIPTION = "Source for waste collection schedule in Rueil-Malmaison, France."
URL = "https://www.rueil-malmaison.fr"

API_BASE = "https://opendata.hauts-de-seine.fr/api/explore/v2.1/catalog/datasets"

DATASETS = {
    "Ordures Ménagères": "fr-219200631-collecte-des-ordures-menageres",
    "Emballages": "fr-219200631-collecte-des-emballages",
    "Verre": "fr-219200631-collecte-du-verre",
    "Déchets Végétaux": "fr-219200631-collecte-des-dechets-vegetaux",
    "Encombrants": "fr-219200631-encombrant",
}

DAYS_FR = {
    "Lundi": 0,
    "Mardi": 1,
    "Mercredi": 2,
    "Jeudi": 3,
    "Vendredi": 4,
    "Samedi": 5,
    "Dimanche": 6,
}

ICON_MAP = {
    "Ordures Ménagères": "mdi:trash-can",
    "Emballages": "mdi:recycle",
    "Verre": "mdi:glass-fragile",
    "Déchets Végétaux": "mdi:leaf",
    "Encombrants": "mdi:sofa",
}

TEST_CASES = {
    "Mairie de Rueil-Malmaison": {"lat": 48.8768, "lon": 2.1875},
}


def _point_in_polygon(lon: float, lat: float, ring: list) -> bool:
    """Ray-casting point-in-polygon for a GeoJSON coordinate ring [[lon, lat], ...]."""
    x, y = lon, lat
    inside = False
    p1x, p1y = ring[0]
    for i in range(1, len(ring) + 1):
        p2x, p2y = ring[i % len(ring)]
        if min(p1y, p2y) < y <= max(p1y, p2y) and x <= max(p1x, p2x):
            if p1y != p2y:
                xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                if p1x == p2x or x <= xinters:
                    inside = not inside
        p1x, p1y = p2x, p2y
    return inside


def _in_season(d: date, perioann: str) -> bool:
    p = perioann.lower()
    if "pas de collecte" in p:
        return False
    if "mars" in p and "d" in p:
        # "De début Mars à mi-Décembre" → March 1 to December 15
        return (3, 1) <= (d.month, d.day) <= (12, 15)
    return True


def _generate_dates(
    frequenc: str,
    jours: str,
    perioann: str,
    today: date,
    horizon: date,
) -> list[date]:
    if "pas de collecte" in frequenc.lower():
        return []

    weekdays = {DAYS_FR[d.strip()] for d in jours.split(",") if d.strip() in DAYS_FR}

    freq_lower = frequenc.lower()
    if "impaire" in freq_lower:
        week_parity = 1
    elif "paire" in freq_lower:
        week_parity = 0
    else:
        week_parity = None

    dates = []
    d = today
    while d <= horizon:
        if (
            d.weekday() in weekdays
            and _in_season(d, perioann)
            and (week_parity is None or d.isocalendar()[1] % 2 == week_parity)
        ):
            dates.append(d)
        d += timedelta(days=1)
    return dates


class Source:
    def __init__(self, lat: float, lon: float) -> None:
        self._lat = float(lat)
        self._lon = float(lon)

    def fetch(self) -> list[Collection]:
        today = date.today()
        horizon = date(today.year + 1, today.month, today.day)
        entries = []

        for waste_type, dataset_id in DATASETS.items():
            r = requests.get(f"{API_BASE}/{dataset_id}/records?limit=20")
            r.raise_for_status()
            records = r.json().get("results", [])

            for record in records:
                gs = record.get("geo_shape", {})
                geom = gs.get("geometry", gs)
                coords = geom.get("coordinates", [[]])
                ring = coords[0] if coords else []
                if not ring or not _point_in_polygon(self._lon, self._lat, ring):
                    continue

                icon = ICON_MAP.get(waste_type)
                for d in _generate_dates(
                    record["frequenc"],
                    record["jours"],
                    record["perioann"],
                    today,
                    horizon,
                ):
                    entries.append(Collection(date=d, t=waste_type, icon=icon))
                break

        return entries
