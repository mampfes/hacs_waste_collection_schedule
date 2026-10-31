"""Dated service rows inside a Drupal AJAX calendar insert command."""

import datetime
import json
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from waste_collection_schedule import date_parsers
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.parsers import Parser


def calendar_url(response, *_, uprn, **__):
    soup = BeautifulSoup(response.text, "html.parser")
    links = [
        urljoin(response.url, str(a["href"]))
        for a in soup.select("a[href]")
        if "/calendar-page?uprn=" in str(a["href"])
    ]
    if len(set(links)) != 1:
        raise SourceArgumentNotFound(
            "uprn",
            uprn,
            message_addition="The council did not publish a bin calendar for this property.",
        )
    return links[0]


def calendar_route(response, *_, **__):
    soup = BeautifulSoup(response.text, "html.parser")
    settings = soup.select_one('script[data-drupal-selector="drupal-settings-json"]')
    if settings is None:
        raise ValueError("Drupal calendar settings are missing")
    data = json.loads(settings.get_text())
    route = data.get("calendarRoute")
    if not route:
        raise ValueError("Drupal collection calendar route is missing")
    return urljoin(response.url, route)


class ServiceCalendarParser(Parser[list[tuple[datetime.date, str]]]):
    def __call__(self, response, source=None):
        data = response.json()
        inserts = [
            c["data"]
            for c in data
            if c.get("command") == "insert"
            and c.get("selector") == "#bin-collection-calendar-widget--content"
        ]
        if len(inserts) != 1:
            raise ValueError("Drupal response has no unique dated bin calendar")
        soup = BeautifulSoup(inserts[0], "html.parser")
        rows = set()
        tables = soup.select("table.calendar")
        if len(tables) < 1:
            raise ValueError("Dated council calendar tables are missing")
        for month in tables:
            heading = month.select_one("thead th")
            if heading is None:
                raise ValueError("Calendar month/year header is missing")
            header = heading.get_text(" ", strip=True)
            if not re.fullmatch(r"[A-Za-z]+ 20\d{2}", header):
                raise ValueError("Calendar header needs a printed month and year")
            published = date_parsers.auto("1 " + header)
            for service in month.select("table.services-row"):
                cell = service.select_one("td.td-date")
                if cell is None:
                    raise ValueError("Published collection day is missing")
                text = cell.get_text(" ", strip=True)
                parsed = date_parsers.auto(text + f" {published.year}")
                if (
                    parsed.month != published.month
                    or ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")[
                        parsed.weekday()
                    ]
                    != text.split(",")[0]
                ):
                    raise ValueError(
                        "Printed collection date disagrees with its calendar month/weekday"
                    )
                cells = service.select("td.service-row")
                if not cells:
                    raise ValueError("Collection date has no bin type")
                for item in cells:
                    classes = {str(c) for c in item.get_attribute_list("class")} - {
                        "service",
                        "service-row",
                    }
                    if len(classes) != 1 or not classes <= {
                        "waste",
                        "recycling",
                        "garden",
                        "food",
                    }:
                        raise ValueError(
                            f"Unknown collection service classes: {classes}"
                        )
                    rows.add((parsed, classes.pop()))
        return sorted(rows)
