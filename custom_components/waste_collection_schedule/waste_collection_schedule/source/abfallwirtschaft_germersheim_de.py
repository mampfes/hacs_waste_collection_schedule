"""Abfallwirtschaft Germersheim, Germany.

Demonstrates: a form whose ICS export needs a CSRF-style token and download
key scraped from a first GET, together with the *current* set of waste-type
checkboxes it renders (so the POST asks for every type actually offered
rather than a hardcoded list) -- then that state is POSTed back to the same
URL to get the ICS. No configured retriever expresses "GET, scrape two hidden
fields and a dynamic checkbox list, then POST all of it back", hence a
source-defined retrieve() (the parse step, converting the returned ICS, is
the plain shared IcsParser).
"""

import re
from typing import ClassVar, final

from bs4 import BeautifulSoup, Tag
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, street
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.parsers import IcsParser
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GARDEN_WASTE,
    GENERAL_WASTE,
    GLASS,
    HAZARDOUS,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_API_URL = "https://www.abfallwirtschaft-germersheim.de/online-service/abfall-termine/abfalltermine-ics-export-bis-240-liter.html"

_CHECKBOX_LABEL_RE = re.compile(r"id_form_icsabfallart_[0-9][0-9]?")


@final
class Source(BaseSource):
    TITLE = "Abfallwirtschaft Germersheim"
    DESCRIPTION = "Source für Abfallkalender Kreis Germersheim"
    URL = "https://www.abfallwirtschaft-germersheim.de"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Bellheim": {"city": "Bellheim", "street": "Albert-Schweitzer-Str."},
        "Hatzenbuehl": {"city": "Hatzenbühl"},
        "hoerdt": {"city": "Hördt", "street": ""},
    }

    PARAMS = (
        city(field="city"),
        street(field="street", optional=True),
    )

    def retrieve(self, source):
        session = source.session
        params: dict = {
            "icsortschaft": self.params["city"],
            "icsabfallart[]": [],
        }
        street_name = self.params.get("street") or ""
        if street_name:
            params["icsstrasse"] = street_name

        r = session.get(_API_URL, params=params)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        ics_download_tag = soup.find(
            "input", {"type": "hidden", "name": "ICS_DOWNLOAD"}
        )
        request_token_tag = soup.find(
            "input", {"type": "hidden", "name": "REQUEST_TOKEN"}
        )
        checkbox_container = soup.find("div", {"class": "ctlg_form_field checkbox"})
        if (
            not isinstance(ics_download_tag, Tag)
            or not isinstance(request_token_tag, Tag)
            or not isinstance(checkbox_container, Tag)
        ):
            raise SourceArgumentNotFound(
                "city", self.params["city"], "could not find the ICS export form."
            )
        ics_download = ics_download_tag.get("value")
        request_token = request_token_tag.get("value")

        waste_type_labels = checkbox_container.find_all(
            "label", {"for": _CHECKBOX_LABEL_RE}
        )
        for waste_type in waste_type_labels:
            params["icsabfallart[]"].append(waste_type.text)

        return session.post(
            _API_URL,
            params=params,
            data={"ICS_DOWNLOAD": ics_download, "REQUEST_TOKEN": request_token},
        )

    parse = IcsParser()
    transform = ICSTransformer(
        type_value_map={
            "Restmüll": GENERAL_WASTE,
            "Bioabfall": ORGANIC,
            "Gelber Sack": RECYCLABLES,
            "Glasbox": GLASS,
            "Heckenschnitt": GARDEN_WASTE,
            "Papier": PAPER,
            "Problemmüll": HAZARDOUS,
        }
    )

    def __init__(self, city: str, street: str = ""):
        super().__init__(city=city, street=street)
