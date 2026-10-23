import json
import re
from typing import ClassVar, NamedTuple, final

from waste_collection_schedule import parsers, preprocessors
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    city,
    dropdown,
    municipality,
    street,
)
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.retrievers import FanOutRetriever, Lookup, Request
from waste_collection_schedule.transformers import JsonTransformer

HARMONOGRAMY_URL = "https://www.czystyregion.pl/Harmonogramy"
RODZAJ_CHOICES = ["wielorodzinna", "jednorodzinna", "firma"]


class _Form(NamedTuple):
    token: str
    gmina_id: str
    region_ids: tuple[str, ...]


def _strip_tags(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", text).strip()


def _form(response, gmina, miejscowosc, **_) -> _Form:
    """Resolve the commune and town against the dropdown data of the page."""
    html = response.text
    token = re.search(r'name="_token" value="([^"]*)"', html)
    block = re.search(r'id="gminy"[^>]*>(.*?)</select>', html, re.S)
    gminy = {
        name.strip(): gid
        for gid, name in re.findall(
            r'<option value="(\d*)">([^<]*)</option>', block.group(1) if block else ""
        )
        if gid
    }
    gmina_id = next(
        (gid for name, gid in gminy.items() if name.casefold() == gmina.casefold()),
        None,
    )
    if token is None or gmina_id is None:
        raise SourceArgumentNotFoundWithSuggestions("gmina", gmina, sorted(gminy))

    regiony_match = re.search(r"var regiony = (\[.*?\]);", html, re.S)
    regiony = json.loads(regiony_match.group(1)) if regiony_match else []
    in_gmina = [r for r in regiony if str(r.get("gmina_id")) == gmina_id]
    region_ids = tuple(
        str(r["id"])
        for r in in_gmina
        if str(r.get("name", "")).strip().casefold() == miejscowosc.casefold()
    )
    if not region_ids:
        raise SourceArgumentNotFoundWithSuggestions(
            "miejscowosc", miejscowosc, sorted({str(r.get("name")) for r in in_gmina})
        )
    return _Form(token.group(1), gmina_id, region_ids)


def _harmonogram(response, region_id, form, ulica=None, **_) -> str | None:
    """The schedule id of one town record, told apart by street where needed."""
    table = re.search(
        r'<table id="harmonogramy".*?<tbody>(.*?)</tbody>', response.text, re.S
    )
    rows = [
        (harmonogram_id, _strip_tags(cell))
        for cell, harmonogram_id in re.findall(
            r"<tr>\s*<td>(.*?)</td>\s*<td>.*?</td>\s*<td>.*?</td>\s*"
            r'<td>.*?/Harmonogramy/(\d+)".*?</tr>',
            table.group(1) if table else "",
            re.S,
        )
    ]
    if not rows:
        return None
    if len(rows) == 1 and len(form.region_ids) == 1:
        return rows[0][0]
    street_name = (ulica or "").strip()
    if street_name:
        matches = [r for r in rows if street_name.casefold() in r[1].casefold()]
        if len(matches) == 1:
            return matches[0][0]
        if not matches and len(form.region_ids) > 1:
            return None  # another record of the same town names the street
        rows = matches or rows
    raise SourceArgAmbiguousWithSuggestions("ulica", street_name, [r[1] for r in rows])


@final
class Source(BaseSource):
    TITLE = "Czysty Region"
    DESCRIPTION = "Source for Związek Międzygminny Czysty Region waste collection (Opole/Silesia region, Poland)."
    URL = "https://www.czystyregion.pl"
    COUNTRY = "pl"
    RAISE_ON_EMPTY = True

    HOWTO: ClassVar[dict] = {
        "en": (
            "Open https://www.czystyregion.pl/Harmonogramy and step through the "
            "dropdowns (Wybierz gminę -> Wybierz rodzaj -> Wybierz miejscowość) "
            "to find the exact spelling of your commune (gmina) and town/village "
            "(miejscowość). If the result table lists more than one row for your "
            "town (e.g. large towns split into several 'Rejon' street groups), "
            "also note a distinctive street name from the 'Rejon' description "
            "shown for your area and pass it as 'ulica'."
        ),
    }

    TEST_CASES: ClassVar[dict] = {
        "Cisek (jednorodzinna)": {
            "gmina": "Cisek",
            "miejscowosc": "Cisek",
            "rodzaj": "jednorodzinna",
        },
        "Cisek (firma)": {
            "gmina": "Cisek",
            "miejscowosc": "Cisek",
            "rodzaj": "firma",
        },
        "Kędzierzyn-Koźle, ul. Piastów (wielorodzinna)": {
            "gmina": "Kędzierzyn-Koźle",
            "miejscowosc": "Kędzierzyn-Koźle",
            "rodzaj": "wielorodzinna",
            "ulica": "Piastów",
        },
        "Polska Cerekiew, ul. Kozielska (jednorodzinna)": {
            "gmina": "Polska Cerekiew",
            "miejscowosc": "Polska Cerekiew",
            "rodzaj": "jednorodzinna",
            "ulica": "Kozielska",
        },
    }

    PARAMS: ClassVar[list] = [
        municipality("gmina"),
        city("miejscowosc"),
        dropdown("rodzaj", RODZAJ_CHOICES),
        street("ulica", optional=True),
    ]

    WASTE_TYPES: ClassVar[list] = [
        wt.BULKY_WASTE,
        wt.GENERAL_WASTE,
        wt.GLASS,
        wt.ORGANIC,
        wt.OTHER,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    retrieve = FanOutRetriever(
        prepare=Lookup(HARMONOGRAMY_URL, pick=_form),
        targets=lambda source, form: form.region_ids,
        fetch=Request(
            lambda region_id, form, harmonogram, **_: (
                f"{HARMONOGRAMY_URL}/{harmonogram}"
            ),
            before=[
                Lookup(
                    HARMONOGRAMY_URL,
                    method="POST",
                    data=lambda region_id, form, rodzaj, **_: {
                        "_token": form.token,
                        "gminy": form.gmina_id,
                        "rodzaj": rodzaj,
                        "regiony": region_id,
                    },
                    pick=_harmonogram,
                )
            ],
            when=lambda region_id, form, harmonogram, **_: harmonogram is not None,
        ),
    )
    parse = parsers.EachResponse(parsers.JsVarParser("events", json_parse=True))
    preprocess = preprocessors.FlattenGroups()
    transform = JsonTransformer(
        date_key="start",
        type_key="title",
        type_value_map={
            "Odpady zmieszane": wt.GENERAL_WASTE,
            "Tworzywa sztuczne/ Metale": wt.RECYCLABLES,
            "Papier": wt.PAPER,
            "Szkło": wt.GLASS,
            "Odpady BIO": wt.ORGANIC,
            "Popiół": wt.OTHER,
            "Zbiórka Akcyjna": wt.BULKY_WASTE,
        },
    )
