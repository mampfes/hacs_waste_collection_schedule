r"""AWB Oldenburg (oldenburg.de).

The calendar is the TYPO3 "collectioncalendar" extension's ICS export, and it
takes two lookups before anything can be downloaded: a GET scrapes the form's
street ``<select>`` and its hidden TYPO3 security tokens (``__csrf`` et al.),
then a POST resubmits those tokens with the resolved street index, the house
number and every waste-type flag, and answers with a per-request ``exportIcs``
link carrying its own cHash. The shared ``LookupChainRetriever`` runs both and
downloads whatever link the second one found.

The provider marks an estimated/uncertain collection date with a trailing
"``: !``" in the ICS summary; ``regex`` on ``IcsParser`` strips it, mirroring
the legacy source's ``ICS(regex=r"(.*)\:\s*\!")``. "Bioabfall" and
"Restabfall" already resolve against the standard German aliases;
"Altpapier", "Gelber Sack/Tonne" and "Sommerbiotonne" are Oldenburg-specific
phrasings mapped explicitly.
"""

from datetime import date
from typing import ClassVar, NamedTuple, final

from bs4 import BeautifulSoup, Tag
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, street
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import IcsParser
from waste_collection_schedule.retrievers import LookupChainRetriever
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GENERAL_WASTE,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_BASE_URL = "https://www.oldenburg.de"
_API_URL = (
    _BASE_URL
    + "/startseite/stadtraum/umwelt/abfall-entsorgung/awb-von-a-bis-z/abfuhrkalender.html"
)
_FORM_FIELD = "tx_collectioncalendar_collectioncalendar"


class _CalendarForm(NamedTuple):
    """The calendar form, ready to submit: where it posts and what it posts."""

    post_url: str
    data: dict


def _read_form(source: BaseSource, keys: tuple) -> _CalendarForm:
    """Resolve the street index and collect the form's TYPO3 security tokens."""
    street_value = source.params["street"]
    house_number_value = source.params["house_number"]

    response = source.session.get(_API_URL)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    # The calendar form is the second form on the page.
    form = soup.find_all("form")[1]

    street_select = form.find("select", {"name": f"{_FORM_FIELD}[street]"})
    if not isinstance(street_select, Tag):
        raise SourceArgumentNotFoundWithSuggestions("street", street_value, [])
    mapping = {
        opt.text.strip(): str(opt["value"])
        for opt in street_select.find_all("option")
        if opt.get("value")
    }
    if street_value not in mapping:
        raise SourceArgumentNotFoundWithSuggestions(
            "street", street_value, list(mapping.keys())
        )

    data = {
        inp["name"]: inp.get("value", "")
        for inp in form.find_all("input", {"name": True})
    }
    data[f"{_FORM_FIELD}[year]"] = str(date.today().year)
    for waste_type_id in range(1, 6):
        data[f"{_FORM_FIELD}[wasteTypes][{waste_type_id}]"] = str(waste_type_id)
    data[f"{_FORM_FIELD}[street]"] = mapping[street_value]
    data[f"{_FORM_FIELD}[houseNumber]"] = str(house_number_value)
    data[f"{_FORM_FIELD}[privacyPolicy-checkbox]"] = "1"

    action = str(form.get("action", ""))
    return _CalendarForm(_BASE_URL + action if action.startswith("/") else action, data)


def _find_export_link(source: BaseSource, keys: tuple) -> str:
    """Submit the form and read the per-request ``exportIcs`` download link."""
    form: _CalendarForm = keys[0]
    response = source.session.post(form.post_url, data=form.data)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    for anchor in soup.find_all("a", href=True):
        if "exportIcs" in anchor["href"]:
            href = str(anchor["href"])
            return _BASE_URL + href if href.startswith("/") else href

    raise SourceArgumentNotFoundWithSuggestions(
        "house_number", source.params["house_number"], []
    )


@final
class Source(BaseSource):
    TITLE = "AWB Oldenburg"
    DESCRIPTION = "Source for 'Abfallwirtschaftsbetrieb Stadt Oldenburg (Oldb)'."
    URL = _BASE_URL
    COUNTRY = "de"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [GENERAL_WASTE, ORGANIC, PAPER, RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "Polizeiinspektion Oldenburg": {"street": "Friedhofsweg", "house_number": 30}
    }

    PARAMS = (
        street(field="street"),
        house_number(field="house_number"),
    )

    retrieve = LookupChainRetriever(
        steps=(_read_form, _find_export_link),
        url=lambda form, export_link, **_: export_link,
        raise_for_status=True,
    )
    parse = IcsParser(regex=r"(.*)\:\s*\!")
    transform = ICSTransformer(
        type_value_map={
            "altpapier": PAPER,
            "gelber sack/tonne": RECYCLABLES,
            "sommerbiotonne": ORGANIC,
        }
    )

    def __init__(self, street: str, house_number: "str | int"):
        super().__init__(street=street, house_number=str(house_number))
