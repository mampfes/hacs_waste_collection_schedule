"""Abfallwirtschaft Germersheim, Germany.

The ICS export is a form that will only answer a POST carrying the CSRF token
and download key it just rendered, plus the set of waste-type checkboxes it
currently offers (so the request asks for every type actually available rather
than a hardcoded list). Reading those three off the form is the one lookup
step; the shared ``LookupChainRetriever`` then POSTs them back to the same URL
and hands the ICS to the shared ``IcsParser``.
"""

import re
from typing import ClassVar, NamedTuple, final

from bs4 import BeautifulSoup, Tag
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, text_field
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.field_terms import STREET
from waste_collection_schedule.parsers import IcsParser
from waste_collection_schedule.retrievers import LookupChainRetriever
from waste_collection_schedule.transformers import ICSTransformer

_API_URL = "https://www.abfallwirtschaft-germersheim.de/online-service/abfall-termine/abfalltermine-ics-export-bis-240-liter.html"

_CHECKBOX_LABEL_RE = re.compile(r"id_form_icsabfallart_[0-9][0-9]?")


class _ExportForm(NamedTuple):
    """What the rendered export form hands the download POST.

    All three come off the same page, so they resolve as one lookup step: a
    second step would mean a second identical GET.
    """

    ics_download: str
    request_token: str
    waste_types: list[str]


def _search_params(city_name: str, street_name: str, waste_types: list) -> dict:
    """The address query string, shared by the form GET and the download POST.

    ``waste_types`` is empty on the GET (the form renders the available types)
    and holds the scraped labels on the POST.
    """
    params: dict = {"icsortschaft": city_name, "icsabfallart[]": waste_types}
    if street_name:
        params["icsstrasse"] = street_name
    return params


def _read_export_form(source: BaseSource, keys: tuple) -> _ExportForm:
    """GET the form and read its download key, CSRF token and waste types."""
    city_name = source.params["city"]
    response = source.session.get(
        _API_URL,
        params=_search_params(city_name, source.params.get("street") or "", []),
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    ics_download_tag = soup.find("input", {"type": "hidden", "name": "ICS_DOWNLOAD"})
    request_token_tag = soup.find("input", {"type": "hidden", "name": "REQUEST_TOKEN"})
    checkbox_container = soup.find("div", {"class": "ctlg_form_field checkbox"})
    if (
        not isinstance(ics_download_tag, Tag)
        or not isinstance(request_token_tag, Tag)
        or not isinstance(checkbox_container, Tag)
    ):
        raise SourceArgumentNotFound(
            "city", city_name, "could not find the ICS export form."
        )

    return _ExportForm(
        ics_download_tag.get("value"),  # type: ignore[arg-type]
        request_token_tag.get("value"),  # type: ignore[arg-type]
        [
            label.text
            for label in checkbox_container.find_all(
                "label", {"for": _CHECKBOX_LABEL_RE}
            )
        ],
    )


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
        text_field("street", term=STREET, default=""),
    )

    retrieve = LookupChainRetriever(
        steps=(_read_export_form,),
        url=_API_URL,
        method="POST",
        params=lambda form, city, street="", **_: _search_params(
            city, street or "", form.waste_types
        ),
        data=lambda form, **_: {
            "ICS_DOWNLOAD": form.ics_download,
            "REQUEST_TOKEN": form.request_token,
        },
    )
    parse = IcsParser()
    transform = ICSTransformer(
        type_value_map={
            "Restmüll": wt.GENERAL_WASTE,
            "Bioabfall": wt.ORGANIC,
            "Gelber Sack": wt.RECYCLABLES,
            "Glasbox": wt.GLASS,
            "Heckenschnitt": wt.GARDEN_WASTE,
            "Papier": wt.PAPER,
            "Problemmüll": wt.HAZARDOUS,
        }
    )
