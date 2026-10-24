import re
from typing import Any, ClassVar, final
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from waste_collection_schedule import date_parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.transformers import JsonTransformer

_PAGE = "https://www.chichester.gov.uk/checkyourbinday"
_FORM_ID = re.compile(r"WASTECOLLECTIONCALENDARV\d+_FORM")
_NOT_FOUND = "unable to find your waste collection dates"

_TYPE_MAP = {
    "Food Waste": wt.FOOD_WASTE,
    "General Waste": wt.GENERAL_WASTE,
    "Recycling": wt.RECYCLABLES,
    "Garden Recycling": wt.GARDEN_WASTE,
}


def _form(response: Any, *_, uprn: str = "", **__) -> dict[str, str]:
    """The bin-day form's action URL and field prefix."""
    soup = BeautifulSoup(response.text, "html.parser")
    form = soup.find("form", id=_FORM_ID)
    if form is None or not form.get("action"):
        raise SourceArgumentNotFound(
            "uprn",
            uprn,
            "The bin day form was not on the council page.",
        )
    return {
        "action": urljoin(_PAGE, str(form["action"])),
        "id": str(form["id"]).split("_", 1)[0],
    }


def _rows(response: Any, source: BaseSource | None = None) -> list[dict[str, str]]:
    """``{date, type}`` rows from the submitted form.

    Each bin is a ``div.binType-*`` followed by a sibling div whose text is
    ``Friday 27 February 2026``. The council titles the bin in sentence case;
    ``str.title`` matches the labels the legacy source published.
    """
    soup = BeautifulSoup(response.text, "html.parser")
    rows: list[dict[str, str]] = []
    for bin_div in soup.find_all("div", class_=re.compile(r"binType-")):
        sibling = bin_div.find_next_sibling("div")
        if sibling is None:
            continue
        rows.append(
            {
                "date": sibling.get_text(strip=True),
                "type": bin_div.get_text(strip=True).title(),
            }
        )
    if rows:
        return rows
    text = soup.get_text(" ", strip=True)
    uprn_value = "" if source is None else source.params.get("uprn", "")
    if _NOT_FOUND in text.lower():
        raise SourceArgumentNotFound(
            "uprn",
            uprn_value,
            "Sorry we are unable to find your waste collection dates. "
            "Your property may be new, a flat or commercial.",
        )
    raise SourceArgumentNotFound(
        "uprn",
        uprn_value,
        "The council page did not list any collection dates.",
    )


@final
class Source(BaseSource):
    TITLE = "Chichester District Council"
    DESCRIPTION = "Source for chichester.gov.uk services for Chichester"
    URL = "https://www.chichester.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    # UPRN 100062612654 is answered with "unable to find your waste collection
    # dates" (a flat or commercial property). The two cases below return a calendar.
    WASTE_TYPES: ClassVar[list] = [
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"uprn": "010002476348"},
        "Test_003": {"uprn": "100061745708"},
    }

    PARAMS = (uprn(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Open https://www.chichester.gov.uk/checkyourbinday, search your "
            "address, and copy the UPRN."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(retrievers.Lookup(_PAGE, pick=_form),),
        url=lambda form, **_: form["action"],
        method="POST",
        data=lambda form, uprn, **_: {
            f"{form['id']}_FORMACTION_NEXT": "Submit",
            f"{form['id']}_CALENDAR_UPRN": str(uprn).strip(),
        },
        raise_for_status=True,
    )
    parse = staticmethod(_rows)
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        parse_date=date_parsers.for_format("%A %d %B %Y"),
        type_value_map=_TYPE_MAP,
    )
