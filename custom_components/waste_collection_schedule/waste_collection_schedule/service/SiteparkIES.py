import datetime
from typing import TYPE_CHECKING

from bs4 import BeautifulSoup
from curl_cffi import requests

from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.retrievers import RetrieverFunc
from waste_collection_schedule.service.ICS import ICS

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource


def _mojibake(term: str) -> str:
    """Re-encode a term to work around a server-side double UTF-8 decode.

    Some Sitepark installations (e.g. hilchenbach.de) mis-decode the
    ``term`` query parameter, so a correctly UTF-8-encoded term containing
    umlauts or "ß" never matches (e.g. "Am Bühl" or "Dammstraße" return no
    results at all). Re-encoding the term as UTF-8 bytes and decoding those
    bytes as Latin-1 reproduces the same mis-decoding the server applies,
    which cancels it out and lets the match succeed. Other installations
    (e.g. ab-peine.de) decode correctly already and this would break them,
    so it is only tried as a fallback, not applied unconditionally.
    """
    return term.encode("utf-8").decode("latin-1")


def match_icon(waste_type: str, icon_map: dict):
    """Return the first icon whose key is contained in the waste type.

    The Sitepark feeds often append a rhythm suffix to the waste type
    (e.g. "Restmülltonne 14-täglichen Rhythmus"), so a substring match is
    used instead of an exact lookup.
    """
    lowered = waste_type.lower()
    for key, icon in icon_map.items():
        if key.lower() in lowered:
            return icon
    return None


class SiteparkIES:
    """Shared client for the Sitepark IES / abto waste-calendar platform.

    A number of German municipalities run the same Sitepark "iKISS" CMS with
    the abto waste module. They all share two endpoints:

    * ``/output/autocomplete.php?out=json&type=abto&select=2&term=<street>``
      returns ``[[pois, "Street (Place)"], ...]`` for a street search. Some
      installations require a ``refid`` (district/municipality id); others
      return all streets across the district when none is given and
      disambiguate by the "(Place)" suffix.
    * ``/output/options.php?ModID=48&call=ical&pois=<pois>`` returns an ICS
      calendar for the resolved point of interest.

    Every request must send a ``Referer`` header pointing at the base domain,
    otherwise the server answers ``403``.
    """

    def __init__(
        self,
        base_url: str,
        *,
        refid: str | None = None,
        download_params: dict | None = None,
        ics: ICS | None = None,
    ):
        self._base_url = base_url.rstrip("/")
        self._refid = refid
        self._download_params = download_params or {}
        self._ics = ics or ICS()
        self._session = requests.Session(impersonate="chrome")

    @property
    def _headers(self) -> dict:
        return {
            "Referer": self._base_url + "/",
            "X-Requested-With": "XMLHttpRequest",
        }

    def autocomplete(self, term: str | None, refid: str | None = None) -> list[list]:
        """Query the abto autocomplete endpoint and return ``[[pois, label], ...]``."""
        params = {
            "out": "json",
            "type": "abto",
            "select": "2",
            "term": term or "",
        }
        rid = refid if refid is not None else self._refid
        if rid is not None:
            params["refid"] = rid

        r = self._session.get(
            f"{self._base_url}/output/autocomplete.php",
            params=params,
            headers=self._headers,
            timeout=30,
        )
        r.raise_for_status()
        # The endpoint answers JSON ``null`` (instead of ``[]``) for some
        # searches, e.g. terms with parentheses or when a refid is required.
        data = r.json()
        return data if isinstance(data, list) else []

    def resolve_refid(
        self,
        ort: str,
        page_url: str,
        value_prefix: str | None = None,
    ) -> str:
        """Resolve an "Ort" to its refid via the ``sf_locid`` dropdown on a page."""
        r = self._session.get(
            page_url, headers={"Referer": self._base_url + "/"}, timeout=30
        )
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        select = soup.find("select", id="sf_locid")
        options: dict = {}
        if select is not None:
            for option in select.find_all("option"):
                value = str(option.get("value") or "").strip()
                name = option.get_text(strip=True)
                if not value or not name:
                    continue
                if value_prefix is not None and not value.startswith(value_prefix):
                    continue
                options[name] = value

        # exact match first, then case-insensitive containment
        if ort in options:
            return options[ort]
        for name, value in options.items():
            if ort.lower() in name.lower():
                return value

        raise SourceArgumentNotFoundWithSuggestions("ort", ort, list(options.keys()))

    def get_pois(
        self,
        strasse: str | None = None,
        ort: str | None = None,
        refid: str | None = None,
    ) -> str:
        """Resolve a street (and optional place) to a single pois id."""
        results = self._query(strasse, refid=refid)

        candidates = results
        if strasse:
            filtered = [item for item in results if strasse.lower() in item[1].lower()]
            if filtered:
                candidates = filtered
        if ort:
            by_ort = [item for item in candidates if ort.lower() in item[1].lower()]
            if by_ort:
                candidates = by_ort

        if not candidates:
            # Re-query without a term to build a helpful suggestion list.
            suggestions = [item[1] for item in self.autocomplete("", refid=refid)]
            raise SourceArgumentNotFoundWithSuggestions(
                "strasse", strasse or "", suggestions or [item[1] for item in results]
            )

        if len(candidates) > 1:
            # Prefer an exact match on the street part (the bit before " (Place)").
            wanted = (strasse or "").strip().lower()
            exact = [
                item
                for item in candidates
                if item[1].split(" (")[0].strip().lower() == wanted
            ]
            if len(exact) == 1:
                return exact[0][0]
            raise SourceArgAmbiguousWithSuggestions(
                "strasse", strasse or "", [item[1] for item in candidates]
            )

        return candidates[0][0]

    def _query(self, term: str | None, refid: str | None) -> list[list]:
        """Autocomplete with fallbacks for terms the endpoint cannot match.

        The abto endpoint returns an empty result for some inputs: umlauts
        or "ß" on installations affected by the double-decode bug (see
        ``_mojibake``), or a trailing space, parentheses or a comma on any
        installation. When that happens, retry with a more tolerant form of
        the term and let the caller filter the (broader) result set locally.
        """
        results = self.autocomplete(term, refid=refid)
        if results or not term:
            return results

        if not term.isascii():
            results = self.autocomplete(_mojibake(term), refid=refid)
            if results:
                return results

        short = term
        for sep in ("(", ",", "  "):
            short = short.split(sep)[0]
        short = short.strip()
        if short and short != term:
            results = self.autocomplete(short, refid=refid)
        return results

    def fetch_ics_response(self, pois: str):
        """Download the raw ICS calendar response for a pois id.

        Split out from :meth:`fetch_ics` so the retrieve and parse steps stay
        separate: a pipeline source's ``retrieve`` delegates to this and hands
        the raw response to the shared ``parsers.IcsParser``. Legacy callers keep
        using :meth:`fetch_ics`, which parses the same response.
        """
        params = {"ModID": "48", "call": "ical", "pois": pois}
        params.update(self._download_params)

        r = self._session.get(
            f"{self._base_url}/output/options.php",
            params=params,
            headers={"Referer": self._base_url + "/"},
            timeout=30,
        )
        r.raise_for_status()
        return r

    def fetch_ics(self, pois: str) -> list[tuple[datetime.date, str]]:
        """Download and parse the ICS calendar for a pois id."""
        return self._ics.convert(self.fetch_ics_response(pois).text)

    def fetch(
        self,
        strasse: str | None = None,
        ort: str | None = None,
        pois: str | None = None,
        refid: str | None = None,
    ) -> list[tuple[datetime.date, str]]:
        """Resolve the pois (unless given directly) and return parsed dates."""
        if not pois:
            pois = self.get_pois(strasse=strasse, ort=ort, refid=refid)
        return self.fetch_ics(pois)


class SiteparkIESRetriever(RetrieverFunc):
    """Resolve the address to a pois and return the raw ICS response.

    The pipeline retrieve step for Sitepark IES sources. It runs the shared
    client's autocomplete/pois lookup (including its typed ``SourceArgument*``
    exceptions on a bad or ambiguous street) and returns the raw ICS response
    for ``parsers.IcsParser`` to convert. A source built on this needs no
    ``retrieve`` override and no hand-rolled request params.

    Args:
        base_url: The municipality's Sitepark base URL.
        refid: Optional district/municipality id for the autocomplete endpoint.
        download_params: Extra query params for the ICS download (e.g. kat/alarm).
        strasse: The ``source.params`` field holding the street.
        ort: The ``source.params`` field holding the optional place/Ortsteil.
    """

    def __init__(
        self,
        base_url: str,
        *,
        refid: str | None = None,
        download_params: dict | None = None,
        strasse: str = "strasse",
        ort: str = "ort",
    ):
        self._base_url = base_url
        self._refid = refid
        self._download_params = download_params
        self._strasse = strasse
        self._ort = ort

    def __call__(self, source: "BaseSource"):
        client = SiteparkIES(
            self._base_url,
            refid=self._refid,
            download_params=self._download_params,
        )
        pois = client.get_pois(
            strasse=source.params.get(self._strasse),
            ort=source.params.get(self._ort),
        )
        return client.fetch_ics_response(pois)
