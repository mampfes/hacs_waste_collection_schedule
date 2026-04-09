import json
from datetime import datetime
from typing import List
from xml.etree import ElementTree

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Western Bay of Plenty District Council"
DESCRIPTION = "Source script for Western Bay of Plenty District Council kerbside collections via kerbsidecollective.co.nz"
URL = "https://kerbsidecollective.co.nz/"
TEST_CASES = {
    "15 Seaview Road": {"address": "15 Seaview Road"},
    "50 Ocean View Road": {"address": "50 Ocean View Road"},
}

API_URL = "https://kerbsidecollective.co.nz/wp-json/wbop/v1"
REQUEST_TIMEOUT = 10
ICON_MAP = {
    "Rubbish": "mdi:trash-can",
    "Mixed Recycling": "mdi:recycle",
    "Glass": "mdi:glass-fragile",
    "Food": "mdi:food-apple",
    "Garden": "mdi:leaf",
}

# XML namespace used in the SOAP responses
_NS = {"r": "http://refusewebservice.westernbaygovt.nz/"}

ADDRESS_SEARCH_URL = f"{API_URL}/addressSearch2"
ADDRESS_INFO_URL = f"{API_URL}/addressInfo2"


def _extract_json(raw: str) -> dict:
    """Extract and return the JSON portion from the addressInfo2 endpoint response.

    The endpoint returns SOAP XML followed by a JSON object.
    """
    idx = raw.find("{")
    if idx < 0:
        raise Exception("No JSON payload found in addressInfo2 response")
    return json.loads(raw[idx:])


class Source:
    def __init__(self, address: str) -> None:
        self._address: str = address.strip()
        self._session: requests.Session = requests.Session()
        self._session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/125.0.0.0 Safari/537.36"
                ),
                "Accept": "*/*",
                "Referer": "https://kerbsidecollective.co.nz/",
                "Origin": "https://kerbsidecollective.co.nz",
            }
        )

    def fetch(self) -> List[Collection]:
        valuation_id = self.get_address_detail()
        bins = self.get_waste_pickup_dates(valuation_id)
        return self.parse_waste_pickup_dates(bins)

    def get_address_detail(self) -> str:
        """Look up the address via addressSearch2 and return its ValuationId."""
        resp = self._session.post(
            ADDRESS_SEARCH_URL,
            data={"term": self._address},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()

        # Response is XML; parse it
        root = ElementTree.fromstring(  # nosec B314
            resp.text.split("}{")[0] if "}{" in resp.text else resp.text
        )

        # Handle the SOAP envelope wrapping — filter to only individual
        # result elements (skip the container <AddressSearchResult> wrapper
        # which has no ValuationId).
        results = [
            r
            for r in root.findall(".//r:AddressSearchResult", _NS)
            if r.findtext("r:ValuationId", default="", namespaces=_NS)
        ]
        if not results:
            raise Exception(
                f"Address not found: '{self._address}'  — "
                "make sure it matches an address in the Western Bay of Plenty district"
            )

        # Return the first result
        return results[0].findtext("r:ValuationId", default="", namespaces=_NS)

    def get_waste_pickup_dates(self, valuation_id: str) -> list:
        """Call addressInfo2 with a ValuationId and return the bin list."""
        resp = self._session.post(
            ADDRESS_INFO_URL,
            data={"term": valuation_id},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()

        data = _extract_json(resp.text)

        result = data.get("GetRefuseInformationByValuationResponse", {}).get(
            "GetRefuseInformationByValuationResult", {}
        )

        if result.get("ValuationFound") != "true":
            raise Exception(
                f"No waste collection data found for ValuationId {valuation_id}"
            )

        connection = result.get("ServiceConnectionList", {}).get(
            "ServiceConnection", {}
        )

        bin_info = connection.get("BinInfo", {})
        bins = bin_info.get("Bin", [])

        # If there is only one bin the API returns a dict instead of a list
        if isinstance(bins, dict):
            bins = [bins]

        return bins

    @staticmethod
    def parse_waste_pickup_dates(bins: list) -> List[Collection]:
        entries: List[Collection] = []
        for b in bins:
            bin_type = b.get("BinType", "Unknown")
            next_date_str = b.get("NextPickupDate", "")
            if not next_date_str:
                continue

            pickup_date = datetime.fromisoformat(next_date_str).date()
            icon = ICON_MAP.get(bin_type)

            entries.append(
                Collection(
                    date=pickup_date,
                    t=bin_type,
                    icon=icon,
                )
            )
        return entries


if __name__ == "__main__":
    import argparse
    import sys
    from pathlib import Path

    # Ensure the local package is importable when running directly
    try:
        from waste_collection_schedule import Collection  # noqa: F811
    except ModuleNotFoundError:
        sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

    parser = argparse.ArgumentParser(
        description="Fetch Western Bay of Plenty kerbside collection dates"
    )
    parser.add_argument("address", nargs="+", help="Address to look up")
    parser.add_argument(
        "--debug", action="store_true", help="Enable HTTP debug logging"
    )
    args = parser.parse_args()
    address = " ".join(args.address).strip()

    src = Source(address)

    if args.debug:
        import logging

        logging.basicConfig(level=logging.DEBUG)
        logging.getLogger("urllib3").setLevel(logging.DEBUG)

    try:
        collections = src.fetch()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        raise SystemExit(1)

    if not collections:
        print("No collections found for the provided address.")
        raise SystemExit(0)

    for c in collections:
        date_str = getattr(c, "date", None)
        type_str = getattr(c, "t", None) or getattr(c, "type", None)
        icon_str = getattr(c, "icon", None)
        print(f"{date_str}  {type_str}  {icon_str or ''}")
