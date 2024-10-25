import json
import re
import unicodedata
from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

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


ICON_MAP = {
    "organic": "mdi:leaf",
    "paper": "mdi:package-variant",
    "light": "mdi:package-variant",
    "general": "mdi:trash-can",
    "bulky": "mdi:sofa",
    "plastic": "mdi:recycle",
    "glass": "mdi:bottle-wine",
    "napkins": "mdi:food",
}


class AreaNotFound(Exception):
    def __init__(self, areas: list[tuple[str, int]]):
        self.areas = areas
        super().__init__("Area not found")


class AreaRequired(AreaNotFound):
    ...


def replace_accents(text: str) -> str:
    # Normalize the text to NFD (Normalization Form Decomposition)
    normalized_text = unicodedata.normalize("NFD", text)

    # Filter out combining diacritical marks
    filtered_text = "".join(
        char for char in normalized_text if unicodedata.category(char) != "Mn"
    )

    # Normalize back to NFC (Normalization Form Composition)
    return unicodedata.normalize("NFC", filtered_text)


class Junker:
    def __init__(
        self,
        municipality: str,
        area: int | None = None,
        area_name: str | None = None,
        use_embed_url: bool = True,
        municipalities_with_area: dict[str, list[int]] = {},
    ):
        self._municipality: str = municipality
        self._area: int | None = area
        self._municipalities_with_area = municipalities_with_area
        self._area_name = area_name

        self._url = EMBED_URL if use_embed_url else PLAIN_URL
        self._area_url = EMBED_URL_WITH_AREA if use_embed_url else PLAIN_URL_WITH_AREA

    def fetch(self) -> list[Collection]:
        mun_str = replace_accents(
            self._municipality.lower().strip().replace(" ", "-").replace("'", "-")
        )
        if self._area:
            url = self._area_url.format(municipality=mun_str, area=self._area)
        else:
            url = self._url.format(municipality=mun_str)

        r = requests.get(url)
        r.raise_for_status()

        zone_match = ZONE_REGEX.search(r.text)

        if zone_match:
            zone_string = zone_match.group(1)
            zones = json.loads(zone_string)
            areas = [(zone["NOME"], zone["ID"]) for zone in zones]
            if not areas:
                raise ValueError("No areas found")

            if self._area_name:
                for area in areas:
                    if replace_accents(area[0]).lower().strip().replace(
                        " ", ""
                    ).replace(",", "").replace("'", "") == replace_accents(
                        self._area_name
                    ).lower().strip().replace(
                        " ", ""
                    ).replace(
                        ",", ""
                    ).replace(
                        "'", ""
                    ):
                        if self._area in (str(area[1]), area[1]):
                            raise ValueError("Something went wrong with the area")
                        self._area = area[1]
                        return self.fetch()

                raise AreaNotFound(areas)
            raise AreaRequired(areas)

        envents_match = EVENTS_REGEX.search(r.text)
        if not envents_match:
            raise ValueError("No events found maybe wrong/not supported municipality")
        events_string = envents_match.group(1)
        data = json.loads(events_string)

        entries = []
        for d in data:
            date = datetime.strptime(d["date"], "%Y-%m-%d").date()
            bin_type = d["vbin_desc"]
            icon = ICON_MAP.get(bin_type.lower().split()[0])  # Collection icon
            entries.append(Collection(date=date, t=bin_type, icon=icon))

        if not entries:
            muns = [
                m
                for m in self._municipalities_with_area
                if m.lower().replace(" ", "")
                == self._municipality.lower().replace(" ", "")
            ]
            mun = muns[0] if muns else self._municipality
            if (
                not self._area
                and mun in self._municipalities_with_area
                and len(self._municipalities_with_area[mun]) == 1
            ):
                # If municipality needs region but only one region is available use it
                self._area = self._municipalities_with_area[self._municipality][0]
                return self.fetch()
            raise ValueError("No collections found maybe you need to specify an area")

        return entries
