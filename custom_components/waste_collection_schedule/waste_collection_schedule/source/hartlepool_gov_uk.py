import json
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Hartlepool Borough Council"
DESCRIPTION = (
    "Source for www.hertlepool.gov.uk services for Hartlepool Borough Council."
)
URL = "https://www.hartlepool.gov.uk"
TEST_CASES = {
    "Test_001": {
        "uprn": "100110021946",
    },
    "Test_002": {
        "uprn": "100110007383",
    },
    "Test_003": {
        "uprn": 10009716952,
    },
}
HEADERS = {
    "user-agent": "Mozilla/5.0",
}
ICON_MAP = {
    "Green": "mdi:trash-can",
    "Grey": "mdi:recycle",
    "Brown": "mdi:leaf",
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {  # Optional dictionary to describe how to get the arguments, will be shown in the GUI configuration form above the input fields, does not need to be translated in all languages
    "en": "You can find your UPRN by visiting https://www.findmyaddress.co.uk/ and entering in your address details.",
}

PARAM_DESCRIPTIONS = {  # Optional dict to describe the arguments, will be shown in the GUI configuration below the respective input field
    "en": {
        "uprn": "Every UK residential property is allocated a Unique Property Reference Number (UPRN). You can find yours by going to https://www.findmyaddress.co.uk/ and entering in your address details.",
    },
}

PARAM_TRANSLATIONS = {  # Optional dict to translate the arguments, will be shown in the GUI configuration form as placeholder text
    "en": {
        "uprn": "Unique Property Reference Number",
    },
}


class Source:
    def __init__(
        self,
        uprn: str | int,
    ):
        self._uprn = str(uprn)

    def fetch(self):

        s = requests.Session()

        # set up session
        r = s.get(
            "https://online.hartlepool.gov.uk/apibroker/domain/online.hartlepool.gov.uk?_=1749571954085&sid=506a6a3e374753c1b6d3a4ede7b7a79d",
            headers=HEADERS,
        )
        r.raise_for_status()

        # get session key
        authRequest = s.get(
            "https://online.hartlepool.gov.uk/authapi/isauthenticated?uri=https%253A%252F%252Fonline.hartlepool.gov.uk%252Fservice%252FRefuse_and_recycling___check_bin_day&hostname=online.hartlepool.gov.uk&withCredentials=true",
            headers=HEADERS,
        )
        authRequest.raise_for_status()
        authData = authRequest.json()
        sessionKey = authData["auth-session"]

        # now query using the uprn
        timestamp = time.time_ns() // 1_000_000  # epoch time in milliseconds
        payload = {
            "formValues": {
                "Section 1": {"collectionLocationUPRN": {"value": self._uprn}}
            }
        }
        scheduleRequest = s.post(
            f"https://online.hartlepool.gov.uk/apibroker/runLookup?id=5ec67e019ffdd&repeat_against=&noRetry=true&getOnlyTokens=undefined&log_id=&app_name=AF-Renderer::Self&_={timestamp}&sid={sessionKey}",
            headers=HEADERS,
            json=payload,
        )
        scheduleRequest.raise_for_status()
        rowdata = json.loads(scheduleRequest.content)["integration"]["transformed"][
            "rows_data"
        ]["0"]["HTMLCollectionDatesText"]
        soup = BeautifulSoup(rowdata, "html.parser")
        divs = soup.find_all("div")

        entries = []
        for div in divs:
            bin, dt = div.find("span").text.strip().split(" ")
            entries.append(
                Collection(
                    date=datetime.strptime(dt, "%d/%m/%Y").date(),
                    t=bin,
                    icon=ICON_MAP.get(bin),
                )
            )

        return entries
