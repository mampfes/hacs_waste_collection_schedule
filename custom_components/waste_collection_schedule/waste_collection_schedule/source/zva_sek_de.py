"""Zweckverband Abfallwirtschaft Schwalm-Eder-Kreis (zva-sek.de).

Demonstrates: resolving a district -> sub-district -> (optional) street
cascade by scraping a <select> off a yearly calendar page and two
semicolon-separated JS-assignment endpoints, then POSTing the resolved ids to
an ICS-generating servlet -- optionally twice, once for next year too, near
year-end. No configured retriever expresses that scrape-then-resolve chain,
hence a source-defined retrieve()/parse() pair.
"""

import re
from datetime import datetime
from typing import ClassVar, final

from bs4 import BeautifulSoup, Tag
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import district, street, text_field
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import IcsParser
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GENERAL_WASTE,
    HAZARDOUS,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_SERVLET = "https://www.zva-sek.de/module/abfallkalender/generate_ical.php"
_MAIN_URL = "https://www.zva-sek.de/online-dienste/abfallkalender-{year}/{file}"
_API_URL = "https://www.zva-sek.de/module/abfallkalender/{file}"

_SUFFIX_RE = re.compile(r"[ ]*am [0-9]+\.[0-9]+\.[0-9]+[ ]*")


def _js_options(text: str) -> list[str]:
    """Read the option labels out of a "f.x.options[n].text = '...'" reply."""
    return [
        part.split(" = ")[1][1:-1]
        for part in text.split(";")[2:-1]
        if "length" not in part
    ]


def _resolve_js_id(text: str, value: str) -> "str | None":
    """Find the id preceding the option whose label matches ``value``.

    Each endpoint replies with alternating ``...text = '...'`` / ``...value =
    '...'`` lines; the id for a given label is the *previous* line's value.
    """
    last_id = None
    for part in text.split(";")[2:-1]:
        if "length" in part:
            continue
        label = part.split(" = ")[1][1:-1]
        if label.lower() == value.lower():
            return last_id
        last_id = label
    return None


@final
class Source(BaseSource):
    TITLE = "Zweckverband Abfallwirtschaft Schwalm-Eder-Kreis"
    DESCRIPTION = "Source for ZVA (Zweckverband Abfallwirtschaft Schwalm-Eder-Kreis)."
    URL = "https://www.zva-sek.de"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        GENERAL_WASTE,
        HAZARDOUS,
        ORGANIC,
        PAPER,
        RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Fritzlar": {
            "bezirk": "Fritzlar",
            "ortsteil": "Fritzlar-kernstadt",
            "strasse": "Ahornweg",
        },
        "Ottrau": {
            "bezirk": "Ottrau",
            "ortsteil": "immichenhain",
            "strasse": "",
        },
        "Knüllwald": {
            "bezirk": "Knüllwald",
            "ortsteil": "Hergetsfeld",
        },
        "Felsberg": {
            "bezirk": "Felsberg",
            "ortsteil": "Felsberg",
        },
        "Guxhagen": {
            "bezirk": "Guxhagen",
            "ortsteil": "Guxhagen",
        },
    }

    PARAMS = (
        text_field("bezirk", "Collection district"),
        district(field="ortsteil"),
        street(field="strasse", optional=True),
    )

    def retrieve(self, source):
        session = source.session
        bezirk = source.params["bezirk"]
        ortsteil = source.params["ortsteil"]
        strasse = source.params.get("strasse") or None
        year = datetime.now().year

        r = session.get(_MAIN_URL.format(year=year, file=f"abfallkalender-{year}.html"))
        if r.status_code == 404:  # try last year's URL if this year isn't up yet
            r = session.get(
                _MAIN_URL.format(year=year, file=f"abfallkalender-{year - 1}.html")
            )
        r.raise_for_status()

        soup = BeautifulSoup(r.text, features="html.parser")
        bezirk_select = soup.find("select", {"name": "ak_bezirk"})
        if not isinstance(bezirk_select, Tag):
            raise SourceArgumentNotFoundWithSuggestions("bezirk", bezirk, [])
        bezirk_options = bezirk_select.find_all("option")
        bezirk_id = None
        for option in bezirk_options:
            if option.text.lower() == bezirk.lower():
                bezirk_id = option.get("value")
                break
        if not bezirk_id:
            raise SourceArgumentNotFoundWithSuggestions(
                "bezirk", bezirk, [option.text for option in bezirk_options]
            )

        r = session.get(
            _API_URL.format(file="get_ortsteile.php"), params={"bez_id": bezirk_id}
        )
        r.raise_for_status()
        ortsteil_id = _resolve_js_id(r.text, ortsteil)
        if not ortsteil_id:
            raise SourceArgumentNotFoundWithSuggestions(
                "ortsteil", ortsteil, _js_options(r.text)
            )

        street_id = None
        if strasse is not None:
            r = session.get(
                _API_URL.format(file="get_strassen.php"),
                params={"ot_id": ortsteil_id.split("-")[0]},
            )
            r.raise_for_status()
            street_id = _resolve_js_id(r.text, strasse)
            if not street_id:
                raise SourceArgumentNotFoundWithSuggestions(
                    "strasse", strasse, _js_options(r.text)
                )

        responses = [self._calendar(session, year, bezirk_id, ortsteil_id, street_id)]
        if datetime.now().month >= 11:
            try:
                responses.append(
                    self._calendar(session, year + 1, bezirk_id, ortsteil_id, street_id)
                )
            except Exception:
                pass
        return responses

    @staticmethod
    def _calendar(session, year, bezirk_id, ortsteil_id, street_id):
        args = {
            "year": str(year),
            "ak_bezirk": bezirk_id,
            "ak_ortsteil": ortsteil_id,
            "alle_arten": "",
            "iCalEnde": 6,
            "iCalBeginn": 17,
        }
        if street_id is not None:
            args["ak_strasse"] = street_id
        r = session.post(_SERVLET, data=args)
        r.raise_for_status()
        return r

    def parse(self, raw, source=None):
        ics_parser = IcsParser()
        entries = []
        for response in raw:
            for date, label in ics_parser(response, source):
                entries.append((date, _SUFFIX_RE.sub("", label)))
        return entries

    # "Altpapier"/"Biomüll" resolve automatically (they're the canonical German
    # display names). The frequency/size-suffixed residual-waste variants and
    # the combined recycling label don't match the shared vocabulary verbatim,
    # so they're forced here; a genuinely uncategorisable special collection
    # ("Altreifen ...") is left to preserve verbatim rather than be guessed at.
    transform = ICSTransformer(
        type_value_map={
            "gelbe(r) tonne/sack": RECYCLABLES,
            "restmüll (3-wöchentlich)": GENERAL_WASTE,
            "restmüll 1,1 m³ (wöchentlich)": GENERAL_WASTE,
            "restmüll 1,1 m³ (2-wöchentlich)": GENERAL_WASTE,
            "restmüll 1,1 m³ (3-wöchentlich)": GENERAL_WASTE,
            "restmüll 1,1 m³ (4-wöchentlich)": GENERAL_WASTE,
            "schadstoffsammlung (achtung: nur selbstanlieferung)": HAZARDOUS,
        }
    )

    def __init__(self, bezirk: str, ortsteil: str, strasse: "str | None" = None):
        super().__init__(bezirk=bezirk, ortsteil=ortsteil, strasse=strasse)
