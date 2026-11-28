"""Source for Lakeshore Recycling Systems (LRS), Illinois and Indiana, USA."""

import logging
import re
from datetime import date, datetime, timedelta

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentException,
    SourceArgumentNotFound,
)

_LOGGER = logging.getLogger(__name__)

TITLE = "Lakeshore Recycling Systems (LRS)"
DESCRIPTION = "Source for Lakeshore Recycling Systems (LRS) residential and commercial pickup days in Illinois and Indiana."
URL = "https://www.lrsrecycles.com"
COUNTRY = "us"
SOURCE_CODEOWNERS = ["@Cornflake5414"]

TEST_CASES = {
    "10 E Washington St, Indianapolis IN": {
        "address": "10 E WASHINGTON ST",
        "zip": "46204",
    },
    "Oak Park Village Hall, IL": {
        "address": "123 Madison Street",
        "zip": "60302",
        "recycling_date": "2026-12-03",
        "organics_start": "04-01",
        "organics_end": "11-30",
    },
    "Deerfield Village Hall, IL": {
        "address": "850 Waukegan Rd",
        "zip": "60015",
        "include_commercial": True,
    },
    "Skokie Village Hall, IL": {"address": "5127 Oakton St", "zip": 60077},
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Enter the street line of your address exactly as LRS stores it, using USPS "
        "abbreviations (ST, AVE, RD, N/S/E/W) and without city or state, e.g. "
        "'123 MADISON ST'. You can check it at https://www.lrsrecycles.com/map under "
        "'Current Customer? Want to see your pickup day?'. For biweekly residential "
        "recycling, set recycling_date to any one known recycling pickup date (YYYY-MM-DD). "
        "If your town collects organics (yard waste/compost) only seasonally, set "
        "organics_start and organics_end (MM-DD, e.g. 04-01 and 11-30); see your "
        "town's page on lrsrecycles.com for the season."
    ),
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Street Address",
        "zip": "ZIP Code",
        "recycling_date": "Known Recycling Date",
        "organics_start": "Organics Season Start",
        "organics_end": "Organics Season End",
        "include_commercial": "Include Commercial Services",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "House number and street, without city/state (e.g. '123 MADISON ST')",
        "zip": "5-digit ZIP code",
        "recycling_date": "Any one known residential recycling pickup date (YYYY-MM-DD); needed for the biweekly recycling schedule",
        "organics_start": "First day of the organics (yard waste/compost) season, MM-DD (e.g. 04-01); leave empty for year-round",
        "organics_end": "Last day of the organics (yard waste/compost) season, MM-DD (e.g. 11-30); leave empty for year-round",
        "include_commercial": "Also show commercial (COMML) services for this address",
    },
}

ICON_MAP = {
    "Trash": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
    "Organics": Icons.ORGANIC,
    "Commercial Trash": Icons.GENERAL_WASTE,
    "Commercial Recycling": Icons.RECYCLING,
    "Commercial Organics": Icons.ORGANIC,
}

API_URL = "https://lrsrecycles-apim-prod-bbdfe2ahaxe8ebgy.z03.azurefd.net/prod/lrswebsite/getPickupDay"
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Origin": "https://www.lrsrecycles.com",
    "Referer": "https://www.lrsrecycles.com/",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
}

WEEKS_AHEAD = 10

DAY_TOKENS = {"MON": 0, "TUE": 1, "WED": 2, "THU": 3, "FRI": 4, "SAT": 5, "SUN": 6}

ABBREVIATIONS = {
    "STREET": "ST",
    "AVENUE": "AVE",
    "ROAD": "RD",
    "DRIVE": "DR",
    "LANE": "LN",
    "COURT": "CT",
    "BOULEVARD": "BLVD",
    "PLACE": "PL",
    "PARKWAY": "PKWY",
    "TERRACE": "TER",
    "CIRCLE": "CIR",
    "HIGHWAY": "HWY",
    "NORTH": "N",
    "SOUTH": "S",
    "EAST": "E",
    "WEST": "W",
}
_ABBR_RE = re.compile(r"\b(" + "|".join(ABBREVIATIONS) + r")\b")


def _normalize_address(address: str) -> str:
    addr = re.sub(r"\s+", " ", str(address).strip()).upper()
    addr = addr.rstrip(".,").strip()
    addr = _ABBR_RE.sub(lambda m: ABBREVIATIONS[m.group(1)], addr)
    return addr


def _nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    d = date(year, month, 1)
    d += timedelta(days=(weekday - d.weekday()) % 7)
    return d + timedelta(weeks=n - 1)


def _last_weekday(year: int, month: int, weekday: int) -> date:
    d = date(year, month + 1, 1) - timedelta(days=1)
    return d - timedelta(days=(d.weekday() - weekday) % 7)


def _holidays(year: int) -> list[date]:
    """Holidays observed by LRS (actual dates, no observed-day moving)."""
    return [
        date(year, 1, 1),  # New Year's Day
        _last_weekday(year, 5, 0),  # Memorial Day
        date(year, 7, 4),  # Independence Day
        _nth_weekday(year, 9, 0, 1),  # Labor Day
        _nth_weekday(year, 11, 3, 4),  # Thanksgiving
        date(year, 12, 25),  # Christmas
    ]


def _week_start(d: date) -> date:
    return d - timedelta(days=d.weekday())


def _shift_for_holiday(d: date, holidays: set[date]) -> date:
    """Push a pickup one day if a weekday holiday falls on/before it in the same week."""
    monday = _week_start(d)
    for h in holidays:
        if h.weekday() < 5 and _week_start(h) == monday and d >= h:
            return d + timedelta(days=1)
    return d


def _parse_days(pickup_days: str) -> list[int]:
    days: list[int] = []
    for token in re.split(r"[ ,]+", str(pickup_days or "").upper()):
        wd = DAY_TOKENS.get(token)
        if wd is not None and wd not in days:
            days.append(wd)
    return days


def _parse_month_day(param: str, value) -> tuple[int, int] | None:
    if value in (None, ""):
        return None
    try:
        d = datetime.strptime(f"2000-{str(value).strip()}", "%Y-%m-%d")
    except ValueError as e:
        raise SourceArgumentException(
            param, f"Invalid {param} '{value}', expected format MM-DD (e.g. 04-01)."
        ) from e
    return (d.month, d.day)


def _in_season(d: date, start: tuple[int, int], end: tuple[int, int]) -> bool:
    md = (d.month, d.day)
    if start <= end:
        return start <= md <= end
    return md >= start or md <= end  # season wraps around the new year


def _type_name(service_type: str) -> str:
    st = re.sub(r"\s+", " ", service_type.strip().upper())
    if st in ("RESI TRASH", "RESI TRASH BD"):
        return "Trash"
    if st == "RESI RECYCLE":
        return "Recycling"
    if st == "RESI ORGANICS":
        return "Organics"
    if st.startswith("COMML"):
        if st.endswith("TRASH"):
            return "Commercial Trash"
        if st.endswith("RECYCLE"):
            return "Commercial Recycling"
        if st.endswith("ORGANICS"):
            return "Commercial Organics"
    return service_type.strip().title()


class Source:
    def __init__(
        self,
        address: str,
        zip: str | int,
        recycling_date: str | date | None = None,
        include_commercial: bool = False,
        organics_start: str | None = None,
        organics_end: str | None = None,
    ):
        self._address = _normalize_address(address)
        if "%" in self._address or "_" in self._address:
            raise SourceArgumentException(
                "address", "The address must not contain '%' or '_' characters."
            )
        if not re.match(r"^\d+[A-Z]?\s+\S", self._address):
            raise SourceArgumentException(
                "address",
                "The address must start with a house number followed by the street, "
                "e.g. '123 MADISON ST' (no city or state).",
            )

        self._zip = str(zip).strip()
        if not re.fullmatch(r"\d{5}", self._zip):
            raise SourceArgumentException("zip", "The ZIP code must be 5 digits.")

        self._recycling_date: date | None = None
        if recycling_date not in (None, ""):
            if isinstance(recycling_date, datetime):
                self._recycling_date = recycling_date.date()
            elif isinstance(recycling_date, date):
                self._recycling_date = recycling_date
            else:
                try:
                    self._recycling_date = datetime.strptime(
                        str(recycling_date).strip(), "%Y-%m-%d"
                    ).date()
                except ValueError as e:
                    raise SourceArgumentException(
                        "recycling_date",
                        f"Invalid recycling_date '{recycling_date}', expected format YYYY-MM-DD.",
                    ) from e

        self._include_commercial = bool(include_commercial)

        self._organics_start = _parse_month_day("organics_start", organics_start)
        self._organics_end = _parse_month_day("organics_end", organics_end)
        if (self._organics_start is None) != (self._organics_end is None):
            raise SourceArgumentException(
                "organics_start" if self._organics_start is None else "organics_end",
                "Set both organics_start and organics_end, or neither.",
            )

    def _get_services(self) -> list[dict]:
        r = requests.post(
            API_URL,
            json={"zip": self._zip, "address": self._address},
            headers=HEADERS,
            timeout=30,
        )
        r.raise_for_status()
        data = r.json().get("data") or []
        if not data:
            raise SourceArgumentNotFound(
                "address",
                self._address,
                "LRS has no pickup information for this address/ZIP. Check the "
                "street line at https://www.lrsrecycles.com/map (use USPS "
                "abbreviations such as ST, AVE, RD and no city/state).",
            )
        return data

    def _is_biweekly_recycling(self, service_type: str) -> bool:
        return service_type.strip().upper() == "RESI RECYCLE"

    def fetch(self) -> list[Collection]:
        services = self._get_services()

        has_resi = any(
            str(s.get("SERVICE_TYPE", "")).strip().upper().startswith("RESI")
            for s in services
        )
        include_comml = self._include_commercial or not has_resi

        start = _week_start(date.today())
        end = start + timedelta(weeks=WEEKS_AHEAD)
        holidays = {h for y in range(start.year, end.year + 1) for h in _holidays(y)}

        ref_week = _week_start(self._recycling_date) if self._recycling_date else None

        seen: set[tuple[date, str]] = set()
        entries: list[Collection] = []

        for service in services:
            service_type = str(service.get("SERVICE_TYPE", "")).strip()
            if not service_type:
                continue
            if service_type.upper().startswith("COMML") and not include_comml:
                continue

            weekdays = _parse_days(service.get("PICKUP_DAYS", ""))
            if not weekdays:
                continue

            biweekly = self._is_biweekly_recycling(service_type)
            if biweekly and ref_week is None:
                _LOGGER.warning(
                    "No recycling_date configured for %s; residential recycling "
                    "is shown weekly although LRS collects it biweekly.",
                    self._address,
                )
                biweekly = False

            name = _type_name(service_type)
            icon = ICON_MAP.get(name, Icons.GENERAL_WASTE)
            seasonal = (
                name == "Organics"
                and self._organics_start is not None
                and self._organics_end is not None
            )

            week = start
            while week < end:
                if biweekly and ref_week is not None:
                    if ((week - ref_week).days // 7) % 2 != 0:
                        week += timedelta(weeks=1)
                        continue
                for wd in weekdays:
                    nominal = week + timedelta(days=wd)
                    if seasonal and not _in_season(
                        nominal,
                        self._organics_start,
                        self._organics_end,  # type: ignore[arg-type]
                    ):
                        continue
                    d = _shift_for_holiday(nominal, holidays)
                    key = (d, name)
                    if key in seen:
                        continue
                    seen.add(key)
                    entries.append(Collection(date=d, t=name, icon=icon))
                week += timedelta(weeks=1)

        if not entries:
            raise SourceArgumentNotFound(
                "address",
                self._address,
                "LRS returned no usable pickup days for this address.",
            )

        return entries
