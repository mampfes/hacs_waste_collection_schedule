"""EKO-REGION residential collection in the villages of Gmina Szczerców."""

from typing import ClassVar, final
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from waste_collection_schedule import config_params, lookups, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.service.EkoRegionCalendar import CalendarParser
from waste_collection_schedule.transformers import ICSTransformer

_URL = "https://eko-region.pl"
_INDEX = f"{_URL}/gmina/szczercow/"


def _calendar_link(response, *_, village):
    choices = {}
    for entry in BeautifulSoup(response.text, "html.parser").select(".city_single"):
        name = entry.find("strong")
        if name is None:
            continue
        for link in entry.select("a[href]"):
            if lookups.normalize_loose(link.get_text()) == lookups.normalize_loose(
                "Nieruchomości Zamieszkałe"
            ):
                choices[name.get_text(strip=True)] = urljoin(response.url, link["href"])
    matches = [
        url
        for name, url in choices.items()
        if lookups.normalize_loose(name) == lookups.normalize_loose(village)
    ]
    if len(matches) != 1:
        raise SourceArgumentNotFoundWithSuggestions("village", village, sorted(choices))
    return matches[0]


@final
class Source(BaseSource):
    TITLE = "EKO-REGION (Gmina Szczerców)"
    DESCRIPTION = (
        "Source for residential waste collection in Gmina Szczerców's villages."
    )
    URL = _URL
    COUNTRY = "pl"
    RAISE_ON_EMPTY = True
    TEST_CASES: ClassVar[dict] = {
        "Szubienice (request example)": {"village": "Szubienice"},
        "Bednarze": {"village": "Bednarze"},
        "Borowa": {"village": "Borowa"},
    }
    ERROR_TEST_CASES: ClassVar[dict] = {
        "Misspelled village": {"village": "Szubinice"},
    }
    PARAMS = (config_params.text_field("village", "Village"),)
    HOWTO: ClassVar[dict] = {
        "en": (
            "Find your village on https://eko-region.pl/gmina/szczercow/ and "
            "enter its name as printed there (for example Szubienice). The source "
            "automatically follows the Nieruchomości Zamieszkałe residential link. "
            "Business/non-residential schedules and Szczerców town's separate "
            "street calendars are not supported. Ash dates marked (popiół) in "
            "the Bio column are classified separately as Other, with the original "
            "Popiół label retained. Bulky-waste notices state multi-day windows "
            "covering different villages, so no exact bulky date is inferred."
        )
    }
    retrieve = retrievers.LookupChainRetriever(
        steps=(retrievers.Lookup(_INDEX, pick=_calendar_link),),
        url=lambda pdf_url, **_: pdf_url,
    )
    parse = CalendarParser()
    transform = ICSTransformer(
        type_value_map={
            "Metale i tworzywa sztuczne": wt.RECYCLABLES,
            "Papier": wt.PAPER,
            "Szkło": wt.GLASS,
            "Bio": wt.ORGANIC,
            "Popiół": wt.OTHER,
            "Zmieszane odpady komunalne": wt.GENERAL_WASTE,
        },
        carry_raw_label=True,
    )
