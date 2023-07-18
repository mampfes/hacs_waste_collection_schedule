#!/usr/bin/env python3


SERVICE_MAP = [
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
        "title": "Abfallwirtschaft Landkreis Böblingen",
        "url": "https://www.awb-bb.de/",
        "service_id": "8215c62763967916979e0e8566b6172e",
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
        "title": "AWB Landkreis Göppingen",
        "url": "https://www.awb-gp.de/",
        "service_id": "365d791b58c7e39b20bb8f167bd33981",
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
        "title": "Abfallwirtschaft Ortenaukreis",
        "url": "https://www.abfallwirtschaft-ortenaukreis.de/",
        "service_id": "bb296b78763112266a391990f803f032",
    },
    {
        "title": "Abfallbewirtschaftung Ostalbkreis",
        "url": "https://www.goa-online.de/",
        "service_id": "3ca331fb42d25e25f95014693ebcf855",
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
        "service_id": "31fb9c7d783a030bf9e4e1994c7d2a91"
    },
    {
        "title": "VIVO Landkreis Miesbach",
        "url": "https://www.vivowarngau.de/",
        "service_id": "4e33d4f09348fdcc924341bf2f27ec86"
    },
    {
        "title":"Abfallzweckverband Rhein-Mosel-Eifel (Landkreis Mayen-Koblenz)",
        "url": "https://www.azv-rme.de/",
        "service_id": "8303df78b822c30ff2c2f98e405f86e6"
    }
]
