import urllib.parse
from html.parser import HTMLParser

import requests
from bs4 import BeautifulSoup
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
    "Neureutherstr. 8": {
        "street": "Neureutherstr.",
        "house_number": "8",
        "r_collect_cycle": "1/2;G",
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
    ):
        self._street = street
        self._hnr = house_number
        self._ics = ICS()
        self._r_collect_cycle = r_collect_cycle
        self._b_collect_cycle = b_collect_cycle
        self._p_collect_cycle = p_collect_cycle

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
        ics_action_url = ""
        page_soup = BeautifulSoup(r.text, "html.parser")
        if download_link := page_soup.find("a", {"class": "downloadics"}):
            ics_action_url = download_link.get("href")
        else:
            action_url, args = self._get_html_form_infos(r.text, "abfuhrkalender")

            error_message = ""

            for key in ("B", "P", "R"):
                if (
                    f"tx_awmabfuhrkalender_abfuhrkalender[leerungszyklus][{key}]"
                    not in args
                ):
                    if self.__getattribute__(f"_{key.lower()}_collect_cycle") == "":
                        cycle_options = {}
                        cycle_options = page_soup.find(
                            "form", id="abfuhrkalender"
                        ).find_all("option")

                        error_message += f"Optional parameter {key.lower()}_collect_cycle required. Possible values: "
                        for option in cycle_options:
                            error_message += f"{option.get("value")} ({option.text})   "
                    else:
                        args[
                            f"tx_awmabfuhrkalender_abfuhrkalender[leerungszyklus][{key}]"
                        ] = self.__getattribute__(f"_{key.lower()}_collect_cycle")

            if error_message:
                raise ValueError(error_message)

            r = s.post(
                action_url,
                data=args,
            )
            r.raise_for_status()

            page_soup = BeautifulSoup(r.text, "html.parser")
            if download_link := page_soup.find("a", {"class": "downloadics"}):
                ics_action_url = download_link.get("href")
            else:
                raise ValueError("Unknown error getting ics link with cycle options.")

        # Download the ics.file
        r = s.get(f"{URL}{urllib.parse.unquote(ics_action_url)}")
        r.raise_for_status()

        dates = self._ics.convert(r.text)

        entries = []
        for d in dates:
            bin_type = d[1].split(",")[0].strip()

            entries.append(Collection(d[0], bin_type, ICON_MAP.get(bin_type)))

        return entries

    def _get_html_form_infos(self, html: str, form_name: str) -> (str, {}, {}):
        """Returns a tuple with form action url and hidden form fields"""

        # collect the url where we post to
        page_soup = BeautifulSoup(html, "html.parser")
        form_soup = page_soup.find("form", id=form_name)
        action_url = f"{URL}{urllib.parse.unquote(form_soup.get("action"))}"

        # collect the hidden input fiels
        parser = HiddenInputParser()
        parser.feed(page_soup.find("form", id=form_name).decode_contents())

        return action_url, parser.args
