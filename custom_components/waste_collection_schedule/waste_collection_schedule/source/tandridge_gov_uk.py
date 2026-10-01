import json
from typing import ClassVar, final
from xml.etree import ElementTree as ET

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.transformers import JsonTransformer

_SEARCH_URL = (
    "https://tdcws01.tandridge.gov.uk/TDCWebAppsPublic/WebServices/"
    "wsLLPGSearch2018/LLPGQuery_v2_3.asmx?op=SearchByAllAddressDetails"
)
_COLLECTIONS_URL = (
    "https://tdcws01.tandridge.gov.uk/TDCWebAppsPublic/TDCMiddleware/"
    "RESTAPI/WhiteSpaceAPI/GetCompleteRecordByUPRN"
)

_NS = {"tdc": "http://www.tandridge.gov.uk/Webservices/"}

_SEARCH_XML_TEMPLATE = """<?xml version="1.0" encoding="utf-8"?>
<soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
  <soap12:Body>
    <SearchByAllAddressDetails xmlns="http://www.tandridge.gov.uk/Webservices/">
      <SearchAddress></SearchAddress>
      <SearchTownName></SearchTownName>
      <SearchLocalityName></SearchLocalityName>
      <SearchPostCode>{postcode}</SearchPostCode>
      <SearchReference></SearchReference>
      <SearchXPos></SearchXPos>
      <SearchYPos></SearchYPos>
      <SearchDistance></SearchDistance>
      <ReturnMaxRecords></ReturnMaxRecords>
      <MustHaveRefType></MustHaveRefType>
      <ShowXrefTypes></ShowXrefTypes>
      <sUseDate></sUseDate>
      <sSearchAlternatives>1,3,6</sSearchAlternatives>
      <sPrimaryClassifications></sPrimaryClassifications>
      <sSecondaryClassifications></sSecondaryClassifications>
      <sTertiaryClassifications></sTertiaryClassifications>
      <ShowNonAddressable></ShowNonAddressable>
      <AllowSearchOrganisations></AllowSearchOrganisations>
    </SearchByAllAddressDetails>
  </soap12:Body>
</soap12:Envelope>"""


def _search_body(*, postcode: str, **_) -> bytes:
    """The SOAP envelope that lists the addresses of a postcode."""
    return _SEARCH_XML_TEMPLATE.format(postcode=postcode).encode("utf-8")


def _uprn(response, *, house_number, **_) -> str:
    """The UPRN of the postcode's address whose house part is the house number."""
    root = ET.fromstring(response.text)
    target = str(house_number).strip().lower()
    candidates: list[tuple[str, str]] = []
    for record in root.findall(".//tdc:LLPGRecord", _NS):
        house_part = record.findtext("tdc:BS7666Format/tdc:HousePart", namespaces=_NS)
        uprn = record.findtext("tdc:BS7666Format/tdc:UPRN", namespaces=_NS)
        if not uprn or not house_part:
            continue
        candidates.append((house_part.strip(), uprn))
    for house_part, uprn in candidates:
        if house_part.lower() == target:
            return uprn
    raise SourceArgumentNotFoundWithSuggestions(
        "house_number",
        str(house_number),
        sorted({house_part for house_part, _ in candidates}),
    )


@final
class Source(BaseSource):
    TITLE = "Tandridge District Council"
    DESCRIPTION = "Source for Tandridge District Council, UK, waste collection."
    URL = "https://www.tandridge.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "14A Station Road East, Oxted": {
            "postcode": "RH8 0PG",
            "house_number": "14A",
        },
        "22A Station Road East, Oxted": {
            "postcode": "RH8 0PG",
            "house_number": "22A",
        },
        "No postcode space": {
            "postcode": "RH80PG",
            "house_number": "16A",
        },
    }

    PARAMS = (postcode("postcode", "house_number"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your postcode and your house number/name exactly as it appears "
            "when you look up your address at "
            "https://tdcws01.tandridge.gov.uk/TDCWebAppsPublic/tfaBranded/408 "
            "(e.g. '14A')."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                _SEARCH_URL,
                method="POST",
                data=_search_body,
                headers={"Content-Type": "text/xml; charset=utf-8"},
                pick=_uprn,
            ),
        ),
        url=_COLLECTIONS_URL,
        method="POST",
        data=lambda uprn, **_: json.dumps({"UPRN": uprn}),
        headers={
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Content-Type": "application/json",
        },
        raise_for_status=True,
    )

    parse = parsers.JsonParser("lstCollections")
    transform = JsonTransformer(
        date_key="Date",
        type_key="Service",
        parse_date=date_parsers.for_format("%d/%m/%Y %H:%M:%S"),
        type_value_map={
            "Domestic Waste Collection Service": wt.GENERAL_WASTE,
            "Recycling Collection Service": wt.RECYCLABLES,
            "Food Waste Collection Service": wt.FOOD_WASTE,
            "Garden Waste Collection Service": wt.GARDEN_WASTE,
            "Electricals and textiles": wt.OTHER,
        },
        carry_raw_label=True,
    )

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
        wt.OTHER,
    ]
