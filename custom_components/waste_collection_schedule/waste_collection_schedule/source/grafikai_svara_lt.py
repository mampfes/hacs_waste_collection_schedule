"""Kauno švara waste collection schedule, based on the company's open-data CSV.

Since autumn 2026 the schedule search site https://grafikai.svara.lt protects
every data call with a Cloudflare Turnstile session, so it can no longer be
used by an integration (#7662). UAB "Kauno švara" instead publishes an
open-data CSV export of all served collection points on its SharePoint site
("Atviri duomenys"). The file is refreshed every night around 03:00 and
contains, for every container:

    region; district; city; street; house number; container id;
    next collection date; collection frequency (Lithuanian text); service name

Only the next collection date(s) are included, so this source additionally
extrapolates further dates from the published frequency ("kas 14 dienų",
"antrąjį mėnesyje antradienį", ...) for a limited horizon. The CSV is
re-read on every fetch, so extrapolated dates are corrected daily by the
official data.
"""

import csv
import datetime
import difflib
import gzip
import io
import logging
import re
import threading
import time
from urllib.parse import parse_qs, urlparse

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFoundWithSuggestions,
)

_LOGGER = logging.getLogger(__name__)

TITLE = "Kauno švara"
DESCRIPTION = (
    'Source for UAB "Kauno švara" (Kaunas city and district, Prienai, Birštonas, '
    "Alytus, Druskininkai, Kaišiadorys, Vilnius) based on the company's "
    "open-data export."
)
URL = "https://grafikai.svara.lt"
COUNTRY = "lt"
TEST_CASES = {
    "Demokratų g. 7, Kaunas": {
        "region": "Kauno m. sav.",
        "street": "Demokratų g.",
        "house_number": "7",
    },
    "Alytaus g. 2, Išlaužo k., Išlaužo sen. Prienų r. sav.": {
        "region": "Prienų r. sav.",
        "street": "Alytaus g.",
        "house_number": 2,
        "district": "Išlaužo sen.",
    },
    "Alytaus g. 2, Verbyliškių k. (selected by city)": {
        "region": "Prienų r. sav.",
        "street": "Alytaus g.",
        "house_number": "2",
        "city": "Verbyliškių k.",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Use the same values as in the address search on https://grafikai.svara.lt: "
        "'Regionas' is the region, 'Seniūnija' the district, 'Gatvė' the street and "
        "'Namo numeris' the house number. If a value is misspelled, the error message "
        "lists the valid alternatives."
    ),
}

PARAM_TRANSLATIONS = {
    "en": {
        "region": "Region (Regionas)",
        "street": "Street (Gatvė)",
        "house_number": "House number (Namo numeris)",
        "district": "District (Seniūnija)",
        "city": "City / settlement (Miestas, gyvenvietė)",
        "containers": "Container IDs",
        "waste_object_ids": "Waste object IDs (deprecated)",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "region": "Municipality as used by Kauno švara, e.g. 'Kauno m. sav.', 'Kauno r. sav.', 'Prienų r. sav.', 'Alytaus m. sav.'.",
        "street": "Street name including the abbreviation, e.g. 'Demokratų g.'.",
        "house_number": "House number as registered, e.g. '7', '2A', '132B'.",
        "district": "Optional. Only needed if the same street and house number exists in several districts of the region, e.g. 'Išlaužo sen.'.",
        "city": "Optional. City or settlement, e.g. 'Kauno m.', 'Garliavos m.', 'Domeikavos k.'. Alternative to district for disambiguation.",
        "containers": "Optional list of container IDs (e.g. 'MK-004108') to restrict the result to specific containers of the address.",
        "waste_object_ids": "Deprecated and ignored. IDs from the old grafikai.svara.lt API are no longer available; use 'containers' instead.",
    },
}

ICON_MAP = {
    "mišrios komunalinės": Icons.GENERAL_WASTE,
    "mišrios komunalinės atliekos": Icons.GENERAL_WASTE,
    "mišrios atliekos": Icons.GENERAL_WASTE,
    "atliekų tvarkymas": Icons.GENERAL_WASTE,
    "antrinės žaliavos": Icons.RECYCLING,
    "antrinės žaliavos (pakuotės)": Icons.RECYCLING,
    "antrinės žaliavos (popierius/plastikas)": Icons.RECYCLING,
    "antrinės žaliavos (popierius)": Icons.PAPER,
    "antrinės žaliavos (stiklas)": Icons.GLASS,
    "maistinės atliekos": Icons.BIO_KITCHEN,
    "žaliosios atliekos": Icons.GARDEN,
    "stambiagabaritės": Icons.BULKY,
}

# Anonymous sharing link published by UAB Kauno švara ("Atviri duomenys").
# Following it yields a FedAuth cookie for the anonymous session plus the
# document GUID; the raw file is then fetched through download.aspx.
_SHARE_URL = (
    "https://kaunosvara.sharepoint.com/:x:/s/Atviriduomenys/"
    "IQAoxJ77_IFQTqsKRL7G5bhvAQS-Vo2yqMaFOgJerhsreP8"
)
_SITE_URL = "https://kaunosvara.sharepoint.com/sites/Atviriduomenys"
_DOC_GUID_FALLBACK = "fb9ec428-81fc-4e50-ab0a-44bec6e5b86f"
_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"
)

# The CSV is ~55 MB and identical for every address, so one download is shared
# between all source instances (gzip-compressed, ~4 MB) for a few hours. The
# file itself only changes once a night.
_CACHE_TTL_SECONDS = 6 * 60 * 60
_cache_lock = threading.Lock()
_cache: dict[str, object] = {"time": 0.0, "gz": b""}

# The open data lists only the next collection date per container. Further
# dates are extrapolated from the published frequency up to this many days.
_EXTRAPOLATION_HORIZON_DAYS = 60
# A row whose date passed more than this many days ago is a series the provider
# no longer maintains, so nothing is extrapolated from it. The grace period
# covers the gap between a collection and the next nightly refresh of the file.
_STALE_ROW_GRACE_DAYS = 2

_MONTHS = {
    "sausį": 1,
    "vasarį": 2,
    "kovą": 3,
    "balandį": 4,
    "gegužę": 5,
    "birželį": 6,
    "liepą": 7,
    "rugpjūtį": 8,
    "rugsėjį": 9,
    "spalį": 10,
    "lapkritį": 11,
    "gruodį": 12,
}
_WEEKDAYS = {
    "pirmadienį": 0,
    "antradienį": 1,
    "trečiadienį": 2,
    "ketvirtadienį": 3,
    "penktadienį": 4,
    "šeštadienį": 5,
    "sekmadienį": 6,
}
_ORDINALS = {
    "pirmąjį": 1,
    "antrąjį": 2,
    "trečiąjį": 3,
    "ketvirtąjį": 4,
    "penktąjį": 5,
}
_RE_EVERY_N_DAYS = re.compile(r"^kas\s+(\d+)\s+dien(?:ų|ą|as)$")
_RE_DAY_OF_MONTH = re.compile(r"^(\d{1,2})\s+mėnesio\s+dieną$")
_RE_NTH_WEEKDAY = re.compile(r"^(\S+)\s+mėnesyje\s+(\S+)$")


def _norm(value: object) -> str:
    """Normalise user input / CSV cells for comparison."""
    return " ".join(str(value).casefold().split())


def _icon_for(service: str) -> str:
    key = _norm(service)
    if key in ICON_MAP:
        return ICON_MAP[key]
    if "stikl" in key:
        return Icons.GLASS
    if "popier" in key or "plastik" in key or "pakuo" in key or "antrin" in key:
        return Icons.RECYCLING
    if "maist" in key:
        return Icons.BIO_KITCHEN
    if "žali" in key:
        return Icons.GARDEN
    if "stambia" in key:
        return Icons.BULKY
    return Icons.GENERAL_WASTE


def _house_sort_key(value: str) -> tuple[int, str]:
    m = re.match(r"(\d+)", value)
    return (int(m.group(1)) if m else 10**9, value)


class _Frequency:
    """Parsed representation of a Kauno švara frequency description."""

    def __init__(self) -> None:
        self.interval_days: int | None = None
        self.months: set[int] = set()
        self.day_of_month: int | None = None
        self.nth_weekday: tuple[int, int] | None = None  # (n, weekday)
        self.weekdays: set[int] = set()

    @classmethod
    def parse(cls, text: str) -> "_Frequency | None":
        """Return a parsed frequency or None when the text is not understood."""
        freq = cls()
        for raw in text.split(","):
            token = " ".join(raw.casefold().split())
            if not token:
                continue
            if token in _MONTHS:
                freq.months.add(_MONTHS[token])
                continue
            if token == "kiekvieną mėnesį":
                freq.months.update(range(1, 13))
                continue
            if token in ("kiekvieną mėnesio dieną", "kiekvieną savaitės dieną"):
                # "any day of month" / "any weekday": no constraint.
                continue
            if token in _WEEKDAYS:
                freq.weekdays.add(_WEEKDAYS[token])
                continue
            m = _RE_EVERY_N_DAYS.match(token)
            if m:
                freq.interval_days = int(m.group(1))
                continue
            m = _RE_DAY_OF_MONTH.match(token)
            if m:
                freq.day_of_month = int(m.group(1))
                continue
            m = _RE_NTH_WEEKDAY.match(token)
            if m and m.group(1) in _ORDINALS and m.group(2) in _WEEKDAYS:
                freq.nth_weekday = (_ORDINALS[m.group(1)], _WEEKDAYS[m.group(2)])
                continue
            return None
        if (
            freq.interval_days is None
            and freq.day_of_month is None
            and freq.nth_weekday is None
            and not freq.weekdays
        ):
            return None
        return freq

    def _month_allowed(self, month: int) -> bool:
        return not self.months or month in self.months

    def dates(self, start: datetime.date, end: datetime.date) -> list[datetime.date]:
        """Generate dates in (start, end] following this frequency."""
        result: list[datetime.date] = []
        if self.interval_days:
            d = start + datetime.timedelta(days=self.interval_days)
            while d <= end:
                if self._month_allowed(d.month):
                    result.append(d)
                d += datetime.timedelta(days=self.interval_days)
            return result

        if self.weekdays:
            d = start + datetime.timedelta(days=1)
            while d <= end:
                if d.weekday() in self.weekdays and self._month_allowed(d.month):
                    result.append(d)
                d += datetime.timedelta(days=1)
            return result

        # Month based rules: iterate over the months from start to end.
        year, month = start.year, start.month
        while datetime.date(year, month, 1) <= end:
            if self._month_allowed(month):
                d: datetime.date | None = None
                if self.day_of_month is not None:
                    try:
                        d = datetime.date(year, month, self.day_of_month)
                    except ValueError:
                        d = None
                elif self.nth_weekday is not None:
                    n, weekday = self.nth_weekday
                    first = datetime.date(year, month, 1)
                    offset = (weekday - first.weekday()) % 7
                    day = 1 + offset + (n - 1) * 7
                    try:
                        d = datetime.date(year, month, day)
                    except ValueError:
                        d = None  # e.g. the fifth Tuesday does not exist
                if d is not None and start < d <= end:
                    result.append(d)
            month += 1
            if month > 12:
                month = 1
                year += 1
        return result


def _download_csv_gz() -> bytes:
    """Download the open-data CSV and return it gzip-compressed."""
    session = requests.Session()
    session.headers["User-Agent"] = _USER_AGENT

    # Step 1: follow the sharing link; this sets the anonymous FedAuth cookie
    # and lands on Doc.aspx?sourcedoc={GUID}.
    r = session.get(_SHARE_URL, timeout=60)
    r.raise_for_status()
    guid = _DOC_GUID_FALLBACK
    site = _SITE_URL
    parsed = urlparse(r.url)
    sourcedoc = parse_qs(parsed.query).get("sourcedoc", [""])[0]
    m = re.search(r"[0-9a-fA-F-]{36}", sourcedoc)
    if m:
        guid = m.group(0)
    m = re.match(r"^(/sites/[^/]+)/", parsed.path)
    if m:
        site = f"{parsed.scheme}://{parsed.netloc}{m.group(1)}"

    # Step 2: download the raw file.
    r = session.get(
        f"{site}/_layouts/15/download.aspx",
        params={"UniqueId": guid},
        stream=True,
        timeout=180,
    )
    r.raise_for_status()
    if "text/html" in r.headers.get("content-type", ""):
        raise RuntimeError(
            "Kauno švara open-data download returned an HTML page instead of the "
            "CSV file; the sharing link may have changed."
        )
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb", compresslevel=3) as gz:
        for chunk in r.iter_content(chunk_size=1 << 18):
            if chunk:
                gz.write(chunk)
    data = buf.getvalue()
    if len(data) < 1000:
        raise RuntimeError("Kauno švara open-data CSV download was unexpectedly small.")
    return data


def _get_csv_gz() -> bytes:
    with _cache_lock:
        age = time.time() - float(_cache["time"])  # type: ignore[arg-type]
        if _cache["gz"] and age < _CACHE_TTL_SECONDS:
            return _cache["gz"]  # type: ignore[return-value]
        data = _download_csv_gz()
        _cache["gz"] = data
        _cache["time"] = time.time()
        _LOGGER.debug("Downloaded Kauno švara open data (%d bytes gzipped)", len(data))
        return data


def _iter_rows(gz_data: bytes):
    with (
        gzip.GzipFile(fileobj=io.BytesIO(gz_data)) as gz,
        io.TextIOWrapper(gz, encoding="utf-8-sig", newline="") as text,
    ):
        for row in csv.reader(text, delimiter=";"):
            if len(row) == 9:
                yield row


class Source:
    def __init__(
        self,
        region: str,
        street: str,
        house_number: str | int,
        district: str | None = None,
        city: str | None = None,
        containers: list[str] | str | None = None,
        waste_object_ids: list[str | int] | None = None,
    ):
        self._region = str(region).strip()
        self._street = str(street).strip()
        self._house_number = str(house_number).strip()
        self._district = str(district).strip() if district else None
        self._city = str(city).strip() if city else None
        if containers is None:
            containers = []
        if isinstance(containers, str):
            containers = [containers]
        self._containers = {_norm(c) for c in containers if str(c).strip()}
        if waste_object_ids:
            _LOGGER.warning(
                "grafikai_svara_lt: 'waste_object_ids' is no longer supported and is "
                "ignored; use 'containers' with the container IDs from the open data"
            )

    def _select_rows(self, gz_data: bytes) -> list[list[str]]:
        region = _norm(self._region)
        street = _norm(self._street)
        house = _norm(self._house_number)

        regions: set[str] = set()
        streets_in_region: set[str] = set()
        street_rows: list[list[str]] = []
        for row in _iter_rows(gz_data):
            if row[0]:
                regions.add(row[0])
            if _norm(row[0]) != region:
                continue
            streets_in_region.add(row[3])
            if _norm(row[3]) == street:
                street_rows.append(row)

        if not streets_in_region:
            raise SourceArgumentNotFoundWithSuggestions(
                "region", self._region, sorted(regions)
            )
        if not street_rows:
            suggestions = difflib.get_close_matches(
                self._street, sorted(streets_in_region), n=10, cutoff=0.5
            )
            raise SourceArgumentNotFoundWithSuggestions(
                "street", self._street, suggestions
            )

        house_rows = [r for r in street_rows if _norm(r[4]) == house]
        if not house_rows:
            numbers = sorted({r[4] for r in street_rows}, key=_house_sort_key)
            raise SourceArgumentNotFoundWithSuggestions(
                "house_number", self._house_number, numbers
            )

        if self._district:
            district = _norm(self._district)
            # Most Kaunas and Alytus rows have an empty district, so an empty
            # cell matches any district rather than excluding the address.
            filtered = [r for r in house_rows if _norm(r[1]) in (district, "")]
            if not filtered:
                raise SourceArgumentNotFoundWithSuggestions(
                    "district", self._district, sorted({r[1] for r in house_rows})
                )
            house_rows = filtered
        if self._city:
            city = _norm(self._city)
            filtered = [r for r in house_rows if _norm(r[2]) == city]
            if not filtered:
                raise SourceArgumentNotFoundWithSuggestions(
                    "city", self._city, sorted({r[2] for r in house_rows})
                )
            house_rows = filtered

        if not self._district and not self._city:
            # An empty district cell is not a second place: the same address is
            # often listed both with and without its district.
            districts = sorted({r[1] for r in house_rows if r[1]})
            if len(districts) > 1:
                raise SourceArgAmbiguousWithSuggestions(
                    "district", self._district, districts
                )
            cities = sorted({r[2] for r in house_rows})
            if len(cities) > 1:
                raise SourceArgAmbiguousWithSuggestions("city", self._city, cities)

        if self._containers:
            filtered = [r for r in house_rows if _norm(r[5]) in self._containers]
            if not filtered:
                raise SourceArgumentNotFoundWithSuggestions(
                    "containers",
                    ", ".join(sorted(self._containers)),
                    sorted({r[5] for r in house_rows}),
                )
            house_rows = filtered
        return house_rows

    def fetch(self) -> list[Collection]:
        rows = self._select_rows(_get_csv_gz())
        today = datetime.date.today()
        end = today + datetime.timedelta(days=_EXTRAPOLATION_HORIZON_DAYS)

        stale_before = today - datetime.timedelta(days=_STALE_ROW_GRACE_DAYS)

        # Every row is a series of its own: a container can have several rows
        # with different rules ("first Tuesday" plus "third Friday") or the same
        # rule on different dates (two rounds of "kas 14 dienų" a week apart).
        seen: set[tuple[datetime.date, str]] = set()
        entries: list[Collection] = []
        for row in rows:
            try:
                listed = datetime.date.fromisoformat(row[6][:10])
            except ValueError:
                continue
            frequency, service = row[7].strip(), row[8].strip()
            dates = {listed}
            if listed >= stale_before:
                freq = _Frequency.parse(frequency)
                if freq is None:
                    _LOGGER.debug(
                        "grafikai_svara_lt: frequency %r not understood, "
                        "using the listed date only",
                        frequency,
                    )
                else:
                    dates.update(d for d in freq.dates(listed, end) if d >= today)
            icon = _icon_for(service)
            for date in sorted(dates):
                key = (date, service)
                if key in seen:
                    continue
                seen.add(key)
                entries.append(Collection(date=date, t=service, icon=icon))
        return entries
