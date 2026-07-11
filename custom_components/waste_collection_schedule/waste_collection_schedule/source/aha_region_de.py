"""Zweckverband Abfallwirtschaft Region Hannover (aha-region.de).

Demonstrates: a genuinely bespoke multi-step retrieve. Getting to the ICS
feed needs, in order: a GET to resolve the street name into a "strasse" id
from a rendered ``<select>``, a POST submitting that id plus the house number
that returns an overview page, and (because some addresses are served by more
than one loading point / "Ladeort") either a single hidden loading-point value
or a ``<select>`` the caller must disambiguate via the optional ``ladeort``
argument, before a final POST requests the ICAL export. Four sequential,
state-threading requests with a data-dependent branch is not a shape any
configured retriever expresses, hence a source-defined ``retrieve`` method
(the default ``parse = IcsParser()`` handles the single ICS response).

Every observed label ("Restabfall", "Bioabfall", "Papier",
"Leichtverpackungen") already resolves against the standard German
vocabulary; ``clean`` only strips the "Abfuhr" suffix and an occasional
uncertain-date " *" marker the provider appends, mirroring the legacy
source's ``d[1].replace("Abfuhr", "").strip().replace(" *", "")``.
"""

from typing import ClassVar, final

from bs4 import BeautifulSoup, Tag
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    house_number,
    municipality,
    street,
    text_field,
)
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequiredWithSuggestions,
)
from waste_collection_schedule.parsers import IcsParser
from waste_collection_schedule.transformers import ICSTransformer

_API_URL = "https://www.aha-region.de/abholtermine/abfuhrkalender"


def _clean_label(label: str) -> str:
    return label.replace("Abfuhr", "").strip().replace(" *", "")


def _normalize(value: str) -> str:
    return value.lower().replace(" ", "")


@final
class Source(BaseSource):
    TITLE = "Zweckverband Abfallwirtschaft Region Hannover"
    DESCRIPTION = "Source for Zweckverband Abfallwirtschaft Region Hannover."
    URL = "https://www.aha-region.de/"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Neustadt a. Rbge., Am Rotdorn / Nöpke, 1 ": {
            "gemeinde": "Neustadt a. Rbge.",
            "strasse": "Am Rotdorn / Nöpke",
            "hnr": 1,
        },
        "Isernhagen, Am Lohner Hof / Isernhagen Fb, 10": {
            "gemeinde": "Isernhagen",
            "strasse": "Am Lohner Hof / Isernhagen Fb",
            "hnr": "10",
        },
        "Hannover, Voltastr. / Vahrenwald, 25": {
            "gemeinde": "Hannover",
            "strasse": "Voltastr. / Vahrenwald",
            "hnr": "25",
        },
        "Hannover, Melanchthonstr., 10A": {
            "gemeinde": "Hannover",
            "strasse": "Melanchthonstr.",
            "hnr": "10",
            "zusatz": "A",
        },
        "Mit Ladeort": {
            "gemeinde": "Gehrden",
            "strasse": "Kirchstr. / Gehrden",
            "hnr": "1",
            "ladeort": "Kirchstr. 6, Gehrden / Gehrden",
        },
    }

    PARAMS = (
        municipality(field="gemeinde"),
        street(field="strasse"),
        house_number(field="hnr"),
        text_field("zusatz", "Address suffix", default=""),
        text_field("ladeort", "Loading point", optional=True),
    )

    parse = IcsParser()
    transform = ICSTransformer(clean=_clean_label)

    def __init__(
        self,
        gemeinde: str,
        strasse: str,
        hnr: "str | int",
        zusatz: "str | int" = "",
        ladeort: "str | None" = None,
    ):
        super().__init__(
            gemeinde=gemeinde,
            strasse=strasse,
            hnr=str(hnr),
            zusatz=str(zusatz),
            ladeort=ladeort,
        )

    def retrieve(self, source):
        session = source.session
        gemeinde = source.params["gemeinde"]
        strasse = source.params["strasse"]
        hnr = source.params["hnr"]
        zusatz = source.params["zusatz"]
        ladeort_wanted = source.params.get("ladeort")

        r = session.get(
            _API_URL, params={"gemeinde": gemeinde, "von": strasse.upper()[0]}
        )
        r.raise_for_status()

        strasse_select = BeautifulSoup(r.text, "html.parser").find(
            "select", {"id": "strasse"}
        )
        if not isinstance(strasse_select, Tag):
            raise SourceArgumentNotFoundWithSuggestions("strasse", strasse, [])
        selects = strasse_select.find_all("option")
        strassen_id = None
        for select in selects:
            if _normalize(select.text) == _normalize(strasse):
                strassen_id = select["value"]
                break

        if not strassen_id:
            raise SourceArgumentNotFoundWithSuggestions(
                "strasse", strasse, [select.text for select in selects]
            )

        args = {
            "gemeinde": gemeinde,
            "jsaus": "",
            "von": strasse.upper()[0],
            "strasse": strassen_id,
            "hausnr": hnr,
            "hausnraddon": zusatz,
            "anzeigen": "Suchen",
        }

        r = session.post(_API_URL, data=args)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        ladeort_single = soup.find(
            "input", {"name": "ladeort", "class": "form-control"}
        )

        if not ladeort_single:
            ladeort_select = soup.find("select", {"name": "ladeort"})
            if not isinstance(ladeort_select, Tag):
                raise SourceArgumentNotFoundWithSuggestions("strasse", strasse, [])
            ladeort_options = ladeort_select.find_all("option")
            if not ladeort_wanted:
                raise SourceArgumentRequiredWithSuggestions(
                    "ladeort",
                    "Ladeort required for this address",
                    [option.text for option in ladeort_options],
                )
            for option in ladeort_options:
                if _normalize(option.text) == _normalize(ladeort_wanted):
                    ladeort_single = option
                    break
            if not ladeort_single:
                raise SourceArgumentNotFoundWithSuggestions(
                    "ladeort",
                    ladeort_wanted,
                    [option.text for option in ladeort_options],
                )

        if not isinstance(ladeort_single, Tag):
            raise SourceArgumentNotFoundWithSuggestions("ladeort", ladeort_wanted, [])
        del args["anzeigen"]
        args["ladeort"] = ladeort_single["value"]
        args["ical"] = "ICAL Jahresübersicht"

        r = session.post(_API_URL, data=args)
        r.raise_for_status()
        r.encoding = "utf-8"
        return r
