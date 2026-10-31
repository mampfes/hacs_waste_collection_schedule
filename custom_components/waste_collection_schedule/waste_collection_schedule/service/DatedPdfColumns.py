"""Read full collection dates in labelled PDF columns, including wrapped rows."""

import datetime
import re
from collections.abc import Iterable

from waste_collection_schedule.parsers import PdfRow


class DatedColumns:
    """Identify columns by their headings and read every printed DD.MM.YYYY.

    Unlike a month-row day-list table, each cell carries its complete date.
    A month's entries may occupy several lines with no repeated month label.
    This reader retains those continuation lines and validates the date year.
    """

    def __init__(self, labels: Iterable[str]):
        self.labels = tuple(labels)

    def __call__(self, records: list[PdfRow], source=None):
        headings = {}
        results = set()
        current_year = datetime.date.today().year
        for page in sorted({r.page for r in records}):
            for row in sorted(
                (r for r in records if r.page == page), key=lambda r: -r.y
            ):
                for word in row.words:
                    for label in self.labels:
                        match = re.search(rf"\b{re.escape(label)}\b", word.text, re.I)
                        if match:
                            headings[label] = word.x0 + (word.x1 - word.x0) * (
                                match.start() + match.end()
                            ) / (2 * len(word.text))
                if len(headings) != len(self.labels):
                    continue
                for word in row.words:
                    for match in re.finditer(
                        r"\b(\d{2})\.(\d{2})\.(20\d{2})\b", word.text
                    ):
                        date = datetime.date(
                            int(match[3]), int(match[2]), int(match[1])
                        )
                        if date.year != current_year:
                            raise ValueError(
                                "Published calendar does not cover the current year"
                            )
                        x = word.x0 + (word.x1 - word.x0) * (
                            match.start() + match.end()
                        ) / (2 * len(word.text))
                        label = min(headings, key=lambda k: abs(x - headings[k]))
                        results.add((date, label))
        if len(headings) != len(self.labels) or {d.month for d, _ in results} != set(
            range(1, 13)
        ):
            raise ValueError(
                "Calendar must contain all labelled columns and twelve dated months"
            )
        return sorted(results)
