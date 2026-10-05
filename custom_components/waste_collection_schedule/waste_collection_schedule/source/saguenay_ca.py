from datetime import date
from typing import ClassVar, final

from bs4 import BeautifulSoup
from waste_collection_schedule import parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import location_id
from waste_collection_schedule.transformers import ICSTransformer

_CALENDAR_URL = "https://ville.saguenay.ca/collecte_calendrier"

# The calendar marks a day with ``collecte-type-N``; one day may carry several.
_TYPES = {
    "collecte-type-1": "Ordures",
    "collecte-type-2": "Recyclage",
    "collecte-type-3": "Compostage",
}


def _rows(response, source) -> list[tuple[date, str]]:
    """One ``(date, label)`` row per marked day of the page's calendar.

    The year is only in the page title ("Calendrier des matières résiduelles
    2026"); each month is an ``<article class="month-N">`` of day articles.
    """
    soup = BeautifulSoup(response.text, "html.parser")
    title = soup.find("h1")
    if title is None:
        raise ValueError("Could not find page title to extract year")
    year = int(title.text.strip().split()[-1])

    rows = []
    for month in range(1, 13):
        month_article = soup.find("article", class_=f"month-{month}")
        if month_article is None:
            continue
        for day_article in month_article.find_all("article"):
            classes = day_article.get("class", [])
            span = day_article.find("span")
            if span is None or not span.text.strip():
                continue
            for css_class, label in _TYPES.items():
                if css_class in classes:
                    rows.append((date(year, month, int(span.text.strip())), label))
    return rows


@final
class Source(BaseSource):
    TITLE = "Ville de Saguenay"
    DESCRIPTION = "Source for ville.saguenay.ca waste collection calendar"
    URL = "https://ville.saguenay.ca"
    COUNTRY = "ca"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.ORGANIC, wt.RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "Test 8773": {"batiment": 8773},
    }

    PARAMS = (location_id("batiment"),)

    HOWTO: ClassVar[dict] = {
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

    # Current year, then next year's calendar.
    retrieve = retrievers.FanOutRetriever(
        targets=lambda source, context: (0, 1),
        fetch=retrievers.Request(
            _CALENDAR_URL,
            params=lambda next_year, context, batiment, **_: {
                "batiment": batiment,
                "annee_suivante": next_year,
            },
        ),
    )
    parse = parsers.EachResponse(_rows)
    transform = ICSTransformer(
        type_value_map={
            "Ordures": wt.GENERAL_WASTE,
            "Recyclage": wt.RECYCLABLES,
            "Compostage": wt.ORGANIC,
        }
    )
