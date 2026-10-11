"""Communauté de Communes de la Plaine de l'Ain (CCPA), France.

The CCPA publishes one yearly collection calendar PDF per commune group
("15_MEXIMIEUX_OUEST_2026_CALENDRIER_A4_CORR-1.pdf"), all linked from one page
whose link text names the commune ("Meximieux OUEST", "Ambronay"). The file
names carry correction suffixes ("_CORR-1", "-2-1") that change whenever a
calendar is re-issued, so the link is found by its text rather than its URL:
``retrievers.yearly_links`` keeps the commune's calendars from this year on,
suggesting the listed communes when the name does not match.

Every calendar is the same two-page day grid ("6 MAR ORDURES", "8 JEU TRI"),
read by ``PdfTextCalendar.DayGridCalendarParser``. pypdf emits the second
page's month columns out of order (July, September, December, August,
October, November), so each month block is dated by the weekdays it prints,
which also fails loudly if a calendar does not fit the year in its file name.
"""

from typing import ClassVar, final

from waste_collection_schedule import parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import municipality
from waste_collection_schedule.service.PdfTextCalendar import (
    FRENCH_WEEKDAY_ORDER,
    DayGridCalendarParser,
    LabelRule,
)
from waste_collection_schedule.transformers import ICSTransformer

_INDEX_URL = (
    "https://cc-plainedelain.fr/les-services/gerer-vos-dechets/"
    "les-calendriers-de-collecte/"
)

# "/15_MEXIMIEUX_OUEST_2026_CALENDRIER_A4_CORR-1.pdf",
# "/16_AMBRONAY_SRB_CALENDRIER_A4_2026-1.pdf": the year sits somewhere in the
# file name (never in the /uploads/YYYY/MM/ folder, which is the upload date).
_PDF_PATTERN = r"/\d+_(?=[^/]*CALENDRIER)[^/]*?(20\d\d)[^/]*\.pdf$"
# The suffix after the year is optional ("..._CALENDRIER_2027.pdf"): an unmatched
# year would fall back to the current one and fail the weekday check.
_YEAR_PATTERN = r"_(20\d\d)(?:[_-][^/]*)?\.pdf$"

_GENERAL = "Ordures ménagères"
_RECYCLING = "Tri sélectif"


@final
class Source(BaseSource):
    TITLE = "Communauté de Communes de la Plaine de l'Ain"
    DESCRIPTION = (
        "Source for the collection calendars of the Communauté de Communes de la "
        "Plaine de l'Ain (CCPA), France."
    )
    URL = "https://cc-plainedelain.fr"
    COUNTRY = "fr"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@bbr111"]
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "Meximieux Ouest": {"municipality": "Meximieux OUEST"},
        "Meximieux Sud et Est": {"municipality": "Meximieux SUD et EST"},
        "Perouges hors cite": {"municipality": "Perouges hors cite"},
    }

    PARAMS = (municipality("municipality"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your commune exactly as it is listed on "
            "https://cc-plainedelain.fr/les-services/gerer-vos-dechets/"
            "les-calendriers-de-collecte/ (for example 'Ambronay', "
            "'Meximieux OUEST' or 'Meximieux SUD et EST'). Case, accents and "
            "hyphens are ignored."
        ),
        "fr": (
            "Saisissez votre commune telle qu'elle figure sur "
            "https://cc-plainedelain.fr/les-services/gerer-vos-dechets/"
            "les-calendriers-de-collecte/ (par exemple « Ambronay », "
            "« Meximieux OUEST » ou « Meximieux SUD et EST »). La casse, les "
            "accents et les traits d'union sont ignorés."
        ),
    }

    retrieve = retrievers.FanOutRetriever(
        prepare=retrievers.Lookup(
            _INDEX_URL,
            pick=retrievers.yearly_links(_PDF_PATTERN, argument="municipality"),
        ),
        targets=lambda source, urls: urls,
        fetch=retrievers.Request(lambda url, urls, **_: url),
    )
    parse = parsers.EachResponse(
        DayGridCalendarParser(
            labels=[
                LabelRule(_GENERAL, r"\bORDURES\b"),
                LabelRule(_RECYCLING, r"\bTRI\b"),
            ],
            line_pattern=r"^(\d{1,2})\s+([A-Z]{3})\b\s*(.*)",
            year_pattern=_YEAR_PATTERN,
            weekday_order=FRENCH_WEEKDAY_ORDER,
        )
    )
    transform = ICSTransformer()
