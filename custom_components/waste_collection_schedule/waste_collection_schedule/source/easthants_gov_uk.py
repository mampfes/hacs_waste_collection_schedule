import datetime
import io
import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTRect, LTTextLine
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import (
    SourceArgumentException,
    SourceArgumentNotFound,
)

TITLE = "East Hampshire District Council"
DESCRIPTION = "Source for East Hampshire District Council bin collection dates."
URL = "https://www.easthants.gov.uk/bin-collections/find-your-bin-calendar"
COUNTRY = "uk"

TEST_CASES = {
    "2 Newfield Road, Liss, GU33 7BW": {"uprn": 1710041123},
}

ADDRESS_URL = "https://maps.easthants.gov.uk/easthampshire.aspx"
HEADERS = {
    "User-Agent": "waste-collection-schedule/easthants_gov_uk",
}
MONTHS = {
    name: number
    for number, name in enumerate(
        (
            "JAN",
            "FEB",
            "MAR",
            "APR",
            "MAY",
            "JUN",
            "JUL",
            "AUG",
            "SEP",
            "OCT",
            "NOV",
            "DEC",
        ),
        start=1,
    )
}
WEEKDAYS = {
    name: number
    for number, name in enumerate(("MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"))
}
DAY_NAMES = {
    name: number
    for number, name in enumerate(
        ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
    )
}

ICON_MAP = {
    "Rubbish": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
    "Glass": Icons.GLASS,
    "Garden Waste": Icons.GARDEN,
}

PARAM_DESCRIPTIONS = {
    "en": {
        "uprn": "The property's Unique Property Reference Number (UPRN).",
    }
}
PARAM_TRANSLATIONS = {"en": {"uprn": "Property reference (UPRN)"}}
HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Search for the property at the East Hampshire bin calendar page or "
        "council map and use its UPRN."
    )
}


def _walk_layout(obj):
    yield obj
    if hasattr(obj, "__iter__"):
        for child in obj:
            yield from _walk_layout(child)


def _layout_objects(content):
    return list(_walk_layout(next(extract_pages(io.BytesIO(content)))))


def _month_headers(objects):
    headers = []
    for obj in objects:
        if not isinstance(obj, LTTextLine):
            continue
        match = re.fullmatch(r"([A-Z]{3})\s+(20\d\d)", obj.get_text().strip())
        if match and match.group(1) in MONTHS:
            headers.append(
                (MONTHS[match.group(1)], int(match.group(2)), obj.x0, obj.x1, obj.y0)
            )
    return headers


def _date_lines(objects):
    dates = []
    for obj in objects:
        if not isinstance(obj, LTTextLine):
            continue
        match = re.fullmatch(
            r"(MON|TUE|WED|THU|FRI|SAT|SUN)\s+(\d{1,2})", obj.get_text().strip()
        )
        if match:
            dates.append((obj, WEEKDAYS[match.group(1)], int(match.group(2))))
    return dates


def _date_for_line(line, day, day_number, headers):
    center_x = (line.x0 + line.x1) / 2
    candidates = [
        header
        for header in headers
        if header[4] > line.y1 and header[2] - 3 <= center_x <= header[3] + 3
    ]
    if not candidates:
        return None
    month, year, *_ = min(candidates, key=lambda header: header[4] - line.y1)
    try:
        return datetime.date(year, month, day_number)
    except ValueError:
        return None


def _cell_colour(line, objects):
    center_x = (line.x0 + line.x1) / 2
    center_y = (line.y0 + line.y1) / 2
    cells = [
        obj
        for obj in objects
        if isinstance(obj, LTRect)
        and obj.fill
        and obj.width > 30
        and obj.height > 8
        and obj.x0 <= center_x <= obj.x1
        and obj.y0 <= center_y <= obj.y1
    ]
    if not cells:
        return None
    return min(cells, key=lambda cell: cell.width * cell.height).non_stroking_color


def _normal_colour(colour):
    if not colour:
        return None
    red, green, blue = colour[:3]
    if green > 0.5 and red < 0.5:
        return "green"
    if red < 0.6 and green < 0.6 and blue < 0.6:
        return "grey"
    if red > 0.8 and green > 0.5 and blue < 0.2:
        return "bank_holiday"
    return None


def _parse_bin_calendar(content):
    objects = _layout_objects(content)
    headers = _month_headers(objects)
    lines = _date_lines(objects)
    text = " ".join(
        re.sub(r"\s+", " ", obj.get_text()).strip().casefold()
        for obj in objects
        if isinstance(obj, LTTextLine)
    )
    parsed = []
    for line, weekday, day_number in lines:
        collection_date = _date_for_line(line, weekday, day_number, headers)
        if collection_date:
            parsed.append(
                (collection_date, weekday, _normal_colour(_cell_colour(line, objects)))
            )
    if not parsed:
        raise SourceArgumentException(
            "uprn", "Could not parse the East Hampshire bin calendar."
        )

    separate_glass = "glass will be collected on" in text
    all_streams = "bags and glass box" in text
    glass_day = None
    bags_day = None
    if separate_glass:
        glass_match = re.search(
            r"glass will be collected on\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)",
            text,
        )
        bags_match = re.search(
            r"rubbish and recycling(?: bags)? will be\s+collected on\s+"
            r"(?:a\s+)?"
            r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday)",
            text,
        )
        glass_day = DAY_NAMES.get(glass_match.group(1).title()) if glass_match else None
        bags_day = DAY_NAMES.get(bags_match.group(1).title()) if bags_match else None
        if glass_day is None or bags_day is None:
            raise SourceArgumentException(
                "uprn", "Could not identify East Hampshire collection days."
            )

    entries = []
    previous_colour = None
    for collection_date, weekday, colour in sorted(parsed):
        if separate_glass:
            types = ["Glass"] if weekday == glass_day else ["Rubbish", "Recycling"]
        elif all_streams:
            types = ["Rubbish", "Recycling", "Glass"]
        elif colour == "green":
            types = ["Rubbish"]
        elif colour == "grey":
            types = ["Recycling", "Glass"]
        elif colour == "bank_holiday":
            # Bank-holiday rows retain the alternating stream from the calendar.
            colour = "grey" if previous_colour == "green" else "green"
            types = ["Rubbish"] if colour == "green" else ["Recycling", "Glass"]
        else:
            raise SourceArgumentException(
                "uprn", "Could not identify a bin calendar row."
            )
        if colour in {"green", "grey"}:
            previous_colour = colour
        entries.extend(
            Collection(date=collection_date, t=bin_type, icon=ICON_MAP[bin_type])
            for bin_type in types
        )
    return entries


def _parse_garden_calendar(content):
    objects = _layout_objects(content)
    headers = _month_headers(objects)
    dates = set()
    for line, weekday, day_number in _date_lines(objects):
        collection_date = _date_for_line(line, weekday, day_number, headers)
        if collection_date:
            dates.add(collection_date)
    if not dates:
        raise SourceArgumentException(
            "uprn", "Could not parse the East Hampshire garden calendar."
        )
    return [
        Collection(date=collection_date, t="Garden Waste", icon=Icons.GARDEN)
        for collection_date in sorted(dates)
    ]


def _calendar_urls(html):
    soup = BeautifulSoup(html, "html.parser")
    panel = soup.find(
        "div", attrs={"aria-label": re.compile("waste and recycling", re.I)}
    )
    if panel is None:
        raise SourceArgumentNotFound(
            "uprn", "unknown", "No East Hampshire address was found."
        )
    urls = {}
    for heading in panel.find_all("h4"):
        link = heading.find_next("a", href=True)
        if not link:
            continue
        title = heading.get_text(" ", strip=True).casefold()
        if "garden" in title:
            urls["garden"] = urljoin(ADDRESS_URL, link["href"])
        elif "bin calendar" in title:
            urls["bins"] = urljoin(ADDRESS_URL, link["href"])
    if "bins" not in urls:
        raise SourceArgumentException(
            "uprn", "The council did not provide a bin calendar for this property."
        )
    return urls


class Source:
    def __init__(self, uprn: str | int):
        self._uprn = str(uprn)

    def fetch(self):
        session = requests.Session()
        session.headers.update(HEADERS)
        response = session.get(
            ADDRESS_URL,
            params={"action": "SetAddress", "UniqueId": self._uprn},
            timeout=30,
        )
        response.raise_for_status()
        urls = _calendar_urls(response.text)

        bin_response = session.get(urls["bins"], timeout=30)
        bin_response.raise_for_status()
        entries = _parse_bin_calendar(bin_response.content)

        if "garden" in urls:
            garden_response = session.get(urls["garden"], timeout=30)
            garden_response.raise_for_status()
            entries.extend(_parse_garden_calendar(garden_response.content))

        today = datetime.datetime.now(datetime.timezone.utc).date()
        entries = [entry for entry in entries if entry.date >= today]
        if not entries:
            raise SourceArgumentException(
                "uprn", "The council returned no upcoming collections."
            )
        return sorted(entries, key=lambda entry: entry.date)
