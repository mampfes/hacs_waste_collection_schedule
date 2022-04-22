import datetime
import json

from bs4 import BeautifulSoup

import requests
from requests.utils import requote_uri

from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Campbelltown City Council"
DESCRIPTION = "Source for Campbelltown City Council rubbish collection."
URL = "https://www.campbelltown.nsw.gov.au/"
TEST_CASES = {
    "Minto Mall": {
        "post_code": "2566",
        "suburb": "Minto",
        "street_name": "Brookfield Road",
        "street_number": "10",
    },
    # "The Scratch Bar": {
    #     "suburb": "Milton",
    #     "street_name": "Park Rd",
    #     "street_number": "8/1",
    # },
    # "Green Beacon": {
    #     "suburb": "Teneriffe",
    #     "street_name": "Helen St",
    #     "street_number": "26",
    # },
}

API_URLS = {
    "address_search": "https://www.campbelltown.nsw.gov.au/ocsvc/public/spatial/findaddress?address={}",
    "collection": "https://www.campbelltown.nsw.gov.au/ocsvc/Public/InMyNeighbourhood/WasteServices?GeoLocationId={}",
}


HEADERS = {"user-agent": "Mozilla/5.0"}


class Source:
    def __init__(
        self, post_code: str, suburb: str, street_name: str, street_number: str
    ):
        self.post_code = post_code
        self.suburb = suburb
        self.street_name = street_name
        self.street_number = street_number

    def fetch(self):

        # Request URL: https://www.campbelltown.nsw.gov.au/ocsvc/public/spatial/findaddress?address=6%20Liebig%20Place%20MINTO%20NSW%202566
        # {"locations":[{"Id":"06e7201d-8c65-4ab1-b52b-0e62512e3351","LatLon":null,"Postcode":"2566","State":"NSW","StreetAddress":"6 Liebig Place","Suburb":"MINTO","Zone":null}],"requestStatus":"Okay","responseMessage":"ok"}

        # https://www.campbelltown.nsw.gov.au/ocsvc/Public/InMyNeighbourhood/WasteServices?GeoLocationId=06e7201d-8c65-4ab1-b52b-0e62512e3351
        # <div class=\"module-widget waste-services-widget\" id=\"binCollectionData\">\u000a<h2 class=\"sub-title\">Waste Collection<\/h2>\u000a<div class=\"grid waste-services-results results-4\"><div class=\"col-xs-12 col-m-6 col-lg-3 waste-services-result regular-service general-waste item-0\">\u000a<article>\u000a  <img class=\"collection-image\" alt=\"General Waste\" src=\"\/files\/sharedassets\/public\/template-files\/binicons\/general-waste.png\" \/>\u000a<div class=\"service-details\">\u000a  General Waste\u000a   <div class=\"next-service\">\u000a     <span>Thursday<br\/>21 Apr 2022<\/span>\u000a   <\/div>\u000a\u000a<\/div>\u000a<\/article>\u000a<\/div><div class=\"col-xs-12 col-m-6 col-lg-3 waste-services-result regular-service recycling item-1\">\u000a<article>\u000a  <img class=\"collection-image\" alt=\"Recycling\" src=\"\/files\/sharedassets\/public\/template-files\/binicons\/recycling.png\" \/>\u000a<div class=\"service-details\">\u000a  Recycling\u000a   <div class=\"next-service\">\u000a     <span>Thursday<br\/>28 Apr 2022<\/span>\u000a   <\/div>\u000a\u000a<\/div>\u000a<\/article>\u000a<\/div><div class=\"col-xs-12 col-m-6 col-lg-3 waste-services-result regular-service green-waste item-2\">\u000a<article>\u000a  <img class=\"collection-image\" alt=\"Green Waste\" src=\"\/files\/sharedassets\/public\/template-files\/binicons\/green-waste.png\" \/>\u000a<div class=\"service-details\">\u000a  Green Waste\u000a   <div class=\"next-service\">\u000a     <span>Thursday<br\/>21 Apr 2022<\/span>\u000a   <\/div>\u000a\u000a<\/div>\u000a<\/article>\u000a<\/div><div class=\"col-xs-12 col-m-6 col-lg-3 waste-services-result regular-service kerbside item-3\">\u000a<article>\u000a  <img class=\"collection-image\" alt=\"Kerbside\" src=\"\/files\/sharedassets\/public\/template-files\/binicons\/wastecalndaricon.png\" \/>\u000a<div class=\"service-details\">\u000a  Waste Calendar\u000a   <div class=\"next-service\">\u000a     <span>Zone A<\/span>\u000a   <\/div>\u000a<div class=\"kerbside-info\">\u000aYour waste calendar is now available online and through the <b>My Waste Bin<\/b> app. Please click  <a href=\"https:\/\/www.campbelltown.nsw.gov.au\/ServicesandFacilities\/WasteandRecycling\/WasteCalendarandMyWasteBinapp\">here<\/a> to view your calendar and to learn more about the <b>My Waste Bin<\/b> app, which you can download to your mobile device.\u000a<\/div>\u000a<\/div>\u000a<\/article>\u000a<\/div>\u000a<h2 class=\"sub-title\">Kerbside clean up<\/h2>\u000a<div class=\"grid waste-services-results results-<ItemData Property='ItemCount'>\">\u000a<div class=\"col-xs-12 col-m-6 col-lg-3 waste-services-result regular-service kerbside item-3\">\u000a<article>\u000a  <img class=\"collection-image\" alt=\"Kerbside\" src=\"\/files\/sharedassets\/public\/template-files\/binicons\/kerbside.png\" \/>\u000a<div class=\"service-details\">\u000a   <div class=\"next-service\">\u000a     <span>Tuesdays<\/span>\u000a   <\/div>\u000a<div class=\"kerbside-info\">\u000aYou must \u000a<a href=\"\/RSF\/ServicesandFacilities\/WasteandRecycling\/GetridofbulkyitemsbybookingaKerbsidecleanup\">book a clean up online<\/a> or call us on <a href=\"tel:02-4645-4000\">02 4645 4000<\/a> before you put any items on the kerbside.\u000a<\/div>\u000a<\/div>\u000a<\/article>\u000a<\/div>\u000a<\/div><\/div>\u000a<\/div>

        locationId = 0

        address = "{0} {1} {2} {3}".format(
            self.street_number, self.street_name, self.suburb, self.post_code
        )

        q = requote_uri(str(API_URLS["address_search"]).format(address))

        # Retrieve suburbs
        r = requests.get(q, headers=HEADERS)

        data = json.loads(r.text)

        # Find the ID for our suburb
        for item in data["locations"]:
            locationId = item["Id"]
            break

        if locationId == 0:
            return []

        # Retrieve the upcoming collections for our property
        q = requote_uri(str(API_URLS["collection"]).format(locationId))

        r = requests.get(q, headers=HEADERS)

        data = json.loads(r.text)

        responseContent = data["responseContent"]

        soup = BeautifulSoup(responseContent, "html.parser")
        services = soup.find_all("div", attrs={"class": "service-details"})

        # binCollectionData = html.find("div", attrs={"id": "binCollectionData"})

        entries = []

        for item in services:
            collectionDate = item.find("span")
            try:
                dateConverted = datetime.datetime.strptime(
                    collectionDate.text, "%A%d %b %Y"
                ).date()
            except:
                dateConverted = ""
            else:
                if "General Waste" in item.text:
                    entries.append(
                        Collection(
                            date=dateConverted, t="Rubbish", icon="mdi:trash-can"
                        )
                    )

                if "Recycling" in item.text:
                    entries.append(
                        Collection(
                            date=dateConverted, t="Recycling", icon="mdi:recycle"
                        )
                    )

                if "Green Waste" in item.text:
                    entries.append(
                        Collection(date=dateConverted, t="Green Waste", icon="mdi:leaf")
                    )

        return entries
