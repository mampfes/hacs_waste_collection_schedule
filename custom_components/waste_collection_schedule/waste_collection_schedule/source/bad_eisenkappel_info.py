import re
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import district
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import RowTransformer

# The municipality's collection page holds one table per month; every row is
# date ("Mi . 14.10.26"), collection ("Abholung von Restmüll, 14-tägige Tour")
# and the villages it covers ("Leppen, Koprein", or "Gesamtes Gemeindegebiet"
# for the whole municipality). A row applies to the chosen region when it
# names it or covers the whole municipality; a region that no row names is
# rejected with the villages the page lists.

API_URL = "https://www.bad-eisenkappel.info/gemeinde/onlineservice/abfuhrtermine.html"

WHOLE_MUNICIPALITY = "Gesamtes Gemeindegebiet"

_DATE = re.compile(r"\d{2}\.\d{2}\.\d{2}")


def _key(name: str) -> str:
    return name.lower().replace(" ", "")


def _label(text: str) -> str:
    return (
        text.strip()
        .removeprefix("Abholung")
        .removeprefix("Entleerung")
        .strip()
        .removeprefix("von")
        .strip()
        .removeprefix("der")
        .strip()
    )


def _rows(trs, source):
    wanted = _key(source.params["region"]) if source else ""
    regions: set[str] = set()
    rows = []
    for tr in trs:
        tds = tr.select("td")
        if len(tds) < 3:
            continue
        date = _DATE.search(tds[0].get_text(strip=True))
        if date is None:
            continue
        covered = tds[2].get_text(strip=True)
        regions.update(region.strip() for region in covered.split(","))
        if covered.lower() == WHOLE_MUNICIPALITY.lower() or wanted in _key(
            covered
        ).split(","):
            rows.append((date.group(), _label(tds[1].get_text(strip=True))))
    regions.discard(WHOLE_MUNICIPALITY)
    if wanted not in {_key(region) for region in regions}:
        raise SourceArgumentNotFoundWithSuggestions(
            "region", source.params["region"] if source else None, sorted(regions)
        )
    return rows


@final
class Source(BaseSource):
    TITLE = "Eisenkappel-Vellach"
    DESCRIPTION = "Source for Eisenkappel-Vellach."
    URL = "https://www.bad-eisenkappel.info/"
    COUNTRY = "at"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.GLASS,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {"Leppen": {"region": "Leppen"}}

    PARAMS = (district("region"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "The region should match one of the regions listed in the third column "
            "of the table at "
            "<https://www.bad-eisenkappel.info/gemeinde/onlineservice/abfuhrtermine.html>"
        ),
        "de": (
            "Der Ortsteil muss einem der Ortsteile in der dritten Spalte der "
            "Tabelle auf "
            "<https://www.bad-eisenkappel.info/gemeinde/onlineservice/abfuhrtermine.html> "
            "entsprechen."
        ),
    }

    retrieve = HttpGetRetriever(url=API_URL)
    parse = parsers.HtmlParser("table tr")
    preprocess = staticmethod(_rows)
    transform = RowTransformer(
        parse_date=date_parsers.for_format("%d.%m.%y"),
        # The 14-day and the 4-week residual-waste tours can fall on one day;
        # keep the label to tell them apart.
        carry_raw_label=True,
        type_value_map={
            "Restmüll, 14-tägige Tour": wt.GENERAL_WASTE,
            "Restmüll, 4-wöchige Tour": wt.GENERAL_WASTE,
            "Biomüll": wt.ORGANIC,
            "Altpapiertonne": wt.PAPER,
            "Glasbehälter": wt.GLASS,
            "Gelbe Säcke - Plastik und Metall": wt.RECYCLABLES,
        },
    )
