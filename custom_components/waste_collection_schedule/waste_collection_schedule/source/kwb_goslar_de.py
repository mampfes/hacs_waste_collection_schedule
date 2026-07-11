"""Kreiswirtschaftsbetriebe Goslar waste calendar (Sitepark IES platform).

A BaseSource pipeline with a source-defined ``retrieve()``. The shared
``SiteparkIESRetriever`` always resolves the pois via the street/Ort
autocomplete lookup, but this provider's legacy source also accepted a direct
``pois`` id (e.g. printed on a household's collection card) that bypasses that
lookup entirely. That is a genuinely irregular flow no configured retriever
expresses (a retriever is picked once, at class-definition time, and cannot
branch per request), so ``retrieve`` is overridden here: when ``pois`` is
supplied it is used directly; otherwise the street/Ort is resolved via the
shared client exactly as ``SiteparkIESRetriever`` would. Either way the method
returns the raw ICS response, so ``parse``/``transform`` stay declarative.
"""

from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    alternatives,
    district,
    street,
    text_field,
)
from waste_collection_schedule.service.SiteparkIES import SiteparkIES
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import ELECTRONICS, HAZARDOUS

_BASE_URL = "https://www.kwb-goslar.de"


@final
class Source(BaseSource):
    TITLE = "Kreiswirtschaftsbetriebe Goslar"
    DESCRIPTION = "Source for kwb-goslar.de waste collection."
    URL = _BASE_URL
    COUNTRY = "de"

    TEST_CASES: ClassVar[dict] = {
        "Berliner Straße (Clausthal-Zellerfeld)": {"pois": "2523.602"},
        "Braunschweiger Straße (Seesen)": {"pois": "2523.409"},
        "Marktstraße (Seesen)": {"strasse": "Marktstraße", "ort": "Seesen"},
    }

    PARAMS = (
        alternatives(
            [street("strasse")],
            [text_field("pois", label="POIS")],
        ),
        district("ort", optional=True),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street (optionally with the place to disambiguate), "
            "or a direct POIS id if you already have one."
        ),
        "de": (
            "Geben Sie Ihre Straße ein (optional mit Ort zur Eindeutigkeit), "
            "oder eine direkte POIS-ID, falls bereits bekannt."
        ),
    }

    RAISE_ON_EMPTY = True

    parse = parsers.IcsParser()
    # "Baum- und Strauchschnitt", "Biotonne", "Blaue Tonne", "Gelbe Tonne" and
    # "Restmülltonne" already auto-resolve against the shared vocabulary;
    # "Mobile Elektroaltgerätesammlung" and "Mobile Schadstoffsammlung" don't
    # match an alias exactly (the shared aliases don't carry the "Mobile ...
    # -sammlung" wording), so each needs an explicit map.
    transform = ICSTransformer(
        type_value_map={
            "Mobile Elektroaltgerätesammlung": ELECTRONICS,
            "Mobile Schadstoffsammlung": HAZARDOUS,
        }
    )

    def __init__(
        self,
        strasse: str | None = None,
        ort: str | None = None,
        pois: str | None = None,
    ):
        # validate() enforces the strasse-or-pois alternative via PARAMS.
        super().__init__(strasse=strasse, ort=ort, pois=pois)

    def retrieve(self, source):
        client = SiteparkIES(_BASE_URL)
        pois = source.params.get("pois")
        if not pois:
            pois = client.get_pois(
                strasse=source.params.get("strasse"),
                ort=source.params.get("ort"),
            )
        return client.fetch_ics_response(pois)
