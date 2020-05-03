import requests
import icalendar
import datetime
from ..helpers import CollectionAppointment
from collections import OrderedDict


DESCRIPTION = "Source for Abfall Landkreis Tuebingen"
URL = "https://www.abfall-kreis-tuebingen.de"
TEST_CASES = OrderedDict(
    [("Dettenhausen", {"ort": 3, "dropzone": 525, "ics_with_drop": False})]
)


class Source:
    def __init__(self, ort, dropzone, ics_with_drop=False):
        self._ort = ort
        self._dropzone = dropzone
        self._ics_with_drop = ics_with_drop

    def fetch(self):
        now = datetime.datetime.now()
        entries = self.fetch_year(now.year)
        if now.month == 12:
            # also get data for next year if we are already in december
            try:
                entries.extend(self.fetch_year(now.year + 1))
            except Exception:
                # ignore if fetch for next year fails
                pass
        return entries

    def fetch_year(self, year):
        args = {
            "action": "execute_create_ics",
            "ort": self._ort,
            "dropzone": self._dropzone,
            "year": year,
            "ics_with_drop": "true" if self._ics_with_drop else "false",
        }

        # step 1: prepare ics file
        r = requests.post(
            "https://www.abfall-kreis-tuebingen.de/wp-admin/admin-ajax.php", data=args
        )

        # request returns a string with the format "\n\n\n\n\n\n\n\n<url>|<file>"
        # with url ::= https://www.abfall-kreis-tuebingen.de/wp-content/uploads/abfuhrtermine_id_XXXXXX.ics
        # and file ::= abfuhrtermine_id_XXXXXX.ics
        (url, file) = r.text.strip().split("|")
        # print(f"url = {url}, file = {file}")

        # step 2: get ics file
        r = requests.get(url)
        r.encoding = "utf-8"  # requests doesn't guess the encoding correctly
        ics_file = r.text

        # step 3: delete ics file
        r = requests.post(
            "https://www.abfall-kreis-tuebingen.de/wp-admin/admin-ajax.php",
            data={"action": "execute_remove_ics"},
        )

        # parse ics file
        calender = icalendar.Calendar.from_ical(ics_file)

        entries = []
        for e in calender.walk():
            if e.name == "VEVENT":
                dtstart = e.get("dtstart").dt.date()
                summary = str(e.get("summary"))
                entries.append(CollectionAppointment(dtstart, summary))

        return entries
