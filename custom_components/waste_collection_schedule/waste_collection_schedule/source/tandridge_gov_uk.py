from datetime import datetime
from xml.etree import ElementTree as ET

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "Tandridge District Council"
DESCRIPTION = "Source for Tandridge District Council, UK, waste collection."
URL = "https://www.tandridge.gov.uk"
COUNTRY = "uk"

TEST_CASES = {
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

ICON_MAP = {
    "Domestic Waste Collection Service": Icons.GENERAL_WASTE,
    "Recycling Collection Service": Icons.RECYCLING,
    "Food Waste Collection Service": Icons.BIO_KITCHEN,
    "Garden Waste Collection Service": Icons.GARDEN,
    "Electricals and textiles": Icons.ELECTRONICS,
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Enter your postcode and your house number/name exactly as it appears "
    "when you look up your address at "
    "https://tdcws01.tandridge.gov.uk/TDCWebAppsPublic/tfaBranded/408 "
    "(e.g. '14A').",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "postcode": "Your postcode (e.g. RH8 0PG)",
        "house_number": "Your house number or name (e.g. 14A)",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "postcode": "Postcode",
        "house_number": "House number/name",
    },
}

_SEARCH_URL = (
    "https://tdcws01.tandridge.gov.uk/TDCWebAppsPublic/WebServices/"
    "wsLLPGSearch2018/LLPGQuery_v2_3.asmx?op=SearchByAllAddressDetails"
)
_COLLECTIONS_URL = (
    "https://tdcws01.tandridge.gov.uk/TDCWebAppsPublic/TDCMiddleware/"
    "RESTAPI/WhiteSpaceAPI/GetCompleteRecordByUPRN"
)

_NS = {
    "soap": "http://www.w3.org/2003/05/soap-envelope",
    "tdc": "http://www.tandridge.gov.uk/Webservices/",
}

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

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
}


class Source:
    def __init__(self, postcode: str, house_number: str):
        self._postcode = postcode
        self._house_number = str(house_number)

    def _find_uprn(self, session: requests.Session) -> str:
        xml_request = _SEARCH_XML_TEMPLATE.format(postcode=self._postcode)
        r = session.post(
            _SEARCH_URL,
            data=xml_request.encode("utf-8"),
            headers={**_HEADERS, "Content-Type": "text/xml; charset=utf-8"},
        )
        r.raise_for_status()

        root = ET.fromstring(r.text)
        records = root.findall(".//tdc:LLPGRecord", _NS)

        target = self._house_number.strip().lower()
        candidates: list[tuple[str, str]] = []
        for record in records:
            house_part = record.findtext(
                "tdc:BS7666Format/tdc:HousePart", namespaces=_NS
            )
            uprn = record.findtext("tdc:BS7666Format/tdc:UPRN", namespaces=_NS)
            if not uprn or not house_part:
                continue
            candidates.append((house_part.strip(), uprn))

        for house_part, uprn in candidates:
            if house_part.lower() == target:
                return uprn

        raise SourceArgumentNotFoundWithSuggestions(
            "house_number",
            self._house_number,
            sorted({house_part for house_part, _ in candidates}),
        )

    def fetch(self) -> list[Collection]:
        session = requests.Session()

        uprn = self._find_uprn(session)

        r = session.post(
            _COLLECTIONS_URL,
            json={"UPRN": uprn},
            headers={
                **_HEADERS,
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Content-Type": "application/json",
            },
        )
        r.raise_for_status()
        data = r.json()

        if not data.get("SuccessFlag"):
            raise SourceArgumentNotFoundWithSuggestions(
                "house_number",
                self._house_number,
                [],
            )

        entries = []
        for item in data.get("lstCollections") or []:
            service = (item.get("Service") or "").strip()
            date_str = item.get("Date")
            if not service or not date_str:
                continue
            date = datetime.strptime(date_str, "%d/%m/%Y %H:%M:%S").date()
            entries.append(Collection(date=date, t=service, icon=ICON_MAP.get(service)))

        return entries
