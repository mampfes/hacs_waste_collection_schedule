import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import (
    SourceArgumentException,
)
from waste_collection_schedule.service.ICS import ICS

TITLE = "Landkreis Helmstedt"
DESCRIPTION = "Source for Landkreis Helmstedt."
URL = "landkreis-helmstedt.de"
TEST_CASES = {
    "Grasleben": {
        "municipal": "Grasleben und Velpke",
        "restabfall": 1,
        "bioabfall": 1,
        "gelber_sack": 3,
        "altpapier": 5,
    },
    "Paläon": {
        "municipal": "Schöningen und Heeseberg",
        "restabfall": 1,
        "bioabfall": 1,
        "gelber_sack": 1,
        "altpapier": 2,
    },
    "Rhode": {
        "municipal": "Nord-Elm und Königslutter Ortsteile",
        "restabfall": 2,
        "bioabfall": 2,
        "gelber_sack": 1,
        "altpapier": 2,
    },
    "Essehof": {
        "municipal": "Lehre",
        "restabfall": 1,
        "bioabfall": 1,
        "gelber_sack": 2,
        "altpapier": 1,
    },
    "Braunschweiger Str.": {
        "municipal": "Königslutter Stadtgebiet",
        "restabfall": 1,
        "bioabfall": 1,
        "gelber_sack": 1,
        "altpapier": 1,
    },
    "Barmke": {
        "municipal": "Helmstedt und Ortsteile",
        "restabfall": 3,
        "bioabfall": 3,
        "gelber_sack": 3,
        "altpapier": 5,
    },
}

API_URL = "https://www.landkreis-helmstedt.de/buerger-leben/bauen-wohnen/abfallentsorgung/abfuhrkalender/"
HEADERS = {
    "user-agent": "Mozilla",
}

# ### Arguments affecting the configuration GUI ####

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {  # Optional dictionary to describe how to get the arguments, will be shown in the GUI configuration form above the input fields, does not need to be translated in all languages
    "en": "Visit "
    + API_URL
    + " and first get the name of the ICS calendar on the website for your municipal, then open the related PDF calendar and find the collection areas.",
    "de": "Öffne "
    + API_URL
    + " und find den Name des ICS Kalenders deiner Gemeinde heraus. Öffne danach den PDF Kalender und suche die passenden Abholgebiete.",
}

PARAM_DESCRIPTIONS = {  # Optional dict to describe the arguments, will be shown in the GUI configuration below the respective input field
    "en": {
        "municipal": 'Copy the name of the ICS calendar from the website for your municipal. This needs to be without the year at the end. For example: "Stadt Königslutter am Elm – ohne Ortsteile" (without quotes).',
        "restabfall": "Number for the collection type from the PDF calendar",
        "altpapier": "Number for the collection type from the PDF calendar",
        "gelber_sack": "Number for the collection type from the PDF calendar",
        "bioabfall": "Number for the collection type from the PDF calendar",
    },
    "de": {
        "municipal": 'Kopiere den Namen des ICS Kalenders der Gemeinde von der Website. Der Name darf nicht das Jahr beinhalten. Z.B. "Stadt Königslutter am Elm – ohne Ortsteile" (ohne Anführungszeichen).',
        "restabfall": "Nummer des Abfuhrgebietes aus dem PDF Kalender.",
        "altpapier": "Nummer des Abfuhrgebietes aus dem PDF Kalender.",
        "gelber_sack": "Nummer des Abfuhrgebietes aus dem PDF Kalender.",
        "bioabfall": "Nummer des Abfuhrgebietes aus dem PDF Kalender.",
    },
}

PARAM_TRANSLATIONS = {  # Optional dict to translate the arguments, will be shown in the GUI configuration form as placeholder text
    "en": {
        "municipal": "Municipal",
        "restabfall": "Domestic",
        "altpapier": "Paper",
        "gelber_sack": "Recycling",
        "bioabfall": "Organic",
    },
    "de": {
        "municipal": "Gemeinde",
        "restabfall": "Restabfall",
        "altpapier": "Altpapier",
        "gelber_sack": "Gelber Sack",
        "bioabfall": "Bioabfall",
    },
}

# ### End of arguments affecting the configuration GUI ####


COLLECTION_TYPE_RESTABFALL = "Restabfall"
COLLECTION_TYPE_ALTPAPIER = "Altpapier"
COLLECTION_TYPE_GELBER_SACK = "Gelber Sack"
COLLECTION_TYPE_BIOABFALL = "Bioabfall"


ICON_MAP = {
    COLLECTION_TYPE_RESTABFALL: "mdi:trash-can",
    COLLECTION_TYPE_ALTPAPIER: "mdi:package-variant",
    COLLECTION_TYPE_GELBER_SACK: "mdi:recycle",
    COLLECTION_TYPE_BIOABFALL: "mdi:leaf",
}


class Source:
    def __init__(
        self,
        municipal: str,
        restabfall: int,
        altpapier: int,
        gelber_sack: int,
        bioabfall: int,
    ):
        self._municipal: str = municipal
        self._restabfall: int = restabfall
        self._altpapier: int = altpapier
        self._gelber_sack: int = gelber_sack
        self._bioabfall: int = bioabfall
        self._ics = ICS()

    def fetch(self):
        r = requests.get(API_URL, headers=HEADERS)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        icsCalendarsForLandkreisHelmstedt = soup.select(
            '.abfrage2 .manager_titel [title="herunterladen/öffnen"]'
        )
        foundMunicipalCalendarICSDownloadURL = ""

        for icsCalendarDownloadLink in icsCalendarsForLandkreisHelmstedt:
            if not icsCalendarDownloadLink:
                continue
            href = icsCalendarDownloadLink.get("href")
            href_name = icsCalendarDownloadLink.getText()
            if not isinstance(href, str):
                continue
            if href_name.startswith(self._municipal):
                foundMunicipalCalendarICSDownloadURL = href
                break

        if not foundMunicipalCalendarICSDownloadURL:
            raise SourceArgumentException(
                argument="municipal",
                message="No Abholgebiet found for "
                + self._municipal
                + ". Please check "
                + API_URL
                + " for correct ICS calendar name.",
            )

        r = requests.get(foundMunicipalCalendarICSDownloadURL, headers=HEADERS)
        r.raise_for_status()

        dates = self._ics.convert(r.text)
        elements = []

        missingAltpapier = True
        missingBioabfall = True
        missingGelberSack = True
        missingRestabfall = True

        for d in dates:
            type = d[1]
            date = d[0]
            pickUpArea = type[-1:]
            pickUpType = type[:-2]

            addDate = False
            if pickUpType == COLLECTION_TYPE_ALTPAPIER:
                if pickUpArea == str(self._altpapier):
                    addDate = True
                    missingAltpapier = False
            elif pickUpType == COLLECTION_TYPE_BIOABFALL:
                if pickUpArea == str(self._bioabfall):
                    addDate = True
                    missingBioabfall = False
            elif pickUpType == COLLECTION_TYPE_GELBER_SACK:
                if pickUpArea == str(self._gelber_sack):
                    addDate = True
                    missingGelberSack = False
            elif pickUpType == COLLECTION_TYPE_RESTABFALL:
                if pickUpArea == str(self._restabfall):
                    addDate = True
                    missingRestabfall = False

            if addDate:
                elements.append(
                    Collection(
                        date=date,  # Collection date
                        t=pickUpType,  # Collection type
                        icon=ICON_MAP.get(pickUpType),  # Collection icon
                    )
                )

        self.abort_when_missing_collection_types(
            missingAltpapier, missingBioabfall, missingGelberSack, missingRestabfall
        )

        return elements

    def abort_when_missing_collection_types(
        self, missingAltpapier, missingBioabfall, missingGelberSack, missingRestabfall
    ):
        if missingGelberSack:
            raise SourceArgumentException(
                argument="gelber_sack",
                message="Check PDF calendar for valid collection areas.",
            )
        if missingAltpapier:
            raise SourceArgumentException(
                argument="altpapier",
                message="Check PDF calendar for valid collection areas.",
            )
        if missingBioabfall:
            raise SourceArgumentException(
                argument="bioabfall",
                message="Check PDF calendar for valid collection areas.",
            )
        if missingRestabfall:
            raise SourceArgumentException(
                argument="restabfall",
                message="Check PDF calendar for valid collection areas.",
            )
