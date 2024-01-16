#!/usr/bin/env python3

SERVICE_MAP = [
    {  # Blankenheim, 53945
        "hpid": 415,
        "realm": 41500,
        "name": "Blankenheim App - Müllkalender",
        "region": "Gemeinde Blankenheim",
        "icons": {
            "158": "mdi:package-variant",  # Altpapier
            "154": "mdi:leaf",  # Biomüll
            "159": "mdi:tree",  # Grüngut
            "157": "mdi:recycle",  # Leichtverpackungen
            "155": "mdi:trash-can",  # Restmüll
            "160": "mdi:truck-flatbed",  # Sondermüll
            "161": "mdi:truck-flatbed",  # Sondermüll Rewe-Parkplatz
        },
    },
    {
        "hpid": 95,
        "realm": 9501,
        "name": "www.lrasha.de - Müllkalender",
        "region": "Landkreis Schwäbisch Hall",
        "disabled": True,
        "icons": {
            "16": "mdi:trash-can",  # Bio- und Restmüllabfuhr (60 l/120 l/240 l/1,1 m³)
            "12": "mdi:recycle",  # Gelbe Säcke
            "14": "mdi:package-variant",  # Papiertonne
        },
    },
    {
        "hpid": 1,
        "realm": 100,
        "name": "www.buehlerzell.de - Müllkalender",
        "region": "Gemeinde Bühlerzell",
        "disabled": True,
        "icons": {
            "44": "mdi:trash-can",  # Bio- und Restmüllabfuhr (60 l/120 l/240 l/1,1 m³)
            "42": "mdi:recycle",  # Gelbe Säcke
            "43": "mdi:package-variant",  # Papiertonne
        },
    },
    {
        "hpid": 107,
        "realm": 10701,
        "name": "www.kressbronn.de - Müllkalender",
        "region": "Gemeinde Kressbronn am Bodensee",
        "disabled": True,
        "icons": {
            "47": "mdi:trash-can",  # Bio- und Restmüllabfuhr
            "46": "mdi:recycle",  # Gelbe Säcke
            "48": "mdi:package-variant",  # Papiertonne
        },
    },
    {
        "hpid": 168,
        "realm": 16801,
        "name": "www.hohenlohekreis.de - Müllkalender",
        "region": "Hohenlohekreis",
        "disabled": True,
        "icons": {
            "31": "mdi:leaf",  # Bioenergietonne
            "36": "mdi:pine-tree",  # Christbaumsammlung
            "30": "mdi:trash-can",  # Restmülltonne
            "33": "mdi:recycle",  # Wertstofftonne Altpapier
            "32": "mdi:package-variant",  # Wertstofftonne Verpackung
        },
    },
    {
        "hpid": 225,
        "realm": 22500,
        "name": "Deggenhausertal App - Müllkalender",
        "region": "Gemeinde Deggenhausertal",
        "icons": {
            "141": "mdi:nail",  # Altmetallsammlung Vereine
            "138": "mdi:leaf",  # Bioabfall 2-wöchentlich
            "139": "mdi:pine-tree",  # Christbaumsammlung
            "143": "mdi:tree",  # Gartenabfall
            "142": "mdi:recycle",  # Gelber Sack
            "146": "mdi:package-variant",  # Papier 4-wöchentlich
            "145": "mdi:package-variant",  # Papiercontainer 2-wöchentlich nur nach Anmeldung
            "140": "mdi:package-variant",  # Papiersammlung Vereine
            "144": "mdi:biohazard",  # Problemstoffsammlung
            "136": "mdi:trash-can",  # Restmüll 2-wöchentlich
            "137": "mdi:trash-can",  # Restmüll 4-wöchentlich
        },
    },
    {
        "hpid": 233,
        "realm": 23301,
        "name": "kraichtal.de - Müllkalender 1",
        "region": "Stadt Kraichtal",
        "disabled": True,
        "icons": {
            "19": "mdi:package-variant",  # Altpapier
            "21": "mdi:trash-can",  # Reststoff
            "25": "mdi:biohazard",  # Schadstoff
            "18": "mdi:recycle",  # Wertstoff
        },
    },
    {
        "hpid": 248,
        "realm": 24800,
        "name": "www.kappelrodeck.de - Müllkalender",
        "region": "Gemeinde Kappelrodeck",
        "disabled": True,
        "icons": {
            "75": "mdi:trash-can",  # Bio- und Restmüllabfuhr (60 l/120 l/240 l/1,1 m³)
            "73": "mdi:recycle",  # Gelbe Säcke
            "74": "mdi:package-variant",  # Papiertonne
        },
    },
    {
        "hpid": 331,
        "realm": 33100,
        "name": "www.schutterwald.de - Müllkalender",
        "region": "Gemeinde Schutterwald",
        "icons": {
            "67": "mdi:trash-can",  # Bio- und Restmüllabfuhr (60 l/120 l/240 l/1,1 m³)
            "65": "mdi:recycle",  # Gelbe Säcke
            "66": "mdi:package-variant",  # Papiertonne
        },
    },
    {
        "hpid": 374,
        "realm": 37401,
        "name": "www.aschheim.de - Müllkalender",
        "region": "Gemeinde Aschheim",
        "disabled": True,
        "icons": {
            "38": "mdi:leaf",  # Biomüll
            "147": "mdi:vacuum",  # Biotonnenreinigung
            "37": "mdi:recycle",  # Gelber Sack
            "41": "mdi:biohazard",  # Giftmobil
            "45": "mdi:tree",  # Häckselaktion
            "61": "mdi:package-variant",  # Papier Aschheim
            "165": "mdi:package-variant",  # Papier Dornach
            "39": "mdi:trash-can",  # Restmüll Nord
            "40": "mdi:trash-can",  # Restmüll Süd
            "68": "mdi:plus",  # Sonderleerung
        },
    },
    {
        "hpid": 390,
        "realm": 39000,
        "name": "Mittelbiberach App - Müllkalender",
        "region": "Gemeinde Mittelbiberach",
        "disabled": True,
        "icons": {
            "149": "mdi:trash-can",  # Bio- und Restmüllabfuhr
            "148": "mdi:recycle",  # Gelbe Säcke
            "150": "mdi:package-variant",  # Papiertonne
        },
    },
    {
        "hpid": 391,
        "realm": 39100,
        "name": "www.ehingen.de - Müllkalender",
        "region": "Stadt Ehingen",
        "disabled": True,
        "icons": {
            "116": "mdi:leaf",  # Biotonne
            "121": "mdi:package-variant",  # Blaue Tonne
            "117": "mdi:pine-tree",  # Christbaum
            "122": "mdi:tree",  # Gartenabraum
            "118": "mdi:recycle",  # Gelber Sack
            "123": "mdi:trash-can",  # Hausmüll
            "119": "mdi:package-variant",  # Vereinssammlung Papier
            "120": "mdi:package-variant",  # Vereinssammlung Papier und Kartonagen
        },
    },
    {
        "hpid": 420,
        "realm": 42000,
        "name": "Senden (Westfalen) App - Müllkalender",
        "region": "Gemeinde Senden (Westfalen)",
        "disabled": True,
        "icons": {
            "97": "mdi:leaf",  # Biotonne
            "95": "mdi:recycle",  # gelbe Tonne/säcke
            "102": "mdi:tree",  # Häcksler - Auf der Horst
            "99": "mdi:tree",  # Häcksler - Drachenwiese, Droste-zu-Senden-Str.
            "100": "mdi:tree",  # Häcksler - Gemeindl. Bauhof
            "101": "mdi:tree",  # Häcksler - Parkplatz Havixbecker Str.
            "98": "mdi:tree",  # Häcksler - Spielplatz Siebenstücken
            "96": "mdi:package-variant",  # Papiertonne
            "94": "mdi:trash-can",  # Restmülltonne
            "103": "mdi:biohazard",  # Schadstoffmobil
        },
    },
    {
        "hpid": 421,
        "realm": 42100,
        "name": "KEPTN App - Müllkalender",
        "region": "Stadt Emden",
        "disabled": True,
        "icons": {
            "56": "mdi:recycle",  # Gelber Sack (Gelbe Tonne)
            "57": "mdi:package-variant",  # Papier, Pappe, Karton (Blaue Tonne)
            "55": "mdi:trash-can",  # Restabfall (Graue Tonne)
        },
    },
    {
        "hpid": 424,
        "realm": 42400,
        "name": "Emmendingen App - Müllkalender",
        "region": "Stadt Emmendingen",
        "icons": {
            "79": "mdi:trash-can",  # Bio- und Restmüllabfuhr (60 l/120 l/240 l/1,1 m³)
            "77": "mdi:recycle",  # Gelbe Säcke
            "78": "mdi:package-variant",  # Papiertonne
        },
    },
    {
        "hpid": 426,
        "realm": 42600,
        "name": "DORFnet - Müllkalender",
        "region": "Gemeinde Kalletal",
        "icons": {
            "63": "mdi:package-variant",  # Blaue Altpapiertonne
            "124": "mdi:recycle",  # Gelbe Tonne
            "64": "mdi:trash-can",  # Graue Restmülltonne
            "69": "mdi:leaf",  # Grüne Biotonne
            "70": "mdi:leaf",  # Saisonbiotonne
            "71": "mdi:biohazard",  # Schadstoffsammlung
            "72": "mdi:baby",  # Windelsack
        },
    },
    {
        "hpid": 441,
        "realm": 44100,
        "name": "Messstetten App - Müllkalender",
        "region": "Stadt Messstetten",
        "icons": {
            "113": "mdi:package-variant",  # Altpapiersammlung
            "107": "mdi:package-variant",  # Altpapiertonne
            "106": "mdi:leaf",  # Biotonne
            "115": "mdi:pine-tree",  # Christbaumsammlung
            "108": "mdi:recycle",  # Gelber Sack
            "109": "mdi:tree",  # Grünabfall-Abfuhr
            "110": "mdi:fridge",  # Kühlgeräte, Bildschirme und Fernsehgeräte
            "104": "mdi:trash-can",  # Restmülltonne
            "105": "mdi:trash-can",  # Restmülltonne 1100 l
            "111": "mdi:biohazard",  # Schadstoffsammlung Gewerbe in der Kreismülldeponie
            "112": "mdi:biohazard",  # Schadstoffsammlung im Wertstoffzentrum
            "114": "mdi:nail",  # Schrottsammlung
        },
    },
    {
        "hpid": 447,
        "realm": 44700,
        "name": "Oberstadion App - Müllkalender",
        "region": "Gemeinde Oberstadion",
        "disabled": True,
        "icons": {
            "128": "mdi:tshirt-crew",  # Altkleider
            "133": "mdi:nail",  # Altmetall
            "162": "mdi:leaf",  # Bioabfalltonne
            "129": "mdi:package-variant",  # Blaue Tonne
            "130": "mdi:pine-tree",  # Christbaumabfuhr
            "132": "mdi:tree",  # Gartenabraum
            "127": "mdi:recycle",  # Gelber Sack
            "126": "mdi:trash-can",  # Hausmüll
            "131": "mdi:tree",  # Holzabfuhr
            "164": "mdi:biohazard",  # Problemstoffannahme im Entsorgungszentrum
            "135": "mdi:biohazard",  # Schadstoffmobil
            "134": "mdi:trash-can-outline",  # Sperrmüll
            "163": "mdi:package-variant",  # Straßensammlung Papier
        },
    },
]
