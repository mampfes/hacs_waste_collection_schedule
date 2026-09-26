"""Jadu Continuum XFP forms (``/xfp/form/<id>``), as UK councils' bin lookups.

Many UK councils build their "check your bin day" page as a Jadu XFP form. The
form is stateful and CSRF-protected, and it works the same way everywhere:

1. GET the form page and read the hidden ``__token`` input.
2. POST the address question: its postcode answer is ``<question>_0_0`` and the
   chosen address (an ``<option>`` whose value is the property's UPRN) is
   ``<question>_1_0``, together with the token, the form's ``page`` id and
   ``next=Next``.
3. The reply is the results page, which each council lays out its own way (a
   table, or a sentence per round), so it is read with the ordinary HTML
   parsers.

Where a council's users know their UPRN, both answers go in one POST. Where
they don't, :class:`XfpFormRetriever` POSTs the postcode alone first, reads the
address list the form answers with, and picks the property by its UPRN or by
the start of its address, reporting the addresses it did find when nothing
matches::

    retrieve = XfpFormRetriever(
        "https://www.oxford.gov.uk/xfp/form/142",
        page="12",
        question="q6ad4e3bf432c83230a0347a6eea6c805c672efeb",
    )
    parse = parsers.HtmlParser("table.data-table tbody tr")

The ``page`` and ``question`` ids are the form's own: read them off the form's
HTML (the ``page`` hidden input and the ``name`` of the postcode field).
"""

import re
from typing import TYPE_CHECKING, Any

from bs4 import BeautifulSoup

from waste_collection_schedule import response_shape
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.retrievers import RetrieverFunc

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource


def _token(html: str, source: "BaseSource") -> str:
    tag = BeautifulSoup(html, "html.parser").find("input", {"name": "__token"})
    value = tag.get("value") if tag is not None else None
    response_shape.expect(
        isinstance(value, str) and bool(value),
        source_name=response_shape.source_name(source),
        detail="XFP form page carries no __token",
        raw=html,
    )
    return str(value)


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().casefold()


class XfpFormRetriever(RetrieverFunc):
    """Answer a Jadu XFP address question and return the results page.

    Args:
        form_url: the form's ``/xfp/form/<id>`` URL, which every POST goes to.
        page: the form page id holding the address question.
        question: the address question's field name prefix (``q<hash>``).
        postcode: the ``source.params`` field holding the postcode.
        uprn: the ``source.params`` field holding the UPRN, or ``None`` for a
            source that identifies the property by ``address`` instead.
        address: the ``source.params`` field holding the start of the address
            as the form lists it, for a source whose users don't know their
            UPRN. Implies ``lookup_address``.
        lookup_address: POST the postcode alone first and choose the property
            from the address list it returns, rather than posting the UPRN
            blind. Needed by forms that reject an address they did not offer.
        landing_url: GET this page for the token instead of the form itself,
            for a council whose form is embedded in another page.
    """

    def __init__(
        self,
        form_url: str,
        *,
        page: str,
        question: str,
        postcode: str = "postcode",
        uprn: "str | None" = "uprn",
        address: "str | None" = None,
        lookup_address: bool = False,
        landing_url: "str | None" = None,
        timeout: int = 30,
    ):
        self.form_url = form_url
        self.page = page
        self.question = question
        self.postcode = postcode
        self.uprn = uprn
        self.address = address
        self.lookup_address = lookup_address or address is not None
        self.landing_url = landing_url
        self.timeout = timeout

    def _answer(self, token: str, postcode: str) -> dict[str, str]:
        return {
            "__token": token,
            "page": self.page,
            "locale": "en_GB",
            f"{self.question}_0_0": postcode,
        }

    def _choose(self, html: str, source: "BaseSource") -> str:
        """The option value (UPRN) of the configured property."""
        soup = BeautifulSoup(html, "html.parser")
        options = [
            (str(option.get("value") or ""), option.get_text(" ", strip=True))
            for option in soup.select(f'select[name="{self.question}_1_0"] option')
        ]
        # The first option is the "Select an address..." placeholder.
        options = [(value, text) for value, text in options if value.strip("0.")]
        postcode = source.params[self.postcode]
        if not options:
            raise SourceArgumentNotFound(self.postcode, postcode)
        addresses = [text for _value, text in options]

        if self.address is not None:
            wanted = _normalise(str(source.params[self.address]))
            matches = [v for v, t in options if _normalise(t).startswith(wanted)]
            if len(matches) == 1:
                return matches[0]
            if matches:
                raise SourceArgAmbiguousWithSuggestions(
                    self.address,
                    source.params[self.address],
                    [t for v, t in options if v in matches],
                )
            raise SourceArgumentNotFoundWithSuggestions(
                self.address, source.params[self.address], addresses
            )

        uprn = str(source.params[self.uprn or "uprn"]).strip()
        for value, _text in options:
            if value.lstrip("0") == uprn.lstrip("0"):
                return value
        raise SourceArgumentNotFoundWithSuggestions(
            self.uprn or "uprn",
            uprn,
            [f"{text} (UPRN {value})" for value, text in options],
        )

    def __call__(self, source: "BaseSource") -> Any:
        session = source.session
        if self.landing_url is not None:
            response = session.get(self.landing_url, timeout=self.timeout)
        else:
            response = session.get(
                self.form_url,
                params={"page": self.page, "locale": "en_GB"},
                timeout=self.timeout,
            )
        response.raise_for_status()
        token = _token(response.text, source)
        postcode = str(source.params[self.postcode]).strip()

        if self.lookup_address:
            response = session.post(
                self.form_url,
                data={**self._answer(token, postcode), "next": "Next"},
                timeout=self.timeout,
            )
            response.raise_for_status()
            token = _token(response.text, source)
            property_id = self._choose(response.text, source)
        else:
            property_id = str(source.params[self.uprn or "uprn"]).strip()

        response = session.post(
            self.form_url,
            data={
                **self._answer(token, postcode),
                f"{self.question}_1_0": property_id,
                "next": "Next",
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response
