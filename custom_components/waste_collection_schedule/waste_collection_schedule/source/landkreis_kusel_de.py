"""Landkreis Kusel (landkreis-kusel.de).

Demonstrates: a two-step "scrape a <select> for the location id, then GET the
ICS feed with it" shape, plus a year-boundary retry the legacy source already
had: if the primary host's earliest event isn't in the current year, the same
two steps are repeated against a year-suffixed alternate host and the results
are merged. No dedicated retriever expresses that merge/retry, so ``retrieve``
is a source-defined override (returning a list of raw ICS texts) paired with a
custom ``parse`` that converts and concatenates them -- the same shape used by
geoport_nwm_de for its own multi-feed merge.
"""

from datetime import datetime, timedelta
from typing import ClassVar, final

from bs4 import BeautifulSoup
from bs4.element import NavigableString
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import municipality
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.service.ICS import ICS
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    BULKY_WASTE,
    GENERAL_WASTE,
    GLASS,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_API_URL = "https://abfallwirtschaft.landkreis-kusel.de"


def _make_comparable(ortsgemeinde: str) -> str:
    return (
        ortsgemeinde.lower()
        .replace("-", "")
        .replace(".", "")
        .replace("/", "")
        .replace(" ", "")
    )


def _pick_location(html: str, ortsgemeinde: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    select = soup.find("select", {"class": "form-select"})
    if not select or isinstance(select, NavigableString):
        raise ValueError("Invalid response from API")

    wanted = _make_comparable(ortsgemeinde)
    for option in select.find_all("option"):
        if _make_comparable(option.text) == wanted:
            value = option.get("value")
            if value:
                return str(value)

    raise SourceArgumentNotFoundWithSuggestions(
        "ortsgemeinde",
        ortsgemeinde,
        [option.text for option in select.find_all("option")],
    )


def _fetch_ics_text(session, api_url: str, ortsgemeinde: str) -> str:
    lookup = session.get(api_url)
    lookup.raise_for_status()
    location = _pick_location(lookup.text, ortsgemeinde)

    now = datetime.now()
    schedule = session.get(
        f"{api_url}/ical",
        params={
            "location": location,
            "startDate": now.strftime("%Y-%m-%d"),
            "endDate": (now + timedelta(days=365)).strftime("%Y-%m-%d"),
        },
    )
    schedule.raise_for_status()
    return schedule.text


@final
class Source(BaseSource):
    TITLE = "Landkreis Kusel"
    DESCRIPTION = "Source for Landkreis Kusel."
    URL = "https://www.landkreis-kusel.de/"
    COUNTRY = "de"

    TEST_CASES: ClassVar[dict] = {
        "Adenbach": {"ortsgemeinde": "Adenbach"},
        "St. Julian - Eschenau": {"ortsgemeinde": "St. Julian - Eschenau"},
        "rutsweiler glan (wrong spelling)": {"ortsgemeinde": "rutsweiler glan"},
        "Kusel": {"ortsgemeinde": "Kusel"},
    }

    PARAMS = (municipality("ortsgemeinde"),)

    RAISE_ON_EMPTY = True

    def retrieve(self, source):
        ortsgemeinde = source.params["ortsgemeinde"]
        texts = [_fetch_ics_text(source.session, _API_URL, ortsgemeinde)]

        # Legacy year-boundary quirk: if the primary feed's earliest event
        # isn't in the current year, the site also publishes a year-suffixed
        # alternate host (e.g. "abfall26" for 2026) that is merged in.
        try:
            first_date = min(d for d, _ in ICS().convert(texts[0]))
            if first_date.year != datetime.now().year:
                alt_url = _API_URL.replace(
                    "abfallwirtschaft", f"abfall{str(datetime.now().year)[2:]}"
                )
                texts.append(_fetch_ics_text(source.session, alt_url, ortsgemeinde))
        except Exception:
            pass

        return texts

    def parse(self, response, source=None):
        entries = []
        for text in response:
            entries.extend(ICS().convert(text))
        return entries

    transform = ICSTransformer(
        type_value_map={
            "Restmüll": GENERAL_WASTE,
            "LVP-Abfälle": RECYCLABLES,
            "Glas": GLASS,
            "Bioabfall": ORGANIC,
            "Papier": PAPER,
            "Umweltmobil": BULKY_WASTE,
        },
        # The feed's SUMMARY is e.g. "LVP-Abfälle (Gelbe Säcke) ()"; only the
        # first word identifies the waste type (matches the legacy source's
        # own ``d[1].split(" ")[0]``).
        clean=lambda label: label.split(" ")[0],
    )

    def __init__(self, ortsgemeinde: str):
        super().__init__(ortsgemeinde=ortsgemeinde)
