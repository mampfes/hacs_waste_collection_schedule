"""AWISTA LOGISTIK Stadt Remscheid (Monaloga online calendar).

Three requests, as in the legacy source: the year form (answered with the street
dropdown), then the chosen street's form, answered with a table of dated rows
("Montag, 05. Oktober 2026").
"""

import re
from datetime import date, datetime
from typing import ClassVar, final

from bs4 import BeautifulSoup
from waste_collection_schedule import recurrence, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street, text_field
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.field_terms import POSTCODE
from waste_collection_schedule.parsers import HtmlParser
from waste_collection_schedule.transformers import HtmlTransformer

API_URL = "https://www.monaloga.de/mportal/awista-logistik/stadt-remscheid/index.php"

_DATE = re.compile(r"(\d{1,2})\.\s*(\w+)\s+(\d{4})")


def _form(year: int, **extra: str) -> dict:
    return {
        "sessionid": "",
        "form_ident_source": "1",
        "year": year,
        "next": "Suchen",
        **extra,
    }


def _street_value(response, street: str, plz=None, **_) -> str:
    """The ``a_street`` form value of the first dropdown option that matches."""
    options = BeautifulSoup(response.text, "html.parser").select(
        "select[name=a_street] option"
    )
    wanted = street.lower().strip()
    zip_code = str(plz).strip() if plz else None
    for option in options:
        name = option.text.split("(")[0].lower().strip()
        if name == wanted and (not zip_code or zip_code in option.text):
            return str(option["value"]) + "|" + street.strip()
    raise SourceArgumentNotFoundWithSuggestions(
        "street",
        f"{street} ({plz})" if plz else street,
        sorted({o.text.strip() for o in options}),
    )


def _date(row) -> date:
    text = row.find_all("td")[0].get_text().split(",")[-1]
    match = _DATE.search(text)
    month = recurrence.month(match.group(2)) if match else None
    if match is None or month is None:
        raise ValueError(f"cannot read date: {text!r}")
    return date(int(match.group(3)), month, int(match.group(1)))


@final
class Source(BaseSource):
    TITLE = "AWISTA LOGISTIK Stadt Remscheid"
    DESCRIPTION = "Source for AWISTA LOGISTIK Stadt Remscheid."
    URL = "https://www.monaloga.de/"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [wt.RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "Adolf-Clarenbach-Straße 42899": {
            "street": "Adolf-Clarenbach-Straße",
            "plz": 42899,
        },
        "Alte Wendung": {"street": "Alte Wendung"},
    }

    PARAMS = (
        street(),
        text_field(
            "plz",
            term=POSTCODE,
            optional=True,
            coerce=lambda value: str(value).strip(),
        ),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street as listed at "
            "https://www.monaloga.de/mportal/awista-logistik/stadt-remscheid/index.php. "
            "Add the postcode (PLZ) if the street name occurs in several postcodes."
        ),
        "de": (
            "Geben Sie Ihre Straße so ein, wie sie im Online-Abfallkalender "
            "aufgeführt ist. Ergänzen Sie die PLZ, falls der Straßenname "
            "mehrfach vorkommt."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                API_URL,
                method="POST",
                data=lambda **_: _form(datetime.now().year, form_ident="0"),
                pick=_street_value,
            ),
        ),
        url=API_URL,
        method="POST",
        data=lambda street_value, **_: _form(
            datetime.now().year, form_ident="1", a_street=street_value
        ),
        raise_for_status=True,
    )
    parse = HtmlParser("#tab1 table tr")
    transform = HtmlTransformer(
        date_getter=_date,
        type_getter=lambda row: row.find_all("td")[-1].get_text().strip(),
        type_value_map={"Leichtverpackungen": wt.RECYCLABLES},
    )
