"""GEO Software address filters, infosheets and French collection rules."""

import json
import re
import unicodedata
from datetime import date, timedelta

from waste_collection_schedule import recurrence
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.preprocessors import Schedule

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
    "janvier": 1,
    "fev": 2,
    "fevrier": 2,
    "mars": 3,
    "avr": 4,
    "avril": 4,
    "mai": 5,
    "juin": 6,
    "juill": 7,
    "juillet": 7,
    "aout": 8,
    "sept": 9,
    "septembre": 9,
    "oct": 10,
    "octobre": 10,
    "nov": 11,
    "novembre": 11,
    "dec": 12,
    "decembre": 12,
}

WEEKLY_FREQUENCIES = {"HEBDOMADAIRE", "BIHEBDOMADAIRE", "TRIHEBDOMADAIRE"}


def _strip_accents(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
    )


def _normalize(s: str) -> str:
    return re.sub("\\s+", " ", _strip_accents(s).lower().strip())


def _french_date(day: str, month: str, year: int) -> date | None:
    month_number = MONTH_MAP.get(_normalize(month).rstrip("."))
    if month_number is None or not day.isdigit():
        return None
    try:
        return date(year, month_number, int(day))
    except ValueError:
        return None


def _parse_precisi_dates(precisi: str, year: int) -> list[date]:
    dates: list[date] = []
    for line in precisi.splitlines():
        line = line.strip()
        month_first = re.fullmatch("([A-Za-zÀ-ÿ]+)\\.?\\s*:\\s*([\\d\\s-]+)", line)
        if month_first:
            for day in month_first.group(2).split("-"):
                parsed = _french_date(day.strip(), month_first.group(1), year)
                if parsed is not None:
                    dates.append(parsed)
            continue
        day_first = re.fullmatch("(\\d{1,2})\\s+([A-Za-zÀ-ÿ]+)\\.?", line)
        if day_first:
            parsed = _french_date(day_first.group(1), day_first.group(2), year)
            if parsed is not None:
                dates.append(parsed)
    return dates


def _parse_precisi_range(precisi: str, year: int) -> tuple[date, date] | None:
    match = re.search(
        "\\ba partir du\\s+(\\d{1,2})\\s+([a-z]+)\\s+au\\s+(\\d{1,2})\\s+([a-z]+)\\b",
        _normalize(precisi),
    )
    if not match:
        return None
    start = _french_date(match.group(1), match.group(2), year)
    end = _french_date(match.group(3), match.group(4), year)
    if start is None or end is None or end < start:
        return None
    return (start, end)


def abbreviate_street(street):
    types = {
        "place": "PL",
        "avenue": "AV",
        "boulevard": "BD",
        "rue": "RUE",
        "allee": "ALL",
        "impasse": "IMP",
        "route": "RTE",
    }
    words = street.strip().split()
    if words and _normalize(words[0]) in types:
        words[0] = types[_normalize(words[0])]
    return " ".join(words)


class _Client:
    def __init__(
        self, base, source_id, filters, info_sheet, commune, street, house_number
    ):
        self.base = base
        self.api = base + "/services/aas/v1"  # codespell:ignore aas
        self.source_id = source_id
        self.filters = filters
        self.info_sheet = info_sheet
        self._commune = commune
        self._street = street
        self._house_number = str(house_number)

    def _query_filter(
        self,
        session,
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
            "sourceId": self.source_id,
            "filtersId": filters_id,
            "input": input_text,
            "prefilter": json.dumps(prefilter),
            "linkedFiltersIds": ",".join(linked_ids),
        }
        r = session.post(
            f"{self.api}/filters/getData",
            data=data,
            timeout=30,
        )
        r.raise_for_status()
        result = r.json()
        if not result:
            return []
        return result[0].get("values", {}).get("values", [])

    def _resolve(
        self, session, filters_id, query, filter_inputs, linked_ids, argument_name
    ):
        if argument_name == "street":
            query = abbreviate_street(query)
        target = _normalize(query)
        candidates = []
        for requested in dict.fromkeys((query, "")):
            candidates = self._query_filter(
                session, filters_id, requested, filter_inputs, linked_ids
            )
            exact = [c for c in candidates if _normalize(str(c["label"])) == target]
            matches = exact or [
                c for c in candidates if target in _normalize(str(c["label"]))
            ]
            matches = list(
                {(str(c["label"]), repr(c.get("values"))): c for c in matches}.values()
            )
            if len(matches) == 1:
                return matches[0]
            if len(matches) > 1:
                raise SourceArgAmbiguousWithSuggestions(
                    argument_name, query, [str(c["label"]) for c in matches]
                )
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

    def retrieve(self, session):
        r = session.get(f"{self.base}/index.html", timeout=30)
        r.raise_for_status()
        m = re.search("bgSessionId\\s*=\\s*'([^']+)'", r.text)
        if not m:
            raise ValueError("Could not initialize GPSEA map session")
        session.headers.update(
            {
                "X-BG-Session": m.group(1),
                "X-Requested-With": "XMLHttpRequest",
                "Referer": f"{self.base}/index.html",
            }
        )
        commune = self._resolve(
            session, self.filters[0], self._commune, [], [], "commune"
        )
        commune_input = self._filter_input(self.filters[0], commune, False)
        street = self._resolve(
            session,
            self.filters[1],
            self._street,
            [commune_input],
            [self.filters[0]],
            "street",
        )
        street_input = self._filter_input(self.filters[1], street, False)
        confirm_candidates = self._query_filter(
            session,
            self.filters[2],
            " ",
            [commune_input, street_input],
            [self.filters[0], self.filters[1]],
        )
        confirm = confirm_candidates[0] if confirm_candidates else street
        confirm_input = self._filter_input(self.filters[2], confirm, True)
        number = self._resolve(
            session,
            self.filters[3],
            self._house_number,
            [commune_input, street_input, confirm_input],
            [self.filters[0], self.filters[1], self.filters[2]],
            "house_number",
        )
        number_input = self._filter_input(self.filters[3], number, False)
        search_filters = {
            "coordinateSystem": {"srid": 3857},
            "currentObject": None,
            "locale": "fr",
            "filterInputs": [commune_input, street_input, confirm_input, number_input],
            "infoSheetContext": None,
            "featureSelectionFilter": {"features": [], "selectionCrs": "EPSG:3857"},
        }
        r = session.post(
            f"{self.api}/searches/execute",
            data={
                "centroid": "true",
                "simplifyGeometry": "false",
                "srid": "EPSG:3857",
                "useExtent": "true",
                "throwErrors": "false",
                "throwTimeoutErrors": "true",
                "limit": "51",
                "offset": "0",
                "searchIds": self.source_id,
                "filters": json.dumps(search_filters),
            },
            timeout=30,
        )
        r.raise_for_status()
        features = r.json().get("features", [])
        if not features:
            raise SourceArgumentNotFoundWithSuggestions(
                "house_number", self._house_number, []
            )
        feature_id = features[0]["properties"]["id_auto"]
        r = session.get(
            f"{self.api}/infoSheets/getData",
            params={
                "centroid": "false",
                "id": self.info_sheet,
                "idValue": feature_id,
                "srs": "EPSG:3857",
            },
            timeout=30,
        )
        r.raise_for_status()
        return r


class CalendarRetriever:
    def __init__(self, base, source_id, filters, info_sheet):
        self.base = base
        self.source_id = source_id
        self.filters = filters
        self.info_sheet = info_sheet

    def __call__(self, source):
        client = _Client(
            self.base, self.source_id, self.filters, self.info_sheet, **source.params
        )
        return client.retrieve(source.session)


def schedules(record, source):
    today = date.today()
    end = today + timedelta(days=365)
    calendar = record.get("Calendrier", "")
    years = re.findall(r"(?<!\d)(20\d{2})(?!\d)", calendar)
    if not years:
        raise ValueError("GPSEA infosheet has no dated calendar link")
    year = int(years[-1])
    for prefix in ("om", "em", "ve", "ec", "dv"):
        frequency = record.get(prefix + "_frequen") or ""
        if not frequency:
            continue
        day = record.get(prefix + "_jour") or ""
        parity = record.get(prefix + "_pairimp") or ""
        precision = record.get(prefix + "_precisi") or ""
        ampm = record.get(prefix + "_am_pm") or ""
        key = prefix + "|" + ampm
        if precision:
            dates = _parse_precisi_dates(precision, year)
            for d in dates:
                if today <= d <= end:
                    yield Schedule(key, d)
            bounded = _parse_precisi_range(precision, year)
            if not dates and not bounded:
                raise ValueError(
                    f"Unrecognized GPSEA dated precision for {prefix}: {precision!r}"
                )
            if bounded:
                start, until = bounded
                yield from _weekly_schedules(
                    key, day, frequency, parity, max(today, start), min(end, until)
                )
        else:
            yield from _weekly_schedules(key, day, frequency, parity, today, end)


def _weekly_schedules(key, day, frequency, parity, start, end):
    if frequency not in WEEKLY_FREQUENCIES and frequency != "QUINZAINE":
        raise ValueError(f"GPSEA frequency needs dated precision: {frequency!r}")
    if end < start:
        return
    for text in day.split():
        weekday = recurrence.weekday(text)
        if weekday is None:
            raise ValueError(f"Unrecognized GPSEA weekday: {text}")
        yield Schedule(
            key,
            recurrence.next_weekday(weekday, on_or_after=start),
            not_before=start,
            until=end,
            iso_week_parity=(
                "even" if parity == "PAIRE" else "odd" if parity == "IMPAIRE" else None
            )
            if frequency == "QUINZAINE"
            else None,
        )
