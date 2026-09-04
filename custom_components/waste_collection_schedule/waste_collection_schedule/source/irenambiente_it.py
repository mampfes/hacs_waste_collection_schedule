from datetime import date, datetime, timedelta, timezone
from typing import Any

import requests
from dateutil.rrule import rrulestr
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Iren Ambiente"
DESCRIPTION = "Source for waste collection in municipalities serviced by Iren Ambiente (Italy - Piedmont, Emilia-Romagna, Liguria)."
URL = "https://servizi.irenambiente.it"
COUNTRY = "it"

TEST_CASES = {
    "Torino Municipio per adrnr": {
        "adrnr": "0000085934",
        "user_type": "UD",
    },
    "Torino Centro per indirizzo": {
        "municipality": "Torino",
        "street": "Piazza Palazzo di Citta",
        "house_number": "3",
        "user_type": "UD",
    },
}

ICON_MAP = {
    "WCARTA": Icons.PAPER,
    "Carta": Icons.PAPER,
    "WINDIFFER": Icons.GENERAL_WASTE,
    "Rifiuto residuo indifferenziato": Icons.GENERAL_WASTE,
    "WORGANICO": Icons.ORGANIC,
    "Rifiuti Organici": Icons.ORGANIC,
    "WPLAIMBAL": Icons.PLASTIC_PACKAGING,
    "Imballaggi in plastica": Icons.PLASTIC_PACKAGING,
    "WVB": Icons.GLASS,
    "Vetro e lattine": Icons.GLASS,
}

PARAM_DESCRIPTIONS = {
    "en": {
        "adrnr": "Address code (adrnr) as found via Iren Ambiente portal. If omitted, municipality, street, and house_number must be provided.",
        "municipality": "Name of the municipality (e.g., 'Torino', 'Moncalieri', 'Reggio nell\\'Emilia', 'Piacenza', 'Parma', 'Genova').",
        "street": "Street name (e.g., 'Via Roma', 'Piazza Castello', 'Piazza Palazzo di Citta').",
        "house_number": "House number (e.g., '1', '3', '12/A').",
        "user_type": "User type: 'UD' for domestic/household, 'ND' for non-domestic/business (optional, default: UD).",
    },
    "it": {
        "adrnr": "Codice civico (adrnr) ricavabile dal portale. Se omesso, è necessario indicare municipality, street e house_number.",
        "municipality": "Nome del comune (es. 'Torino', 'Moncalieri', 'Reggio nell\\'Emilia', 'Piacenza', 'Parma', 'Genova').",
        "street": "Nome della via o piazza (es. 'Via Roma', 'Piazza Castello', 'Piazza Palazzo di Citta').",
        "house_number": "Numero civico (es. '1', '3', '12/A').",
        "user_type": "Tipologia utenza: 'UD' per domestica, 'ND' per non domestica (opzionale, predefinito UD).",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "it": (
        "Puoi configurare la sorgente indicando 'municipality', 'street' e 'house_number', "
        "oppure fornendo direttamente il codice 'adrnr' catturabile tramite gli strumenti sviluppatore (F12) "
        "dal portale https://servizi.irenambiente.it/comune/calendario-di-raccolta-e-indicazioni-dotazioni.html."
    ),
    "en": (
        "You can configure the source by specifying 'municipality', 'street', and 'house_number', "
        "or directly via 'adrnr' obtained from Developer Tools (F12) on the portal: "
        "https://servizi.irenambiente.it/comune/calendario-di-raccolta-e-indicazioni-dotazioni.html."
    ),
}

API_BASE_URL = "https://net.irenambiente.it/restv1/api/cms"
PORTAL_SERVICES_URL = "https://servizi.irenambiente.it/bin/iam/api-services"


class Source:
    def __init__(
        self,
        adrnr: str | None = None,
        municipality: str | None = None,
        street: str | None = None,
        house_number: str | None = None,
        user_type: str = "UD",
    ) -> None:
        self._adrnr = str(adrnr).strip() if adrnr else None
        self._municipality = municipality.strip() if municipality else None
        self._street = street.strip() if street else None
        self._house_number = str(house_number).strip() if house_number else None
        self._user_type = user_type.upper().strip() if user_type else "UD"

        if not self._adrnr and not (
            self._municipality and self._street and self._house_number
        ):
            raise SourceArgumentNotFound(
                "adrnr",
                "",
                "Specify either 'adrnr' or ('municipality', 'street', and 'house_number').",
            )

    def _resolve_adrnr(self, session: requests.Session) -> str:
        # 1. Ricerca Comune
        resp = session.get(f"{API_BASE_URL}/comuni", timeout=30)
        resp.raise_for_status()
        comuni: list[dict[str, Any]] = resp.json() or []
        muni_lower = self._municipality.lower()  # type: ignore[union-attr]
        comune_match = next(
            (c for c in comuni if c.get("Comune", "").strip().lower() == muni_lower),
            None,
        )

        if not comune_match:
            suggestions = [
                c.get("Comune", "")
                for c in comuni
                if muni_lower in c.get("Comune", "").lower()
            ]
            raise SourceArgumentNotFoundWithSuggestions(
                "municipality",
                self._municipality,
                suggestions,  # type: ignore[arg-type]
            )

        istat = comune_match.get("Istat")
        if not istat:
            raise SourceArgumentNotFound(
                "municipality",
                self._municipality,  # type: ignore[arg-type]
                f"No Istat code found for municipality '{self._municipality}'.",
            )

        # 2. Ricerca Via
        resp = session.get(
            f"{API_BASE_URL}/vie/{istat}",
            params={"search": self._street},
            timeout=30,
        )
        resp.raise_for_status()
        vie: list[dict[str, Any]] = resp.json() or []
        street_lower = self._street.lower()  # type: ignore[union-attr]

        via_match = next(
            (v for v in vie if v.get("Street", "").strip().lower() == street_lower),
            None,
        )
        if not via_match and vie:
            via_match = vie[0]

        if not via_match:
            raise SourceArgumentNotFound(
                "street",
                self._street,  # type: ignore[arg-type]
                f"Street '{self._street}' not found in municipality '{self._municipality}'.",
            )

        street_code = via_match.get("StreetCode")
        if not street_code:
            raise SourceArgumentNotFound(
                "street",
                self._street,  # type: ignore[arg-type]
                f"StreetCode not found for street '{self._street}'.",
            )

        # 3. Ricerca Civico ed estrazione AdrNr
        params = {
            "api": "civici",
            "istat": istat,
            "streetcode": street_code,
            "search": self._house_number,
            "limit": 20,
        }
        resp = session.get(PORTAL_SERVICES_URL, params=params, timeout=30)
        resp.raise_for_status()
        civici_data = resp.json() or {}
        civici: list[dict[str, Any]] = civici_data.get("data", [])

        civico_target = self._house_number.lower()  # type: ignore[union-attr]
        civico_match = next(
            (
                c
                for c in civici
                if str(c.get("Civico", "")).strip().lower() == civico_target
            ),
            None,
        )
        if not civico_match and civici:
            civico_match = civici[0]

        if not civico_match:
            raise SourceArgumentNotFound(
                "house_number",
                self._house_number,  # type: ignore[arg-type]
                f"House number '{self._house_number}' not found for street '{self._street}'.",
            )

        adrnr = civico_match.get("AdrNr")
        if not adrnr:
            raise SourceArgumentNotFound(
                "adrnr",
                "",
                f"Could not extract AdrNr for house number '{self._house_number}'.",
            )

        return str(adrnr).strip()

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        session.headers.update(
            {
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0 (HomeAssistant Waste Collection Schedule)",
                "Referer": "https://servizi.irenambiente.it/comune/calendario-di-raccolta-e-indicazioni-dotazioni.html",
            }
        )

        adrnr = self._adrnr or self._resolve_adrnr(session)
        api_url = f"{API_BASE_URL}/calendarioraccoltacivico/{adrnr}"

        response = session.get(api_url, timeout=30)
        response.raise_for_status()

        data = response.json()
        if not data or not isinstance(data, list):
            raise SourceArgumentNotFound(
                "adrnr",
                adrnr,
                f"No calendar entries found for adrnr '{adrnr}'.",
            )

        entries = [
            item
            for item in data
            if item.get("TipoUtenza", "").upper() == self._user_type
            and not item.get("NonVisibile", False)
        ]

        if not entries:
            entries = [item for item in data if not item.get("NonVisibile", False)]

        today = datetime.now(timezone.utc).date()
        start_dt = datetime(
            today.year, today.month, today.day, tzinfo=timezone.utc
        ) - timedelta(days=14)
        end_dt = datetime(
            today.year, today.month, today.day, tzinfo=timezone.utc
        ) + timedelta(days=120)

        entries_by_date: dict[date, set[str]] = {}

        for item in entries:
            waste_name = item.get("Materiale") or item.get("IdRifiuto")
            if not waste_name:
                continue

            rrule_str = item.get("ICalRRule")
            if not rrule_str:
                continue

            dtstart_raw = item.get("DataInizioValidita")
            if dtstart_raw:
                try:
                    dtstart_date = date.fromisoformat(dtstart_raw.split("T")[0])
                    dtstart = datetime(
                        dtstart_date.year,
                        dtstart_date.month,
                        dtstart_date.day,
                        tzinfo=timezone.utc,
                    )
                except ValueError:
                    dtstart = start_dt
            else:
                dtstart = start_dt

            try:
                rule = rrulestr(rrule_str, dtstart=dtstart)
            except (ValueError, TypeError):
                continue

            occurrences = {dt.date() for dt in rule.between(start_dt, end_dt, inc=True)}

            for holiday_info in item.get("FestivitaCalendario") or []:
                holiday_date_raw = holiday_info.get("DataFestivita")
                if not holiday_date_raw:
                    continue

                try:
                    holiday_date = date.fromisoformat(holiday_date_raw.strip())
                except ValueError:
                    continue

                occurrences.discard(holiday_date)

                replacement_date_raw = holiday_info.get("DataConferimento")
                if replacement_date_raw:
                    try:
                        replacement_date = date.fromisoformat(
                            replacement_date_raw.strip()
                        )
                        if (
                            today - timedelta(days=14)
                            <= replacement_date
                            <= today + timedelta(days=120)
                        ):
                            occurrences.add(replacement_date)
                    except ValueError:
                        pass

            for d in occurrences:
                entries_by_date.setdefault(d, set()).add(waste_name)

        collections: list[Collection] = []
        for d, waste_types in entries_by_date.items():
            for waste_type in sorted(waste_types):
                icon = ICON_MAP.get(waste_type)
                collections.append(Collection(date=d, t=waste_type, icon=icon))

        return collections
