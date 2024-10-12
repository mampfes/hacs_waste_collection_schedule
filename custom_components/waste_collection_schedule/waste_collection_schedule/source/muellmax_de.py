from html.parser import HTMLParser

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS
from waste_collection_schedule.service.MuellmaxDe import SERVICE_MAP

TITLE = "Müllmax"
DESCRIPTION = "Source for Müllmax waste collection."
URL = "https://www.muellmax.de"


def EXTRA_INFO():
    return [
        {
            "title": s["title"],
            "url": s["url"],
            "default_params": {"service": s["service_id"]},
        }
        for s in SERVICE_MAP
    ]


TEST_CASES = {
    "Rhein-Sieg-Kreis, Alfter": {
        "service": "Rsa",
        "mm_frm_ort_sel": "Alfter",
        "mm_frm_str_sel": "Ahrweg (105-Ende/94-Ende)",
    },
    "Münster, Achatiusweg": {"service": "Awm", "mm_frm_str_sel": "Achatiusweg"},
    "Hal, Postweg": {"service": "Hal", "mm_frm_str_sel": "Postweg"},
    "giessen": {
        "service": "Lkg",
        "mm_frm_ort_sel": "Langgöns",
        "mm_frm_str_sel": "Hauptstraße",
    },
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
}

PARAM_TRANSLATIONS = {
    "de": {
        "service": "Service",
        "mm_frm_ort_sel": "Ort",
        "mm_frm_str_sel": "Straße",
        "mm_frm_hnr_sel": "Hausnummer",
    },
}


# Parser for HTML checkbox
class InputCheckboxParser(HTMLParser):
    def __init__(self, startswith):
        super().__init__()
        self._startswith = startswith
        self._value = {}

    @property
    def value(self):
        return self._value

    def handle_starttag(self, tag, attrs):
        if tag == "input":
            d = dict(attrs)
            if d.get("name", "").startswith(self._startswith):
                self._value[d["name"]] = d.get("value")


# Parser for HTML input (hidden) text
class InputTextParser(HTMLParser):
    def __init__(self, **identifiers):
        super().__init__()
        self._identifiers = identifiers
        self._value = None

    @property
    def value(self):
        return self._value

    def handle_starttag(self, tag, attrs):
        if tag == "input":
            d = dict(attrs)
            for key, value in self._identifiers.items():
                if key not in d or d[key] != value:
                    return
            self._value = d.get("value")


class Source:
    def __init__(
        self, service, mm_frm_ort_sel=None, mm_frm_str_sel=None, mm_frm_hnr_sel=None
    ):
        self._service = service
        self._mm_frm_ort_sel = mm_frm_ort_sel
        self._mm_frm_str_sel = mm_frm_str_sel
        self._mm_frm_hnr_sel = mm_frm_hnr_sel
        self._ics = ICS()

    def fetch(self):
        mm_ses = InputTextParser(name="mm_ses")

        url = f"https://www.muellmax.de/abfallkalender/{self._service.lower()}/res/{self._service}Start.php"
        r = requests.get(url, headers=HEADERS)
        mm_ses.feed(r.text)

        # select "Abfuhrtermine", returns ort or an empty street search field
        args = {"mm_ses": mm_ses.value, "mm_aus_ort.x": 0, "mm_aus_ort.x": 0}
        r = requests.post(url, data=args, headers=HEADERS)
        mm_ses.feed(r.text)

        if self._mm_frm_ort_sel is not None:
            # select city
            args = {
                "mm_ses": mm_ses.value,
                "xxx": 1,
                "mm_frm_ort_sel": self._mm_frm_ort_sel,
                "mm_aus_ort_submit": "weiter",
            }
            r = requests.post(url, data=args, headers=HEADERS)
            mm_ses.feed(r.text)

        if self._mm_frm_str_sel is not None:
            # select street
            args = {
                "mm_ses": mm_ses.value,
                "xxx": 1,
                "mm_frm_str_sel": self._mm_frm_str_sel,
                "mm_aus_str_sel_submit": "suchen",
            }
            r = requests.post(url, data=args, headers=HEADERS)
            mm_ses.feed(r.text)

        if self._mm_frm_hnr_sel is not None:
            # select house number
            args = {
                "mm_ses": mm_ses.value,
                "xxx": 1,
                "mm_frm_hnr_sel": self._mm_frm_hnr_sel,
                "mm_aus_hnr_sel_submit": "weiter",
            }
            r = requests.post(url, data=args, headers=HEADERS)
            mm_ses.feed(r.text)

        # select to get ical
        args = {"mm_ses": mm_ses.value, "xxx": 1, "mm_ica_auswahl": "iCalendar-Datei"}
        r = requests.post(url, data=args, headers=HEADERS)
        mm_ses.feed(r.text)

        mm_frm_fra = InputCheckboxParser(startswith="mm_frm_fra")
        mm_frm_fra.feed(r.text)

        # get ics file
        args = {"mm_ses": mm_ses.value, "xxx": 1, "mm_frm_type": "termine"}
        args.update(mm_frm_fra.value)
        args.update({"mm_ica_gen": "iCalendar-Datei laden"})
        r = requests.post(url, data=args, headers=HEADERS)
        mm_ses.feed(r.text)

        entries = []

        # parse ics file
        try:
            dates = self._ics.convert(r.text)
        except ValueError as e:
            raise ValueError(
                "Got invalid response from the server, please recheck your arguments"
            ) from e

        entries = []
        for d in dates:
            entries.append(Collection(d[0], d[1]))
        return entries
