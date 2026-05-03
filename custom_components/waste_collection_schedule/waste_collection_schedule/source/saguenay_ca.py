from datetime import date

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "Ville de Saguenay"
DESCRIPTION = "Source for ville.saguenay.ca waste collection calendar"
URL = "https://ville.saguenay.ca"
TEST_CASES = {
    "Test 8773": {"batiment": 8773},
}

ICON_MAP = {
    "Ordures": "mdi:trash-can",
    "Recyclage": "mdi:recycle",
    "Compostage": "mdi:leaf",
}

PARAM_TRANSLATIONS = {
    "en": {
        "batiment": "Building ID",
    },
    "de": {
        "batiment": "Gebäude-ID",
    },
    "it": {
        "batiment": "ID edificio",
    },
    "fr": {
        "batiment": "Numéro de bâtiment",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "batiment": "Building ID (cle_batiment) from the AJAX request payload",
    },
    "de": {
        "batiment": "Gebäude-ID (cle_batiment) aus dem AJAX-Anfrage-Payload",
    },
    "it": {
        "batiment": "ID edificio (cle_batiment) dal payload della richiesta AJAX",
    },
    "fr": {
        "batiment": "Numéro de bâtiment (cle_batiment) dans la requête AJAX",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "1. Go to https://ville.saguenay.ca/services-aux-citoyens/environnement/horaire-des-collectes "
        "2. Open your browser's developer tools (F12) and go to the Network tab "
        "3. Enter your address in the search field "
        "4. Look for a request named 'collectesinfos' (URL: https://ville.saguenay.ca/ajax/collectes/collectesinfos) "
        "5. In the Payload tab, copy the value of 'cle_batiment' "
        "6. Use this number as the batiment parameter"
    ),
    "fr": (
        "1. Allez à https://ville.saguenay.ca/services-aux-citoyens/environnement/horaire-des-collectes "
        "2. Ouvrez les outils de développement de votre navigateur (F12) et allez à l'onglet Réseau "
        "3. Entrez votre adresse dans le champ de recherche "
        "4. Cherchez une requête nommée 'collectesinfos' (URL: https://ville.saguenay.ca/ajax/collectes/collectesinfos) "
        "5. Dans l'onglet Payload, copiez la valeur de 'cle_batiment' "
        "6. Utilisez ce numéro comme paramètre batiment"
    ),
}

URL_TEMPLATE = "https://ville.saguenay.ca/collecte_calendrier?batiment={batiment}&annee_suivante={next_year}"


class Source:
    def __init__(self, batiment: int):
        self._batiment = batiment

    def fetch(self) -> list[Collection]:
        entries = []
        for next_year in (0, 1):
            url = URL_TEMPLATE.format(batiment=self._batiment, next_year=next_year)
            r = requests.get(url)
            r.raise_for_status()

            soup = BeautifulSoup(r.text, "html.parser")

            # Extract year from title: "Calendrier des matières résiduelles 2026"
            title = soup.find("h1")
            if title is None:
                raise ValueError("Could not find page title to extract year")
            year = int(title.text.strip().split()[-1])

            # Iterate through each month (month-1 to month-12)
            for month_num in range(1, 13):
                month_article = soup.find("article", class_=f"month-{month_num}")
                if month_article is None:
                    continue

                for article in month_article.find_all("article"):
                    classes = article.get("class", [])
                    if not any(c.startswith("collecte-type-") for c in classes):
                        continue

                    span = article.find("span")
                    if span is None:
                        continue
                    day_text = span.text.strip()
                    if not day_text:
                        continue
                    day = int(day_text)

                    types = []
                    if "collecte-type-1" in classes:
                        types.append("Ordures")
                    if "collecte-type-2" in classes:
                        types.append("Recyclage")
                    if "collecte-type-3" in classes:
                        types.append("Compostage")

                    collection_date = date(year, month_num, day)
                    for waste_type in types:
                        entries.append(
                            Collection(
                                date=collection_date,
                                t=waste_type,
                                icon=ICON_MAP.get(waste_type),
                            )
                        )

        if not entries:
            raise SourceArgumentNotFound("batiment", self._batiment)

        return entries
