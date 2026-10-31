import datetime
import json
import logging
import time

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

_LOGGER = logging.getLogger(__name__)

TITLE = "Hygea"
DESCRIPTION = "Source for Hygea garbage collection"
URL = "https://www.hygea.be/"
TEST_CASES = {
    "Soignies": {"streetIndex": "3758"},
    "Frameries": {"streetIndex": "4203"},
    "Erquelinnes": {"cp": "6560"},
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "This source is deprecated and will be removed in the next major release: "
        "Hygea's relaunched website no longer serves the calendar it reads and "
        "shows the Recycle! calendar instead. Use the recycleapp_be source "
        "(Recycle!) with your postcode, street and house number as on "
        "https://www.recycleapp.be."
    ),
    "fr": (
        "Cette source est obsolète et sera supprimée dans la prochaine version "
        "majeure : le nouveau site de Hygea ne fournit plus le calendrier qu'elle "
        "lit et affiche le calendrier Recycle! à la place. Utilisez la source "
        "recycleapp_be (Recycle!) avec votre code postal, votre rue et votre "
        "numéro comme sur https://www.recycleapp.be."
    ),
}

WASTE_MAP = {
    "om": {"type": "Ordures ménagères", "icon": "mdi:trash-can"},
    "pmc": {"type": "PMC", "icon": "mdi:recycle"},
    "sacvert": {"type": "Déchets Organiques", "icon": "mdi:trash-can"},
    "fourth": {"type": "Papier & cartons", "icon": "mdi:leaf"},
}


class Source:
    def __init__(self, streetIndex=None, cp=None):
        _LOGGER.warning(
            "The hygea_be source is deprecated and will be removed in the next "
            "major release. Hygea's relaunched website no longer serves the "
            "calendar this source reads (displaycal.html now returns a web page) "
            "and shows the Recycle! calendar instead. Use source 'recycleapp_be' "
            "with your postcode, street and house_number. See "
            "https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/hygea_be.md"
        )
        self._street_index = streetIndex
        self._cp = cp

    def fetch(self):
        params = {"start": int(time.time()), "end": int(time.time() + 2678400)}
        if self._street_index is not None:
            params["street"] = self._street_index
            response = requests.get(
                "https://www.hygea.be/displaycal.html", params=params
            )
        elif self._cp is not None:
            params["street"] = self._cp
            response = requests.get(
                "https://www.hygea.be/displaycalws.html", params=params
            )
        response.raise_for_status()
        data = json.loads(response.text)

        entries = []
        for day in data:
            date = datetime.datetime.strptime(
                day["start"], "%Y-%m-%dT%H:%M:%S%z"
            ).date()

            # example for day["className"]: 12  notadded pos136 om multi
            waste_types = set(day["className"].split())
            for abbr, map in WASTE_MAP.items():
                if abbr in waste_types:
                    c = Collection(date=date, t=map["type"], icon=map["icon"])
                    entries.append(c)

        return entries
