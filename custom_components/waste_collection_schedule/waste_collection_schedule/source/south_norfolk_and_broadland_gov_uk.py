import json
from typing import ClassVar, final
from urllib.parse import quote

from bs4 import BeautifulSoup
from waste_collection_schedule import date_parsers, regions, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    alternatives,
    postcode,
    raw_object,
    street_address,
)
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.service.HtmlForms import FormStep, HtmlFormRetriever
from waste_collection_schedule.service.MyArea import (
    CALENDAR_HOST,
    MyAreaParser,
    calendar_uprn,
)
from waste_collection_schedule.transformers import JsonTransformer

_BASE = "https://area.southnorfolkandbroadland.gov.uk/"
_NS = "http://webaspx-collections.azurewebsites.net/"


def _comparable(value):
    return str(value).replace(",", "").replace(" ", "").lower()


def _token(response):
    tag = BeautifulSoup(response.text, "html.parser").select_one(
        'input[name="__RequestVerificationToken"]'
    )
    if tag is None or not tag.get("value"):
        raise ValueError("Missing My Area verification token")
    return str(tag["value"])


def _select(response, postcode, address, **_):
    page = BeautifulSoup(response.text, "html.parser")
    options = page.select("select#UprnAddress option")
    if not options:
        raise SourceArgumentNotFound("postcode", postcode)
    wanted, code = _comparable(address), _comparable(postcode)
    for option in options:
        if _comparable(option.get_text()) in (wanted, wanted.replace(code, "")):
            return {
                "Postcode": code,
                "__RequestVerificationToken": _token(response),
                "UprnAddress": str(option["value"]),
            }
    raise SourceArgumentNotFoundWithSuggestions(
        "address", address, [option.get_text() for option in options]
    )


def _soap(target, context, **_):
    return (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
        ' xmlns:xsd="http://www.w3.org/2001/XMLSchema"'
        ' xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">'
        "<soap:Body>" + f'<getRoundCalendarForUPRN xmlns="{_NS}">'
        "<council>SNO</council><webServicePassword></webServicePassword>"
        "<username></username><usernamePassword></usernamePassword>"
        f"<UPRN>{target}</UPRN><from>Chtml</from></getRoundCalendarForUPRN>"
        "</soap:Body></soap:Envelope>"
    ).encode("utf-8")


def _targets(source, response):
    uprn = calendar_uprn(response)
    return [uprn] if uprn is not None else []


@final
class Source(BaseSource):
    TITLE = "Broadland District Council"
    DESCRIPTION = "Source for southnorfolkandbroadland.gov.uk services for South Norfolk and Broadland, UK"
    URL = "https://area.southnorfolkandbroadland.gov.uk/"
    REGIONS = (
        regions.region(
            "South Norfolk Council", url="https://southnorfolkandbroadland.gov.uk/"
        ),
    )
    TEST_CASES: ClassVar[dict] = {
        "Broadland residential address - UPRN payload": {
            "address_payload": {
                "Uprn": "010014355477",
                "Address": "29 Mallard Way, Sprowston, Norwich, Norfolk, NR7 8DN",
                "X": "626227.00000",
                "Y": "312136.00000",
                "Ward": "Sprowston East",
                "Parish": "Sprowston",
                "Village": "Sprowston",
                "Street": "Mallard Way",
                "Authority": "2610",
            }
        },
        "Broadland residential address - postcode": {
            "postcode": "NR7 8DN",
            "address": "29 Mallard Way, Sprowston, Norfolk, NR7 8DN",
        },
        "South Norfolk residential address - UPRN payload": {
            "address_payload": {
                "Uprn": "002630130840",
                "Address": "1 Brindle Drive, Mulbarton, Norfolk, NR14 8BX",
                "X": "619142.00000",
                "Y": "300585.00000",
                "Ward": "Mulbarton And Stoke Holy Cross",
                "Parish": "Mulbarton",
                "Village": "Mulbarton",
                "Street": "Brindle Drive",
                "Authority": "2630",
            }
        },
        "South Norfolk residential address - postcode": {
            "postcode": "NR14 8BX",
            "address": "1 Brindle Drive, Mulbarton, Norfolk, NR14 8BX",
        },
        "Broadland business address (Tesco) - UPRN payload": {
            "address_payload": {
                "Uprn": "100091575309",
                "Address": "Tesco Stores Ltd, Blue Boar Lane, Sprowston, Norwich, Norfolk, NR7 8AB",
                "X": "625657.00000",
                "Y": "312146.00000",
                "Ward": "Sprowston East",
                "Parish": "Sprowston",
                "Village": "Sprowston",
                "Street": "Blue Boar Lane",
                "Authority": "2610",
            }
        },
    }
    COUNTRY = "uk"
    PARAMS = (
        alternatives(
            [raw_object("address_payload", "My Area address payload", optional=False)],
            [postcode(), street_address()],
        ),
    )
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
        wt.FOOD_WASTE,
    ]
    HOWTO: ClassVar[dict] = {
        "en": "Enter the postcode and address from My Area, or supply the address_payload object from its MyArea.Data cookie. Since the v3 pipeline migration, waste types use canonical, localised names; update filters, automations and customisations using the old labels."
    }
    retrieve = retrievers.FanOutRetriever(
        prepare=retrievers.SelectRetriever(
            lambda source: (
                "payload" if source.params.get("address_payload") else "address"
            ),
            {
                "payload": retrievers.Request(
                    _BASE,
                    headers=lambda address_payload, **_: {
                        "Cookie": f"MyArea.Data={quote(json.dumps(address_payload))}"
                    },
                ),
                "address": HtmlFormRetriever(
                    _BASE + "FindAddress",
                    steps=(
                        FormStep(
                            form='input[name="__RequestVerificationToken"]',
                            argument="postcode",
                            fields=lambda response, postcode, **_: {
                                "Postcode": _comparable(postcode),
                                "__RequestVerificationToken": _token(response),
                            },
                        ),
                        FormStep(
                            form="select#UprnAddress",
                            argument="address",
                            fields=_select,
                        ),
                    ),
                ),
            },
        ),
        targets=_targets,
        include_prepared=True,
        fetch=retrievers.Request(
            f"https://{CALENDAR_HOST}/WSCollExternal.asmx",
            method="POST",
            data=_soap,
            headers={
                "Content-Type": "text/xml; charset=utf-8",
                "SOAPAction": f'"{_NS}getRoundCalendarForUPRN"',
            },
        ),
    )
    parse = MyAreaParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        parse_date=date_parsers.auto,
        type_value_map={
            "Rubbish": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Garden (if applicable)": wt.GARDEN_WASTE,
            "Garden": wt.GARDEN_WASTE,
            "Food": wt.FOOD_WASTE,
            "Ref": wt.GENERAL_WASTE,
            "Rec": wt.RECYCLABLES,
            "Grn": wt.GARDEN_WASTE,
            "Gar": wt.GARDEN_WASTE,
            "Foo": wt.FOOD_WASTE,
        },
    )
