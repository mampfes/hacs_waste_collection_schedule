import html
import re
from datetime import date
from typing import ClassVar, final
from urllib.parse import urljoin

from waste_collection_schedule import field_terms, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.transformers import RowTransformer

BASE_URL = "https://www.geilenkirchen.de"
CALENDAR_URL = (
    f"{BASE_URL}/rathaus/online-dienstleistungen-und-andere-angebote/abfallkalender/"
)
MONTHS_DE = {
    "april": 4,
    "august": 8,
    "dezember": 12,
    "februar": 2,
    "januar": 1,
    "juli": 7,
    "juni": 6,
    "mai": 5,
    "märz": 3,
    "november": 11,
    "oktober": 10,
    "september": 9,
}
DATE_PATTERN = re.compile(r"(\d{1,2})\.\s*([A-Za-zÄÖÜäöü]+)\s*(\d{4})")
RESULT_LINK_PATTERN = re.compile(
    r'<h3><a href="([^"]*/abfallkalender/details/[^"]+)">\s*([^<]+?)\s*</a></h3>'
)


def _normalize(value):
    value = html.unescape(value).strip().lower()
    value = value.translate(str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"}))
    return re.sub(r"[^a-z0-9]", "", value)


def _results(response, *_, **kwargs):
    return [
        (html.unescape(name), urljoin(BASE_URL, href))
        for href, name in RESULT_LINK_PATTERN.findall(response.text)
    ]


def _variant(street):
    return street.replace("ß", "ss").replace("straße", "strasse")


def _detail_url(initial, variant, first_word, *, street):
    results = initial or variant or first_word or []
    for name, url in results:
        if _normalize(name) == _normalize(street):
            return url
    if len(results) == 1:
        return results[0][1]
    raise SourceArgumentNotFoundWithSuggestions(
        "street", street, sorted({name for name, _ in results})
    )


def _events(rows, source):
    result = []
    for row in rows:
        date_cell = row.select_one(".col.col-1")
        type_link = row.select_one("a[data-fancybox]")
        if date_cell is None or type_link is None:
            continue
        match = DATE_PATTERN.search(date_cell.get_text(strip=True))
        if match is None:
            continue
        day, month_name, year = match.groups()
        month = MONTHS_DE.get(month_name.lower())
        if month is not None:
            result.append(
                (date(int(year), month, int(day)), type_link.get_text(strip=True))
            )
    return result


def _clean(label):
    for prefix, canonical in (
        ("Restabfall", "Restabfall"),
        ("Bioabfall", "Bioabfall"),
        ("Leichtverpackungen", "Leichtverpackungen"),
        ("Altpapier", "Altpapier"),
        ("Grünschnittabfuhr", "Grünschnittabfuhr"),
    ):
        if prefix in label:
            return canonical
    return label


@final
class Source(BaseSource):
    TITLE = "Stadt Geilenkirchen"
    DESCRIPTION = (
        "Source for the waste collection calendar of the city of Geilenkirchen, North "
        "Rhine-Westphalia, Germany."
    )
    URL = "https://www.geilenkirchen.de"
    COUNTRY = "de"
    TEST_CASES: ClassVar[dict] = {
        "Aldenhovener Strasse": {"street": "Aldenhovener Strasse"},
        "Ahornweg": {"street": "Ahornweg"},
        "Aldenhovener Straße (spelling fallback)": {"street": "Aldenhovener Straße"},
    }
    SOURCE_CODEOWNERS: ClassVar[list[str]] = ["@bbr111"]
    HOWTO: ClassVar[dict[str, str]] = {
        "en": "Visit the collection calendar at "
        "https://www.geilenkirchen.de/rathaus/online-dienstleistungen-und-andere-angebote/abfallkalender/ "
        "and use the street search box there to find the exact spelling of your street "
        "(streets are spelled with 'strasse', not 'straße'). Use that exact name as the "
        "'street' argument. If the name you enter cannot be found, or matches more than "
        "one street, the resulting error message lists the closest matches.",
        "de": "Besuchen Sie den Abfallkalender unter "
        "https://www.geilenkirchen.de/rathaus/online-dienstleistungen-und-andere-angebote/abfallkalender/ "
        "und nutzen Sie dort die Straßensuche, um die genaue Schreibweise Ihrer Straße "
        "zu finden (Straßen werden mit 'strasse' statt 'straße' geschrieben). Verwenden "
        "Sie diesen genauen Namen als 'street'-Parameter. Wird der eingegebene Name "
        "nicht gefunden oder trifft auf mehrere Straßen zu, listet die Fehlermeldung "
        "die passendsten Treffer auf.",
    }
    RAISE_ON_EMPTY = True

    PARAMS = (text_field("street", term=field_terms.STREET),)
    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unknown street": {"street": "__unknown_street__"}
    }
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.RECYCLABLES,
        wt.PAPER,
        wt.GARDEN_WASTE,
    ]
    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                CALENDAR_URL,
                method="POST",
                data=lambda street: {"module1428[search]": street},
                pick=_results,
            ),
            retrievers.Lookup(
                CALENDAR_URL,
                method="POST",
                data=lambda *_, street: {"module1428[search]": _variant(street)},
                pick=_results,
                when=lambda initial, *, street: (
                    not initial and _variant(street) != street
                ),
            ),
            retrievers.Lookup(
                CALENDAR_URL,
                method="POST",
                data=lambda *_, street: {
                    "module1428[search]": street.strip().split()[0]
                },
                pick=_results,
                when=lambda initial, variant, *, street: (
                    not (initial or variant) and " " in street.strip()
                ),
            ),
        ),
        url=_detail_url,
        method="POST",
        data=lambda *_, **kwargs: {
            "module1432[types][]": "0",
            "module1432[timeframe]": "3",
        },
        raise_for_status=True,
    )
    parse = parsers.HtmlParser(".tablerow")
    preprocess = staticmethod(_events)
    transform = RowTransformer(
        clean=_clean,
        type_value_map={
            "Restabfall": wt.GENERAL_WASTE,
            "Bioabfall": wt.ORGANIC,
            "Leichtverpackungen": wt.RECYCLABLES,
            "Altpapier": wt.PAPER,
            "Grünschnittabfuhr": wt.GARDEN_WASTE,
        },
        carry_raw_label=True,
    )
