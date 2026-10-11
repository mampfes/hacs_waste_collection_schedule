from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    dropdown,
    service_id,
    street_address,
    text_field,
)
from waste_collection_schedule.regions import region
from waste_collection_schedule.service.Publidata import (
    TYPE_MAP,
    ScheduleExpander,
    calendar_retriever,
)
from waste_collection_schedule.transformers import ICSTransformer


@final
class Source(BaseSource):
    TITLE = "Publidata generic source"
    DESCRIPTION = "Publidata is a French public operator with a reach of up to 6M inhabitants. Check if your area is concerned on their website."
    URL = "https://www.publidata.io/fr/"
    COUNTRY = "fr"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.BULKY_WASTE,
        wt.GARDEN_WASTE,
        wt.GLASS,
        wt.PAPER,
        wt.ORGANIC,
    ]

    REGIONS = (
        region(
            "CA Saint Germain Boucles de Seine",
            url="https://www.saintgermainbouclesdeseine.fr/",
            instance_id=1420,
        ),
        region(
            "Grand Paris Seine et Oise",
            url="https://infos-dechets.gpseo.fr/",
            instance_id=1294,
        ),
        region(
            "Orléans Métropole",
            url="https://triermondechet.orleans-metropole.fr/",
            instance_id=100,
        ),
        region(
            "Tours Métropole", url="https://www.tours-metropole.fr/", instance_id=65
        ),
        region(
            "Saumur Val de Loire",
            url="https://www.saumurvaldeloire.fr/",
            instance_id=159,
        ),
        region(
            "Châteauroux Métropole",
            url="https://www.chateauroux-metropole.fr/",
            instance_id=897,
        ),
        region(
            "Saint Quentin en Yvelines",
            url="https://www.saint-quentin-en-yvelines.fr/",
            instance_id=701,
        ),
        region(
            "Versailles Grand Parc",
            url="https://www.versaillesgrandparc.fr/",
            instance_id=251,
        ),
        region(
            "Grand Paris Seine Ouest",
            url="https://www.dechets.seineouest.fr/",
            instance_id=101,
        ),
        region("ValEco", url="https://www.valeco41.fr/", instance_id=750),
        region("ValDem", url="https://www.valdem.fr/", instance_id=751),
        region(
            "Dreux Agglomération",
            url="https://www.dreux-agglomeration.fr/",
            instance_id=725,
        ),
        region(
            "Ardenne Métropole",
            url="https://www.ardenne-metropole.fr/",
            instance_id=670,
        ),
        region(
            "Dunkerque Grand Littoral",
            url="https://www.mesinfosdechets.cud.fr/",
            instance_id=673,
        ),
        region(
            "Grand Calais Terres et Mers",
            url="https://www.grandcalais.fr/",
            instance_id=679,
        ),
        region(
            "Métropole Européenne de Lille",
            url="https://www.lillemetropole.fr/",
            instance_id=876,
        ),
        region("Valcobreizh", url="https://dechets.valcobreizh.fr", instance_id=1003),
        region(
            "SIVOM Rive Droite",
            url="https://www.sivom-rivedroite.fr/",
            instance_id=1027,
        ),
        region(
            "Le Havre Seine Métropole",
            url="https://tripratik.lehavreseinemetropole.fr/",
            instance_id=1408,
        ),
        region(
            "Communauté de Communes Pévèle Carembault",
            url="https://www.pevelecarembault.fr/",
            instance_id=1141,
        ),
        region(
            "Métropole du Grand Nancy",
            url="https://mhdd.grandnancy.eu/",
            instance_id=1436,
        ),
        region("Le Cotentin", url="https://dechets.lecotentin.fr/", instance_id=1011),
        region(
            "SIAVED (Valenciennes Métropole)",
            url="https://www.siaved.fr/votre-calendrier-de-collecte",
            instance_id=1067,
        ),
        region(
            "Sud Sainte Baume",
            url="https://www.agglo-sudsaintebaume.fr/",
            instance_id=1483,
        ),
        region(
            "Agglo d'Agen",
            url="https://www.agglo-agen.net/vie-quotidienne/collecte-et-traitement-des-dechets/particuliers/calendriers-et-informations-collecte",
            instance_id=1264,
        ),
        region(
            "SICTOM du Marsan",
            url="https://sictomdumarsan.fr/la-collecte/mes-jours-de-collecte/",
            instance_id=158,
        ),
        region(
            "Valodev 18",
            url="https://valodev18.fr/la-collecte-des-vos-dechets/",
            instance_id=1619,
        ),
        region(
            "CA Sophia Antipolis",
            url="https://www.agglo-sophiaantipolis.fr/vivre-et-habiter/gerer-ses-dechets",
            instance_id=1398,
        ),
    )

    TEST_CASES: ClassVar[dict] = {
        "CASGBS, Le Pecq": {
            "address": "1 rue de Paris",
            "insee_code": "78481",
            "instance_id": 1420,
        },
        "GPSEO, Mantes la Ville": {
            "address": "11 rue Jean Moulin",
            "insee_code": "78362",
            "instance_id": 1294,
        },
        "Orleans Métropole, Boigny sur Bionne": {
            "address": "13 rue de la Commanderie",
            "insee_code": "45034",
            "instance_id": 100,
        },
        "Tours Métropole, Ballan-Miré": {
            "address": "3 Rue de Miré",
            "insee_code": "37018",
            "instance_id": 65,
        },
        "Grand Nancy, Laxou": {
            "address": "1 Rue de l'Embanie",
            "insee_code": "54304",
            "instance_id": 1436,
        },
        "Le Cotentin, Cherbourg-en-Cotentin": {
            "address": "435 rue Maxime-Laubeuf",
            "insee_code": "50129",
            "instance_id": 1011,
        },
        "SIAVED, Verchain-Maugré": {
            "address": "2 place du 8 mai",
            "insee_code": "59610",
            "instance_id": 1067,
        },
        "Sud Sainte Baume, Saint-Cyr-sur-Mer": {
            "address": "20 Rue Victor Hugo",
            "insee_code": "83112",
            "instance_id": 1483,
        },
        "Agglo d'Agen, Boé": {
            "address": "1 Rue de la Birade",
            "insee_code": "47031",
            "instance_id": 1264,
        },
        "SICTOM du Marsan, Mont-de-Marsan": {
            "address": "1 rue Impasse Henri IV",
            "insee_code": "40192",
            "instance_id": 158,
        },
        "Valodev 18, Vierzon": {
            "address": "1 Avenue du 8 Mai 1945",
            "insee_code": "18279",
            "instance_id": 1619,
        },
        "CASA Sophia Antipolis, Antibes (individual)": {
            "address": "10 rue de la République",
            "insee_code": "06004",
            "instance_id": 1398,
            "public_type": "individual_housing",
        },
        "CASA Sophia Antipolis, Valbonne (collective)": {
            "address": "10 rue Albert Einstein",
            "insee_code": "06152",
            "instance_id": 1398,
            "public_type": "collective_housing",
        },
        "Métropole Européenne de Lille, Provin": {  # codespell:ignore provin
            "address": "Rue Pierre Maille",
            "insee_code": "59477",
            "instance_id": 876,
        },
    }

    PARAMS = (
        street_address("address"),
        text_field("insee_code", "INSEE code"),
        service_id("instance_id"),
        dropdown(
            "public_type",
            ["individual_housing", "collective_housing"],
            label="Housing type",
            optional=True,
        ),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street address (number and street name only, without city "
            "or postcode). Find your commune's current INSEE code at "
            "https://www.insee.fr/fr/recherche/recherche-geographique; merged "
            "communes (communes nouvelles) have a new code. The `instance_id` is "
            "pre-filled when you select a known service provider; for an unlisted "
            "one, find it with the browser's network inspector on the provider's "
            "waste widget. `public_type` (`individual_housing` or "
            "`collective_housing`) is only needed where the schedules differ per "
            "housing type."
        ),
    }

    retrieve = calendar_retriever("publidata.io")
    parse = parsers.JsonParser()
    preprocess = ScheduleExpander()
    transform = ICSTransformer(type_value_map=TYPE_MAP)
