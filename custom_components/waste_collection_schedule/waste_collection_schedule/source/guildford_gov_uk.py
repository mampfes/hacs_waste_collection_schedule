import json
from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "guildford.gov.uk"
DESCRIPTION = "Source for guildford.gov.uk services for Guildford, UK."
# Find the UPRN of your address using https://www.findmyaddress.co.uk/search
URL = "https://guildford.gov.uk"
TEST_CASES = {
    "GU12": {"uprn": "10007060305"},
    "GU1": {"uprn": "100061398158"},
    "GU2": {"uprn": "100061391831"},
}

ICONS = {
    "Refuse": "mdi:trash-can",
    "Food": "mdi:food-apple",
    "Recycling": "mdi:recycle",
    "Garden Waste": "mdi:leaf",
}


class Source:
    def __init__(self, uprn):
        self._uprn = uprn

    def fetch(self):
        # The API uses this framework cookie, which seems to last 2 weeks.
        framework = "-SjNAdgW9yv96YgKI8MiFA"
        headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0','Accept': '*/*','Accept-Language': 'en-GB,en;q=0.5','Referer': 'https://my.guildford.gov.uk/customers/s/view-bin-collections','X-SFDC-Page-Scope-Id': '2f1b8c8c-7f21-4c8e-97ff-7d382bef472e', 'X-SFDC-Request-Id': '310489300000000d0f' ,'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8','Origin': 'https://my.guildford.gov.uk', 'Connection': 'keep-alive', 'Cookie': 'renderCtx=%7B%22pageId%22%3A%22d16a45fafd2d-434c-9867-13157cad5ae0%22%2C%22schema%22%3A%22Published%22%2C%22viewType%22%3A%22Published%22%2C%22brandingSetId%22%3A%2291620535-2a5f-4116-830f-f7be831ad395%22%2C%22audienceIds%22%3A%226Au4K000000L1vJ%2C6Au4K000000L1vF%22%7D; CookieConsentPolicy=0:1; LSKey-c$CookieConsentPolicy=0:1; CookieConsentPolicy=0:0; LSKey-c$CookieConsentPolicy=0:0; pctrk=cd6cad4a-1a62-4b4b-a9e7-5df4a5eede9b; sfdc-stream=!av30lCajg42+B19mc4XCkPx8HEy5Mkzqs0SBfqVYJh6EaGzz631DI9Km3o0DTHGHsyz5MSeL5l6yMg==; force-proxy-stream=!LAorEQlyJAsY1yCvxttwW2ftStfhSkP54cqVjoflXoWOf54cRL0W4TSeMTqu5hHUMI5Z1RLqq/fmfQ==; force-stream=!av30lCajg42+B19mc4XCkPx8HEy5Mkzqs0SBfqVYJh6EaGzz631DI9Km3o0DTHGHsyz5MSeL5l6yMg==', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors','Sec-Fetch-Site': 'same-origin','TE': 'trailers'}
        data="message=%7B%22actions%22%3A%5B%7B%22id%22%3A%22291%3Ba%22%2C%22descriptor%22%3A%22apex%3A%2F%2FBinScheduleDisplayCmpController%2FACTION%24GetBinSchedules%22%2C%22callingDescriptor%22%3A%22markup%3A%2F%2Fc%3ABinScheduleDisplay%22%2C%22params%22%3A%7B%22database%22%3A%22domestic%22%2C%22UPRN%22%3A%22"+self._uprn+"%22%7D%2C%22version%22%3Anull%7D%5D%7D&aura.context=%7B%22mode%22%3A%22PROD%22%2C%22fwuid%22%3A%22i" + framework + "%22%2C%22app%22%3A%22siteforce%3AcommunityApp%22%2C%22loaded%22%3A%7B%22APPLICATION%40markup%3A%2F%2Fsiteforce%3AcommunityApp%22%3A%22PAjEh9HEIZmsDpK-Y8SVTg%22%2C%22COMPONENT%40markup%3A%2F%2Fflowruntime%3AflowRuntimeForFlexiPage%22%3A%22mAcRFr74U2AGVmxwdG0jJw%22%7D%2C%22dn%22%3A%5B%5D%2C%22globals%22%3A%7B%22eswConfigDeveloperName%22%3Anull%2C%22isVoiceOver%22%3Anull%2C%22setupAppContextId%22%3Anull%2C%22density%22%3Anull%2C%22srcdoc%22%3Anull%2C%22appContextId%22%3Anull%2C%22dynamicTypeSize%22%3Anull%7D%2C%22uad%22%3Afalse%7D&aura.pageURI=%2Fcustomers%2Fs%2Fview-bin-collections&aura.token=null"
        url = "https://my.guildford.gov.uk/customers/s/sfsites/aura?r=10&other.BinScheduleDisplayCmp.GetBinSchedules=1"
        r = requests.post(url, data=data, headers=headers)
        # If the cookie isn't accepted you get an error message back telling you the cookie it _is_ expecting (Which was nice)
        if "exceptionMessage" in r.text:
         #print("Error returned")
         # But the error is one long string, no JSON :(
         str = r.text.split(" ")
         current = 0
         while current < len(str):
           #Having split the string in a space delimited list, walk through lookin for the cookie it was expecting
           if str[current] == "Expected:" :
              framework = str[current+1]
              #print(framework)
              # Having updated the cookie, try the POST request again. It should work (As we're providing the cookie it told us to use !)
              data="message=%7B%22actions%22%3A%5B%7B%22id%22%3A%22291%3Ba%22%2C%22descriptor%22%3A%22apex%3A%2F%2FBinScheduleDisplayCmpController%2FACTION%24GetBinSchedules%22%2C%22callingDescriptor%22%3A%22markup%3A%2F%2Fc%3ABinScheduleDisplay%22%2C%22params%22%3A%7B%22database%22%3A%22domestic%22%2C%22UPRN%22%3A%22"+self._uprn+"%22%7D%2C%22version%22%3Anull%7D%5D%7D&aura.context=%7B%22mode%22%3A%22PROD%22%2C%22fwuid%22%3A%22" + framework + "%22%2C%22app%22%3A%22siteforce%3AcommunityApp%22%2C%22loaded%22%3A%7B%22APPLICATION%40markup%3A%2F%2Fsiteforce%3AcommunityApp%22%3A%22PAjEh9HEIZmsDpK-Y8SVTg%22%2C%22COMPONENT%40markup%3A%2F%2Fflowruntime%3AflowRuntimeForFlexiPage%22%3A%22mAcRFr74U2AGVmxwdG0jJw%22%7D%2C%22dn%22%3A%5B%5D%2C%22globals%22%3A%7B%22eswConfigDeveloperName%22%3Anull%2C%22isVoiceOver%22%3Anull%2C%22setupAppContextId%22%3Anull%2C%22density%22%3Anull%2C%22srcdoc%22%3Anull%2C%22appContextId%22%3Anull%2C%22dynamicTypeSize%22%3Anull%7D%2C%22uad%22%3Afalse%7D&aura.pageURI=%2Fcustomers%2Fs%2Fview-bin-collections&aura.token=null"
              r = requests.post(url, data=data, headers=headers)
           current += 1
        #print (r.text)
        # extract data from json
        # The rest of this code is mostly lifted from the examples in the repo.
        text = json.loads(r.text)
        schedule=text['actions'][0]['returnValue']['FeatureSchedules']
        entries = []

        for collection in schedule:
            try:
                entries.append(
                    Collection(
                        date=datetime.strptime(
                            collection["NextDate"], "%Y-%m-%dT%H:%M:%S.000Z"
                        ).date(),
                        t=collection["FeatureName"],
                        icon=ICONS[collection["FeatureName"]],
                    )
                )
            except ValueError:
                pass  # ignore date conversion failure for not scheduled collections
        
        return entries
