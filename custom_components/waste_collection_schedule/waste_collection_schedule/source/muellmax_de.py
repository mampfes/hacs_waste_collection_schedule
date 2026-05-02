from html.parser import HTMLParser

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
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
    # "Rhein-Sieg-Kreis, Alfter": {
    #     "service": "Rsa",
    #     "mm_frm_ort_sel": "Alfter",
    #     "mm_frm_str_sel": "Ahrweg (105-Ende/94-Ende)",
    # },
    # "Münster, Achatiusweg": {"service": "Awm", "mm_frm_str_sel": "Achatiusweg"},
    # "Hal, Postweg": {"service": "Hal", "mm_frm_str_sel": "Postweg"},
    # "giessen": {
    #     "service": "Lkg",
    #     "mm_frm_ort_sel": "Langgöns",
    #     "mm_frm_str_sel": "Hauptstraße",
    # },
    "USB Freiligrathstraße 55": {
        "service": "Usb",
        "mm_frm_str_sel": "Freiligrathstraße",
        "mm_frm_hnr_sel": "44791;Innenstadt;55;",
    },
    "ASH Schäferstraße 49 (plain number)": {
        "service": "Ash",
        "mm_frm_str_sel": "Schäferstraße",
        "mm_frm_hnr_sel": "49",
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


# Parser for HTML select options
class SelectOptionParser(HTMLParser):
    def __init__(self, select_name):
        super().__init__()
        self._select_name = select_name
        self._in_select = False
        self._options = []

    @property
    def options(self):
        return self._options

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "select" and d.get("name") == self._select_name:
            self._in_select = True
        if tag == "option" and self._in_select:
            value = d.get("value", "")
            if value:
                self._options.append(value)

    def handle_endtag(self, tag):
        if tag == "select":
            self._in_select = False


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
        self,
        service,
        mm_frm_ort_sel=None,
        mm_frm_str_sel=None,
        mm_frm_hnr_sel=None,
    ):
        self._service = service
        self._mm_frm_ort_sel = mm_frm_ort_sel
        self._mm_frm_str_sel = mm_frm_str_sel
        self._mm_frm_hnr_sel = mm_frm_hnr_sel
        self._ics = ICS()

    def fetch(self):
        mm_ses = InputTextParser(name="mm_ses")

        url = (
            f"https://www.muellmax.de/abfallkalender/"
            f"{self._service.lower()}/res/"
            f"{self._service}Start.php"
        )
        session = requests.Session()
        r = session.get(url, headers=HEADERS)
        mm_ses.feed(r.text)

        # select "Abfuhrtermine", returns ort or an empty street search field
        args = {"mm_ses": mm_ses.value, "mm_aus_ort.x": 0, "mm_aus_ort.y": 0}
        r = session.post(url, data=args, headers=HEADERS)
        mm_ses.feed(r.text)

        if self._mm_frm_ort_sel is not None:
            # select city
            args = {
                "mm_ses": mm_ses.value,
                "xxx": 1,
                "mm_frm_ort_sel": self._mm_frm_ort_sel,
                "mm_aus_ort_submit": "weiter",
            }
            r = session.post(url, data=args, headers=HEADERS)
            mm_ses.feed(r.text)

        if self._mm_frm_str_sel is not None:
            # show street selection page
            args = {
                "mm_ses": mm_ses.value,
                "xxx": 1,
                "mm_frm_str_name": self._mm_frm_str_sel,
                "mm_aus_str_txt_submit": "suchen",
            }
            r = session.post(url, data=args, headers=HEADERS)
            mm_ses.feed(r.text)

            # select street
            args = {
                "mm_ses": mm_ses.value,
                "xxx": 1,
                "mm_frm_str_sel": self._mm_frm_str_sel,
                "mm_aus_str_sel_submit": "weiter",
            }
            r = session.post(url, data=args, headers=HEADERS)
            mm_ses.feed(r.text)

        # auto-detect if house number selection is required
        if "mm_frm_hnr_sel" in r.text:
            hnr_value = self._mm_frm_hnr_sel
            if hnr_value is None:
                op = SelectOptionParser("mm_frm_hnr_sel")
                op.feed(r.text)
                raise SourceArgumentNotFoundWithSuggestions(
                    "mm_frm_hnr_sel", "", op.options
                )

            # if user provided a plain number, match against dropdown options
            if ";" not in str(hnr_value):
                op = SelectOptionParser("mm_frm_hnr_sel")
                op.feed(r.text)
                matches = [o for o in op.options if o.split(";")[2] == str(hnr_value)]
                if len(matches) == 1:
                    hnr_value = matches[0]
                elif len(matches) == 0:
                    raise SourceArgumentNotFoundWithSuggestions(
                        "mm_frm_hnr_sel", str(hnr_value), op.options
                    )
                else:
                    raise SourceArgumentNotFoundWithSuggestions(
                        "mm_frm_hnr_sel", str(hnr_value), matches
                    )

            args = {
                "mm_ses": mm_ses.value,
                "xxx": 1,
                "mm_frm_hnr_sel": hnr_value,
                "mm_aus_hnr_sel_submit": "weiter",
            }
            r = session.post(url, data=args, headers=HEADERS)
            mm_ses.feed(r.text)

        # select to get ical
        args = {
            "mm_ses": mm_ses.value,
            "xxx": 1,
            "mm_ica_auswahl": "iCalendar-Datei",
        }
        r = session.post(url, data=args, headers=HEADERS)
        mm_ses.feed(r.text)

        mm_frm_fra = InputCheckboxParser(startswith="mm_frm_fra")
        mm_frm_fra.feed(r.text)

        # get ics file
        args = {"mm_ses": mm_ses.value, "xxx": 1, "mm_frm_type": "termine"}
        args.update(mm_frm_fra.value)
        args.update({"mm_ica_gen": "iCalendar-Datei laden"})
        r = session.post(url, data=args, headers=HEADERS)
        mm_ses.feed(r.text)

        entries = []

        # parse ics file
        try:
            dates = self._ics.convert(r.text)
        except ValueError as e:
            raise ValueError(
                "Got invalid response from the server, " "please recheck your arguments"
            ) from e

        entries = []
        for d in dates:
            entries.append(Collection(d[0], d[1]))
        return entries
