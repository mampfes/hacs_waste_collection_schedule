"""The G3W-Suite ``live_addresses`` property API (Mole Valley).

``<api>/<postcode>?page=N`` lists the addresses of a postcode ten at a time, as
a GeoJSON feature collection. Each feature already carries the whole property
page (``three_column_layout_html``), bins panel included, so no second request
is needed once the address is found. The pages are walked until the one whose
address starts with the house number or name is found; one past the last page
the API answers 404 with ``{"result": false}``.

The host sends its leaf certificate without the intermediate, so no default
trust store can build a chain to it; the requests are made with
``verify=False``, as the legacy source did. Without an ``Accept`` header
naming JSON the API answers a browser-impersonating client with its HTML
browsable view.

:class:`LiveAddressesRetriever` returns the matched property's HTML as the
response, ready for ``parsers.HtmlTextParser``.
"""

import re
from typing import TYPE_CHECKING, Any

from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource


class PropertyPage:
    """A response stand-in carrying the matched property's HTML."""

    status_code = 200

    def __init__(self, text: str):
        self.text = text

    def raise_for_status(self) -> None:
        """Nothing to raise: the page was read out of a successful reply."""


class LiveAddressesRetriever:
    """The property page for ``source.params[postcode]`` / ``[house_number]``.

    Args:
        api: the ``.../api/live_addresses/`` base URL.
        postcode: name of the postcode parameter.
        house_number: name of the house number or name parameter, matched
            case-insensitively at the start of the address, before a space or
            comma (so ``1`` does not match ``10``).
        timeout: request timeout in seconds.
    """

    def __init__(
        self,
        api: str,
        *,
        postcode: str = "postcode",
        house_number: str = "house_number",
        timeout: int = 30,
    ):
        self.api = api
        self.postcode = postcode
        self.house_number = house_number
        self.timeout = timeout

    def _page(self, source: "BaseSource", postcode: str, page: int) -> Any:
        return source.session.get(
            self.api + postcode,
            params={"page": page},
            headers={"Accept": "application/json"},
            verify=False,  # the server does not send its intermediate CA cert
            timeout=self.timeout,
        )

    def __call__(self, source: "BaseSource") -> PropertyPage:
        postcode = str(source.params[self.postcode]).strip()
        wanted = str(source.params[self.house_number]).strip().lower()
        pattern = re.compile(r"^" + re.escape(wanted) + r"[\s,]")
        suggestions: list[str] = []
        page = 1
        while True:
            response = self._page(source, postcode, page)
            data = response.json()
            # One past the last page: 404 with {"result": false}.
            if not data.get("result", True):
                break
            response.raise_for_status()
            features = data.get("results", {}).get("features", [])
            if not features:
                break
            for feature in features:
                address = feature["properties"]["address_string"]
                suggestions.append(address)
                if pattern.match(address.lower()):
                    return PropertyPage(
                        feature["properties"]["three_column_layout_html"]
                    )
            if not data.get("next"):
                break
            page += 1
        raise SourceArgumentNotFoundWithSuggestions(
            self.house_number, wanted, suggestions
        )
