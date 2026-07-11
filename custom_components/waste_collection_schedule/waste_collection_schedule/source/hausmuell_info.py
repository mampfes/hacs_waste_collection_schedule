"""hausmüll.info, a multi-tenant calendar platform for several German operators.

Demonstrates: a cascading address-refinement wizard (Ort -> Ortsteil ->
Straße -> Hausnummer -> Zusatz) where each step is itself a fuzzy search that
may need retrying with special characters folded or replaced (the provider's
search endpoints are inconsistent about matching "ß"/umlauts verbatim). No
configured retriever expresses "repeat this lookup, trying several character
foldings, until one returns a non-empty result", so the whole flow stays a
source-defined ``retrieve``.

Every operator in ``SUPPORTED_PROVIDERS`` is preserved as its own ``Region``
(the typed successor to the legacy ``EXTRA_INFO`` list), so none of the towns
this source covers are dropped by the conversion.
"""

from datetime import datetime
from typing import ClassVar, final
from urllib.parse import urlencode, urljoin

from bs4 import BeautifulSoup, Tag
from waste_collection_schedule import parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    district,
    house_number,
    street,
    text_field,
)
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.regions import region
from waste_collection_schedule.retrievers import Response
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GARDEN_WASTE,
    GENERAL_WASTE,
    GLASS,
    HAZARDOUS,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

API_URL = "https://{}.hausmuell.info/"

SUPPORTED_PROVIDERS: list = [
    {
        "subdomain": "ebkds",
        "title": "Eigenbetrieb Kommunalwirtschaftliche Dienstleistungen Suhl",
        "url": "https://www.ebkds.de/",
    },
    {
        "subdomain": "erfurt",
        "title": "Stadtwerke Erfurt, SWE",
        "url": "https://www.stadtwerke-erfurt.de/",
    },
    {
        "subdomain": "schmalkalden-meiningen",
        "title": "Kreiswerke Schmalkalden-Meiningen GmbH",
        "url": "https://www.kwsm.de/",
    },
    {
        "subdomain": "ew",
        "title": "Eichsfeldwerke GmbH",
        "url": "https://www.eichsfeldwerke.de/",
    },
    {
        "subdomain": "azv",
        "title": "Abfallwirtschaftszweckverband Wartburgkreis (AZV)",
        "url": "https://www.azv-wak-ea.de/",
    },
    {
        "subdomain": "boerde",
        "title": "Landkreis Börde AöR (KsB)",
        "url": "https://www.ks-boerde.de",
    },
    {
        "subdomain": "asc",
        "title": "Chemnitz (ASR)",
        "url": "https://www.asr-chemnitz.de/",
    },
    {"subdomain": "wesel", "title": "ASG Wesel", "url": "https://www.asg-wesel.de/"},
]


def _replace_special_chars(s: str) -> str:
    return (
        s.replace("ß", "s")
        .replace("ä", "a")
        .replace("ö", "o")
        .replace("ü", "u")
        .replace("Ä", "A")
        .replace("Ö", "O")
        .replace("Ü", "U")
    )


def _replace_special_chars_with_underscore(s: str) -> str:
    return (
        s.replace("ß", "_")
        .replace("ä", "_")
        .replace("ö", "_")
        .replace("ü", "_")
        .replace("Ä", "_")
        .replace("Ö", "_")
        .replace("Ü", "_")
    )


def _replace_special_chars_args(d: dict, replace_func=_replace_special_chars) -> dict:
    return {
        k: ([replace_func(i) for i in v] if isinstance(v, list) else replace_func(v))
        for k, v in d.items()
    }


# curl_cffi's ``data=`` (unlike plain ``requests``) stringifies a list value
# (``{"input_str": ["a", "a"]}`` becomes the literal text ``"['a', 'a']"``)
# instead of repeating the key, and this provider's search endpoints only
# work with the latter. The body is therefore pre-encoded with ``doseq=True``
# to match the wire format the legacy source actually sent -- which also
# means the Content-Type curl_cffi infers for a dict body (form-urlencoded)
# must be set explicitly, since a raw string body defaults to
# application/octet-stream and the server won't populate $_POST from it.
_FORM_HEADERS = {"Content-Type": "application/x-www-form-urlencoded"}


def _urlencode_form(data: dict) -> str:
    return urlencode(data, doseq=True)


def _clean_label(label: str) -> str:
    """Fix the provider's mojibake and strip the wrapper phrases it adds.

    "Ã¼" is a UTF-8-as-Latin-1 mis-decode of "ü" that survives even after
    forcing the response encoding (a legacy quirk of this provider, kept
    exactly). "Entsorgung:"/"Verschobene Abholung:" are prefix/label noise the
    provider adds around the actual bin name; stripping both (not just the
    former, as the legacy source did only for its icon lookup) means a
    rescheduled collection now resolves to the same canonical type as a
    regular one instead of falling through to a raw "Verschobene Abholung:
    ..." label.
    """
    text = label.replace("Ã¼", "ü").replace("Entsorgung:", "")
    lowered = text.lower()
    marker = "verschobene abholung:"
    idx = lowered.find(marker)
    if idx != -1:
        text = text[:idx] + text[idx + len(marker) :]
    return text.strip()


@final
class Source(BaseSource):
    TITLE = "hausmüll.info"
    DESCRIPTION = "Source for hausmüll.info."
    URL = "https://hausmuell.info"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Dietzhausen Am Rain 10 ebkds": {
            "ort": "Dietzhausen",
            "strasse": "Am Rain",
            "hausnummer": 10,
            "subdomain": "ebkds",
        },
        "Adam-Ries-Straße 5, Erfurt": {
            "subdomain": "erfurt",
            "strasse": "Adam-Ries-Straße",
            "hausnummer": "5",
        },
        "schmalkalden-meiningen, Obermaßfeld-Grimmenthal": {
            "subdomain": "schmalkalden-meiningen",
            "ort": "Obermaßfeld-Grimmenthal",
        },
        "schmalkalden-meiningen, Dillstädt": {
            "subdomain": "schmalkalden-meiningen",
            "ort": "Dillstädt",
        },
        "schmalkalden-meiningen Zella-Mehils Benshausen Albrechter Straße": {
            "subdomain": "schmalkalden-meiningen",
            "ort": "Zella-Mehlis",
            "ortsteil": "Benshausen",
            "strasse": "Albrechtser Straße",
        },
        "schmalkalden-meiningen Breitungen, Bußhof": {
            "subdomain": "schmalkalden-meiningen",
            "ort": "Breitungen",
            "ortsteil": "Bußhof",
        },
        "ew, Döringsdorf, Wanfrieder Str.": {
            "subdomain": "ew",
            "ort": "Döringsdorf",
            "strasse": "Wanfrieder Str.",
        },
        "ew, Bernterode (WBS), Hinter den Höfen": {
            "subdomain": "ew",
            "ort": "Bernterode (WBS)",
            "strasse": "Hinter den Höfen",
        },
        "azv, Berka vor dem Hainich": {
            "subdomain": "azv",
            "ort": "Berka vor dem Hainich",
        },
        "azv, Hörselberg-Hainich": {
            "subdomain": "azv",
            "ort": "Hörselberg-Hainich",
            "ortsteil": "Ettenhausen/Nesse",
        },
        "börde, Belsdorf (Altkreis BÖ), Alleringerslebener Straße 15a": {
            "subdomain": "boerde",
            "ort": "Belsdorf (Altkreis BÖ)",
            "strasse": "Alleringerslebener Straße",
            "hausnummer": "15a",
        },
        "chemnitz, Straße des Friedens/Wittgensdorf 2 a": {
            "subdomain": "asc",
            "strasse": "Straße des Friedens/Wittgensdorf",
            "hausnummer": "2 a",
        },
        "wesel Flüren, In der Flürener Heide": {
            "subdomain": "wesel",
            "ort": "Flüren",
            "strasse": "In der Flürener Heide",
        },
    }

    # One structure, many independent operators: preserve every one of
    # SUPPORTED_PROVIDERS as its own Region so none are dropped by the
    # conversion.
    REGIONS = tuple(
        region(p["title"], url=p["url"], subdomain=p["subdomain"])
        for p in SUPPORTED_PROVIDERS
    )

    PARAMS = (
        text_field("subdomain", "Subdomain"),
        district(field="ort", optional=True),
        text_field("ortsteil", "District", optional=True),
        street(field="strasse", optional=True),
        house_number(field="hausnummer", optional=True),
    )

    parse = parsers.IcsParser()
    transform = ICSTransformer(
        clean=_clean_label,
        type_value_map={
            "hausmüll": GENERAL_WASTE,
            "restabfall": GENERAL_WASTE,
            "restmüll": GENERAL_WASTE,
            "glass": GLASS,
            "biomüll": ORGANIC,
            "biomüll mit reinigung": ORGANIC,
            "bioabfall mit reinigung": ORGANIC,
            "bioabfall": ORGANIC,
            "papier": PAPER,
            "papier, pappe, karton": PAPER,
            "papier, pappe & kart.": PAPER,
            "pappe, papier & kart.": PAPER,
            "altpapier": PAPER,
            "gelbe tonne": RECYCLABLES,
            "gelber sack": RECYCLABLES,
            "gelber sack / gelbe tonne": RECYCLABLES,
            "leichtverpackungen": RECYCLABLES,
            "leichtstoffverpackungen": RECYCLABLES,
            "grünschnitt": GARDEN_WASTE,
            "schadstoffe": HAZARDOUS,
            "schadstoffmobil": HAZARDOUS,
            "problemmüll": HAZARDOUS,
        },
    )

    def __init__(
        self,
        subdomain: str,
        ort: "str | None" = None,
        ortsteil: "str | None" = None,
        strasse: "str | None" = None,
        hausnummer: "str | int | None" = None,
    ):
        super().__init__(
            subdomain=subdomain,
            ort=ort or "",
            ortsteil=ortsteil or "",
            strasse=strasse or "",
            hausnummer=str(hausnummer) if hausnummer else "",
        )

    @staticmethod
    def _get_elemts(response_text: str) -> list:
        li = BeautifulSoup(response_text, "html.parser").find("li")
        if not isinstance(li, Tag):
            return ["0"]
        onclick = li.get("onclick")
        if not isinstance(onclick, str):
            return ["0"]
        ids = onclick.split(")")[0].split("(")[1].split(",")
        return [i.strip() for i in ids if i.strip().isdigit()]

    def _request_all(
        self, session, field: str, url: str, data: dict, params: dict
    ) -> Response:
        r = session.post(
            url, data=_urlencode_form(data), params=params, headers=_FORM_HEADERS
        )
        if "kein Eintrag gefunden" not in r.text and r.text.strip() != "<ul></ul>":
            return r
        r = session.post(
            url,
            data=_urlencode_form(_replace_special_chars_args(data)),
            params=_replace_special_chars_args(params),
            headers=_FORM_HEADERS,
        )
        if "kein Eintrag gefunden" not in r.text and r.text.strip() != "<ul></ul>":
            return r
        r = session.post(
            url,
            data=_urlencode_form(
                _replace_special_chars_args(
                    data, _replace_special_chars_with_underscore
                )
            ),
            params=_replace_special_chars_args(params),
            headers=_FORM_HEADERS,
        )
        if "kein Eintrag gefunden" not in r.text and r.text.strip() != "<ul></ul>":
            return r
        raise SourceArgumentNotFoundWithSuggestions(field, params.get("input"), [])

    def retrieve(self, source):
        session = self.session
        p = self.params
        api_url = API_URL.format(p["subdomain"])

        args = {
            "hidden_kalenderart": "privat",
            "input_ort": p["ort"],
            "input_ortsteil": p["ortsteil"],
            "input_str": [p["strasse"], p["strasse"]],
            "input_hnr": [p["hausnummer"], p["hausnummer"]],
            "ort_id": "0",
            "ortteil_id": "0",
            "str_id": "0",
            "hidden_id_ort": "0",
            "hidden_id_ortsteil": "0",
            "hidden_id_str": "0",
            "hidden_id_hnr": "0",
            "hidden_id_egebiet": "0",
            "hidden_send_btn": "ics",
            "hiddenYear": str(datetime.now().year),
        }

        # Some operators (e.g. "erfurt") permanently redirect their
        # hausmuell.info subdomain to their own domain. Follow redirects
        # manually (rather than relying on the auto-followed response's
        # resolved .url, as the legacy source did) so every hop is a
        # separately recorded/replayable interaction for the offline fixture
        # tests, instead of a single followed response whose pre-redirect
        # request URL would otherwise be indistinguishable from its target.
        r = session.get(api_url, allow_redirects=False)
        hops = 0
        while r.status_code in (301, 302, 303, 307, 308) and hops < 5:
            location = r.headers.get("location")
            if not location:
                break
            api_url = urljoin(api_url, location)
            r = session.get(api_url, allow_redirects=False)
            hops += 1
        search_url = api_url + "search/"
        ics_url = api_url + "ics/ics.php"

        soup = BeautifulSoup(r.text, "html.parser")
        for i in soup.find_all("input"):
            name = i.get("name")
            if name and name.startswith("showBins"):
                args[name] = "on"

        if p["ort"]:
            # Mirrors the legacy source: "input" is left set to whichever
            # field was searched last (the endpoints key off the query-string
            # "input" passed as `params` below; this body value is otherwise
            # stale/unused, but is replicated for exact wire-format parity).
            args["input"] = p["ort"]
            r = self._request_all(
                session,
                "ort",
                search_url + "search_orte.php",
                args,
                {"input": p["ort"], "ort_id": "0"},
            )
            ids = self._get_elemts(r.text)
            args["hidden_id_ort"] = args["ort_id"] = ids[0]
            if len(ids) > 1:
                args["hidden_id_egebiet"] = ids[1]

        if p["ortsteil"]:
            r = self._request_all(
                session,
                "ortsteil",
                search_url + "search_ortsteile.php",
                args,
                {"input": p["ortsteil"], "ort_id": args["ort_id"]},
            )
            ids = self._get_elemts(r.text)
            args["ort_id"] = args["hidden_id_ortsteil"] = (
                args["hidden_id_ort"] if ids[0] == "0" else ids[0]
            )
            if len(ids) > 1:
                args["hidden_id_egebiet"] = ids[1]

        if p["strasse"]:
            r = self._request_all(
                session,
                "strasse",
                search_url + "search_strassen.php",
                args,
                {"input": p["strasse"], "str_id": "0", "ort_id": args["ort_id"]},
            )
            ids = self._get_elemts(r.text)
            args["hidden_id_str"] = args["str_id"] = ids[0]
            if len(ids) > 1:
                args["hidden_id_egebiet"] = ids[1]

        if p["hausnummer"]:
            args["input"] = p["hausnummer"]
            r = self._request_all(
                session,
                "hausnummer",
                search_url + "search_hnr.php",
                args,
                {"input": p["hausnummer"], "hnr_id": "0", "str_id": args["str_id"]},
            )
            ids = self._get_elemts(r.text)
            args["hidden_id_hnr"] = args["hnr_id"] = ids[0]
            if len(ids) > 1:
                args["hidden_id_egebiet"] = ids[1]

        r = session.post(
            search_url + "check_zusatz.php",
            data=_urlencode_form(args),
            headers=_FORM_HEADERS,
        )
        id_string = BeautifulSoup(r.text, "html.parser").find("span")
        args["hidden_id_zusatz"] = (
            args["hidden_id_hnr"] if id_string is None else id_string.text.strip()
        )

        r = session.post(ics_url, data=_urlencode_form(args), headers=_FORM_HEADERS)
        r.raise_for_status()
        # Force the encoding before the first .text access: some HTTP clients
        # (curl_cffi included) cache the decoded text on first read and
        # refuse a later re-decode, unlike plain requests.
        r.encoding = "utf-8"

        if "Bitte geben Sie Ihre Daten korrekt an." in r.text:
            raise SourceArgumentNotFoundWithSuggestions("subdomain", p["subdomain"], [])

        return r
