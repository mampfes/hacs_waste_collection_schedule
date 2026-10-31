"""Read Imielno's independently grouped village/date tables."""

import datetime
import re

from waste_collection_schedule import lookups
from waste_collection_schedule.parsers import PdfRow

_MONTHS = ("I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII")


class VillageDateRows:
    """Keep wrapped village names and the actual printed Roman-month dates."""

    def __call__(self, records: list[PdfRow], source):
        text = " ".join(w.text for row in records for w in row.words)
        year_match = re.search(r"GRUDZIEŃ\s+(20\d{2})", text)
        if year_match is None or int(year_match[1]) != datetime.date.today().year:
            raise ValueError("Imielno calendar does not cover the current year")
        year = int(year_match[1])
        village = lookups.normalize_loose(source.params["area"])
        results = set()
        label = None
        boundary = None
        names: list[str] = []
        dates: list[datetime.date] = []
        matched = set()

        def finish():
            if not dates:
                return
            if {d.month for d in dates} != set(range(1, 13)) or len(dates) != 12:
                raise ValueError(
                    "Expected twelve explicitly dated months per village row"
                )
            villages = [lookups.normalize_loose(v) for v in " ".join(names).split(",")]
            if village in villages:
                matched.add(label)
                results.update((date, label) for date in dates)

        for row in sorted(records, key=lambda r: (r.page, -r.y)):
            line = " ".join(w.text for w in row.words)
            if "MIEJCOWOŚCI" in line:
                finish()
                names, dates = [], []
                heading = next(w for w in row.words if "MIEJCOWOŚCI" in w.text)
                fraction = next((w for w in row.words if "ODPADY" in w.text), None)
                if fraction is None:
                    raise ValueError("Village table has no fraction heading")
                boundary = (heading.x1 + fraction.x0) / 2
                label = "Zmieszane i bio" if "BIOODPADY" in line else "Segregowane"
                continue
            if "TERMIN ODBIORU ODPADÓW WIELKOGABARYTOWYCH" in line:
                finish()
                names, dates = [], []
                bulky = re.findall(r"\b(\d{2})\.(\d{2})\.(20\d{2})\b", line)
                if not bulky:
                    raise ValueError("Bulky collection notice has no dates")
                for day, month, date_year in bulky:
                    if int(date_year) != year:
                        raise ValueError("Bulky dates disagree with calendar year")
                    results.add(
                        (datetime.date(year, int(month), int(day)), "Wielkogabarytowe")
                    )
                label = None
            if label is None or boundary is None:
                continue
            left = [w.text for w in row.words if w.x0 < boundary]
            right = " ".join(w.text for w in row.words if w.x0 >= boundary)
            printed = re.findall(r"\b(\d{1,2})\.([IVX]+)(?![IVX])", right)
            if printed:
                finish()
                names = left
                dates = [
                    datetime.date(year, _MONTHS.index(month) + 1, int(day))
                    for day, month in printed
                ]
            elif dates:
                names.extend(left)
        finish()
        if matched != {"Zmieszane i bio", "Segregowane"}:
            raise ValueError("Village must match both independent household tables")
        return sorted(results)
