from typing import ClassVar, final

from bs4 import BeautifulSoup
from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.transformers import HtmlTransformer

FORMS = "https://forms.north-norfolk.gov.uk/xforms"


def _token(response) -> str:
    """The anti-forgery token the next form post must carry."""
    return BeautifulSoup(response.content, "html.parser").find(
        "input", {"name": "__RequestVerificationToken"}
    )["value"]


def _landing(response, **_):
    """The landing page (its URL after the redirect) and its token."""
    return response.url, _token(response)


def _strongs(item) -> list:
    """A collection list item carries bin, weekday and date as three <strong>."""
    return item.find_all("strong")


def _date(item) -> str | None:
    # A property that does not subscribe to a collection has an empty item.
    strongs = _strongs(item)
    return strongs[2].get_text() if len(strongs) >= 3 else None


def _label(item) -> str:
    return _strongs(item)[0].get_text()


def _address_form(response, landing, search_token, **_) -> dict:
    """The council's own record of the property, as the address form wants it."""
    found = response.json()
    return {
        "__RequestVerificationToken": search_token,
        "SearchPostcode": found["postcode"],
        "Address": found["uprn"],
        "GisUprn": found["uprn"],
        "GisUsrn": found["bS7666USRN"],
        "GisTownName": found["townName"],
        "GisPostTown": found["postTown"],
        "GisPostCode": found["postcode"],
        "GisAddress": found["locAddress1BS7666"],
        "Address1": "",
        "Address2": "",
        "Address3": "",
        "Address4": "",
        "Postcode": "",
        "LocalSearch": "True",
        "DisableManualEntry": "True",
        "ComponentMode": "False",
        "IsDirty": "True",
    }


@final
class Source(BaseSource):
    TITLE = "North Norfolk District Council"
    DESCRIPTION = (
        "Source for waste collection services for North Norfolk District Council"
    )
    URL = "https://www.north-norfolk.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"uprn": "100090878875"},
        "Test_002": {"uprn": 100090883974},
        "Test_003": {"uprn": "100090880632"},
    }

    PARAMS = (uprn(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "An easy way to discover your Unique Property Reference Number (UPRN) "
            "is by going to https://www.findmyaddress.co.uk/ and entering in your "
            "address details."
        ),
    }

    # Launch the journey, confirm its landing page, look the property up by UPRN
    # and post the result to the address form, which answers with the schedule.
    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(f"{FORMS}/Launch/New/BinDaysJourney", pick=_landing),
            retrievers.Lookup(
                lambda landing, **_: landing[0],
                method="POST",
                data=lambda landing, **_: {
                    "__RequestVerificationToken": landing[1],
                    "Confirm": "true",
                    "BusinessName": "",
                    "IsDirty": "False",
                    "Journey": "BinDaysJourney",
                },
                pick=lambda response, *keys, **_: _token(response),
            ),
            retrievers.Lookup(
                f"{FORMS}/AddressSearch/GetAddressForUprn",
                params=lambda *keys, uprn, **_: {
                    "uprn": str(uprn),
                    "localAddress": "True",
                },
                pick=lambda response, landing, search_token, **_: _address_form(
                    response, landing, search_token
                ),
            ),
        ),
        url=f"{FORMS}/Address/Show/CollectionAddress",
        method="POST",
        data=lambda landing, search_token, form, **_: form,
        raise_for_status=True,
    )

    # Every <li> of the page; only the schedule items carry three <strong>.
    parse = parsers.HtmlParser("li")

    # The page names the day and month but not the year.
    transform = HtmlTransformer(
        date_getter=_date,
        type_getter=_label,
        parse_date=date_parsers.nearest_year("%A %d %B"),
        type_value_map={
            "Grey bin": wt.GENERAL_WASTE,
            "Green bin": wt.RECYCLABLES,
            "Brown bin": wt.GARDEN_WASTE,
        },
    )
