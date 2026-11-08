"""Makarski komunalac d.o.o. (Makarska, Croatia).

The provider publishes one ICS file per collection schedule on its calendar
page and renames the files over time, so the current link is discovered on
the page rather than hardcoded. Each link is labelled by the schedule name
found in its file name, and the user's ``schedule`` selects the file.
"""

from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import dropdown
from waste_collection_schedule.service.ICS import IcsFeedsParser, IcsIndexRetriever
from waste_collection_schedule.transformers import ICSTransformer

_PAGE_URL = "https://makarski-komunalac.hr/info/kalendar_odvoza.html"

# schedule name -> keyword in the ICS file name linked on the calendar page
_SCHEDULES = {
    "Ponedjeljak/Četvrtak": "ponedjeljak",
    "Utorak/Subota": "utorak",
}

_TYPE_VALUE_MAP = {
    "miješani komunalni otpad (mko)": wt.GENERAL_WASTE,
    "plastika": wt.PLASTIC,
    "papir": wt.PAPER,
}


def _schedule(anchor) -> str | None:
    """The collection schedule a download link serves, read off its file name."""
    href = anchor["href"].lower()
    return next((name for name, key in _SCHEDULES.items() if key in href), None)


@final
class Source(BaseSource):
    TITLE = "Makarski komunalac"
    DESCRIPTION = (
        "Source for Makarski komunalac d.o.o., Makarska, Croatia waste collection."
    )
    URL = "https://makarski-komunalac.hr"
    COUNTRY = "hr"
    SOURCE_CODEOWNERS: ClassVar[list[str]] = ["@wagnst"]

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.PLASTIC, wt.PAPER]

    TEST_CASES: ClassVar[dict] = {
        "Ponedjeljak/Četvrtak": {"schedule": "Ponedjeljak/Četvrtak"},
        "Utorak/Subota": {"schedule": "Utorak/Subota"},
    }

    HOWTO: ClassVar[dict[str, str]] = {
        "en": "Enter your street (without house number) in the search box on https://makarski-komunalac.hr/info/kalendar_odvoza.html to find out whether your address is collected on the Ponedjeljak/Četvrtak (Monday/Thursday) or the Utorak/Subota (Tuesday/Saturday) schedule.",
        "de": "Geben Sie Ihre Straße (ohne Hausnummer) in das Suchfeld auf https://makarski-komunalac.hr/info/kalendar_odvoza.html ein, um herauszufinden, ob Ihre Adresse nach dem Plan Ponedjeljak/Četvrtak (Montag/Donnerstag) oder Utorak/Subota (Dienstag/Samstag) abgeholt wird.",
    }

    PARAMS = (dropdown("schedule", list(_SCHEDULES), "Collection schedule"),)

    retrieve = IcsIndexRetriever(
        index_url=_PAGE_URL,
        label=_schedule,
        argument="schedule",
    )

    # summaries read "Odvoz: Plastika"; keep only the waste type
    parse = IcsFeedsParser(parsers.IcsParser(regex=r"Odvoz:\s*(.*)"))

    transform = ICSTransformer(type_value_map=_TYPE_VALUE_MAP)
