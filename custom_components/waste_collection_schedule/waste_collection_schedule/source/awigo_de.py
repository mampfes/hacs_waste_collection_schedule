"""AWIGO Abfallwirtschaft Landkreis Osnabrück GmbH (awigo.de).

Demonstrates: a stateless PHP wizard driven by a chain of "legacy_eID" POSTs
(getCities -> getStreets -> getNumbers -> getICSfile), each request fully
specifying the previously resolved ids as parameters rather than relying on
server-side session state. All waste types (rest, paper, yellow, brown,
mobile) are enabled in a single pass: the API returns an events-free ICS
(headers only) when just one type is requested, so at least two must be
enabled together, and each ICS event already carries its own waste-type name
(issue #4562). The final getICSfile call itself returns a follow-up download
URL as plain text (not the ICS body), which must be fetched separately: that is
a LookupChainRetriever whose last step resolves the download address and hands
it straight back as the schedule URL.
"""

import re
from typing import ClassVar, final

from bs4 import BeautifulSoup
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, municipality, street
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import IcsParser
from waste_collection_schedule.preprocessors import RowRelabel
from waste_collection_schedule.retrievers import Lookup, LookupChainRetriever
from waste_collection_schedule.transformers import ICSTransformer

_API_URL = "https://www.awigo.de/index.php"
_WASTE_TYPE_KEYS = ("rest", "paper", "yellow", "brown", "mobile")


def _compare_cities(a: str, b: str) -> bool:
    return (
        re.sub(r"\([0-9]+\)", "", a.lower()).strip()
        == re.sub(r"\([0-9]+\)", "", b.lower()).strip()
    )


def _options(html: str) -> list:
    return BeautifulSoup(html, "html.parser").find_all("option")


def _args(method: str, **ids: object) -> dict:
    """The wizard's parameters for one step, in the order the endpoint sees them.

    Every request restates the whole state, because the wizard keeps none. All
    waste types are enabled on every call: a single-type request answers with an
    events-free ICS, so at least two must be asked for together (issue #4562).
    """
    args: dict = {"legacy_eID": "awigoCalendar", "calendar[method]": method}
    for waste_type in _WASTE_TYPE_KEYS:
        args[f"calendar[{waste_type}]"] = 1
    for name in ("cityID", "streetID", "locationID"):
        if name in ids:
            args[f"calendar[{name}]"] = ids[name]
    return args


def _step(method: str, pick) -> Lookup:
    """One wizard call, restating every id resolved so far.

    The bracketed PHP array keys (e.g. "calendar[rest]") are sent as literal
    query params -- curl_cffi percent-encodes the brackets itself, which the
    endpoint accepts identically to the raw form the legacy `requests`-based
    urlencode(..., safe="[]") produced.
    """
    return Lookup(
        _API_URL,
        method="POST",
        params=lambda *keys, **_: _args(
            method,
            **dict(zip(("cityID", "streetID", "locationID"), keys, strict=False)),
        ),
        pick=pick,
    )


def _pick(options: list, wanted: str, argument: str, matches) -> str:
    """The option whose text the caller accepts, or a not-found with the list."""
    found = next((o.get("value") for o in options if matches(o.text)), None)
    if found is None:
        raise SourceArgumentNotFoundWithSuggestions(
            argument, wanted, [o.text for o in options]
        )
    return found


def _pick_city(response, *keys, ort, **_) -> str:
    return _pick(
        _options(response.text), ort, "ort", lambda text: _compare_cities(ort, text)
    )


def _pick_street(response, *keys, strasse, **_) -> str:
    return _pick(
        _options(response.text),
        strasse,
        "strasse",
        lambda text: text.lower().strip() == strasse.lower().strip(),
    )


def _pick_number(response, *keys, hnr, **_) -> str:
    wanted = str(hnr).lower().strip().replace(" ", "")
    return _pick(
        _options(response.text),
        hnr,
        "hnr",
        lambda text: text.lower().strip().replace(" ", "") == wanted,
    )


def _download_url(response, *keys, **_) -> str:
    """getICSfile answers with the download address, not the ICS."""
    return response.text.strip()


@final
class Source(BaseSource):
    TITLE = "AWIGO Abfallwirtschaft Landkreis Osnabrück GmbH"
    DESCRIPTION = "Source for AWIGO Abfallwirtschaft Landkreis Osnabrück GmbH."
    URL = "https://www.awigo.de/"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Bippen Am Bad 4": {"ort": "Bippen", "strasse": "Am Bad", "hnr": 4},
        "fürstenau, Am Gültum, 9": {
            "ort": "Fürstenau",
            "strasse": "Am Gültum",
            "hnr": 9,
        },
        "Melle, Allee, 78-80": {"ort": "Melle", "strasse": "Allee", "hnr": "78-80"},
        "Berge": {"ort": "Berge", "strasse": "Poststr.", "hnr": 3},
    }

    PARAMS = (
        municipality(field="ort"),
        street(field="strasse"),
        house_number(field="hnr"),
    )

    retrieve = LookupChainRetriever(
        steps=(
            _step("getCities", _pick_city),
            _step("getStreets", _pick_street),
            _step("getNumbers", _pick_number),
            _step("getICSfile", _download_url),
        ),
        # The last step already resolved the download address.
        url=lambda *keys, **_: keys[-1],
        encoding="utf-8",
    )

    parse = IcsParser()

    # Every SUMMARY is the round's name with the same sentence glued on.
    preprocess = RowRelabel(strip=r"wird abgeholt\.")

    transform = ICSTransformer(
        type_value_map={
            "Restmülltonne": wt.GENERAL_WASTE,
            "Glass": wt.GLASS,
            "Bio-Tonne": wt.ORGANIC,
            "Papiermülltonne": wt.PAPER,
            "Gelbe Tonne/Gelben Sack": wt.RECYCLABLES,
        }
    )
