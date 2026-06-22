from typing import final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import cascading_select, text_field
from waste_collection_schedule.regions import Region, region
from waste_collection_schedule.service.AbfallIO import (
    SERVICE_MAP,
    AbfallIoParser,
    AbfallIoRetriever,
    list_choices,
)
from waste_collection_schedule.transformers import ICSTransformer

# Demonstrates: a fully declarative source over a stateful platform wizard. The
# AbfallPlus / abfall.io acquisition (POST "init" for a token, walk the kommune
# -> (bezirk) -> strasse -> (house number) cascade, POST "export_ics") and the
# response cleaning live in the service module as AbfallIoRetriever +
# AbfallIoParser, so this source only declares the pipeline; the German bin
# names are resolved by the shared multilingual vocabulary via ICSTransformer.
#
# The 4-level config wizard (kommune -> bezirk -> strasse -> house number, each
# fetched from the previous choice) is expressed with config_params.cascading_
# select: get_choices(field, selections) delegates to the service's list_choices,
# which walks the same form to list one level's options as (name, id) pairs, so
# the config flow shows names while storing the ids the fetch already uses.


@final
class Source(BaseSource):
    TITLE = "Abfall.IO / AbfallPlus"
    DESCRIPTION = (
        "Source for AbfallPlus.de waste collection. Service is hosted on abfall.io."
    )
    URL = "https://www.abfallplus.de"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True

    TEST_CASES = {
        "Landshut": {
            "key": "bd0c2d0177a0849a905cded5cb734a6f",
            "f_id_kommune": 2655,
            "f_id_bezirk": 2655,
            "f_id_strasse": 763,
        },
        "Schoenmackers": {
            "key": "e5543a3e190cb8d91c645660ad60965f",
            "f_id_kommune": 3682,
            "f_id_strasse": "3682adenauerplatz",
            "f_id_strasse_hnr": "20417",
        },
        "Ludwigshafen am Rhein": {
            "key": "6efba91e69a5b454ac0ae3497978fe1d",
            "f_id_kommune": "5916",
            "f_id_strasse": "5916abteistrasse",
            "f_id_strasse_hnr": 33,
        },
        "AWB Limburg-Weilburg": {
            "key": "0ff491ffdf614d6f34870659c0c8d917",
            "f_id_kommune": 6031,
            "f_id_strasse": 621,
            "f_id_strasse_hnr": 872,
            "f_abfallarten": [27, 28, 17, 67],
        },
        "Landkreis Prignitz, Gemeinde Karstädt, Blüthen": {
            "key": "798f59a75627f5d7686dab0c7226c877",
            "f_id_kommune": 3229,
            "f_id_bezirk": 31,
            "f_id_strasse": 322,
            "f_id_strasse_hnr": 323,
        },
        "Landkreis Prignitz, Gemeinde Karstädt, restliche Straßen": {
            "key": "798f59a75627f5d7686dab0c7226c877",
            "f_id_kommune": 3229,
            "f_id_bezirk": 41,
            "f_id_strasse": 333,
            "f_id_strasse_hnr": 333,
        },
    }

    PARAMS = [
        text_field("key", "Key"),
        cascading_select(
            ("f_id_kommune", "Kommune"),
            ("f_id_bezirk", "Bezirk"),
            ("f_id_strasse", "Straße"),
            ("f_id_strasse_hnr", "Hausnummer"),
        ),
        text_field("f_abfallarten", "Abfallarten", optional=True),
    ]

    retrieve = AbfallIoRetriever()
    parse = AbfallIoParser()
    transform = ICSTransformer()

    def __init__(
        self,
        key: str,
        f_id_kommune: int | str,
        f_id_strasse: int | str,
        f_id_bezirk: int | str | None = None,
        f_id_strasse_hnr: int | str | None = None,
        f_abfallarten: list[int] | None = None,
    ):
        super().__init__(
            key=key,
            f_id_kommune=f_id_kommune,
            f_id_strasse=f_id_strasse,
            f_id_bezirk=f_id_bezirk,
            f_id_strasse_hnr=f_id_strasse_hnr,
            f_abfallarten=f_abfallarten,
        )

    @staticmethod
    def REGIONS() -> list[Region]:
        return [
            region(s["title"], url=s["url"], key=s["service_id"]) for s in SERVICE_MAP
        ]

    @classmethod
    def get_choices(cls, field: str, selections: dict) -> list[tuple[str, str]]:
        """Options for one cascade level given the levels chosen so far.

        Implements the config_params.cascading_select contract. Returns
        (visible name, stored id) pairs walked live from the abfall.io form, or
        [] when this level does not apply to the current selections.
        """
        key = selections.get("key")
        if not key:
            return []
        return list_choices(str(key), field, selections)
