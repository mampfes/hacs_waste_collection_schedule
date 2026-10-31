from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    customer_number,
    street_address,
    text_field,
)
from waste_collection_schedule.service.CgiMinaSidor import (
    TYPE_VALUE_MAP,
    CgiMinaSidorParser,
    CgiMinaSidorRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Gästrike Återvinnare"
    DESCRIPTION = "Source for Gästrike Återvinnare waste collection"
    URL = "https://minasidor.gastrikeatervinnare.se/"
    COUNTRY = "se"
    RAISE_ON_EMPTY = True
    SOURCE_CODEOWNERS: ClassVar[list] = ["@emiltorp"]

    WASTE_TYPES: ClassVar[list] = [
        wt.FOOD_WASTE,
        wt.GENERAL_WASTE,
        wt.OTHER,
        wt.PAPER,
        wt.PLASTIC,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Mina sidor": {
            "customer_number": "!secret gastrikeatervinnare_se_customer_number",
            "password": "!secret gastrikeatervinnare_se_password",
        },
    }

    PARAMS = (
        customer_number(),
        text_field("password", "Password"),
        street_address(optional=True),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Gästrike Återvinnare no longer publishes collection days openly; they "
            "are shown on Mina sidor (https://minasidor.gastrikeatervinnare.se) "
            "after login. Enter the customer number and password you log in with "
            "there (BankID login is not supported: create a password via 'Glömt "
            "lösenord' on the login page). If the account has bins at several "
            "addresses, enter one as shown on Mina sidor, e.g. 'Storgatan 1, "
            "GÄVLE'; otherwise leave the address empty."
        ),
    }

    retrieve = CgiMinaSidorRetriever("https://minasidor.gastrikeatervinnare.se")
    parse = CgiMinaSidorParser(address="address")
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        # Plastic packaging is a bin of its own here, next to the paper one.
        type_value_map={**TYPE_VALUE_MAP, "Plastförpackningar": wt.PLASTIC},
        carry_raw_label=True,
    )
