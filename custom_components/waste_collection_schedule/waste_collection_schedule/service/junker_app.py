#!/usr/bin/env python3

import datetime
import json
import re
import unicodedata
from typing import TYPE_CHECKING, Any

from waste_collection_schedule.exceptions import (
    SourceArgumentException,
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequiredWithSuggestions,
)
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc
from waste_collection_schedule.waste_types import GENERAL_WASTE, GLASS, RECYCLABLES

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource

# Junker's raw ``vbin_desc`` labels the shared multilingual vocabulary
# (waste_types.resolve) does not already recognise verbatim (e.g. "Organic
# waste", "Paper", "Glass", "Plastic" all resolve on their own). Anything not
# listed here and not resolved falls back to waste_types.preserved(), so an
# unrecognised label is still shown (never silently dropped to OTHER) rather
# than mis-mapped by guesswork.
TYPE_VALUE_MAP = {
    "General waste collection": GENERAL_WASTE,
    "Glass/Cans": GLASS,
    "Plastic and metals": RECYCLABLES,
    "Light packaging": RECYCLABLES,
    "Plastic crates": RECYCLABLES,
}


EMBED_URL = "https://differenziata.junker.app/embed/{municipality}/calendario"
EMBED_URL_WITH_AREA = (
    "https://differenziata.junker.app/embed/{municipality}/area/{area}/calendario"
)
PLAIN_URL = "https://differenziata.junkerapp.it/{municipality}/calendario"
PLAIN_URL_WITH_AREA = (
    "https://differenziata.junkerapp.it/{municipality}/{area}/calendario"
)

EVENTS_REGEX = re.compile(r"var\s+events\s*=\s*(\[.*?\])\s*;")
ZONE_REGEX = re.compile(r"var\s+zone\s*=\s*(\[.*?\])\s*;")


def _replace_accents(text: str) -> str:
    normalized_text = unicodedata.normalize("NFD", text)
    filtered_text = "".join(
        char for char in normalized_text if unicodedata.category(char) != "Mn"
    )
    return unicodedata.normalize("NFC", filtered_text)


def _slugify(municipality: str) -> str:
    return _replace_accents(
        municipality.lower().strip().replace(" ", "-").replace("'", "-")
    )


def _normalize_area_name(name: str) -> str:
    return (
        _replace_accents(name)
        .lower()
        .strip()
        .replace(" ", "")
        .replace(",", "")
        .replace("'", "")
    )


# --------------------------------------------------------------------------- #
# Pipeline components (BaseSource architecture)
#
# Junker's ``/embed/{municipality}/calendario`` page embeds either a ``var
# events = [...]`` payload (the collection dates for one area) or, when the
# municipality has more than one collection zone and none was selected, a
# ``var zone = [...]`` payload listing the available areas. Resolving an area
# by *name* (the generic Junker APP source) means re-requesting the page with
# the matched area id; resolving by a known-*id* table (Alia Servizi
# Ambientali's municipality -> area-id map) means retrying once with the
# provider's only area when a first, area-less fetch comes back empty. Both
# flows are acquisition (HTTP + zone/event extraction), so they live in
# JunkerRetriever; JunkerParser does no I/O, it only turns the extracted raw
# ``events`` list into ``(date, label)`` rows.
# --------------------------------------------------------------------------- #


class JunkerRetriever(RetrieverFunc):
    """Resolve a municipality/area and return the raw ``events`` list.

    Args are the ``source.params`` field names holding the municipality and the
    area, plus the provider-specific shape of the ``area`` value:

    * ``use_embed_url``: ``differenziata.junker.app`` (True, Alia) vs
      ``differenziata.junkerapp.it`` (False, the generic Junker APP source).
    * ``area_is_name``: when True, ``area`` is a human-readable zone name that
      must be resolved against the page's ``var zone`` listing (the generic
      source's ``area`` argument). When False (default), ``area`` is used
      directly as the numeric area id in the URL (Alia's ``area`` argument).
    * ``municipalities_with_area``: an optional, provider-specific municipality
      -> [area id, ...] table. When a municipality resolves to exactly one
      area here, an empty area-less fetch is retried once with that area
      (Alia's static fallback for municipalities that require an area but
      only ever have one).
    """

    def __init__(
        self,
        municipality: str = "municipality",
        area: str = "area",
        use_embed_url: bool = True,
        area_is_name: bool = False,
        municipalities_with_area: "dict[str, list[int]] | None" = None,
    ):
        self.municipality = municipality
        self.area = area
        self.use_embed_url = use_embed_url
        self.area_is_name = area_is_name
        self.municipalities_with_area = municipalities_with_area or {}

    def __call__(self, source: "BaseSource") -> "list[dict[str, Any]]":
        params = source.params
        municipality_raw = params[self.municipality]
        area_value = params.get(self.area) or None

        area_id = None if self.area_is_name else area_value
        area_name = area_value if self.area_is_name else None

        return self._resolve(source, municipality_raw, area_id, area_name)

    def _resolve(
        self,
        source: "BaseSource",
        municipality_raw: str,
        area_id: Any,
        area_name: "str | None",
    ) -> "list[dict[str, Any]]":
        mun_str = _slugify(municipality_raw)
        url_tmpl = EMBED_URL if self.use_embed_url else PLAIN_URL
        area_url_tmpl = (
            EMBED_URL_WITH_AREA if self.use_embed_url else PLAIN_URL_WITH_AREA
        )

        url = (
            area_url_tmpl.format(municipality=mun_str, area=area_id)
            if area_id
            else url_tmpl.format(municipality=mun_str)
        )

        r = source.session.get(url)
        r.raise_for_status()

        zone_match = ZONE_REGEX.search(r.text)
        if zone_match:
            return self._resolve_zone(
                source, municipality_raw, zone_match.group(1), area_name
            )

        events_match = EVENTS_REGEX.search(r.text)
        if not events_match:
            raise SourceArgumentException(
                self.municipality,
                "No events found, the municipality may be wrong or unsupported.",
            )
        events: list[dict[str, Any]] = json.loads(events_match.group(1))

        if not events:
            fallback_area = self._single_area_fallback(municipality_raw, area_id)
            if fallback_area is not None:
                return self._resolve(source, municipality_raw, fallback_area, None)
            raise SourceArgumentException(
                self.area, "No collections found, you may need to specify an area."
            )

        return events

    def _resolve_zone(
        self,
        source: "BaseSource",
        municipality_raw: str,
        zone_string: str,
        area_name: "str | None",
    ) -> "list[dict[str, Any]]":
        zones = json.loads(zone_string)
        areas = [(zone["NOME"], zone["ID"]) for zone in zones]
        if not areas:
            raise SourceArgumentException(
                self.municipality, "No areas found for this municipality."
            )

        if area_name is not None:
            normalized_target = _normalize_area_name(area_name)
            for name, zone_id in areas:
                if _normalize_area_name(name) == normalized_target:
                    return self._resolve(source, municipality_raw, zone_id, None)
            raise SourceArgumentNotFoundWithSuggestions(
                self.area, area_name, [name for name, _ in areas]
            )

        raise SourceArgumentRequiredWithSuggestions(
            self.area,
            "required for this municipality",
            [name for name, _ in areas],
        )

    def _single_area_fallback(
        self, municipality_raw: str, area_id: Any
    ) -> "int | None":
        if area_id or not self.municipalities_with_area:
            return None
        matches = [
            m
            for m in self.municipalities_with_area
            if m.lower().replace(" ", "") == municipality_raw.lower().replace(" ", "")
        ]
        mun = matches[0] if matches else municipality_raw
        areas = self.municipalities_with_area.get(mun)
        if areas and len(areas) == 1:
            return areas[0]
        return None


class JunkerParser(Parser["list[tuple[datetime.date, str]]"]):
    """Decode the raw ``events`` list into ``(date, label)`` rows.

    Does no I/O, so it runs standalone against a cached ``events`` fixture.
    """

    def __call__(
        self,
        raw: "list[dict[str, Any]]",
        source: "BaseSource | None" = None,
    ) -> "list[tuple[datetime.date, str]]":
        from waste_collection_schedule import response_shape

        response_shape.expect(
            isinstance(raw, list),
            source_name=response_shape.source_name(source),
            detail="Junker response is not a list of events",
            raw=raw,
        )

        rows: list[tuple[datetime.date, str]] = []
        for event in raw:
            collection_date = datetime.datetime.strptime(
                event["date"], "%Y-%m-%d"
            ).date()
            rows.append((collection_date, event["vbin_desc"]))
        return rows
