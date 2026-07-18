from typing import final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import area_id, municipality
from waste_collection_schedule.regions import region
from waste_collection_schedule.service.junker_app import (
    TYPE_VALUE_MAP,
    JunkerParser,
    JunkerRetriever,
)
from waste_collection_schedule.transformers import RowTransformer

TITLE = "Alia Servizi Ambientali S.p.A."
DESCRIPTION = "Source for Alia Servizi Ambientali S.p.A.."
URL = "https://www.aliaserviziambientali.it"
COUNTRY = "it"

HOWTO = {
    "en": (
        "Visit <https://www.aliaserviziambientali.it/it-it/raccolta-rifiuti> and "
        "select your municipality. If you see an embedded calendar you can just "
        "use the municipality name and leave the area empty. If you see a list "
        "of areas, follow the link to the area calendar; there you can find the "
        "area ID in the URL, for example: "
        "`https://differenziata.junker.app/embed/barberino-tavarnelle/area/67333/calendario` "
        "the area ID is `67333`."
    ),
    "it": (
        "Visita https://www.aliaserviziambientali.it/it-it/raccolta-rifiuti e "
        "seleziona il tuo comune. Se vedi un calendario incorporato, puoi "
        "semplicemente utilizzare il nome del comune e lasciare vuoto il campo "
        "dell'area. Se invece vedi un elenco di aree, devi seguire il link al "
        "calendario dell'area; lì puoi trovare l'ID dell'area nell'URL, ad "
        "esempio: https://differenziata.junker.app/embed/barberino-tavarnelle/"
        "area/67333/calendario l'ID dell'area è 67333."
    ),
}

TEST_CASES = {
    "Gambassi Terme": {"municipality": "Gambassi Terme"},
    "Barberino Tavarnelle Loc. San Donato": {
        "municipality": "Barberino Tavarnelle",
        "area": 67334,
    },
    "Arrighi, Castello, Lecore, San Mauro (centro storico), San Rocco, San Piero a Ponti e Sant'Angelo a Lecore": {
        "municipality": "Signa",
        "area": 11970,
    },
}

# Municipality -> known area ids, for providers where a municipality resolves
# to more than one collection zone. Also feeds JunkerRetriever's single-area
# fallback: a municipality listed here with exactly one area is retried with
# that area when an area-less fetch comes back empty.
MUNICIPALITIES_WITH_AREA = {
    "Bagno a Ripoli": [12035, 12036],
    "Barberino Tavarnelle": [67333, 67334],
    "Calenzano": [11887, 11886],
    "Carmignano": [11888, 11889],
    "Empoli": [11890, 11926, 11891],
    "Fiesole": [11905, 11906, 11907, 11908],
    "Figline e Incisa Valdarno": [11904, 11903],
    "Firenze": [12089, 12082],
    "Greve in Chianti": [12048, 12049, 12046, 12047],
    "Impruneta": [12054, 12068, 12053, 12055],
    "Marliana": [13016],
    "Montecatini Terme": [12037, 12038],
    "Pescia": [11959, 11963, 11960, 11964, 11961, 11965],
    "Pistoia": [
        12101,
        12729,
        12728,
        12103,
        12730,
        12731,
        13004,
        13005,
        12951,
        12954,
        12952,
        12953,
    ],
    "Poggio a Caiano": [11898, 11899],
    "Prato": [
        12007,
        12008,
        12009,
        12010,
        12011,
        12012,
        12013,
        12014,
        67812,
        12016,
        12030,
        12031,
        12032,
        12033,
        12034,
        12015,
        12025,
        12026,
        12027,
        12028,
        12029,
        12017,
        12018,
        12019,
        12020,
        12022,
        12021,
        12021,
        68415,
        12023,
        12024,
    ],
    "Sambuca Pistoiese": [13018, 13019],
    "San Casciano in Val di Pesa": [12057, 12058],
    "San Marcello Piteglio": [13020, 13021],
    "Scandicci": [
        11909,
        11911,
        11912,
        11913,
        11914,
        11915,
        11916,
        11917,
        11918,
        11919,
        11920,
        11921,
        11922,
    ],
    "Sesto Fiorentino": [11972, 11973],
    "Signa": [11970, 11969, 11971],
    "Vaiano": [11893, 11894],
}

MUNICIPALITIES_WITHOUT_AREA = [
    "Agliana",
    "Barberino di Mugello",
    "Borgo San Lorenzo",
    "Buggiano",
    "Campi Bisenzio",
    "Cantagallo",
    "Capraia e Limite",
    "Castelfiorentino",
    "Cerreto Guidi",
    "Certaldo",
    "Chiesina Uzzanese",
    "Fucecchio",
    "Gambassi Terme",
    "Lamporecchio",
    "Larciano",
    "Lastra a Signa",
    "Massa e Cozzile",
    "Monsummano Terme",
    "Montaione",
    "Montale",
    "Montelupo Fiorentino",
    "Montemurlo",
    "Montespertoli",
    "Pieve a Nievole",
    "Ponte Buggianese",
    "Quarrata",
    "Rignano sull'Arno",
    "Scarperia e San Piero",
    "Serravalle Pistoiese",
    "Uzzano",
    "Vaglia",
    "Vernio",
    "Vicchio",
    "Vinci",
]

MUNICIPALITIES = list(MUNICIPALITIES_WITH_AREA.keys()) + MUNICIPALITIES_WITHOUT_AREA


@final
class Source(BaseSource):
    TITLE = TITLE
    DESCRIPTION = DESCRIPTION
    URL = URL
    COUNTRY = COUNTRY
    HOWTO = HOWTO

    TEST_CASES = TEST_CASES

    PARAMS = (
        municipality(field="municipality"),
        area_id(field="area", optional=True),
    )

    REGIONS = tuple(region(mun, municipality=mun) for mun in MUNICIPALITIES)

    retrieve = JunkerRetriever(
        use_embed_url=True,
        area_is_name=False,
        municipalities_with_area=MUNICIPALITIES_WITH_AREA,
    )
    parse = JunkerParser()
    transform = RowTransformer(type_value_map=TYPE_VALUE_MAP)
