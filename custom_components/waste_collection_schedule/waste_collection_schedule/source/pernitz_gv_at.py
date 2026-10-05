import datetime
from typing import Any, ClassVar, final

from waste_collection_schedule import date_parsers, parsers, recurrence, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import dropdown
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.preprocessors import Compose, RowFilter
from waste_collection_schedule.transformers import RowTransformer

_RAYONS = ("1", "2")

# Paper is only published as a recurring rule ("every 1st Saturday of the
# month", collected by the volunteer fire brigade), not as a list of dates.
_PAPER_LABEL = "Papier"
_PAPER_MONTHS_AHEAD = 18
_SATURDAY = 5


def _keep_chosen_rayon(row: Any, source: "BaseSource | None") -> bool:
    """Drop the residual-waste list of the other Rayon."""
    label = row[1]
    if not label.startswith("Restmüll Rayon "):
        return True
    return label == f"Restmüll Rayon {str(source.params['rayon']).strip()}"  # type: ignore[union-attr]


def _with_paper(rows: Any, source: "BaseSource | None" = None) -> list:
    """Validate the Rayon and add the recurring paper collection."""
    rayon = str(source.params["rayon"]).strip() if source is not None else ""
    if rayon not in _RAYONS:
        raise SourceArgumentNotFoundWithSuggestions(
            "rayon", source.params["rayon"] if source else None, list(_RAYONS)
        )
    paper = [
        (day, _PAPER_LABEL)
        for day in recurrence.monthly_nth_weekdays(
            _SATURDAY,
            1,
            _PAPER_MONTHS_AHEAD,
            on_or_after=datetime.date.today().replace(day=1),
        )
    ]
    return [*rows, *paper]


@final
class Source(BaseSource):
    TITLE = "Marktgemeinde Pernitz"
    DESCRIPTION = "Source for Marktgemeinde Pernitz, Austria."
    URL = "https://www.pernitz.gv.at"
    COUNTRY = "at"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@bbr111"]
    RAISE_ON_EMPTY = True

    # "Gelber Sack" and "Gelber Container" are published on the same days and
    # both resolve to Recycling; merge the duplicates by default (the raw label
    # is carried into the description).
    IGNORE_DUPLICATES_DEFAULT = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Rayon 1": {"rayon": 1},
        "Rayon 2": {"rayon": 2},
    }

    PARAMS = (
        dropdown(
            "rayon",
            list(_RAYONS),
            label="Rayon",
        ),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "The general waste (Restmüll) collection zone, 1 or 2, that your street "
            "belongs to. See the street list at "
            "https://pernitz.gv.at/verwaltung/wertstoffsammelstelle-und-muellabfuhr/ "
            "to determine your zone."
        ),
        "de": (
            "Der Restmüll-Abfuhrbezirk (Rayon), 1 oder 2, zu dem Ihre Straße gehört. "
            "Die Straßenliste finden Sie unter "
            "https://pernitz.gv.at/verwaltung/wertstoffsammelstelle-und-muellabfuhr/."
        ),
    }

    retrieve = retrievers.HttpGetRetriever(
        url="https://pernitz.gv.at/verwaltung/wertstoffsammelstelle-und-muellabfuhr/"
    )

    parse = parsers.HtmlLabelledDates(
        "div.et_pb_accordion_item",
        label="h5.et_pb_toggle_title",
        date="div.et_pb_toggle_content",
        date_pattern=r"(\d{1,2}\.\s*\d{1,2}\.\s*\d{4})",
        all_dates=True,
    )

    preprocess = Compose(RowFilter(_keep_chosen_rayon), _with_paper)

    transform = RowTransformer(
        parse_date=date_parsers.for_format("%d.%m.%Y"),
        type_value_map={
            "Restmüll Rayon 1": wt.GENERAL_WASTE,
            "Restmüll Rayon 2": wt.GENERAL_WASTE,
            "Biotonne": wt.ORGANIC,
            "Gelber Sack": wt.RECYCLABLES,
            "Gelber Container": wt.RECYCLABLES,
            "Papier": wt.PAPER,
        },
        carry_raw_label=True,
    )
