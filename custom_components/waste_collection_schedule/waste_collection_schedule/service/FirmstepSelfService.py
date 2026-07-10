"""Firmstep Self-Service (selfservice.<council>.gov.uk) shared components.

These target the Civica/Firmstep citizen-portal pattern used by several UK
councils. Each council exposes a URL of the form

    https://selfservice.<council>.gov.uk/renderform.aspx?t=…&k=…

that returns an HTML form containing a ``__RequestVerificationToken`` anti-CSRF
input together with other hidden fields (``FormGuid``, ``ObjectTemplateID``,
``CurrentSectionID``, …). Submitting that form often requires an address
look-up via ``core/addresslookup`` which accepts a postcode and returns a list
of UPRN-keyed address records.

Two acquisition shapes are covered, one retriever each:

* :class:`FirmstepAddressFormRetriever` — the council exposes a single field
  that accepts either a UPRN or a postcode. Post the value as-is first (a
  UPRN nearly always renders directly); if the response comes back with no
  matching rows and the value doesn't already look like a UPRN, fall back to
  ``core/addresslookup`` and retry once with the first resolved UPRN
  (derbyshiredales_gov_uk, southkesteven_gov_uk).
* :class:`RushcliffeAddressRetriever` — the council needs a postcode *and* a
  full address to disambiguate, always resolved via ``core/addresslookup``
  before the render POST (rushcliffe_gov_uk).
"""

import re
from collections.abc import Iterable
from datetime import date, datetime
from typing import TYPE_CHECKING, Any, ClassVar

from bs4 import BeautifulSoup

from waste_collection_schedule import preprocessors, response_shape
from waste_collection_schedule.exceptions import (
    SourceArgumentException,
    SourceArgumentNotFound,
)
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource

REQUIRED_FORM_FIELDS = {
    "__RequestVerificationToken",
    "FormGuid",
    "ObjectTemplateID",
    "CurrentSectionID",
}


def _get_hidden_form_inputs(session: Any, form_url: str, timeout: int = 30) -> dict:
    """GET *form_url* and return every hidden ``<input>`` as a ``name -> value`` dict."""
    r = session.get(form_url, timeout=timeout)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    return {
        inp["name"]: inp.get("value", "")
        for inp in soup.find_all("input", type="hidden")
        if inp.get("name")
    }


def _get_verification_token(session: Any, form_url: str, timeout: int = 30) -> str:
    """GET *form_url*, extract and return the ``__RequestVerificationToken`` value."""
    inputs = _get_hidden_form_inputs(session, form_url, timeout=timeout)
    token = inputs.get("__RequestVerificationToken")
    if not token:
        raise SourceArgumentException(
            "form",
            f"__RequestVerificationToken not found in form response from {form_url}",
        )
    return token


def _lookup_addresses(
    session: Any,
    lookup_url: str,
    postcode: str,
    *,
    search_nlpg: str = "True",
    timeout: int = 30,
) -> dict:
    """POST *lookup_url* (``core/addresslookup``) and return a ``{uprn_key: address}`` mapping.

    Handles both response formats returned by the Firmstep portal: an old/dict
    format (keys are UPRN strings, values are display addresses) and a
    new/list format (a JSON array of ``{"Key": uprn, "Value": address}``).
    """
    r = session.post(
        lookup_url,
        data={"query": postcode, "searchNlpg": search_nlpg, "classification": ""},
        timeout=timeout,
    )
    r.raise_for_status()
    raw = r.json()
    if isinstance(raw, dict):
        return dict(raw)
    if isinstance(raw, list):
        return {
            item["Key"]: item["Value"]
            for item in raw
            if isinstance(item, dict) and "Key" in item and "Value" in item
        }
    return {}


# --------------------------------------------------------------------------- #
# Pipeline components (BaseSource architecture)
# --------------------------------------------------------------------------- #


class FirmstepAddressFormRetriever(RetrieverFunc):
    """Post a single UPRN/postcode field to a RenderForm, retried once via lookup.

    Args:
        form_url: The ``renderform`` GET URL to scrape hidden fields/token from.
        render_url: The ``RenderForm`` POST URL.
        address_lookup_url: The ``core/addresslookup`` POST URL used for the
            fallback retry.
        value_field: The form field name the property value is posted under
            (Firmstep auto-generates a per-council/per-form field id, e.g.
            ``"FF2924"``).
        static_fields: Extra literal fields to include on every render POST
            (label/flag fields Firmstep expects alongside ``value_field``).
        row_selector: A CSS selector matching a real collection row. Used to
            decide whether the first render response already has data; if not
            (and the supplied value isn't already a UPRN), the retriever falls
            back to an address lookup and retries once.
        address_param: The ``source.params`` field holding the property value.
        search_nlpg: Value for the lookup's ``searchNlpg`` field.
    """

    def __init__(
        self,
        *,
        form_url: str,
        render_url: str,
        address_lookup_url: str,
        value_field: str,
        static_fields: "dict[str, str]",
        row_selector: str,
        address_param: str = "address_id",
        search_nlpg: str = "False",
        timeout: int = 30,
    ):
        self.form_url = form_url
        self.render_url = render_url
        self.address_lookup_url = address_lookup_url
        self.value_field = value_field
        self.static_fields = static_fields
        self.row_selector = row_selector
        self.address_param = address_param
        self.search_nlpg = search_nlpg
        self.timeout = timeout

    def __call__(self, source: "BaseSource") -> Any:
        address_value = str(source.params[self.address_param])
        response = self._render(source, address_value)
        if address_value.startswith("U") or self._has_rows(response):
            return response

        addresses = _lookup_addresses(
            source.session,
            self.address_lookup_url,
            address_value,
            search_nlpg=self.search_nlpg,
            timeout=self.timeout,
        )
        # A postcode can resolve to several records, and the first is
        # sometimes a "Street Record" that carries no collection schedule.
        # Render each resolved address in turn and return the first that
        # actually has rows, rather than blindly taking the first key (which
        # dead-ended postcodes like Bourne/Grantham for south_kesteven).
        for uprn in addresses:
            rendered = self._render(source, uprn)
            if self._has_rows(rendered):
                return rendered
        return response

    def _render(self, source: "BaseSource", address_value: str) -> Any:
        form_inputs = _get_hidden_form_inputs(
            source.session, self.form_url, timeout=self.timeout
        )
        if not REQUIRED_FORM_FIELDS.issubset(form_inputs):
            raise SourceArgumentException(
                self.address_param,
                "unable to read the council's form metadata; the provider may "
                "have changed its site.",
            )
        payload = {
            "__RequestVerificationToken": form_inputs["__RequestVerificationToken"],
            "FormGuid": form_inputs["FormGuid"],
            "ObjectTemplateID": form_inputs["ObjectTemplateID"],
            "Trigger": "submit",
            "CurrentSectionID": form_inputs["CurrentSectionID"],
            self.value_field: address_value,
            **self.static_fields,
        }
        r = source.session.post(self.render_url, data=payload, timeout=self.timeout)
        r.raise_for_status()
        return r

    def _has_rows(self, response: Any) -> bool:
        soup = BeautifulSoup(response.text, "html.parser")
        return bool(soup.select(self.row_selector))


class DerbyshireDalesRowClassifier(preprocessors.Preprocessor[Any, "tuple[date, str]"]):
    """Classify a Domestic/Recycling/Food row into ``(date, bucket)`` records.

    A recycling collection also empties the garden waste bin on the same day
    (not shown as its own row on the page), so a recycling row yields both a
    "recycling waste" and a "garden waste" record. "Sacks" rows duplicate the
    recycling collection and anything else unrecognised is skipped, matching
    derbyshiredales_gov_uk's page wording, which does not follow the shared
    multilingual vocabulary.
    """

    _DATE_FORMAT = "%A %d %B, %Y"

    def __call__(
        self, rows: Any, source: "BaseSource | None" = None
    ) -> "Iterable[tuple[date, str]]":
        seen: set[tuple[date, str]] = set()
        for row in rows:
            date_col = row.find("div", class_="col-sm-5")
            type_col = row.find("div", class_="col-sm-6")
            if not date_col or not type_col:
                continue
            raw_date = date_col.get_text(separator=" ", strip=True)
            try:
                collection_date = datetime.strptime(raw_date, self._DATE_FORMAT).date()
            except ValueError:
                continue

            lower = type_col.get_text(strip=True).lower()
            if "domestic" in lower:
                labels = ["domestic waste"]
            elif "recycling" in lower:
                labels = ["recycling waste", "garden waste"]
            elif "food" in lower:
                labels = ["food waste"]
            else:
                # Includes "sacks" rows (a recycling duplicate) and anything
                # else the page wording doesn't identify.
                continue

            for label in labels:
                key = (collection_date, label)
                if key not in seen:
                    seen.add(key)
                    yield key


class SouthKestevenRowClassifier(preprocessors.Preprocessor[Any, "tuple[date, str]"]):
    """Classify a colour-coded bin row into ``(date, bucket-or-raw-label)`` records.

    Rows whose type text doesn't match a known colour/keyword are still kept
    (with the raw text as the label, resolved by the shared multilingual
    vocabulary or preserved verbatim), matching southkesteven_gov_uk's
    original "keep the row even without a determined bin colour" behaviour.
    """

    _DATE_FORMAT = "%A %d %B, %Y"
    _EXACT: ClassVar[set[str]] = {"black", "gray", "green", "purple"}
    _KEYWORDS: ClassVar[tuple[tuple[str, str], ...]] = (
        ("refuse", "black"),
        ("recycling", "gray"),
        ("paper", "gray"),
        ("green", "green"),
        ("purple", "purple"),
    )

    def __call__(
        self, rows: Any, source: "BaseSource | None" = None
    ) -> "Iterable[tuple[date, str]]":
        for row in rows:
            cols = row.find_all("td", class_="Alloy-table-col")
            if len(cols) < 2:
                continue
            raw_date = cols[0].get_text(strip=True)
            raw_type = cols[1].get_text(strip=True)
            try:
                collection_date = datetime.strptime(raw_date, self._DATE_FORMAT).date()
            except ValueError:
                continue

            lower = raw_type.lower()
            if lower in self._EXACT:
                label = lower
            else:
                label = next(
                    (bucket for keyword, bucket in self._KEYWORDS if keyword in lower),
                    raw_type,
                )
            yield collection_date, label


class RushcliffeAddressRetriever(RetrieverFunc):
    """Resolve postcode+address to a UPRN via addresslookup, then POST the panel.

    Unlike :class:`FirmstepAddressFormRetriever`, this council's field needs an
    *exact* address match (not "first result") because a postcode returns many
    properties, so the caller supplies both a postcode and the full address
    text to disambiguate.

    Args:
        form_url: GET URL used to scrape the anti-CSRF token.
        address_lookup_url: The ``core/addresslookup`` POST URL.
        form_post_url: The ``renderform/Form`` POST URL.
        static_fields: Literal POST fields already known for this council
            (``FormGuid``, ``ObjectTemplateID``, ``Trigger``, ``CurrentSectionID``, …).
        uprn_field: The form field the resolved UPRN is posted under.
        address_param / postcode_param: The ``source.params`` fields holding
            the user-supplied address text and postcode.
    """

    def __init__(
        self,
        *,
        form_url: str,
        address_lookup_url: str,
        form_post_url: str,
        static_fields: "dict[str, Any]",
        uprn_field: str = "FF3518",
        address_param: str = "address",
        postcode_param: str = "postcode",
        timeout: int = 30,
    ):
        self.form_url = form_url
        self.address_lookup_url = address_lookup_url
        self.form_post_url = form_post_url
        self.static_fields = static_fields
        self.uprn_field = uprn_field
        self.address_param = address_param
        self.postcode_param = postcode_param
        self.timeout = timeout

    @staticmethod
    def _matches(candidate: str, wanted: str) -> bool:
        a = candidate.strip().replace(" ", "").replace(",", "").lower()
        b = wanted.strip().replace(" ", "").replace(",", "").lower()
        return a == b or a.startswith(b) or b.startswith(a)

    def __call__(self, source: "BaseSource") -> Any:
        postcode = source.params[self.postcode_param]
        address = source.params[self.address_param]

        token = _get_verification_token(
            source.session, self.form_url, timeout=self.timeout
        )
        addresses = _lookup_addresses(
            source.session, self.address_lookup_url, postcode, timeout=self.timeout
        )

        uprn = next(
            (key for key, value in addresses.items() if self._matches(value, address)),
            None,
        )
        if uprn is None:
            raise SourceArgumentNotFound(self.address_param, address)

        # Firmstep pairs each field id (e.g. FF3518) with companion fields
        # "<id>lbltxt" (display label) and "<id>-text" (free-text value). The
        # legacy source built the last key as `uprn_field + "FF3518-text"`,
        # doubling the id into "FF3518FF3518-text" (a copy-paste slip). The
        # server keys the lookup off the UPRN in the field itself, so the
        # mis-named companion was silently ignored and results still returned;
        # this restores the intended "<id>-text" companion.
        payload: dict[str, Any] = {
            **self.static_fields,
            "__RequestVerificationToken": token,
            self.uprn_field: uprn,
            f"{self.uprn_field}lbltxt": address,
            f"{self.uprn_field}-text": postcode,
        }
        r = source.session.post(self.form_post_url, data=payload, timeout=self.timeout)
        r.raise_for_status()
        return r


class RushcliffePanelParser(Parser["list[tuple[date, str]]"]):
    """Decode the ``div.ss_confPanel`` result panel into ``(date, bin_type)`` rows.

    Each panel line reads like ``"Your next <type> bin (...) is due on
    DD/MM/YYYY"``, occasionally with more than one date on the line. Does no
    I/O, so it runs standalone against a cached HTML fixture.
    """

    def __init__(self, panel_selector: str = "div.ss_confPanel"):
        self.panel_selector = panel_selector

    def __call__(
        self, response: Any, source: "BaseSource | None" = None
    ) -> "list[tuple[date, str]]":
        soup = BeautifulSoup(response.text, "html.parser")
        panel = soup.select_one(self.panel_selector)
        response_shape.expect(
            panel is not None,
            source_name=response_shape.source_name(source),
            detail=f"required element {self.panel_selector!r} not found",
            raw=response.text,
        )

        markup = str(panel).replace("<b>", "").replace("</b>", "")
        rows: list[tuple[date, str]] = []
        for line in markup.split("<br/>"):
            line = line.strip()
            if not line.startswith("Your"):
                continue
            before_bin = line.split(" bin", 1)[0].replace("Your next ", "")
            bin_type = before_bin.split("(", 1)[0].strip()
            for d in re.findall(r"\d{2}/\d{2}/\d{4}", line):
                rows.append((datetime.strptime(d, "%d/%m/%Y").date(), bin_type))
        return rows
