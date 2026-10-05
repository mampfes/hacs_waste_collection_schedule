import datetime
from typing import ClassVar, final

from bs4 import BeautifulSoup
from waste_collection_schedule import parsers, preprocessors, recurrence, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import municipality, waste_types
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.regions import region
from waste_collection_schedule.transformers import ICSTransformer

BASE_URL = "https://www.ezv.li"
CALENDAR_URL = f"{BASE_URL}/abfallentsorgung/abfallkalender"

MUNICIPALITIES = [
    "balzers",
    "triesen",
    "triesenberg",
    "vaduz",
    "schaan",
    "planken",
    "gamprin-bendern",
    "ruggell",
    "mauren-schaanwald",
    "eschen-nendeln",
    "schellenberg",
]

# The site's own category names, as the user selects them in `waste_type`.
SELECTABLE_TYPES = {
    "kehricht": "Kehricht",
    "gruenabfuhr": "Grünabfuhr",
}


def _municipality(value: str) -> str:
    return str(value).lower().strip()


def _selected_labels(waste_type: str | list[str] | None) -> set[str]:
    """The site labels a ``waste_type`` argument (a comma list, "all") selects."""
    if isinstance(waste_type, (list, tuple)):
        waste_type = ",".join(str(item) for item in waste_type)
    accepted = [*SELECTABLE_TYPES, "all", "both"]
    if waste_type is None or not str(waste_type).strip():
        return {SELECTABLE_TYPES["kehricht"]}
    selected: set[str] = set()
    for token in str(waste_type).lower().replace(";", ",").split(","):
        token = token.strip()
        if not token:
            continue
        if token in ("all", "both"):
            selected.update(SELECTABLE_TYPES.values())
        elif token in SELECTABLE_TYPES:
            selected.add(SELECTABLE_TYPES[token])
        else:
            raise SourceArgumentNotFoundWithSuggestions("waste_type", token, accepted)
    if not selected:
        raise SourceArgumentNotFoundWithSuggestions("waste_type", waste_type, accepted)
    return selected


def _check_arguments(municipality: str, waste_type=None, **_) -> None:
    """Reject a bad argument before any request is made (always resolves to None)."""
    if _municipality(municipality) not in MUNICIPALITIES:
        raise SourceArgumentNotFoundWithSuggestions(
            "municipality", _municipality(municipality), MUNICIPALITIES
        )
    _selected_labels(waste_type)


def _month_urls(response, *_keys, **_params) -> list[str]:
    """The calendar page's month select lists one page per month."""
    soup = BeautifulSoup(response.text, "html.parser")
    urls = []
    for option in soup.select("select#pica-filter-month option"):
        value = str(option.get("value", "")).split("#")[0]
        if value:
            urls.append(f"{BASE_URL}{value}")
    return urls


def _month_rows(response, source=None) -> list[tuple[datetime.date, str]]:
    """``(date, label)`` rows of one month page."""
    soup = BeautifulSoup(response.text, "html.parser")
    # The year is only given in the caption of the selected month option.
    selected = soup.select_one("select#pica-filter-month option[selected]")
    if selected is None:
        return []
    caption = str(selected.get("data-caption", "")).split()
    try:
        year = int(caption[-1])
        month = recurrence.month(caption[0])
    except (ValueError, IndexError):
        return []
    if month is None:
        return []

    rows = []
    for day_element in soup.select("div.pica-day"):
        day_text = day_element.select_one(".pica-date-header-day")
        if day_text is None:
            continue
        try:
            date = datetime.date(year, month, int(day_text.get_text(strip=True)))
        except ValueError:
            continue
        for name in day_element.select(".pica-category-name"):
            rows.append((date, name.get_text(strip=True)))
    return rows


def _keep_selected(row, source) -> bool:
    return row[1] in _selected_labels(source.params.get("waste_type"))


@final
class Source(BaseSource):
    TITLE = "Entsorgungszweckverband der Gemeinden Liechtensteins (EZV)"
    DESCRIPTION = "Source for the waste collection calendar of the EZV, Liechtenstein."
    URL = "https://www.ezv.li/abfallentsorgung/abfallkalender/"
    COUNTRY = "li"
    RAISE_ON_EMPTY = True

    REGIONS = tuple(
        region(m.replace("-", " ").title(), municipality=m) for m in MUNICIPALITIES
    )

    TEST_CASES: ClassVar[dict] = {
        "Balzers Kehricht": {"municipality": "balzers", "waste_type": "kehricht"},
        "Vaduz Grünabfuhr": {"municipality": "vaduz", "waste_type": "gruenabfuhr"},
        "Schaan Kehricht": {"municipality": "schaan", "waste_type": "kehricht"},
        "Balzers Both": {"municipality": "balzers", "waste_type": "all"},
    }

    PARAMS = (municipality("municipality"), waste_types("waste_type"))

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your municipality in lower case (balzers, triesen, triesenberg, "
            "vaduz, schaan, planken, gamprin-bendern, ruggell, mauren-schaanwald, "
            "eschen-nendeln or schellenberg). The waste type is optional: "
            "'kehricht' (default), 'gruenabfuhr', 'all' or a comma-separated list. "
            "See https://www.ezv.li/abfallentsorgung/abfallkalender/ for the schedule."
        ),
        "de": (
            "Geben Sie Ihre Gemeinde in Kleinbuchstaben ein (balzers, triesen, "
            "triesenberg, vaduz, schaan, planken, gamprin-bendern, ruggell, "
            "mauren-schaanwald, eschen-nendeln oder schellenberg). Der Abfalltyp "
            "ist optional: 'kehricht' (Standard), 'gruenabfuhr', 'all' oder eine "
            "komma-separierte Liste. Den Kalender finden Sie unter "
            "https://www.ezv.li/abfallentsorgung/abfallkalender/."
        ),
    }

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.GARDEN_WASTE]

    retrieve = retrievers.FanOutRetriever(
        prepare=retrievers.Lookup(
            lambda municipality, **_: f"{CALENDAR_URL}/{_municipality(municipality)}",
            given=_check_arguments,
            pick=_month_urls,
        ),
        targets=lambda source, urls: urls,
    )
    parse = parsers.EachResponse(_month_rows)
    preprocess = preprocessors.RowFilter(_keep_selected)
    transform = ICSTransformer(
        type_value_map={
            "Kehricht": wt.GENERAL_WASTE,
            "Grünabfuhr": wt.GARDEN_WASTE,
        }
    )
