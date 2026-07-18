"""AWIGO Abfallwirtschaft Landkreis Osnabrück GmbH (awigo.de).

Demonstrates: a stateless PHP wizard driven by a chain of "legacy_eID" POSTs
(getCities -> getStreets -> getNumbers -> getICSfile), each request fully
specifying the previously resolved ids as parameters rather than relying on
server-side session state. All waste types (rest, paper, yellow, brown,
mobile) are enabled in a single pass: the API returns an events-free ICS
(headers only) when just one type is requested, so at least two must be
enabled together, and each ICS event already carries its own waste-type name
(issue #4562). The final getICSfile call itself returns a follow-up download
URL as plain text (not the ICS body), which must be fetched separately. No
configured retriever expresses this four-step resolve-then-download shape,
hence a source-defined retrieve()/parse() pair.
"""

import re
from typing import ClassVar, final

from bs4 import BeautifulSoup
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, municipality, street
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import IcsParser
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GENERAL_WASTE,
    GLASS,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_API_URL = "https://www.awigo.de/index.php"
_WASTE_TYPE_KEYS = ("rest", "paper", "yellow", "brown", "mobile")


def _compare_cities(a: str, b: str) -> bool:
    return (
        re.sub(r"\([0-9]+\)", "", a.lower()).strip()
        == re.sub(r"\([0-9]+\)", "", b.lower()).strip()
    )


def _post(session, args: dict):
    # The bracketed PHP array keys (e.g. "calendar[rest]") are sent as literal
    # query params -- curl_cffi percent-encodes the brackets itself, which the
    # endpoint accepts identically to the raw form the legacy `requests`-based
    # urlencode(..., safe="[]") produced.
    r = session.post(_API_URL, params=args)
    r.raise_for_status()
    return r


def _options(html: str) -> list:
    return BeautifulSoup(html, "html.parser").find_all("option")


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

    def retrieve(self, source):
        session = source.session
        ort = source.params["ort"]
        strasse = source.params["strasse"]
        hnr = str(source.params["hnr"]).lower().strip().replace(" ", "")

        # Enable every waste type in one pass: a single-type request returns
        # an events-free ICS, so at least two must be requested together. Each
        # ICS event carries its own waste-type name, so nothing is lost by
        # doing so. See GitHub issue #4562.
        args: dict = {
            "legacy_eID": "awigoCalendar",
            "calendar[method]": "getCities",
        }
        for wt in _WASTE_TYPE_KEYS:
            args[f"calendar[{wt}]"] = 1

        r = _post(session, args)
        options = _options(r.text)
        city_id = next(
            (o.get("value") for o in options if _compare_cities(ort, o.text)),
            None,
        )
        if city_id is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "ort", ort, [o.text for o in options]
            )
        args["calendar[cityID]"] = city_id

        args["calendar[method]"] = "getStreets"
        r = _post(session, args)
        options = _options(r.text)
        street_id = next(
            (
                o.get("value")
                for o in options
                if o.text.lower().strip() == strasse.lower().strip()
            ),
            None,
        )
        if street_id is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "strasse", strasse, [o.text for o in options]
            )
        args["calendar[streetID]"] = street_id

        args["calendar[method]"] = "getNumbers"
        r = _post(session, args)
        options = _options(r.text)
        location_id = next(
            (
                o.get("value")
                for o in options
                if o.text.lower().strip().replace(" ", "") == hnr
            ),
            None,
        )
        if location_id is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "hnr", source.params["hnr"], [o.text for o in options]
            )
        args["calendar[locationID]"] = location_id

        args["calendar[method]"] = "getICSfile"
        r = _post(session, args)
        ics_response = session.get(r.text.strip())
        ics_response.encoding = "utf-8"
        return [ics_response]

    def parse(self, raw, source):
        ics_parser = IcsParser()
        entries = []
        for response in raw:
            entries.extend(ics_parser(response, source))
        return entries

    def preprocess(self, entries, source):
        for date_, name in entries:
            yield (date_, name.replace("wird abgeholt.", "").strip())

    transform = ICSTransformer(
        type_value_map={
            "Restmülltonne": GENERAL_WASTE,
            "Glass": GLASS,
            "Bio-Tonne": ORGANIC,
            "Papiermülltonne": PAPER,
            "Gelbe Tonne/Gelben Sack": RECYCLABLES,
        }
    )

    def __init__(self, ort: str, strasse: str, hnr: "str | int"):
        super().__init__(ort=ort, strasse=strasse, hnr=hnr)
