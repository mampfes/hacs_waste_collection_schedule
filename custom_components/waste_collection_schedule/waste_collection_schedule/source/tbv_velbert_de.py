from typing import ClassVar, final

from bs4 import BeautifulSoup
from waste_collection_schedule import parsers, preprocessors, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street
from waste_collection_schedule.transformers import RowTransformer

API_BASE = "https://www.tbv-velbert.de"
SEARCH_FIELD = "tx_tbvabfall_strassensuche[suchbegriff]"

_TYPE_MAP = {
    "Restmüll-Gefäß": wt.GENERAL_WASTE,
    "Gelbe Tonne": wt.RECYCLABLES,
    "Bio-Tonne": wt.ORGANIC,
    "Papier-Tonne": wt.PAPER,
}


def _search_form(response, *keys, **_) -> tuple[str, dict[str, str]]:
    """The street-search form: its action URL and its hidden fields.

    TYPO3 signs the form (``cHash`` in the action, ``__trustedProperties`` and
    ``__referrer`` hashes in the hidden fields), so it is replayed as served.
    """
    form = BeautifulSoup(response.text, "html.parser").select_one(
        "div.tx-tbvabfall form"
    )
    action = form.get("action") if form is not None else None
    if form is None or not isinstance(action, str):
        raise ValueError("Could not find the street search form.")
    fields = {
        str(tag["name"]): str(tag["value"])
        for tag in form.select("input")
        if tag.get("name") and tag.get("value")
    }
    return (API_BASE + action if action.startswith("/") else action), fields


@final
class Source(BaseSource):
    TITLE = "TBV Velbert"
    DESCRIPTION = "Source script for tbv-velbert.de, germany"
    URL = "https://www.tbv-velbert.de"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.ORGANIC,
        wt.PAPER,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Lindenkamp": {"street": "Am Lindenkamp 33"},
        "Rathaus": {"street": "Thomasstraße 1"},
    }

    PARAMS = (street(),)

    HOWTO: ClassVar[dict] = {
        "de": (
            "Straße und Hausnummer so eingeben, wie sie im Abfallkalender auf "
            "tbv-velbert.de/abfall gesucht werden, z. B. 'Am Lindenkamp 33'."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(retrievers.Lookup(f"{API_BASE}/abfall", pick=_search_form),),
        url=lambda form, **_: form[0],
        method="POST",
        data=lambda form, street, **_: {**form[1], SEARCH_FIELD: street},
        raise_for_status=True,
    )

    # Only the result column: the page below it carries a holiday-shift
    # notice whose dates are not collections.
    parse = parsers.HtmlParser("div.right-side")

    preprocess = preprocessors.Compose(
        lambda blocks, source: " ".join(block.get_text(" ") for block in blocks),
        preprocessors.TextGroupedDates(
            keys=_TYPE_MAP,
            date_pattern=r"(?P<day>\d{2})\.(?P<month>\d{2})\.(?P<year>\d{4})",
        ),
    )

    transform = RowTransformer(type_value_map=_TYPE_MAP)
