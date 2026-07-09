import datetime

from bs4 import BeautifulSoup
from curl_cffi import requests

from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.service.ICS import ICS


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
        """Autocomplete with a fallback for terms the endpoint cannot match.

        The abto endpoint returns an empty result for some inputs (e.g. terms
        containing "ß", a trailing space, parentheses or a comma). When that
        happens, retry with the leading, more tolerant part of the term and let
        the caller filter the (broader) result set locally.
        """
        results = self.autocomplete(term, refid=refid)
        if results or not term:
            return results

        short = term
        for sep in ("ß", "(", ",", "  "):
            short = short.split(sep)[0]
        short = short.strip()
        if short and short != term:
            results = self.autocomplete(short, refid=refid)
        return results

    def fetch_ics(self, pois: str) -> list[tuple[datetime.date, str]]:
        """Download and parse the ICS calendar for a pois id."""
        params = {"ModID": "48", "call": "ical", "pois": pois}
        params.update(self._download_params)

        r = self._session.get(
            f"{self._base_url}/output/options.php",
            params=params,
            headers={"Referer": self._base_url + "/"},
            timeout=30,
        )
        r.raise_for_status()
        return self._ics.convert(r.text)

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
