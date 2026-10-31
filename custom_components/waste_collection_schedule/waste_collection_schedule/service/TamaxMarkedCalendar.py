"""Read TAMAX's coloured ISO-month grids and their dated bulky notices."""

import calendar
import datetime
import re

from waste_collection_schedule.service.MarkedPdfCalendar import MarkedPdfCalendarParser


class HouseholdCalendarParser(MarkedPdfCalendarParser):
    """Read actual coloured dates, with a separately dated bulky collection."""

    def __init__(self, *, separate_ash: bool):
        yellow, red, brown = (1, 1, 0), (1, 0, 0.4), (0.769, 0.349, 0.0667)
        colors = {
            "Zmieszane": [yellow, red],
            "Segregowane": [red],
            "Bio": [yellow] if separate_ash else [yellow, red],
            "Popiół": [brown] if separate_ash else [red],
        }
        super().__init__(
            months=list(calendar.month_name)[1:],
            weekdays=["Pn", "Wt", "Śr", "Cz", "Pt", "Sb", "N"],
            year_pattern=r"(20\d{2})-\d{2}",
            month_heading_pattern=r"(?P<year>20\d{2})-(?P<month>0[1-9]|1[0-2])",
            colors=colors,
        )

    def __call__(self, response, source=None):
        rows = super().__call__(response, source)
        if not rows or {r["date"].year for r in rows} != {datetime.date.today().year}:
            raise ValueError("Published household calendar does not cover this year")
        text = rows[0]["calendar_text"]
        notice = re.search(
            r"ODBIÓR ODPADÓW WIELKOGABARYTOWYCH(.*?)(?=PUNKT SELEKTYWNEGO|$)",
            text,
            re.IGNORECASE,
        )
        dates = re.findall(
            r"\b(\d{1,2})\.(\d{1,2})\.(20\d{2})", notice[1] if notice else ""
        )
        if len(dates) != 1:
            raise ValueError("Expected one explicitly dated bulky collection notice")
        day, month, year = map(int, dates[0])
        date = datetime.date(year, month, day)
        if date.year != datetime.date.today().year:
            raise ValueError("Bulky notice does not cover the current year")
        return [*rows, {"date": date, "type": "Wielkogabarytowe"}]
