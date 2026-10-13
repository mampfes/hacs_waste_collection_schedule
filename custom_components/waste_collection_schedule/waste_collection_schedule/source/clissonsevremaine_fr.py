from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import municipality
from waste_collection_schedule.regions import Region
from waste_collection_schedule.service.Calendarize import (
    CALENDAR_URL,
    COMMUNES,
    CalendarParser,
    CalendarRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Clisson Sèvre et Maine Agglo"
    DESCRIPTION = "Source for Clisson Sèvre et Maine Agglo, the inter-municipal authority responsible for waste collection in 18 municipalities of the Loire-Atlantique department, France."
    URL = "https://environnement.clissonsevremaine.fr"
    COUNTRY = "fr"
    TEST_CASES: ClassVar[dict] = {
        "Gorges": {"commune": "Gorges"},
        "Maisdon-sur-Sèvre - zone 1": {"commune": "Maisdon-sur-Sèvre - zone 1"},
        "La Haye-Fouassière - Zone B": {"commune": "La Haye-Fouassière - Zone B"},
        "Clisson, rue Saint-Antoine": {"commune": "clisson, rue saint-antoine"},
    }
    SOURCE_CODEOWNERS: ClassVar[list[str]] = ["@JeyMuller"]
    HOWTO: ClassVar[dict[str, str]] = {
        "en": f"Open {CALENDAR_URL} and pick your municipality in the drop-down menu. Use the wording shown there. Some municipalities are split into several collection zones; the maps at the end of the downloadable PDF calendars tell you which zone your street belongs to.",
        "fr": f"Ouvrez {CALENDAR_URL} et choisissez votre commune dans la liste déroulante. Reprenez le libellé affiché. Certaines communes sont découpées en plusieurs zones de collecte ; les cartes situées à la fin des calendriers PDF téléchargeables indiquent la zone de votre rue.",
    }
    PARAMS = (municipality("commune"),)
    REGIONS = tuple(
        Region(
            title=commune,
            url="https://environnement.clissonsevremaine.fr",
            params={"commune": commune},
        )
        for commune in COMMUNES
    )

    retrieve = CalendarRetriever()
    parse = CalendarParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={
            "Ordures ménagères": wt.GENERAL_WASTE,
            "Emballages": wt.RECYCLABLES,
        },
    )
