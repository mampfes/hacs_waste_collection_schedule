import datetime
import re
from collections.abc import Iterable
from typing import ClassVar, final

from waste_collection_schedule import config_params, recurrence
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.parsers import PdfWordLayout, PdfWordLayoutParser
from waste_collection_schedule.preprocessors import RecurrenceExpander, Schedule
from waste_collection_schedule.retrievers import PdfLinkRetriever
from waste_collection_schedule.transformers import ICSTransformer

_INDEX_URL = "https://www.gelsiambiente.it/servizi/calendario-dei-servizi/"
_PDF_PATTERN = r"Giussano_Calendario-servizi[^/\"]*\.pdf$"

_ZONES = ("A", "B", "C")

# The calendar is a weekly rule: one block of rounds per zone, each round
# printed under the weekday it is collected on. How many weeks to project.
_WEEKS = 52

# A zone's block is four lines, about 10pt apart, around its label.
_BLOCK_HEIGHT = 25

# "• 1° gennaio • 1° maggio ..." in the "FESTIVITÀ" notice.
_HOLIDAY = re.compile(r"(\d{1,2})\s*°?\s+([^\W\d_]+)")


def _holidays(lines: Iterable[str], today: datetime.date) -> list[datetime.date]:
    """The fixed days the PDF says nothing is collected, over the projected span."""
    days: list[tuple[int, int]] = []
    for line in lines:
        if "•" not in line:
            continue
        for day, name in _HOLIDAY.findall(line):
            month = recurrence.month(name)
            if month:
                days.append((month, int(day)))
    end = today + datetime.timedelta(weeks=_WEEKS + 1)
    return [
        datetime.date(year, month, day)
        for year in range(today.year, end.year + 1)
        for month, day in days
    ]


def _describe(
    document: PdfWordLayout, source: BaseSource | None = None
) -> Iterable[Schedule]:
    """The configured zone's rounds, each as a weekly schedule on its weekday."""
    zone = str(source.params["zone"]).strip().upper() if source else ""
    page = [line for line in document.lines if line.page == 0]
    headings = {
        day: word
        for word in document.words
        if word.page == 0
        and word.text.isupper()
        and (day := recurrence.weekday(word.text)) is not None
    }
    zone_y = {
        line.text[-1]: line.y for line in page if re.fullmatch(r"ZONA [A-Z]", line.text)
    }
    if not headings or zone not in zone_y:
        return
    heading_y = min(word.y for word in headings.values())
    today = datetime.date.today()
    exclude = _holidays((line.text for line in page), today)
    for line in page:
        # Rounds sit below the weekday headings; the zone label is not one.
        if line.y >= heading_y or line.text.startswith("ZONA "):
            continue
        # A round belongs to the zone whose label is nearest down the page and to
        # the weekday whose heading is nearest across.
        if min(zone_y, key=lambda name: abs(zone_y[name] - line.y)) != zone:
            continue
        # ... and within the block's height, which keeps out the legend and footer.
        if abs(zone_y[zone] - line.y) > _BLOCK_HEIGHT:
            continue
        day = min(headings, key=lambda number: abs(headings[number].x - line.x))
        yield Schedule(
            line.text,
            recurrence.next_weekday(day, on_or_after=today),
            count=_WEEKS,
            exclude=exclude,
        )


@final
class Source(BaseSource):
    TITLE = "Gelsia Ambiente (Giussano)"
    DESCRIPTION = "Source for Gelsia Ambiente waste collection schedule in Giussano."
    URL = "https://www.gelsiambiente.it"
    COUNTRY = "it"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.ORGANIC,
        wt.PAPER,
        wt.GLASS,
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.OTHER,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Zone A": {"zone": "A"},
        "Zone B": {"zone": "B"},
        "Zone C": {"zone": "C"},
    }

    PARAMS = (config_params.dropdown("zone", list(_ZONES), label="Zone"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Giussano is split into zones A, B and C by street. Find your street "
            "in the zone lists on page 2 and 3 of the municipal calendar "
            "(https://www.gelsiambiente.it/servizi/calendario-dei-servizi/) "
            "and select that zone."
        ),
        "it": (
            "Giussano è divisa in zone A, B e C in base alla via. Trova la tua via "
            "negli elenchi delle zone alle pagine 2 e 3 del calendario comunale "
            "(https://www.gelsiambiente.it/servizi/calendario-dei-servizi/) e "
            "seleziona quella zona."
        ),
    }

    retrieve = PdfLinkRetriever(
        index_url=_INDEX_URL, pattern=_PDF_PATTERN, select="first"
    )
    parse = PdfWordLayoutParser(min_words=100)
    preprocess = RecurrenceExpander(_describe)
    transform = ICSTransformer(
        type_value_map={
            "UMIDO": wt.ORGANIC,
            "CARTA/CARTONE": wt.PAPER,
            "VETRO": wt.GLASS,
            "S. BLURFID": wt.GENERAL_WASTE,
            "S. GIALLO": wt.RECYCLABLES,
            "S. ARANCIONE": wt.OTHER,
        }
    )
