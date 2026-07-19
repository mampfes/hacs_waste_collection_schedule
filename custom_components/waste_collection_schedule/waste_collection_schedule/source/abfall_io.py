from typing import ClassVar, final

from waste_collection_schedule import field_terms
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    api_key,
    cascading_select,
    waste_types,
)
from waste_collection_schedule.regions import Region, region
from waste_collection_schedule.service.AbfallIO import (
    AbfallIoParser,
    AbfallIoRetriever,
    list_choices,
)
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GENERAL_WASTE,
    HAZARDOUS,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

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


# The provider registry for this one structure: each entry becomes a Region
# (a discoverable listing with its abfall.io key pre-filled). New providers are
# added here, in the source that owns them.
_PROVIDERS = [
    {
        "title": "EGST Steinfurt",
        "url": "https://www.egst.de/",
        "service_id": "e21758b9c711463552fb9c70ac7d4273",
    },
    {
        "title": "ALBA Berlin",
        "url": "https://berlin.alba.info/",
        "service_id": "9583a2fa1df97ed95363382c73b41b1b",
    },
    {
        "title": "ASO Abfall-Service Osterholz",
        "url": "https://www.aso-ohz.de/",
        "service_id": "040b38fe83f026f161f30f282b2748c0",
    },
    {
        "title": "Landkreis Bayreuth",
        "url": "https://www.landkreis-bayreuth.de/",
        "service_id": "951da001077dc651a3bf437bc829964e",
    },
    {
        "title": "Landkreis Calw",
        "url": "https://www.kreis-calw.de/",
        "service_id": "690a3ae4906c52b232c1322e2f88550c",
    },
    {
        "title": "Entsorgungsbetriebe Essen",
        "url": "https://www.ebe-essen.de/",
        "service_id": "9b5390f095c779b9128a51db35092c9c",
    },
    {
        "title": "Abfallwirtschaft Landkreis Freudenstadt",
        "url": "https://www.awb-fds.de/",
        "service_id": "595f903540a36fe8610ec39aa3a06f6a",
    },
    {
        "title": "Göttinger Entsorgungsbetriebe",
        "url": "https://www.geb-goettingen.de/",
        "service_id": "7dd0d724cbbd008f597d18fcb1f474cb",
    },
    {
        "title": "Landkreis Heilbronn",
        "url": "https://www.landkreis-heilbronn.de/",
        "service_id": "1a1e7b200165683738adddc4bd0199a2",
    },
    {
        "title": "Abfallwirtschaft Landkreis Kitzingen",
        "url": "https://www.abfallwelt.de/",
        "service_id": "594f805eb33677ad5bc645aeeeaf2623",
    },
    {
        "title": "Abfallwirtschaft Landkreis Landsberg am Lech",
        "url": "https://www.abfallberatung-landsberg.de/",
        "service_id": "7df877d4f0e63decfb4d11686c54c5d6",
    },
    {
        "title": "Stadt Landshut",
        "url": "https://www.landshut.de/",
        "service_id": "bd0c2d0177a0849a905cded5cb734a6f",
    },
    {
        "title": "Ludwigshafen am Rhein",
        "url": "https://www.ludwigshafen.de/",
        "service_id": "6efba91e69a5b454ac0ae3497978fe1d",
    },
    {
        "title": "MüllALARM / Schönmackers",
        "url": "https://www.schoenmackers.de/",
        "service_id": "e5543a3e190cb8d91c645660ad60965f",
    },
    {
        "title": "Abfallbewirtschaftung Ostalbkreis",
        "url": "https://www.goa-online.de/",
        "service_id": "3ca331fb42d25e25f95014693ebcf855",
    },
    {
        "title": "Landkreis Oldenburg",
        "url": "https://www.oldenburg-kreis.de/",
        "service_id": "27708a019a2e35de7eb4bbe7c851609f",
    },
    {
        "title": "Landkreis Ostallgäu",
        "url": "https://www.buerger-ostallgaeu.de/",
        "service_id": "342cedd68ca114560ed4ca4b7c4e5ab6",
    },
    {
        "title": "Rhein-Neckar-Kreis",
        "url": "https://www.rhein-neckar-kreis.de/",
        "service_id": "914fb9d000a9a05af4fd54cfba478860",
    },
    {
        "title": "Landkreis Rotenburg (Wümme)",
        "url": "https://lk-awr.de/",
        "service_id": "645adb3c27370a61f7eabbb2039de4f1",
    },
    {
        "title": "Landkreis Sigmaringen",
        "url": "https://www.landkreis-sigmaringen.de/",
        "service_id": "39886c5699d14e040063c0142cd0740b",
    },
    {
        "title": "Landratsamt Traunstein",
        "url": "https://www.traunstein.com/",
        "service_id": "279cc5db4db838d1cfbf42f6f0176a90",
    },
    {
        "title": "Landratsamt Unterallgäu",
        "url": "https://www.landratsamt-unterallgaeu.de/",
        "service_id": "c22b850ea4eff207a273e46847e417c5",
    },
    {
        "title": "AWB Westerwaldkreis",
        "url": "https://wab.rlp.de/",
        "service_id": "248deacbb49b06e868d29cb53c8ef034",
    },
    {
        "title": "Landkreis Limburg-Weilburg",
        "url": "https://www.awb-lm.de/",
        "service_id": "0ff491ffdf614d6f34870659c0c8d917",
    },
    {
        "title": "Landkreis Weißenburg-Gunzenhausen",
        "url": "https://www.landkreis-wug.de",
        "service_id": "31fb9c7d783a030bf9e4e1994c7d2a91",
    },
    {
        "title": "VIVO Landkreis Miesbach",
        "url": "https://www.vivowarngau.de/",
        "service_id": "4e33d4f09348fdcc924341bf2f27ec86",
    },
    {
        "title": "Abfallzweckverband Rhein-Mosel-Eifel (Landkreis Mayen-Koblenz)",
        "url": "https://www.azv-rme.de/",
        "service_id": "8303df78b822c30ff2c2f98e405f86e6",
    },
    {
        "title": "Team Orange (Landkreis Würzburg)",
        "url": "https://www.team-orange.info/",
        "service_id": "3701fd1ff111f63996ab46a448669ea3",
    },
    {
        "title": "Landkreis Cuxhaven",
        "url": "https://www.landkreis-cuxhaven.de/",
        "service_id": "49fe8a63a056adbfc43f051f61dd4a44",
    },
    {
        "title": "Landkreis Rottweil",
        "url": "https://landkreis-rottweil.de",
        "service_id": "d287412901d68d66825e588a60c94641",
    },
    {
        "title": "ASG Nordsachsen",
        "url": "https://www.asg-nordsachsen.de/",
        "service_id": "1d78841c5d7fc43ebe52b9dc01f6b962",
    },
    {
        "title": "AVR Kommunal, Rhein-Neckar-Kreis",
        "url": "https://www.avr-kommunal.de/",
        "service_id": "914fb9d000a9a05af4fd54cfba478860",
    },
    {
        "title": "AWG Abfallwirtschaft Landkreis Calw",
        "url": "https://www.awg-info.de/",
        "service_id": "0813ea99f520c462373386564a99a51e",
    },
    {
        "title": "Amt Bad Wilsnack/Weisen (Landkreis Prignitz)",
        "url": "https://www.landkreis-prignitz.de/",
        "service_id": "1e9592418582666e2a5d1c62b2683435",
    },
    {
        "title": "Gemeinde Groß Pankow (Landkreis Prignitz)",
        "url": "https://www.landkreis-prignitz.de/",
        "service_id": "af91b65d2753a219309072837d8ea4e1",
    },
    {
        "title": "Gemeinde Gumtow (Landkreis Prignitz)",
        "url": "https://www.landkreis-prignitz.de/",
        "service_id": "3cefa45ab357d231891bb497253c630f",
    },
    {
        "title": "Gemeinde Karstädt (Landkreis Prignitz)",
        "url": "https://www.landkreis-prignitz.de/",
        "service_id": "798f59a75627f5d7686dab0c7226c877",
    },
    {
        "title": "Amt Lenzen-Elbtalaue (Landkreis Prignitz)",
        "url": "https://www.landkreis-prignitz.de/",
        "service_id": "bb937857acd951dfc8de5be8b8a49f6d",
    },
    {
        "title": "Amt Meyenburg (Landkreis Prignitz)",
        "url": "https://www.landkreis-prignitz.de/",
        "service_id": "4638881e7bebe6869e2e86de5f8aa09e",
    },
    {
        "title": "Stadt Perleberg (Landkreis Prignitz)",
        "url": "https://www.landkreis-prignitz.de/",
        "service_id": "9fb3e2e5498e825250105ee272102a7b",
    },
    {
        "title": "Gemeinde Plattenburg (Landkreis Prignitz)",
        "url": "https://www.landkreis-prignitz.de/",
        "service_id": "a0461612534502273c518e28d4f6f1e4",
    },
    {
        "title": "Stadt Pritzwalk (Landkreis Prignitz)",
        "url": "https://www.landkreis-prignitz.de/",
        "service_id": "d92f59ef4066ae6d299478996d1d8430",
    },
    {
        "title": "Amt Putlitz/Berge (Landkreis Prignitz)",
        "url": "https://www.landkreis-prignitz.de/",
        "service_id": "4f06df48f154246415e57ce12b26abe5",
    },
    {
        "title": "Stadt Wittenberge (Landkreis Prignitz)",
        "url": "https://www.landkreis-prignitz.de/",
        "service_id": "b870ecfa6e1f882680758d374ba3fa2d",
    },
]


@final
class Source(BaseSource):
    TITLE = "Abfall.IO / AbfallPlus"
    DESCRIPTION = (
        "Source for AbfallPlus.de waste collection. Service is hosted on abfall.io."
    )
    URL = "https://www.abfallplus.de"
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

    PARAMS = (
        api_key("key"),
        cascading_select(
            ("f_id_kommune", field_terms.MUNICIPALITY),
            ("f_id_bezirk", field_terms.DISTRICT),
            ("f_id_strasse", field_terms.STREET),
            ("f_id_strasse_hnr", field_terms.HOUSE_NUMBER),
        ),
        waste_types("f_abfallarten"),
    )

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
            region(s["title"], url=s["url"], key=s["service_id"]) for s in _PROVIDERS
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
