"""BristolAlloyCalendar retrieval and parsing through the shared, verified HTTP session."""

# Adapted from UKBinCollectionData by robbrad:
# https://github.com/robbrad/UKBinCollectionData

from waste_collection_schedule.retrievers import Lookup, Request

HEADERS = {
    "Accept": "*/*",
    "Accept-Language": "en-GB,en;q=0.9",
    "Connection": "keep-alive",
    "Ocp-Apim-Subscription-Key": "47ffd667d69c4a858f92fc38dc24b150",
    "Ocp-Apim-Trace": "true",
    "Origin": "https://bristolcouncil.powerappsportals.com",
    "Referer": "https://bristolcouncil.powerappsportals.com/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "cross-site",
    "Sec-GPC": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36",
}


calendar_retriever = Request(
    "https://bcprdapidyna002.azure-api.net/bcprdfundyna001-alloy/NextCollectionDates",
    method="POST",
    headers=HEADERS,
    json=lambda _page, _property, uprn, **_: {"uprn": str(uprn).zfill(12)},
    before=(
        Lookup(
            "https://bristolcouncil.powerappsportals.com/completedynamicformunauth/",
            headers=HEADERS,
            params={"servicetypeid": "7dce896c-b3ba-ea11-a812-000d3a7f1cdc"},
            pick=lambda response, **_: None,
        ),
        Lookup(
            "https://bcprdapidyna002.azure-api.net/bcprdfundyna001-llpg/DetailedLLPG",
            method="POST",
            headers=HEADERS,
            json=lambda _page, uprn, **_: {"Uprn": "UPRN" + str(uprn).zfill(12)},
            pick=lambda response, _page, **_: None,
        ),
    ),
)
