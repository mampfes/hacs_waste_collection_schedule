"""AWM München, Germany.

Demonstrates: a large, genuinely branching TYPO3 form wizard. Posting the
address may return the ICS download link directly, or the site may first
need a location id per waste-stream (when an address has more than one
container location) and/or a collection-cycle string per waste-stream (when a
stream can be emptied on more than one schedule) -- each a separate POST only
required when the previous response's HTML contains that stream's <select>.
That branching, and the "one response can carry several `a.downloadics` links
to fetch and merge", is
:class:`~waste_collection_schedule.service.AwmMuenchen.CollectionCalendarRetriever`,
so this source is a declarative composition of it with ``EachResponse``.
"""

from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, street, text_field
from waste_collection_schedule.service.AwmMuenchen import (
    DOMAIN,
    CollectionCalendarRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GENERAL_WASTE,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)


def _clean_label(label: str) -> str:
    return label.split(",")[0].replace("Achtung:", "").strip()


@final
class Source(BaseSource):
    TITLE = "AWM München"
    DESCRIPTION = "Source for AWM München."
    URL = DOMAIN
    COUNTRY = "de"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Waltenbergerstr. 1": {
            "street": "Waltenbergerstr.",
            "house_number": "1",
        },
        "Geretsrieder Str. 10a": {
            "street": "Geretsrieder Str.",
            "house_number": "10a",
        },
        "Bellinzonastraße 19": {
            "street": "Bellinzonastr.",
            "house_number": "19",
            "r_location_id": "70050134",
            "b_location_id": "70050134",
            "p_location_id": "70050134",
        },
        "Marienplatz 1": {
            "street": "Marienplatz",
            "house_number": "1",
            "r_collection_cycle_string": "001;U",
            "p_collection_cycle_string": "002;U",
        },
    }

    PARAMS = (
        street(field="street"),
        house_number(field="house_number"),
        text_field("r_location_id", "Residual waste location ID", optional=True),
        text_field("b_location_id", "Organic waste location ID", optional=True),
        text_field("p_location_id", "Paper location ID", optional=True),
        text_field(
            "r_collection_cycle_string",
            "Residual waste emptying cycle",
            optional=True,
        ),
        text_field(
            "b_collection_cycle_string", "Organic waste emptying cycle", optional=True
        ),
        text_field("p_collection_cycle_string", "Paper emptying cycle", optional=True),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Fill in the street and house number, then submit. If the address "
            "has more than one container location or emptying cycle per "
            "waste stream, the fetch error lists the valid values to enter "
            "for the corresponding *_location_id / *_collection_cycle_string "
            "argument."
        ),
        "de": (
            "Straße und Hausnummer ausfüllen, dann abschicken. Falls die "
            "Adresse mehrere Standorte oder Leerungszyklen pro Abfallart "
            "hat, listet die Fehlermeldung die gültigen Werte für das "
            "jeweilige Argument *_location_id / *_collection_cycle_string auf."
        ),
        "it": (
            "Compilare la via e il numero civico, quindi inviare. Se "
            "l'indirizzo ha più posizioni del contenitore o cicli di "
            "svuotamento per flusso di rifiuti, l'errore elenca i valori "
            "validi per l'argomento *_location_id / *_collection_cycle_string."
        ),
        "fr": (
            "Remplir la rue et le numéro, puis envoyer. Si l'adresse a "
            "plusieurs emplacements de conteneur ou cycles de vidage par "
            "flux de déchets, l'erreur liste les valeurs valides pour "
            "l'argument *_location_id / *_collection_cycle_string concerné."
        ),
    }

    transform = ICSTransformer(
        clean=_clean_label,
        type_value_map={
            "Restmülltonne": GENERAL_WASTE,
            "Biotonne": ORGANIC,
            "Papiertonne": PAPER,
            "Wertstofftonne": RECYCLABLES,
        },
    )

    def __init__(
        self,
        street: str,
        house_number: str,
        r_location_id: str = "",
        b_location_id: str = "",
        p_location_id: str = "",
        r_collection_cycle_string: str = "",
        b_collection_cycle_string: str = "",
        p_collection_cycle_string: str = "",
    ):
        super().__init__(
            street=street,
            house_number=house_number,
            r_location_id=r_location_id,
            b_location_id=b_location_id,
            p_location_id=p_location_id,
            r_collection_cycle_string=r_collection_cycle_string,
            b_collection_cycle_string=b_collection_cycle_string,
            p_collection_cycle_string=p_collection_cycle_string,
        )

    retrieve = CollectionCalendarRetriever()

    # One response per waste stream's ICS download link.
    parse = parsers.EachResponse(parsers.IcsParser())
