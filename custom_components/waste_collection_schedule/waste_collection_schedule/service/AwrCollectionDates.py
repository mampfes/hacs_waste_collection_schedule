"""Shared client for the AWR/AWSH ``collection_dates`` API (DE, Schleswig-Holstein).

Two neighbouring northern German authorities, Abfallwirtschaft
Rendsburg-Eckernförde (``awr.de``) and Abfallwirtschaft Südholstein
(``awsh.de``), serve their calendar from the same JSON API, mounted at the same
paths on each host::

    /api_v2/collection_dates/1/orte
    /api_v2/collection_dates/1/ort/<city_id>/strassen
    /api_v2/collection_dates/1/ort/<city_id>/abfallarten
    /api_v2/collection_dates/1/ort/<city_id>/strasse/<street_id>
        /hausnummern/0/abfallarten/<ids>/kalender.ics

Same field names, same response envelopes, same ICS output down to the
container-size annotation the summaries carry. Getting to the calendar takes
three sequential lookups, because each one needs the id the previous one
resolved: the city, then the street within that city, then the waste-type ids
that city actually has. :class:`CollectionDatesRetriever` is that whole chain,
so a source on this platform declares only its base URL.

The ``1`` in the path is the tenant id, and the trailing ``hausnummern/0`` asks
for the whole street rather than one house. Both deployments use those values,
so they are fixed here rather than exposed as options nobody would vary.
"""

import re
from typing import TYPE_CHECKING

from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.retrievers import Response, RetrieverFunc

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource

# Event summaries carry a container-size/frequency annotation, e.g.
# "Restabfall ab 770L(2-wöchentlich)" or "Bioabfall(14-täglich)". Stripping it
# exposes the plain waste-type name so the shared multilingual vocabulary can
# resolve it; a label that does not fit this shape passes through untouched.
_TRAILING_PARENTHETICAL = re.compile(r"\s*\([^)]*\)\s*$")
_TRAILING_BIN_SIZE = re.compile(r"\s+ab\s+\d+\s*l\b.*$", re.IGNORECASE)


def clean_waste_type(label: str) -> str:
    """Strip the container-size/frequency annotation off an event summary."""
    label = _TRAILING_PARENTHETICAL.sub("", label)
    label = _TRAILING_BIN_SIZE.sub("", label)
    return label.strip()


class CollectionDatesRetriever(RetrieverFunc):
    """Resolve city, street and waste-type ids, then download the ICS calendar.

    The pipeline retrieve step for the platform: three JSON lookups followed by
    the ``kalender.ics`` download, returned raw for ``parsers.IcsParser``. An
    unresolved city or street raises with the values the API listed, so the UI
    can suggest the spelling the provider expects.

    Args:
        base_url: the deployment's scheme and host, e.g. ``https://www.awr.de``.
    """

    def __init__(self, *, base_url: str):
        self._api = f"{base_url.rstrip('/')}/api_v2/collection_dates/1"

    def _resolve(
        self,
        source: "BaseSource",
        path: str,
        envelope: str,
        label_key: str,
        id_key: str,
        argument: str,
    ) -> str:
        """Look one level up in ``path`` and return the id matching the param."""
        wanted = source.params[argument]
        response = source.session.get(f"{self._api}/{path}")
        response.raise_for_status()
        by_label = {
            entry[label_key]: entry[id_key] for entry in response.json()[envelope]
        }
        if wanted not in by_label:
            raise SourceArgumentNotFoundWithSuggestions(
                argument, wanted, by_label.keys()
            )
        return by_label[wanted]

    def __call__(self, source: "BaseSource") -> Response:
        city_id = self._resolve(
            source, "orte", "orte", "ortsbezeichnung", "ortsnummer", "city"
        )
        street_id = self._resolve(
            source,
            f"ort/{city_id}/strassen",
            "strassen",
            "strassenbezeichnung",
            "strassennummer",
            "street",
        )

        # Not a lookup against a user argument: the calendar URL wants every
        # waste-type id this city collects, so the whole list is requested.
        waste_types = source.session.get(f"{self._api}/ort/{city_id}/abfallarten")
        waste_types.raise_for_status()
        waste_type_ids = "-".join(
            entry["id"] for entry in waste_types.json()["abfallarten"]
        )

        calendar = source.session.get(
            f"{self._api}/ort/{city_id}/strasse/{street_id}"
            f"/hausnummern/0/abfallarten/{waste_type_ids}/kalender.ics"
        )
        calendar.raise_for_status()
        return calendar
