"""OpenERZ collection calendars (Switzerland).

The public OpenERZ API (https://openerz.metaodi.ch) publishes iCal feeds for
Zürich and partner municipalities. Regions and collection areas are listed by
``/api/parameter/regions`` and ``/api/parameter/areas``; a postcode is required
for some regions (e.g. Zürich, Langnau) and unused for others (e.g. Basel).

The calendar is requested as ``/api/calendar.ics`` with a start/end window
computed from the calendar year (current year plus the next, when published).
No hard-coded year is used. A region's area list can be empty, in which case
the area dropdown is skipped.

Replaces the generic ICS YAML preset ``doc/ics/yaml/openerz_metaodi_ch.yaml``
(issue #5803). Existing configs that use the generic ``ics`` source with the
same calendar URL and params keep working; the named picker entry is retired.
"""

from __future__ import annotations

import re
from typing import ClassVar, final

from curl_cffi import requests as curl_requests
from waste_collection_schedule import field_terms, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import cascading_select, text_field
from waste_collection_schedule.service.ICS import IcsFeedsParser, IcsSessionRetriever
from waste_collection_schedule.transformers import ICSTransformer

_BASE_URL = "https://openerz.metaodi.ch"
_CALENDAR_URL = f"{_BASE_URL}/api/calendar.ics"
_REGIONS_URL = f"{_BASE_URL}/api/parameter/regions"
_AREAS_URL = f"{_BASE_URL}/api/parameter/areas"
_TIMEOUT = 30

# Display names for the slugs the API returns. Unlisted slugs stay title-cased.
_REGION_LABELS = {
    "adliswil": "Adliswil",
    "basel": "Basel",
    "bassersdorf": "Bassersdorf",
    "duebendorf": "Dübendorf",
    "embrach": "Embrach",
    "gossau-zh": "Gossau ZH",
    "hombrechtikon": "Hombrechtikon",
    "horgen": "Horgen",
    "kilchberg": "Kilchberg",
    "langnau": "Langnau",
    "oberrieden": "Oberrieden",
    "richterswil": "Richterswil",
    "rueschlikon": "Rüschlikon",
    "seon": "Seon",
    "stgallen": "St. Gallen",
    "thalwil": "Thalwil",
    "uster": "Uster",
    "waedenswil": "Wädenswil",
    "wangen-bruttisellen": "Wangen-Brüttisellen",
    "wetzikon": "Wetzikon",
    "wiesendangen": "Wiesendangen",
    "winterthur": "Winterthur",
    "zurich": "Zürich",
}


def _region_label(slug: str) -> str:
    return _REGION_LABELS.get(slug, slug.replace("-", " ").title())


def _clean_summary(summary: str) -> str:
    """Drop the ``, ZIP: …`` / ``, Area: …`` suffix the ICS summaries carry."""
    return re.sub(r",\s*(ZIP|Area):\s*.*$", "", summary).strip()


def _feed_params(
    region: str, year: int, zip: str | None = None, area: str | None = None, **_: object
) -> dict[str, str]:
    params = {
        "region": region,
        "start": f"{year}-01-01",
        "end": f"{year}-12-31",
        "sort": "date",
        "limit": "500",
    }
    if zip:
        params["zip"] = zip
    if area:
        params["area"] = area
    return params


def _session() -> curl_requests.Session:
    return curl_requests.Session(impersonate="chrome")


@final
class Source(BaseSource):
    TITLE = "OpenERZ"
    DESCRIPTION = (
        "Source for collection calendars published through the OpenERZ API "
        "(Zürich and partner municipalities)."
    )
    URL = _BASE_URL
    COUNTRY = "ch"
    SOURCE_CODEOWNERS: ClassVar[list[str]] = ["@bbr111"]
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.CARTONS,
        wt.GARDEN_WASTE,
        wt.BULKY_WASTE,
        wt.HAZARDOUS,
        wt.METAL,
        wt.OTHER,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Zürich 8048": {"region": "zurich", "zip": "8048", "area": "8048"},
        "Langnau 8135": {"region": "langnau", "zip": "8135"},
        "Wädenswil area C": {"region": "waedenswil", "area": "C"},
    }

    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unknown region": {"region": "nowhere"},
    }

    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            "Select your region. Enter a postcode if the region uses one "
            "(for example Zürich or Langnau); some regions such as Basel do "
            "not. Then pick a collection area if the region has any — the "
            "field is skipped when the API lists none."
        ),
        "de": (
            "Wählen Sie Ihre Region. Geben Sie eine Postleitzahl ein, wenn "
            "die Region eine verwendet (zum Beispiel Zürich oder Langnau); "
            "einige Regionen wie Basel tun das nicht. Anschließend wählen "
            "Sie ein Sammelgebiet, falls die Region welche anbietet — das "
            "Feld entfällt, wenn die API keines listet."
        ),
        "fr": (
            "Sélectionnez votre région. Saisissez un code postal si la région "
            "en utilise un (tels que Zurich ou Langnau) ; certaines "
            "régions comme Bâle n'en ont pas. Choisissez ensuite une zone de "
            "collecte si la région en propose — le champ est masqué lorsque "
            "l'API n'en liste aucune."
        ),
    }

    PARAMS = (
        cascading_select(
            ("region", field_terms.REGION),
            ("area", "Area"),
        ),
        text_field("zip", term=field_terms.POSTCODE, optional=True),
    )

    retrieve = IcsSessionRetriever(
        feed_url=_CALENDAR_URL,
        feed_params=_feed_params,
        lookahead_month=1,
        argument="region",
    )

    parse = IcsFeedsParser(parsers.IcsParser())

    transform = ICSTransformer(
        clean=_clean_summary,
        type_value_map={
            "General waste collection": wt.GENERAL_WASTE,
            "Organic waste collection": wt.ORGANIC,
            "Paper waste collection": wt.PAPER,
            "Cardboard waste collection": wt.CARTONS,
            "Chipping Service": wt.GARDEN_WASTE,
            "Bulky Goods waste collection": wt.BULKY_WASTE,
            "Special waste collection": wt.HAZARDOUS,
            "Metal waste collection": wt.METAL,
            "Incombustible waste collection": wt.OTHER,
            "Mobile": wt.OTHER,
        },
    )

    @classmethod
    def get_choices(
        cls, field: str, selections: dict[str, str]
    ) -> list[str] | list[tuple[str, str]]:
        """Region and area lists from the public OpenERZ parameter API."""
        session = _session()
        if field == "region":
            response = session.get(_REGIONS_URL, timeout=_TIMEOUT)
            response.raise_for_status()
            slugs = response.json().get("result") or []
            return [(_region_label(slug), slug) for slug in slugs]
        if field == "area":
            region = selections.get("region")
            if not region:
                return []
            response = session.get(
                _AREAS_URL, params={"region": region}, timeout=_TIMEOUT
            )
            response.raise_for_status()
            rows = response.json().get("result") or []
            areas: list[str] = []
            for row in rows:
                area = row.get("area") if isinstance(row, dict) else row
                if area is not None and str(area) not in areas:
                    areas.append(str(area))
            return areas
        return []
