import urllib.parse
from html.parser import HTMLParser
from typing import Tuple

import requests
from bs4 import BeautifulSoup, Tag
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "AWM München"
DESCRIPTION = "Source for AWM München."
URL = "https://www.awm-muenchen.de"
TEST_CASES = {
    "Waltenbergerstr. 1": {
        "street": "Waltenbergerstr.",
        "house_number": "1",
    },
    "Geretsrieder Str. 10a": {
        "street": "Geretsrieder Str.",
        "house_number": "10a",
    },
    "Bellinzonastraße 19": {
        "street": "Bellinzonastr.",
        "house_number": "19",
        "r_collect_cycle": "001;U",
        "b_collect_cycle": "1/2;G",
        "p_collect_cycle": "1/2;U",
        "restmuell_location_id": "70050134",
        "bio_location_id": "70050134",
        "papier_location_id": "70050134",
    },
}

ICON_MAP = {
    "Restmülltonne": "mdi:delete",
    "Biotonne": "mdi:leaf",
    "Papiertonne": "mdi:newspaper",
    "Wertstofftonne": "mdi:recycle",
}

BASE_URL = "https://www.awm-muenchen.de"


# Parser for HTML input (hidden) text
class HiddenInputParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self._args = {}

    @property
    def args(self):
        return self._args

    def handle_starttag(self, tag, attrs):
        if tag == "input":
            d = dict(attrs)
            if str(d["type"]).lower() == "hidden":
                self._args[d["name"]] = d["value"] if "value" in d else ""


class Source:
    def __init__(
        self,
        street: str,
        house_number: str,
        r_collect_cycle="",
        b_collect_cycle="",
        p_collect_cycle="",
        restmuell_location_id="",
        bio_location_id="",
        papier_location_id=""
    ):
        self._street = street
        self._hnr = house_number
        self._ics = ICS()
        self._r_collect_cycle = r_collect_cycle
        self._b_collect_cycle = b_collect_cycle
        self._p_collect_cycle = p_collect_cycle
        self._restmuell_location_id = restmuell_location_id
        self._bio_location_id       = bio_location_id
        self._papier_location_id    = papier_location_id

    def fetch(self):
        s = requests.session()

        # special request header is required, server backend checks for Origin
        headers = {
            "Origin": "https://www.awm-muenchen.de",
        }
        s.headers.update(headers)

        # request default page
        r = s.get(f"{BASE_URL}/entsorgen/abfuhrkalender")
        r.raise_for_status()
        r.encoding = "utf-8"

        step1_action_url, args = self._get_html_form_infos(r.text, "abfuhrkalender")

        # add the address information
        args["tx_awmabfuhrkalender_abfuhrkalender[strasse]"] = self._street
        args["tx_awmabfuhrkalender_abfuhrkalender[hausnummer]"] = self._hnr
        args["tx_awmabfuhrkalender_abfuhrkalender[section]"] = "address"
        args["tx_awmabfuhrkalender_abfuhrkalender[submitAbfuhrkalender]"] = "true"

        # ready for step 1 - we post the address
        r = s.post(
            step1_action_url,
            data=args,
        )
        r.raise_for_status()

        # result is the result page or the collection cycle select page
        entries = []
        page_soup = BeautifulSoup(r.text, "html.parser")
        if download_links := page_soup.find_all("a", {"class": "downloadics"}):
            # This means we have found the ICS download link right away and can download.
            for download_link in download_links:
                self._retrieve_and_append_entries(s, download_link, entries)
        else:
            # This means we must provide the form with additional arguments
            # * leerungszyklus[R|B|P]: arbitrary strings, are not shown in the web page
            # * section: ics
            # * singlestandplatz: false
            # * standplatzwahl: true
            # * stellplatz[bio|papier|restmuell]: location IDs, from the selections in the web forms
            action_url, args = self._get_html_form_infos(r.text, "abfuhrkalender")
            error_message = ""

            # Let's hard-code each parameter for better readability...
            if self._r_collect_cycle == "":
                error_message += f"\nParameter 'r_collect_cycle' required. See documentation."
            else:
                args["tx_awmabfuhrkalender_abfuhrkalender[leerungszyklus][R]"] = self._r_collect_cycle
            if self._b_collect_cycle == "":
                error_message += f"\nParameter 'b_collect_cycle' required. See documentation."
            else:
                args["tx_awmabfuhrkalender_abfuhrkalender[leerungszyklus][B]"] = self._b_collect_cycle
            if self._p_collect_cycle == "":
                error_message += f"\nParameter 'p_collect_cycle' required. See documentation."
            else:
                args["tx_awmabfuhrkalender_abfuhrkalender[leerungszyklus][P]"] = self._p_collect_cycle
            # add the constant arguments
            args["section"] = "ics"
            args["singlestandplatz"] = "false"
            args["standplatzwahl"] = "true"
            
            # now the location ids...
            if self._restmuell_location_id == "":
                error_message += f"\nParameter 'restmuell_location_id' required. Possible numeric values are: "
                cycle_options = {}
                cycle_options = page_soup.find("select", id="tx_awmabfuhrkalender_abfuhrkalender[stellplatz][restmuell]").find_all("option")
                for option in cycle_options:
                    error_message += f"\n• '{option.get('value')}' for {option.text}"
            else:
                args["tx_awmabfuhrkalender_abfuhrkalender[stellplatz][restmuell]"] = self._restmuell_location_id
            
            if self._bio_location_id == "":
                error_message += f"\nParameter 'bio_location_id' required. Possible numeric values are: "
                cycle_options = {}
                cycle_options = page_soup.find("select", id="tx_awmabfuhrkalender_abfuhrkalender[stellplatz][bio]").find_all("option")
                for option in cycle_options:
                    error_message += f"\n• '{option.get('value')}' for {option.text}"
            else:
                args["tx_awmabfuhrkalender_abfuhrkalender[stellplatz][bio]"] = self._bio_location_id
            
            if self._papier_location_id == "":
                error_message += f"\nParameter 'papier_location_id' required. Possible numeric values are: "
                cycle_options = {}
                cycle_options = page_soup.find("select", id="tx_awmabfuhrkalender_abfuhrkalender[stellplatz][papier]").find_all("option")
                for option in cycle_options:
                    error_message += f"\n• '{option.get('value')}' for {option.text}"
            else:
                args["tx_awmabfuhrkalender_abfuhrkalender[stellplatz][papier]"] = self._papier_location_id

            if error_message:
                raise ValueError(error_message)

            r = s.post(
                action_url,
                data=args,
            )
            r.raise_for_status()

            page_soup = BeautifulSoup(r.text, "html.parser")
            if download_links := page_soup.find_all("a", {"class": "downloadics"}):
                for download_link in download_links:
                    self._retrieve_and_append_entries(s, download_link, entries)
            else:
                raise ValueError("Unknown error getting ics link with cycle options.")

        return entries

    def _retrieve_and_append_entries(
        self, s: requests.Session, download_link: Tag, entries: list
    ):
        ics_action_url = download_link.get("href")
        r = s.get(f"{URL}{urllib.parse.unquote(ics_action_url)}")
        r.raise_for_status()

        dates = self._ics.convert(r.text)

        for d in dates:
            bin_type = d[1].split(",")[0].replace("Achtung:", "").strip()
            entries.append(Collection(d[0], bin_type, ICON_MAP.get(bin_type)))

    def _get_html_form_infos(self, html: str, form_name: str) -> Tuple[str, dict]:
        """Return a tuple with form action url and hidden form fields."""
        # collect the url where we post to
        page_soup = BeautifulSoup(html, "html.parser")
        form_soup = page_soup.find("form", id=form_name)
        action_url = f"{URL}{urllib.parse.unquote(form_soup.get('action'))}"

        # collect the hidden input fields
        parser = HiddenInputParser()
        parser.feed(page_soup.find("form", id=form_name).decode_contents())

        return action_url, parser.args
