"""Firmstep Self-Service (selfservice.<council>.gov.uk) shared helpers.

These utilities target the Civica/Firmstep citizen-portal pattern used by
several UK councils.  Each council exposes a URL of the form

    https://selfservice.<council>.gov.uk/renderform.aspx?t=…&k=…

that returns an HTML form containing a ``__RequestVerificationToken`` anti-CSRF
input together with other hidden fields (``FormGuid``, ``ObjectTemplateID``,
``CurrentSectionID``, …).  Submitting that form often requires an address
look-up via ``core/addresslookup`` which accepts a postcode and returns a list
of UPRN-keyed address records.

Use these helpers when a source follows the pattern:

1. GET ``renderform.aspx?t=…&k=…`` → collect hidden form fields / token.
2. POST ``core/addresslookup`` with a postcode → resolve a UPRN key.
3. POST ``RenderForm`` / ``renderform/Form`` with the resolved UPRN → parse result.
"""

import json

import requests
from bs4 import BeautifulSoup


def get_hidden_form_inputs(
    session: requests.Session, form_url: str, timeout: int = 30
) -> dict:
    """GET *form_url* and return every hidden ``<input>`` as a ``name → value`` dict.

    Useful when a source needs more than just the verification token from the
    initial form page (e.g. ``FormGuid``, ``ObjectTemplateID``,
    ``CurrentSectionID``).
    """
    r = session.get(form_url, timeout=timeout)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    return {
        inp["name"]: inp.get("value", "")
        for inp in soup.find_all("input", type="hidden")
        if inp.get("name")
    }


def get_verification_token(
    session: requests.Session, form_url: str, timeout: int = 30
) -> str:
    """GET *form_url*, extract and return ``__RequestVerificationToken`` value."""
    inputs = get_hidden_form_inputs(session, form_url, timeout=timeout)
    token = inputs.get("__RequestVerificationToken")
    if not token:
        raise ValueError(
            f"__RequestVerificationToken not found in form response from {form_url}"
        )
    return token


def lookup_addresses(
    session: requests.Session,
    lookup_url: str,
    postcode: str,
    *,
    search_nlpg: str = "True",
    timeout: int = 30,
) -> dict:
    """POST *lookup_url* (``core/addresslookup``) and return a ``{uprn_key: address}`` mapping.

    Handles both response formats returned by the Firmstep portal:

    * **Old / dict format** – the response body is a JSON object whose keys
      are UPRN strings and whose values are display addresses.
    * **New / list format** – the response body is a JSON array of objects
      with ``"Key"`` (UPRN) and ``"Value"`` (address) properties.

    Parameters
    ----------
    session:
        An active :class:`requests.Session` (cookies / headers already set).
    lookup_url:
        Full URL of the ``core/addresslookup`` endpoint.
    postcode:
        Postcode (or address fragment) to search for.
    search_nlpg:
        Value for the ``searchNlpg`` form field.  Defaults to ``"True"``
        (standard national lookup); pass ``"False"`` for councils that use a
        local gazetteer only.
    timeout:
        Request timeout in seconds.
    """
    r = session.post(
        lookup_url,
        data={"query": postcode, "searchNlpg": search_nlpg, "classification": ""},
        timeout=timeout,
    )
    r.raise_for_status()
    raw = json.loads(r.text)
    if isinstance(raw, dict):
        return dict(raw)
    if isinstance(raw, list):
        return {
            item["Key"]: item["Value"]
            for item in raw
            if isinstance(item, dict) and "Key" in item and "Value" in item
        }
    return {}
