import json
import re
import time
import unicodedata
from datetime import date, timedelta

import requests
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "Grand Paris Sud Est Avenir (GPSEA)"
DESCRIPTION = "Source script for sudestavenir.fr, waste collection schedules for the Grand Paris Sud Est Avenir (GPSEA) intercommunal territory"
URL = "https://sudestavenir.fr/"
COUNTRY = "fr"

# GEO Software ("ACF") map application backing the address search widget on
# sudestavenir.fr. IDs below are fixed configuration of that application,
# discovered via its browser network traffic.
APP_ID = "3394f2c6-49bc-11ea-90a1-114edab0a319"
APP_BASE = f"https://geo.gpsea.fr/adws/app/{APP_ID}"
API_BASE = f"{APP_BASE}/services/aas/v1"

SOURCE_ID = "ecce3c92-5194-11ea-9e88-250d8464572d"
FILTER_COMMUNE = "79029f6a-f185-11e9-9256-e1c42467b095"
FILTER_STREET = "a09256bf-f185-11e9-9256-e1c42467b095"
FILTER_STREET_CONFIRM = "e3fd1e85-5188-11ea-9e88-250d8464572d"
FILTER_NUMBER = "af552d94-f185-11e9-9256-e1c42467b095"
INFOSHEET_ID = "2215b34d-11f1-11eb-8a48-9979b5aed361"

WASTE_TYPES = {
    "om": "Ordures ménagères",
    "em": "Emballages",
    "ve": "Verre",
    "ec": "Encombrants",
    "dv": "Déchets végétaux",
}

ICON_MAP = {
    "om": Icons.GENERAL_WASTE,
    "em": Icons.RECYCLING,
    "ve": Icons.GLASS,
    "ec": Icons.BULKY,
    "dv": Icons.GARDEN,
}

DAY_MAP = {
    "lundi": 0,
    "mardi": 1,
    "mercredi": 2,
    "jeudi": 3,
    "vendredi": 4,
    "samedi": 5,
    "dimanche": 6,
}

MONTH_MAP = {
    "janv": 1,
    "fev": 2,
    "mars": 3,
    "avr": 4,
    "mai": 5,
    "juin": 6,
    "juill": 7,
    "aout": 8,
    "sept": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}

WEEKLY_FREQUENCIES = {"HEBDOMADAIRE", "BIHEBDOMADAIRE", "TRIHEBDOMADAIRE"}

TEST_CASES = {
    "1 Place du Grand Pavois, Creteil": {
        "commune": "Creteil",
        "street": "Place du Grand Pavois",
        "house_number": "1",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "commune": "Your commune within the GPSEA territory",
        "street": "Your street name",
        "house_number": "Your house number",
    },
    "fr": {
        "commune": "Votre commune du territoire GPSEA",
        "street": "Le nom de votre voie",
        "house_number": "Votre numéro de voie",
    },
    "de": {
        "commune": "Ihre Gemeinde im GPSEA-Gebiet",
        "street": "Ihr Straßenname",
        "house_number": "Ihre Hausnummer",
    },
}

PARAM_TRANSLATIONS = {
    "en": {"commune": "Commune", "street": "Street", "house_number": "House number"},
    "fr": {"commune": "Commune", "street": "Voie", "house_number": "Numéro"},
    "de": {"commune": "Gemeinde", "street": "Straße", "house_number": "Hausnummer"},
}


def _strip_accents(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
    )


def _normalize(s: str) -> str:
    return re.sub(r"\s+", " ", _strip_accents(s).lower().strip())


def _parse_precisi_dates(precisi: str, year: int) -> list[date]:
    dates: list[date] = []
    for line in precisi.splitlines():
        m = re.match(r"^([A-Za-zÀ-ÿ]+)\.\s*:\s*([\d\s\-]+)$", line.strip())
        if not m:
            continue
        month = MONTH_MAP.get(_strip_accents(m.group(1)).lower().rstrip("."))
        if month is None:
            continue
        for day_str in m.group(2).split("-"):
            day_str = day_str.strip()
            if not day_str.isdigit():
                continue
            try:
                dates.append(date(year, month, int(day_str)))
            except ValueError:
                continue
    return dates


def _weekly_dates(jour: str, start: date, end: date) -> list[date]:
    weekdays = [DAY_MAP[d] for d in jour.split() if d in DAY_MAP]
    dates: list[date] = []
    for weekday in weekdays:
        d = start + timedelta(days=(weekday - start.weekday()) % 7)
        while d <= end:
            dates.append(d)
            d += timedelta(weeks=1)
    return dates


def _biweekly_dates(jour: str, pairimp: str, start: date, end: date) -> list[date]:
    weekdays = [DAY_MAP[d] for d in jour.split() if d in DAY_MAP]
    dates: list[date] = []
    for weekday in weekdays:
        d = start + timedelta(days=(weekday - start.weekday()) % 7)
        while d <= end:
            iso_week = d.isocalendar()[1]
            if (
                not pairimp
                or (pairimp == "PAIRE" and iso_week % 2 == 0)
                or (pairimp == "IMPAIRE" and iso_week % 2 == 1)
            ):
                dates.append(d)
            d += timedelta(weeks=1)
    return dates


class Source:
    def __init__(self, commune: str, street: str, house_number: str):
        self._commune = commune
        self._street = street
        self._house_number = str(house_number)

    def _query_filter(
        self,
        session: requests.Session,
        filters_id: str,
        input_text: str,
        filter_inputs: list[dict],
        linked_ids: list[str],
    ) -> list[dict]:
        prefilter = {
            "locale": "fr",
            "filterInputs": filter_inputs,
            "featureSelectionFilter": None,
        }
        data = {
            "sourceId": SOURCE_ID,
            "filtersId": filters_id,
            "input": input_text,
            "prefilter": json.dumps(prefilter),
            "linkedFiltersIds": ",".join(linked_ids),
        }
        r = session.post(
            f"{API_BASE}/filters/getData",
            params={"dummy": int(time.time() * 1000)},
            data=data,
        )
        r.raise_for_status()
        result = r.json()
        if not result:
            return []
        return result[0].get("values", {}).get("values", [])

    def _resolve(
        self,
        session: requests.Session,
        filters_id: str,
        query: str,
        filter_inputs: list[dict],
        linked_ids: list[str],
        argument_name: str,
    ) -> dict:
        candidates = self._query_filter(
            session, filters_id, query, filter_inputs, linked_ids
        )
        target = _normalize(query)
        for c in candidates:
            if _normalize(str(c["label"])) == target:
                return c
        for c in candidates:
            if target in _normalize(str(c["label"])):
                return c

        # Some filters (e.g. the commune list) ignore server-side text
        # filtering and always return their full list only when queried
        # with an empty input. Retry unfiltered and match locally.
        if query:
            candidates = self._query_filter(
                session, filters_id, "", filter_inputs, linked_ids
            )
            for c in candidates:
                if _normalize(str(c["label"])) == target:
                    return c
            for c in candidates:
                if target in _normalize(str(c["label"])):
                    return c

        raise SourceArgumentNotFoundWithSuggestions(
            argument_name, query, [str(c["label"]) for c in candidates]
        )

    @staticmethod
    def _filter_input(filters_id: str, candidate: dict, from_suggestion: bool) -> dict:
        return {
            "id": filters_id,
            "index": 0,
            "label": candidate["label"],
            "values": candidate["values"],
            "fromSuggestion": from_suggestion,
        }

    def fetch(self) -> list[Collection]:
        session = requests.Session()

        r = session.get(f"{APP_BASE}/index.html")
        r.raise_for_status()
        m = re.search(r"bgSessionId\s*=\s*'([^']+)'", r.text)
        if not m:
            raise requests.exceptions.RequestException(
                "Could not initialize GPSEA map session"
            )
        session.headers.update(
            {
                "X-BG-Session": m.group(1),
                "X-Requested-With": "XMLHttpRequest",
                "Referer": f"{APP_BASE}/index.html",
            }
        )

        commune = self._resolve(
            session, FILTER_COMMUNE, self._commune, [], [], "commune"
        )
        commune_input = self._filter_input(FILTER_COMMUNE, commune, False)

        street = self._resolve(
            session,
            FILTER_STREET,
            self._street,
            [commune_input],
            [FILTER_COMMUNE],
            "street",
        )
        street_input = self._filter_input(FILTER_STREET, street, False)

        confirm_candidates = self._query_filter(
            session,
            FILTER_STREET_CONFIRM,
            " ",
            [commune_input, street_input],
            [FILTER_COMMUNE, FILTER_STREET],
        )
        confirm = confirm_candidates[0] if confirm_candidates else street
        confirm_input = self._filter_input(FILTER_STREET_CONFIRM, confirm, True)

        number = self._resolve(
            session,
            FILTER_NUMBER,
            self._house_number,
            [commune_input, street_input, confirm_input],
            [FILTER_COMMUNE, FILTER_STREET, FILTER_STREET_CONFIRM],
            "house_number",
        )
        number_input = self._filter_input(FILTER_NUMBER, number, False)

        search_filters = {
            "coordinateSystem": {"srid": 3857},
            "currentObject": None,
            "locale": "fr",
            "filterInputs": [commune_input, street_input, confirm_input, number_input],
            "infoSheetContext": None,
            "featureSelectionFilter": {"features": [], "selectionCrs": "EPSG:3857"},
        }
        r = session.post(
            f"{API_BASE}/searches/execute",
            params={"dummy": int(time.time() * 1000)},
            data={
                "centroid": "true",
                "simplifyGeometry": "false",
                "srid": "EPSG:3857",
                "useExtent": "true",
                "throwErrors": "false",
                "throwTimeoutErrors": "true",
                "limit": "51",
                "offset": "0",
                "searchIds": SOURCE_ID,
                "filters": json.dumps(search_filters),
            },
        )
        r.raise_for_status()
        features = r.json().get("features", [])
        if not features:
            raise SourceArgumentNotFoundWithSuggestions(
                "house_number", self._house_number, []
            )
        feature_id = features[0]["properties"]["id_auto"]

        r = session.get(
            f"{API_BASE}/infoSheets/getData",
            params={
                "dummy": int(time.time() * 1000),
                "centroid": "false",
                "id": INFOSHEET_ID,
                "idValue": feature_id,
                "srs": "EPSG:3857",
            },
        )
        r.raise_for_status()
        properties = r.json().get("properties", {})

        entries: list[Collection] = []
        today = date.today()
        end = today + timedelta(days=365)
        for prefix, label in WASTE_TYPES.items():
            jour = properties.get(f"{prefix}_jour") or ""
            frequen = properties.get(f"{prefix}_frequen") or ""
            pairimp = properties.get(f"{prefix}_pairimp") or ""
            precisi = properties.get(f"{prefix}_precisi")
            am_pm = properties.get(f"{prefix}_am_pm")

            if not frequen:
                continue

            description = (
                "Matin" if am_pm == "AM" else "Après-midi" if am_pm == "PM" else None
            )

            if precisi:
                # The server precomputes exact days-of-month for the current
                # annual calendar only; day-of-week alignment shifts each
                # year so these figures cannot be extrapolated to next year.
                dates = [
                    d for d in _parse_precisi_dates(precisi, today.year) if d >= today
                ]
            elif jour and frequen in WEEKLY_FREQUENCIES:
                dates = _weekly_dates(jour, today, end)
            elif jour and frequen == "QUINZAINE":
                dates = _biweekly_dates(jour, pairimp, today, end)
            else:
                continue

            for d in dates:
                entries.append(
                    Collection(
                        date=d, t=label, icon=ICON_MAP[prefix], description=description
                    )
                )

        return entries
