import datetime
import io
import re

import requests
from bs4 import BeautifulSoup
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTChar, LTCurve, LTRect, LTTextLine
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import (
    SourceArgumentException,
    SourceArgumentNotFound,
)

TITLE = "City of Edinburgh Council"
DESCRIPTION = (
    "Source for bin collection dates from the City of Edinburgh Council directory."
)
URL = "https://www.edinburgh.gov.uk/homepage/10474/bin-collections"
COUNTRY = "uk"

DIRECTORY_SEARCH = "https://www.edinburgh.gov.uk/directory/search"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"
HEADERS = {
    "User-Agent": "waste-collection-schedule/Edinburgh (+https://github.com/mampfes/hacs_waste_collection_schedule)"
}
DAY_NAMES = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]
CALENDAR_CODES = {day[:3]: day for day in DAY_NAMES}
MONTHS = {
    name: number
    for number, name in enumerate(
        (
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ),
        start=1,
    )
}
MONTHS.update({name[:3]: number for name, number in MONTHS.items()})

TEST_CASES = {"Test1": {"postcode": "EH10 4AY", "paon": "1 Morningside Road"}}

ICON_MAP = {
    "Food Waste Bin": Icons.BIO_KITCHEN,
    "Brown Garden Waste Bin": Icons.GARDEN,
    "Grey Bin": Icons.GENERAL_WASTE,
    "Green Bin": Icons.RECYCLING,
    "Glass Box": Icons.GLASS,
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Enter the property's postcode. The house number and street name can also be supplied to select the council record precisely.",
}
PARAM_DESCRIPTIONS = {
    "en": {
        "postcode": "Postcode of the property (required)",
        "paon": "Primary addressable object, such as house number and street (optional)",
    }
}
PARAM_TRANSLATIONS = {"en": {"postcode": "Postcode", "paon": "House number and street"}}


def _extract_street(paon):
    if not paon:
        return None
    value = str(paon).strip()
    if not value:
        return None
    without_number = re.sub(r"^\d+[A-Za-z]?\s+", "", value)
    if without_number != value:
        return without_number
    return value if not value[0].isdigit() else None


def _resolve_street(postcode, paon):
    street = _extract_street(paon)
    if street:
        return street
    # A postcode can cover several streets, so use its geocoded road as a fallback.
    try:
        response = requests.get(
            f"https://api.postcodes.io/postcodes/{str(postcode).replace(' ', '')}",
            headers=HEADERS,
            timeout=10,
        )
        if response.status_code != 200:
            return None
        result = response.json().get("result") or {}
        reverse = requests.get(
            NOMINATIM_URL,
            params={
                "lat": result["latitude"],
                "lon": result["longitude"],
                "format": "json",
                "addressdetails": 1,
            },
            headers=HEADERS,
            timeout=10,
        )
        if reverse.status_code == 200:
            address = reverse.json().get("address", {})
            return address.get("road") or address.get("street")
    except (KeyError, TypeError, ValueError, requests.RequestException):
        return None
    return None


def _search(street, directory_id):
    response = requests.get(
        DIRECTORY_SEARCH,
        params={"directoryID": str(directory_id), "keywords": street},
        headers=HEADERS,
        timeout=15,
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    records = []
    for link in soup.select("a.list__link[href*='/directory-record/']"):
        href = link.get("href", "")
        if not href.startswith("http"):
            href = "https://www.edinburgh.gov.uk" + href
        records.append((href, link.get_text(strip=True)))
    if not records:
        raise SourceArgumentNotFound(
            "postcode",
            street,
            "No Edinburgh collection record was found for this street.",
        )
    for href, title in records:
        if title.casefold() == street.casefold():
            return href
    return records[0][0]


def _record_details(url):
    response = requests.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    details = {}
    for dt in soup.find_all("dt"):
        label = dt.get_text(" ", strip=True).casefold()
        dd = dt.find_next_sibling("dd")
        if not dd:
            continue
        details[label] = dd.get_text(" ", strip=True)
        link = dd.find("a", href=True)
        if link:
            href = link["href"].strip()
            if not href.startswith("http"):
                href = "https://www.edinburgh.gov.uk" + href
            details[f"{label} url"] = href
    return details


def _download_pdf(url):
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    if not response.content.startswith(b"%PDF"):
        raise SourceArgumentException(
            "paon", f"Edinburgh calendar URL did not return a PDF: {url}"
        )
    return response.content


def _walk_layout(obj):
    if isinstance(obj, (LTChar, LTTextLine, LTRect, LTCurve)):
        yield obj
    if hasattr(obj, "__iter__"):
        for child in obj:
            yield from _walk_layout(child)


def _calendar_headers(objects):
    # PDFs may contain "Month Year" as one text line or as separate objects.
    headers = []
    split_months = []
    split_years = []
    for obj in objects:
        if not isinstance(obj, LTTextLine):
            continue
        text = obj.get_text().strip()
        match = re.fullmatch(r"([A-Za-z]+)\s+(20\d\d)", text)
        if match and match.group(1) in MONTHS:
            headers.append(
                (MONTHS[match.group(1)], int(match.group(2)), obj.x0, obj.x1, obj.y0)
            )
        elif text in MONTHS:
            split_months.append((MONTHS[text], obj.x0, obj.x1, obj.y0))
        elif re.fullmatch(r"20\d\d", text):
            split_years.append((int(text), obj.x0, obj.x1, obj.y0))
    for month, x0, x1, y0 in split_months:
        year = min(
            split_years,
            key=lambda value: abs(((value[1] + value[2]) / 2) - ((x0 + x1) / 2)),
            default=None,
        )
        if year and abs(((year[1] + year[2]) / 2) - ((x0 + x1) / 2)) < 15:
            headers.append((month, year[0], x0, x1, y0))
    return headers


def _marker_date(marker, headers, chars):
    center_x = (marker.x0 + marker.x1) / 2
    center_y = (marker.y0 + marker.y1) / 2
    digits = [
        char
        for char in chars
        if marker.x0 <= (char.x0 + char.x1) / 2 <= marker.x1
        and marker.y0 <= (char.y0 + char.y1) / 2 <= marker.y1
        and char.get_text().strip().isdigit()
    ]
    value = "".join(
        char.get_text() for char in sorted(digits, key=lambda char: char.x0)
    )
    if not value:
        return None
    candidates = [
        header
        for header in headers
        if header[2] <= center_x <= header[3] and header[4] > center_y
    ]
    if not candidates:
        # Split month/year headers do not have useful x1 values.
        candidates = [
            header
            for header in headers
            if abs(header[2] - center_x) < 30 and header[4] > center_y
        ]
    if not candidates:
        return None
    month, year, *_ = min(candidates, key=lambda header: header[4] - center_y)
    try:
        return datetime.date(year, month, int(value))
    except ValueError:
        return None


def _parse_calendar_pdf(content):
    objects = list(_walk_layout(next(extract_pages(io.BytesIO(content)))))
    headers = _calendar_headers(objects)
    chars = [obj for obj in objects if isinstance(obj, LTChar)]
    page_text = " ".join(
        obj.get_text().strip().casefold()
        for obj in objects
        if isinstance(obj, LTTextLine)
    )
    # The council uses marker fill/outline and explanatory text to identify streams.
    black_types = (
        ["Green Bin"]
        if "glass recycling box is collected every two weeks" in page_text
        and "mixed recycling box is collected every two weeks" in page_text
        else ["Grey Bin", "Glass Box"]
        if "grey non-recyclable waste bin and box for glass" in page_text
        else ["Grey Bin"]
        if "grey non-recyclable waste bin is" in page_text
        else []
    )
    outline_types = (
        ["Glass Box"]
        if "glass recycling box is collected every two weeks" in page_text
        and "mixed recycling box is collected every two weeks" in page_text
        else ["Green Bin", "Glass Box"]
        if "green bin for recycling and box for glass" in page_text
        else ["Green Bin"]
        if "green bin for recycling is" in page_text
        else []
    )
    if not black_types or not outline_types:
        raise SourceArgumentException(
            "paon", "Could not identify the bin streams in the Edinburgh calendar PDF."
        )
    dates = {bin_type: set() for bin_type in (*black_types, *outline_types)}
    for marker in objects:
        is_black = (
            isinstance(marker, LTRect)
            and marker.fill
            and 15 < marker.width < 30
            and 15 < marker.height < 30
        )
        is_outline = (
            isinstance(marker, LTCurve)
            and marker.stroke
            and not marker.fill
            and 15 < marker.width < 40
            and 15 < marker.height < 30
        )
        if not (is_black or is_outline):
            continue
        collection_date = _marker_date(marker, headers, chars)
        if collection_date:
            for bin_type in black_types if is_black else outline_types:
                dates[bin_type].add(collection_date)
    if not any(dates.values()):
        raise SourceArgumentException(
            "paon",
            "Could not parse any dated collections from the Edinburgh calendar PDF.",
        )
    return dates


def _parse_garden_pdf(content):
    objects = list(_walk_layout(next(extract_pages(io.BytesIO(content)))))
    headers = _calendar_headers(objects)
    chars = [obj for obj in objects if isinstance(obj, LTChar)]
    dates = set()
    for marker in objects:
        # Garden calendars use larger filled circles than the kerbside calendars.
        is_garden_marker = (
            isinstance(marker, LTCurve)
            and marker.fill
            and 30 < marker.width < 40
            and 30 < marker.height < 40
        )
        if is_garden_marker:
            collection_date = _marker_date(marker, headers, chars)
            if collection_date:
                dates.add(collection_date)
    if not dates:
        raise SourceArgumentException(
            "paon",
            "Could not parse any dated garden collections from the Edinburgh calendar PDF.",
        )
    return dates


def _parse_code(code):
    match = re.fullmatch(r"(Mon|Tue|Wed|Thu|Fri|Sat|Sun)_(\d)[A-Z]?", code or "")
    if not match:
        return None, None
    return CALENDAR_CODES[match.group(1)], int(match.group(2)) - 1


def _parse_garden_code(code):
    match = re.fullmatch(
        r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday)-(\d)", code or ""
    )
    if not match:
        return None, None
    return match.group(1).capitalize(), int(match.group(2)) - 1


def _next_weekday_dates(weekday, count, today):
    first = today + datetime.timedelta(days=(weekday - today.weekday()) % 7)
    return [first + datetime.timedelta(days=7 * index) for index in range(count)]


class Source:
    def __init__(self, postcode: str, paon: str | None = None):
        self._postcode = postcode
        self._paon = paon

    def fetch(self):
        street = _resolve_street(self._postcode, self._paon)
        if not street:
            raise SourceArgumentException(
                "paon", "Could not resolve a street from the supplied address."
            )

        three_url = _search(street, 10251)
        three_details = _record_details(three_url)
        day, _ = _parse_code(three_details.get("calendar code"))
        if day is None:
            raise SourceArgumentException(
                "paon", "Council returned an invalid three-bin calendar code."
            )
        calendar_url = three_details.get("calendar code url") or three_details.get(
            "calendar url"
        )
        if not calendar_url:
            raise SourceArgumentException(
                "paon", "Edinburgh record did not include a calendar PDF URL."
            )
        calendar_dates = _parse_calendar_pdf(_download_pdf(calendar_url))

        food_url = _search(street, 10248)
        food_day = _record_details(food_url).get("collection day")
        if food_day not in DAY_NAMES:
            raise SourceArgumentException(
                "paon", "Council returned an invalid food-waste collection day."
            )

        garden_url = _search(street, 10250)
        garden_details = _record_details(garden_url)
        garden_pdf_url = garden_details.get("calendar url") or garden_details.get(
            "garden calendar url"
        )
        garden_match = re.search(
            r"garden-waste-calendar-([^/?#]+)", garden_pdf_url or ""
        )
        garden_code = garden_match.group(1) if garden_match else None
        garden_day, _ = _parse_garden_code(garden_code)
        if garden_day is None or not garden_pdf_url:
            raise SourceArgumentException(
                "paon", "Council returned an invalid garden-waste calendar record."
            )
        garden_dates = _parse_garden_pdf(_download_pdf(garden_pdf_url))

        today = datetime.datetime.now(datetime.timezone.utc).date()
        entries = []
        # Food PDFs publish the weekday, not each date, so derive upcoming weeks.
        for date in _next_weekday_dates(DAY_NAMES.index(food_day), 56, today):
            entries.append(
                Collection(
                    date=date,
                    t="Food Waste Bin",
                    icon=ICON_MAP["Food Waste Bin"],
                )
            )
        for date in garden_dates:
            if date < today:
                continue
            entries.append(
                Collection(
                    date=date,
                    t="Brown Garden Waste Bin",
                    icon=ICON_MAP["Brown Garden Waste Bin"],
                )
            )
        for bin_type in ("Grey Bin", "Green Bin", "Glass Box"):
            for date in calendar_dates.get(bin_type, set()):
                if date >= today:
                    entries.append(
                        Collection(date=date, t=bin_type, icon=ICON_MAP[bin_type])
                    )
        return sorted(entries, key=lambda entry: entry.date)
