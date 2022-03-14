import logging
import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "UMWELTPROFIS"
DESCRIPTION = "Source for Umweltprofis"
URL = "https://www.umweltprofis.at"
TEST_CASES = {
    "Ebensee": {"url": "https://data.umweltprofis.at/OpenData/AppointmentService/AppointmentService.asmx/GetIcalWastePickupCalendar?key=KXX_K0bIXDdk0NrTkk3xWqLM9-bsNgIVBE6FMXDObTqxmp9S39nIqwhf9LTIAX9shrlpfCYU7TG_8pS9NjkAJnM_ruQ1SYm3V9YXVRfLRws1"},
}

_LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(self, url):
        self._url = url
        self._ics = ICS()

    def fetch(self):
        r = requests.get(self._url)
        if r.status_code != 200:
            _LOGGER.error("Error querying calendar data")
            return []

        fixed_text = r.text.replace("REFRESH - INTERVAL; VALUE = ", "REFRESH-INTERVAL;VALUE=")

        dates = self._ics.convert(fixed_text)

        entries = []
        for d in dates:
            entries.append(Collection(d[0], d[1]))
        return entries
