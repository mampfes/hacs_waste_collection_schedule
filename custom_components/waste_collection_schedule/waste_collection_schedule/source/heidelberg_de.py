from typing import ClassVar, final

from waste_collection_schedule import parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import boolean, street
from waste_collection_schedule.service import HeidelbergDatenplattform as hd
from waste_collection_schedule.transformers import ICSTransformer


@final
class Source(BaseSource):
    TITLE = "Heidelberg"
    DESCRIPTION = "Support for the waste collection schedule provided by the Office of Waste Management and Municipal Cleansing Heidelberg"
    URL = "https://www.heidelberg.de/abfall"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Typical street": {"street": "Alte Bergheimer Straße"},
        "No weekly collection of residual and bio waste possible": {
            "street": "Molkenkurweg"
        },
        "Bi-weekly residual collection as option - uneven street number": {
            "street": "Alte Bergheimer Straße",
            "collect_residual_waste_weekly": False,
            "even_house_number": False,
        },
        "Bi-weekly residual collection as option - even street number": {
            "street": "Alte Bergheimer Straße",
            "collect_residual_waste_weekly": False,
            "even_house_number": True,
        },
    }

    PARAMS = (
        street("street"),
        boolean(
            "collect_residual_waste_weekly",
            "Weekly residual waste collection",
            default=True,
        ),
        boolean(
            "even_house_number",
            "House number to collect from is even",
            default=False,
        ),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street exactly as listed on heidelberg.de/abfall. Where "
            "the street allows a fortnightly residual waste round, switch off "
            "`collect_residual_waste_weekly` and state whether your house number "
            "is even."
        ),
        "de": (
            "Geben Sie die Straße exakt so an, wie sie auf heidelberg.de/abfall "
            "aufgeführt ist. Wenn für die Straße eine 14-tägige Restmüllabfuhr "
            "möglich ist, deaktivieren Sie `collect_residual_waste_weekly` und "
            "geben Sie an, ob Ihre Hausnummer gerade ist."
        ),
    }

    retrieve = retrievers.HttpGetRetriever(
        url=hd.COLLECTIONS_URL,
        params=lambda street, **_: {"street": street},
    )
    parse = parsers.ArgumentGuard(
        parsers.JsonParser(),
        argument="street",
        matches=hd.has_collections,
        suggestions=retrievers.Suggestions(hd.STREETS_URL, pick=hd.street_names),
    )
    preprocess = hd.ScheduleExpander()
    transform = ICSTransformer(
        type_value_map={
            "bio": wt.ORGANIC,
            "dsd": wt.RECYCLABLES,
            "paper": wt.PAPER,
            "rest": wt.GENERAL_WASTE,
            "christmas": wt.GARDEN_WASTE,
        }
    )
