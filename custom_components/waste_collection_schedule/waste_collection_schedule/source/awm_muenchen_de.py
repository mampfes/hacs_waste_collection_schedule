import urllib.parse
from html.parser import HTMLParser
from typing import Tuple

import requests
from bs4 import BeautifulSoup, Tag
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentRequiredWithSuggestions
from waste_collection_schedule.service.ICS import ICS
import re
import logging

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
        "r_location_id": "70050134",
        "b_location_id": "70050134",
        "p_location_id": "70050134",
    },
    "Marienplatz 1": {
        "street": "Marienplatz",
        "house_number": "1",
        "r_collection_cycle_string": "001;U",
        "p_collection_cycle_string": "002;U"
    }
}

ICON_MAP = {
    "Restmülltonne": "mdi:delete",
    "Biotonne": "mdi:leaf",
    "Papiertonne": "mdi:newspaper",
    "Wertstofftonne": "mdi:recycle",
}

BASE_URL = "https://www.awm-muenchen.de"

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Fill in the street and house number, then submit. The form fields are tested one after the other and offer a selection of permitted values if necessary. Alternatively, enter known values directly. More details: https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/awm_muenchen_de.md",
    "de": "Straße und Hausnummer ausfüllen, dann abschicken. Die Formularfelder werden nacheinander getested und bieten ggf. eine Auswahl der zulässigen Werte an. Alternativ bekannt Werte direkt eingeben. Mehr Details: https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/awm_muenchen_de.md",
    "it": "Compilare la via e il numero civico, quindi inviare. I campi del modulo vengono testati uno dopo l'altro e possono offrire una selezione di valori consentiti. In alternativa, è possibile inserire direttamente i valori noti. Ulteriori dettagli: https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/awm_muenchen_de.md",
    "fr": "Remplir la rue et le numéro, puis envoyer. Les champs du formulaire sont testés les uns après les autres et proposent, le cas échéant, un choix de valeurs autorisées. Sinon, connu Saisir directement les valeurs. Plus de détails : https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/awm_muenchen_de.md",
}

PARAM_TRANSLATIONS = {
    "en": {
        "calendar_title": "Calendar name",
        "r_collection_cycle_string": "Residual waste emptying cycle (e.g. '1/2;G' or forum selection)",
        "b_collection_cycle_string": "Organic waste garbage can emptying cycle (e.g. '1/2;G' or form selection)",
        "p_collection_cycle_string": "Paper garbage can emptying cycle (e.g. '1/2;G' or form selection)",
        "r_location_id": "Residual waste location ID (e.g. '70027977' or forum selection)",
        "b_location_id": "Organic waste garbage can location ID (e.g. '70027977' or forum selection)",
        "p_location_id": "Paper garbage can location ID (e.g. '70027977' or forum selection)",
        "house_number": "House number",
        "street": "Street"
    },
    "de": {
        "calendar_title": "Kalender-Name",
        "r_collection_cycle_string": "Restmüll Leerungszyklus (z.B. '1/2;G' oder Forumularauswahl)",
        "b_collection_cycle_string": "Biotonne Leerungszyklus (z.B. '1/2;G' oder Forumularauswahl)",
        "p_collection_cycle_string": "Papiertonne Leerungszyklus (z.B. '1/2;G' oder Forumularauswahl)",
        "r_location_id": "Restmüll Standort-ID (z.B. '70027977' oder Forumularauswahl)",
        "b_location_id": "Biotonne Standort-ID (z.B. '70027977' oder Forumularauswahl)",
        "p_location_id": "Papiertonne Standort-ID (z.B. '70027977' oder Forumularauswahl)",
        "house_number": "Hausnummer",
        "street": "Straße"
    },
    "it": {
        "calendar_title" : "Nom du calendrier",
        "r_collection_cycle_string" : "cycle de vidage des déchets résiduels (par ex. '1/2;G' ou choix du formulaire)",
        "b_collection_cycle_string" : "Cycle de vidage des biodéchets (par ex. '1/2;G' ou sélection du formulaire)",
        "p_collection_cycle_string" : "Cycle de vidage de la poubelle à papier (par ex. '1/2;G' ou sélection du formulaire)",
        "r_location_id" : "ID de site des déchets résiduels (par exemple, '70027977' ou sélection de formulaire)",
        "b_location_id" : "ID de site de la poubelle bio (par exemple, '70027977' ou sélection du formulaire)",
        "p_location_id" : "ID du site de la poubelle à papier (par exemple, '70027977' ou sélection du formulaire)",
        "house_number" : "numéro de maison",
        "street" :"rue"
    },
    "fr": {
        "calendar_title" : "Nom du calendrier",
        "r_collection_cycle_string" : "cycle de vidage des déchets résiduels (par ex. '1/2;G' ou choix du formulaire)",
        "b_collection_cycle_string" : "Cycle de vidage des biodéchets (par ex. '1/2;G' ou sélection du formulaire)",
        "p_collection_cycle_string" : "Cycle de vidage de la poubelle à papier (par ex. '1/2;G' ou sélection du formulaire)",
        "r_location_id" : "ID de site des déchets résiduels (par exemple, '70027977' ou sélection de formulaire)",
        "b_location_id" : "ID de site de la poubelle bio (par exemple, '70027977' ou sélection du formulaire)",
        "p_location_id" : "ID du site de la poubelle à papier (par exemple, '70027977' ou sélection du formulaire)",
        "house_number" : "numéro de maison",
        "street" :"rue"
    },
}

_LOGGER = logging.getLogger(__name__)

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
        r_location_id: str="",
        b_location_id: str="",
        p_location_id: str="",
        r_collection_cycle_string: str="",
        b_collection_cycle_string: str="",
        p_collection_cycle_string: str=""
    ):
        self._street = street
        self._hnr = house_number
        self._ics = ICS()
        self._r_location_id = r_location_id
        self._b_location_id = b_location_id
        self._p_location_id = p_location_id
        self._r_collection_cycle_string = r_collection_cycle_string
        self._b_collection_cycle_string = b_collection_cycle_string
        self._p_collection_cycle_string = p_collection_cycle_string

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
        _LOGGER.debug("got first response after address.")

        # We have POSTed the address. Now there are four follow-up options (error paths excluded):
        # 1. Download ICS already
        # 2. Enter location ids -> POST and download
        # 3. Enter collection cycle strings -> POST and download
        # 4. Enter location ids -> POST, collection cycle strings -> POST and download
        entries = []
        page_soup = BeautifulSoup(r.text, "html.parser")
        if download_links := page_soup.find_all("a", {"class": "downloadics"}):
            # This means we have found the ICS download link right away and can download.
            for download_link in download_links:
                self._retrieve_and_append_entries(s, download_link, entries)
            if len(entries) == 0:
                raise ValueError("The provided arguments (street and house number) were accepted by the AWM server, but 0 calendar entries were retrieved. This may be a temporary issue.")
            _LOGGER.info("Got ICS with "+str(len(entries))+" entries.")
            return entries

        _LOGGER.debug("No ICS-Link, continueing in code...")

        # This means we must provide the form with additional arguments
        # * depending on the address: stellplatz[bio|papier|restmuell]: location IDs, from the selections in the web forms
        # * depending on the address: leerungszyklus[B|P|R]: collection cycle strings, from the selections in the web forms
        action_url, args = self._get_html_form_infos(r.text, "abfuhrkalender")

        # So, let's see if we need to collect / provide the location IDs...
        # =================================================================
        r_location_id_options = []
        b_location_id_options = []
        p_location_id_options = []
        try:
            r_location_id_options = page_soup.find("select", id="tx_awmabfuhrkalender_abfuhrkalender[stellplatz][restmuell]").find_all("option")
        except:
            pass
        try:
            b_location_id_options = page_soup.find("select", id="tx_awmabfuhrkalender_abfuhrkalender[stellplatz][bio]").find_all("option")
        except:
            pass
        try:
            p_location_id_options = page_soup.find("select", id="tx_awmabfuhrkalender_abfuhrkalender[stellplatz][papier]").find_all("option")
        except:
            pass
        _LOGGER.debug("Location-ID options:")
        _LOGGER.debug(str(r_location_id_options))
        _LOGGER.debug(str(b_location_id_options))
        _LOGGER.debug(str(p_location_id_options))
        
        if len(r_location_id_options) > 0 or len(b_location_id_options) > 0 or len(p_location_id_options) > 0:
            _LOGGER.debug("Ok, we need location IDs.")
            # YES. We need to provide these, because at least one of R, B or P needs a selection.
            # Collect which ever are needed from the input and POST.
            # Note: We'll use a very dirty hack to extract the value we want from the HA form input / select. See comment below.
            # First, the Restmuell...
            if self._r_location_id == "":
                # Great, no location ID set, but do we really need one?
                if len(r_location_id_options) > 0:
                    # YES! Therefore, user must enter a value or select it from the drop down.
                    raise(
                        SourceArgumentRequiredWithSuggestions(
                            argument="r_location_id",
                            reason="multiple choices returned from AWM service.",
                            suggestions = [f"'{option.get('value')}' for {option.text}" for option in r_location_id_options]
                        )
                    )
                else:
                    # NO, not required. Don't add anything to the array.
                    pass
            else:
                # Ok, option was set in UI, e.g., to:
                # * """'12345678' for XYZ-Street 12""" from a suggestion, and with regex "\d+" we get 12345678
                # * """11122233""", because the user knows their location ID already, then with regex "\d+" we get 11122233
                args["tx_awmabfuhrkalender_abfuhrkalender[stellplatz][restmuell]"] = re.findall("\\d+", self._r_location_id)[0]
            
            # Second, the Biomuell...
            if self._b_location_id == "":
                if len(b_location_id_options) > 0:
                    raise(
                        SourceArgumentRequiredWithSuggestions(
                            argument="b_location_id",
                            reason="multiple choices returned from AWM service.",
                            suggestions = [f"'{option.get('value')}' for {option.text}" for option in b_location_id_options]
                        )
                    )
            else:
                args["tx_awmabfuhrkalender_abfuhrkalender[stellplatz][restmuell]"] = re.findall("\\d+", self._b_location_id)[0]
            
            # Third and last, the Papermuell...
            if self._p_location_id == "":
                if len(p_location_id_options) > 0:
                    raise(
                        SourceArgumentRequiredWithSuggestions(
                            argument="p_location_id",
                            reason="multiple choices returned from AWM service.",
                            suggestions = [f"'{option.get('value')}' for {option.text}" for option in p_location_id_options]
                        )
                    )
            else:
                args["tx_awmabfuhrkalender_abfuhrkalender[stellplatz][restmuell]"] = re.findall("\\d+", self._p_location_id)[0]
            _LOGGER.debug("Location-ID path, POSTing args:")
            _LOGGER.debug(str(args))

            r = s.post(
                action_url,
                data=args,
            )
            r.raise_for_status()            
            _LOGGER.debug("got second response after address + location IDs.")

            # Careful here: remember the scope of the variable "page_soup":
            # if we needed to provide location ids, this code here will overwrite the page_soup.
            # Therefore, now there are only two  options:
            # 1. download ICS right away
            # 2. new HTML contains selection for collection cycle strings
            page_soup = BeautifulSoup(r.text, "html.parser")
            if download_links := page_soup.find_all("a", {"class": "downloadics"}):
                # This means we have found the ICS download link after the location id selection and can download.
                for download_link in download_links:
                    self._retrieve_and_append_entries(s, download_link, entries)
                if len(entries) == 0:
                    raise ValueError("The provided arguments (street and house number, and location ids) were accepted by the AWM server, but 0 calendar entries were retrieved. This may be a temporary issue.")
                _LOGGER.info("Got ICS with "+str(len(entries))+" entries.")
                return entries
            action_url, args = self._get_html_form_infos(r.text, "abfuhrkalender")
            _LOGGER.debug("No ICS-Link, continueing in code...")
        
        # Ok, either the location IDs were not required, or not enough.
        # Let's see if we need to provide collection cycle strings...
        # =================================================================
        r_collection_cycle_options = []
        b_collection_cycle_options = []
        p_collection_cycle_options = []
        try:
            r_collection_cycle_options = page_soup.find("select", {"name": "tx_awmabfuhrkalender_abfuhrkalender[leerungszyklus][R]"}).find_all("option")
        except:
            pass
        try:
            b_collection_cycle_options = page_soup.find("select", {"name": "tx_awmabfuhrkalender_abfuhrkalender[leerungszyklus][B]"}).find_all("option")
        except:
            pass
        try:
            p_collection_cycle_options = page_soup.find("select", {"name": "tx_awmabfuhrkalender_abfuhrkalender[leerungszyklus][P]"}).find_all("option")
        except:
            pass
        _LOGGER.debug("Collection Cycle String options:")
        _LOGGER.debug(str(r_collection_cycle_options))
        _LOGGER.debug(str(b_collection_cycle_options))
        _LOGGER.debug(str(p_collection_cycle_options))

        if len(r_collection_cycle_options) > 0 or len(b_collection_cycle_options) > 0 or len(p_collection_cycle_options) > 0:
            # YES. We need to provide these, becaue either R, B or P needs a selection.
            # Collect which ever are needed from the input and POST.
            # Note: We'll use a very dirty hack to extract the value we want from the HA form input / select. See comment below.
            # First, the Restmuell...
            if self._r_collection_cycle_string == "":
                # Great, no collection cycle string set, but do we really need one?
                if len(r_collection_cycle_options) > 0:
                    # YES! Therefore, user must enter a value or select it from the drop down.
                    raise(
                        SourceArgumentRequiredWithSuggestions(
                            argument="r_collection_cycle_string",
                            reason="multiple choices returned from AWM service.",
                            suggestions = [f"'{option.get('value')}' for {option.text}" for option in r_collection_cycle_options]
                        )
                    )
                else:
                    # NO, not required. Don't add anything to the array.
                    pass
            else:
                # Ok, option was set in UI, e.g. to:
                # * """'001;U' for 1x pro Woche""", and with regex "(?:\d{3}|\d\/\d);[A-Z]" we get 001;U
                # * ""'1/2;G""", because the user knows their collection cycle string already, then with regex "(?:\d{3}|\d\/\d);[A-Z]" we get 1/2;G
                args["tx_awmabfuhrkalender_abfuhrkalender[leerungszyklus][R]"] = re.findall("(?:\\d{3}|\\d\\/\\d);[A-Z]", self._r_collection_cycle_string)[0]

            # Second, the Biomuell...
            if self._b_collection_cycle_string == "":
                if len(b_collection_cycle_options) > 0:
                    raise(
                        SourceArgumentRequiredWithSuggestions(
                            argument="b_collection_cycle_string",
                            reason="multiple choices returned from AWM service.",
                            suggestions = [f"'{option.get('value')}' for {option.text}" for option in b_collection_cycle_options]
                        )
                    )
            else:
                args["tx_awmabfuhrkalender_abfuhrkalender[leerungszyklus][B]"] = re.findall("(?:\\d{3}|\\d\\/\\d);[A-Z]", self._b_collection_cycle_string)[0]

            # Third, the Papermuell...
            if self._p_collection_cycle_string == "":
                if len(p_collection_cycle_options) > 0:
                    raise(
                        SourceArgumentRequiredWithSuggestions(
                            argument="p_collection_cycle_string",
                            reason="multiple choices returned from AWM service.",
                            suggestions = [f"'{option.get('value')}' for {option.text}" for option in p_collection_cycle_options]
                        )
                    )
            else:
                args["tx_awmabfuhrkalender_abfuhrkalender[leerungszyklus][P]"] = re.findall("(?:\\d{3}|\\d\\/\\d);[A-Z]", self._p_collection_cycle_string)[0]

            r = s.post(
                action_url,
                data=args,
            )
            r.raise_for_status()
            _LOGGER.debug("got third response after address [+ location IDs ?] + collection cycle strings.")

            # After this POST, there must be the link for the ICS.
            page_soup = BeautifulSoup(r.text, "html.parser")
            if download_links := page_soup.find_all("a", {"class": "downloadics"}):
                # This means we have found the ICS download link after the location id selection, and the collection-cycle-string input and can download.
                for download_link in download_links:
                    self._retrieve_and_append_entries(s, download_link, entries)
                if len(entries) == 0:
                    raise ValueError("The provided arguments (street and house number, location ids, and collection cycles) were accepted by the AWM server, but 0 calendar entries were retrieved. This may be a temporary issue.")
                return entries

        raise ValueError("Unknown error getting ICS link with calendar entries from AWM server.")

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
