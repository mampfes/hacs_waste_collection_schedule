#!/usr/bin/env python3

from typing import TYPE_CHECKING

from bs4 import BeautifulSoup, Tag

from ..exceptions import SourceArgumentNotFoundWithSuggestions
from ..retrievers import RetrieverFunc

if TYPE_CHECKING:
    from ..base_source import BaseSource


# --------------------------------------------------------------------------- #
# Pipeline components (BaseSource architecture)
#
# Müllmax is a deep, stateful form-wizard: GET a session token, then up to ~7
# conditional POSTs (select Abfuhrtermine, optional city, optional street
# search+select, auto-detected house number, choose iCalendar, tick every
# fraction, download), re-reading each page only to extract the form state
# (session id, house-number options, fraction checkboxes) that drives the next
# request. That acquisition belongs to the platform, so it lives here as a
# retriever rather than in every Müllmax source:
#
#     retrieve = MuellmaxRetriever()
#     parse    = IcsParser()      # the final response is a plain iCalendar feed
#
# MuellmaxRetriever walks the form on the shared session and returns the final
# ICS response; an ordinary IcsParser + ICSTransformer then turn it into
# collections, with the German bin names resolved by the shared vocabulary.
# --------------------------------------------------------------------------- #


def _soup(text: str) -> BeautifulSoup:
    return BeautifulSoup(text, "html.parser")


def _session_token(text: str) -> "str | None":
    """The hidden ``mm_ses`` token threaded through every step of the form."""
    el = _soup(text).find("input", attrs={"name": "mm_ses"})
    value = el.get("value") if isinstance(el, Tag) else None
    return value if isinstance(value, str) else None


def _hnr_options(text: str) -> list[str]:
    select = _soup(text).find("select", attrs={"name": "mm_frm_hnr_sel"})
    if not isinstance(select, Tag):
        return []
    options: list[str] = []
    for option in select.find_all("option"):
        value = option.get("value") if isinstance(option, Tag) else None
        if isinstance(value, str) and value:
            options.append(value)
    return options


def _fraction_checkboxes(text: str) -> dict[str, str]:
    """Every ``mm_frm_fra*`` checkbox, so the download covers all waste types."""
    values: dict[str, str] = {}
    for inp in _soup(text).find_all("input"):
        if not isinstance(inp, Tag):
            continue
        name = inp.get("name")
        if isinstance(name, str) and name.startswith("mm_frm_fra"):
            value = inp.get("value")
            values[name] = value if isinstance(value, str) else ""
    return values


def _resolve_house_number(given: "str | None", text: str) -> str:
    """Map a plain house number to the form's full ``id;area;number;`` option."""
    options = _hnr_options(text)
    if given is None:
        raise SourceArgumentNotFoundWithSuggestions("mm_frm_hnr_sel", "", options)
    if ";" in given:
        return given
    matches = [o for o in options if o.split(";")[2:3] == [given]]
    if len(matches) == 1:
        return matches[0]
    raise SourceArgumentNotFoundWithSuggestions(
        "mm_frm_hnr_sel", given, matches or options
    )


class MuellmaxRetriever(RetrieverFunc):
    """Walk the Müllmax form wizard and return the final iCalendar response.

    Reads the platform's fixed field names from ``source.params``: ``service``
    and the optional ``mm_frm_ort_sel`` / ``mm_frm_str_sel`` / ``mm_frm_hnr_sel``.
    Runs on the shared session so the ``mm_ses`` token and cookies persist across
    the conditional steps.
    """

    def __call__(self, source: "BaseSource"):
        service = source.params["service"]
        url = (
            f"https://www.muellmax.de/abfallkalender/{service.lower()}"
            f"/res/{service}Start.php"
        )
        session = source.session

        response = session.get(url)
        token = _session_token(response.text)

        def step(data: dict) -> None:
            nonlocal response, token
            response = session.post(url, data={"mm_ses": token, **data})
            token = _session_token(response.text) or token

        # Select "Abfuhrtermine"; returns either a city selector or a street search.
        step({"mm_aus_ort.x": 0, "mm_aus_ort.y": 0})

        ort = source.params.get("mm_frm_ort_sel")
        if ort:
            step({"xxx": 1, "mm_frm_ort_sel": ort, "mm_aus_ort_submit": "weiter"})

        street = source.params.get("mm_frm_str_sel")
        if street:
            step(
                {"xxx": 1, "mm_frm_str_name": street, "mm_aus_str_txt_submit": "suchen"}
            )
            step(
                {"xxx": 1, "mm_frm_str_sel": street, "mm_aus_str_sel_submit": "weiter"}
            )

        # The form decides whether a house number is needed for this address.
        if "mm_frm_hnr_sel" in response.text:
            hnr = _resolve_house_number(
                source.params.get("mm_frm_hnr_sel"), response.text
            )
            step({"xxx": 1, "mm_frm_hnr_sel": hnr, "mm_aus_hnr_sel_submit": "weiter"})

        # Switch the output to an iCalendar file, tick every fraction, download.
        step({"xxx": 1, "mm_ica_auswahl": "iCalendar-Datei"})
        fractions = _fraction_checkboxes(response.text)
        step(
            {
                "xxx": 1,
                "mm_frm_type": "termine",
                **fractions,
                "mm_ica_gen": "iCalendar-Datei laden",
            }
        )
        return response
