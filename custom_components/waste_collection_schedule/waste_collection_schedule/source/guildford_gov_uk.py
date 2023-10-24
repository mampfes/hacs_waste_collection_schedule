import json
from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Guildford Borough Council"
DESCRIPTION = "Source for guildford.gov.uk services for Guildford, UK."
URL = "https://guildford.gov.uk"
TEST_CASES = {
    "GU12": {"uprn": "10007060305"},
    "GU1": {"uprn": "100061398158"},
    "GU2": {"uprn": 100061391831},
}

ICON_MAP = {
    "Refuse": "mdi:trash-can",
    "Food": "mdi:food-apple",
    "Recycling": "mdi:recycle",
    "Garden Waste": "mdi:leaf",
}

API_URL = "https://my.guildford.gov.uk/customers/s/sfsites/aura?r=10&other.BinScheduleDisplayCmp.GetBinSchedules=1"


class Source:
    def __init__(self, uprn):
        self._uprn = str(uprn)

    def fetch(self):
        # The API uses this framework cookie, which seems to last 2 weeks.
        framework = "-SjNAdgW9yv96YgKI8MiFA"
        params = (
            "message=%7B%22actions%22%3A%5B%7B%22id%22%3A%22291%3Ba%22%2C%22descriptor%22%3A%22apex%3A%2F%2FBinScheduleDisplayCmpController%2FACTION%24GetBinSchedules%22%2C%22callingDescriptor%22%3A%22markup%3A%2F%2Fc%3ABinScheduleDisplay%22%2C%22params%22%3A%7B%22database%22%3A%22domestic%22%2C%22UPRN%22%3A%22"
            + self._uprn
            + "%22%7D%2C%22version%22%3Anull%7D%5D%7D&aura.context=%7B%22mode%22%3A%22PROD%22%2C%22fwuid%22%3A%22i"
            + framework
            + "%22%2C%22app%22%3A%22siteforce%3AcommunityApp%22%2C%22loaded%22%3A%7B%22APPLICATION%40markup%3A%2F%2Fsiteforce%3AcommunityApp%22%3A%22PAjEh9HEIZmsDpK-Y8SVTg%22%2C%22COMPONENT%40markup%3A%2F%2Fflowruntime%3AflowRuntimeForFlexiPage%22%3A%22mAcRFr74U2AGVmxwdG0jJw%22%7D%2C%22dn%22%3A%5B%5D%2C%22globals%22%3A%7B%22eswConfigDeveloperName%22%3Anull%2C%22isVoiceOver%22%3Anull%2C%22setupAppContextId%22%3Anull%2C%22density%22%3Anull%2C%22srcdoc%22%3Anull%2C%22appContextId%22%3Anull%2C%22dynamicTypeSize%22%3Anull%7D%2C%22uad%22%3Afalse%7D&aura.pageURI=%2Fcustomers%2Fs%2Fview-bin-collections&aura.token=null"
        )
        r = requests.post(API_URL, params=params)
        r.raise_for_status()

        # If the cookie isn't accepted you get an error message back telling you the cookie it _is_ expecting (Which was nice)
        if "exceptionMessage" in r.text:
            # But the error is one long string, no JSON :(
            str = r.text.split(" ")
            current = 0
            while current < len(str):
                # Having split the string in a space delimited list, walk through lookin for the cookie it was expecting
                if str[current] == "Expected:":
                    framework = str[current + 1]
                    # Having updated the cookie, try the POST request again. It should work (As we're providing the cookie it told us to use !)
                    params = (
                        "message=%7B%22actions%22%3A%5B%7B%22id%22%3A%22291%3Ba%22%2C%22descriptor%22%3A%22apex%3A%2F%2FBinScheduleDisplayCmpController%2FACTION%24GetBinSchedules%22%2C%22callingDescriptor%22%3A%22markup%3A%2F%2Fc%3ABinScheduleDisplay%22%2C%22params%22%3A%7B%22database%22%3A%22domestic%22%2C%22UPRN%22%3A%22"
                        + self._uprn
                        + "%22%7D%2C%22version%22%3Anull%7D%5D%7D&aura.context=%7B%22mode%22%3A%22PROD%22%2C%22fwuid%22%3A%22"
                        + framework
                        + "%22%2C%22app%22%3A%22siteforce%3AcommunityApp%22%2C%22loaded%22%3A%7B%22APPLICATION%40markup%3A%2F%2Fsiteforce%3AcommunityApp%22%3A%22PAjEh9HEIZmsDpK-Y8SVTg%22%2C%22COMPONENT%40markup%3A%2F%2Fflowruntime%3AflowRuntimeForFlexiPage%22%3A%22mAcRFr74U2AGVmxwdG0jJw%22%7D%2C%22dn%22%3A%5B%5D%2C%22globals%22%3A%7B%22eswConfigDeveloperName%22%3Anull%2C%22isVoiceOver%22%3Anull%2C%22setupAppContextId%22%3Anull%2C%22density%22%3Anull%2C%22srcdoc%22%3Anull%2C%22appContextId%22%3Anull%2C%22dynamicTypeSize%22%3Anull%7D%2C%22uad%22%3Afalse%7D&aura.pageURI=%2Fcustomers%2Fs%2Fview-bin-collections&aura.token=null"
                    )
                    r = requests.post(API_URL, params=params)
                current += 1

        # extract data from json
        text = json.loads(r.text)
        schedule = text["actions"][0]["returnValue"]["FeatureSchedules"]
        entries = []

        for collection in schedule:
            try:
                entries.append(
                    Collection(
                        date=datetime.strptime(
                            collection["NextDate"], "%Y-%m-%dT%H:%M:%S.000Z"
                        ).date(),
                        t=collection["FeatureName"],
                        icon=ICON_MAP.get(collection["FeatureName"]),
                    )
                )
            except ValueError:
                pass  # ignore date conversion failure for not scheduled collections

        return entries
