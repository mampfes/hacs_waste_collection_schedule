"""AWB Oldenburg (oldenburg.de).

Demonstrates: a TYPO3 "collectioncalendar" extension's ICS export -- a GET
scrapes the calendar form's street ``<select>`` and its hidden TYPO3 security
tokens (``__csrf`` et al.), a POST resubmits those tokens together with the
resolved street index, house number and every waste-type flag, and the
response embeds a per-request ``exportIcs`` download link (carrying its own
cHash) that must then be fetched. Three sequential, state-threading requests
is not a shape any configured retriever expresses, hence a source-defined
``retrieve`` method.

The provider marks an estimated/uncertain collection date with a trailing
"``: !``" in the ICS summary; ``regex`` on ``IcsParser`` strips it, mirroring
the legacy source's ``ICS(regex=r"(.*)\\:\\s*\\!")``. "Bioabfall" and
"Restabfall" already resolve against the standard German aliases;
"Altpapier", "Gelber Sack/Tonne" and "Sommerbiotonne" are Oldenburg-specific
phrasings mapped explicitly.
"""

from datetime import date
from typing import ClassVar, final

from bs4 import BeautifulSoup, Tag
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, street
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import IcsParser
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import ORGANIC, PAPER, RECYCLABLES

_BASE_URL = "https://www.oldenburg.de"
_API_URL = (
    _BASE_URL
    + "/startseite/stadtraum/umwelt/abfall-entsorgung/awb-von-a-bis-z/abfuhrkalender.html"
)
_FORM_FIELD = "tx_collectioncalendar_collectioncalendar"


@final
class Source(BaseSource):
    TITLE = "AWB Oldenburg"
    DESCRIPTION = "Source for 'Abfallwirtschaftsbetrieb Stadt Oldenburg (Oldb)'."
    URL = _BASE_URL
    COUNTRY = "de"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Polizeiinspektion Oldenburg": {"street": "Friedhofsweg", "house_number": 30}
    }

    PARAMS = (
        street(field="street"),
        house_number(field="house_number"),
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

    def retrieve(self, source):
        session = source.session
        street_value = source.params["street"]
        house_number_value = source.params["house_number"]

        r = session.get(_API_URL)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

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
        street_idx = mapping[street_value]

        # Collect the TYPO3 security tokens from the form's hidden inputs.
        data = {
            inp["name"]: inp.get("value", "")
            for inp in form.find_all("input", {"name": True})
        }
        data[f"{_FORM_FIELD}[year]"] = str(date.today().year)
        for waste_type_id in range(1, 6):
            data[f"{_FORM_FIELD}[wasteTypes][{waste_type_id}]"] = str(waste_type_id)
        data[f"{_FORM_FIELD}[street]"] = street_idx
        data[f"{_FORM_FIELD}[houseNumber]"] = str(house_number_value)
        data[f"{_FORM_FIELD}[privacyPolicy-checkbox]"] = "1"

        action = str(form.get("action", ""))
        post_url = _BASE_URL + action if action.startswith("/") else action

        r2 = session.post(post_url, data=data)
        r2.raise_for_status()
        soup2 = BeautifulSoup(r2.text, "html.parser")

        ics_link = None
        for a in soup2.find_all("a", href=True):
            if "exportIcs" in a["href"]:
                href = str(a["href"])
                ics_link = _BASE_URL + href if href.startswith("/") else href
                break

        if not ics_link:
            raise SourceArgumentNotFoundWithSuggestions(
                "house_number", house_number_value, []
            )

        r3 = session.get(ics_link)
        r3.raise_for_status()
        return r3
