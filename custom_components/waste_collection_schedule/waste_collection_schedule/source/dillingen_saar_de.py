import datetime
import requests
from waste_collection_schedule import Collection
from waste_collection_schedule.service.ICS import ICS
from datetime import datetime



TITLE = "Dillingen Saar" # Title will show up in README.md and info.md
DESCRIPTION = "Source script for waste collection Dillingen Saar"  # Describe your source
URL = "https://www.dillingen-saar.de/"  # Insert url to service homepage. URL will show up in README.md and info.md
TEST_CASES = {  # Insert arguments for test cases to be used by test_sources.py script
    "Am Fischerberg": {"street": "Am Fischerberg"}, #https://service-dillingen-saar.fbo.de/date/Am%20Fischerberg/2023-01-01/+1%20year/?format=ics&type=rm,gs,bio,pa
    "Odilienplatz": {"street": "Odilienplatz"},     #https://service-dillingen-saar.fbo.de/date/Odilienplatz/2023-01-01/+1%20year/?format=ics&type=rm,gs,bio,pa
    "Lilienstraße": {"street": "Lilienstraße"},      #https://service-dillingen-saar.fbo.de/date/Lilienstra%C3%9Fe/2023-01-01/+1%20year/?format=ics&type=rm,gs,bio,pa
    "Joseph-Roederer-Straße": {"street": "Joseph-Roederer-Straße"} #https://service-dillingen-saar.fbo.de/date/Joseph-Roederer-Stra%C3%9Fe/2023-01-01/+1%20year/?format=ics&type=rm,gs,bio,pa
}

API_URL = "https://service-dillingen-saar.fbo.de/date/"

ICON_MAP = {
    "Altpapier": "mdi:package-variant",
    "Restmüll": "mdi:trash-can",
    "Gelber Sack": "mdi:recycle",
}


class Source:
    def __init__(self, street: str):
        self._street = street
        self._ics = ICS()


    def fetch(self):

        # the url contains the current year, but this doesn't really seems to matter at least for the ical, since the result is always the same
        # still replace it for compatibility sake
        now = datetime.now()

        url = f"{API_URL}/{self._street}/{str(now.year)}-01-01/+1%20year/?format=ics&type=rm,gs,bio,pa"
        res = requests.get(url)
        res.raise_for_status()


        # Convert ICS String to events
        dates = self._ics.convert(res.text)


        entries = []
        for d in dates:
            icon = ICON_MAP.get(d[1], "mdi:trash-can")
            entries.append(Collection(
                date=d[0],
                t=d[1].split("...")[0], # string of all characters up to but not including the first "..."
                icon=icon
            )
        )

        return entries
