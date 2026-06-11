import csv
import io
import os
import tempfile
from datetime import date, timedelta

import certifi
import requests
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "Montpellier Méditerranée Métropole"
DESCRIPTION = "Source for waste collection schedules in Montpellier Méditerranée Métropole, France."
URL = "https://data.montpellier3m.fr"
COUNTRY = "fr"

TEST_CASES = {
    "Montpellier, Rue Parlier 3": {
        "street_name": "Rue Parlier",
        "house_number": 3,
        "commune": "MONTPELLIER",
    },
    "Montpellier, Rue Parlier 8": {
        "street_name": "Rue Parlier",
        "house_number": 8,
        "commune": "MONTPELLIER",
    },
    "Lattes, Avenue de Montpellier": {
        "street_name": "Avenue de Montpellier",
        "commune": "LATTES",
    },
    "Castelnau-le-Lez, Chemin des Alouettes": {
        "street_name": "Chemin des Alouettes",
        "commune": "CASTELNAU-LE-LEZ",
    },
}

ICON_MAP = {
    "Ordures ménagères": Icons.GENERAL_WASTE,
    "Tri sélectif": Icons.RECYCLING,
    "Biodéchets": Icons.ORGANIC,
    "Encombrants": Icons.BULKY,
}

DAY_CODE_MAP = {
    "L": 0,
    "M": 1,
    "W": 2,
    "J": 3,
    "V": 4,
    "S": 5,
    "D": 6,
}

STREET_TYPE_MAP = {
    "R": "RUE",
    "AV": "AVENUE",
    "CHE": "CHEMIN",
    "IMP": "IMPASSE",
    "ALL": "ALLEE",
    "RTE": "ROUTE",
    "PL": "PLACE",
    "BD": "BOULEVARD",
    "SQ": "SQUARE",
    "CI": "CITE",
    "DOM": "DOMAINE",
    "LOT": "LOTISSEMENT",
    "LOTISSEMENT": "LOTISSEMENT",
    "GR": "GRAND RUE",
    "PLAN": "PLAN",
    "COUR": "COUR",
}

WASTE_TYPES = [
    ("om_jour", "om_typ_col", "Ordures ménagères"),
    ("ts_jour", "ts_typ_col", "Tri sélectif"),
    ("bio_jour", "bio_typ_co", "Biodéchets"),
    ("enc_u_jour", "enu_typ_co", "Encombrants"),
]

CSV_URL = "https://data.montpellier3m.fr/sites/default/files/ressources/MMM_MMM_ReferentielCollecte.csv"

# data.montpellier3m.fr serves an incomplete TLS chain: it sends only the leaf
# certificate (CN=*.montpellier3m.fr) and omits the GlobalSign intermediate that
# issued it. certifi (used by requests) ships the GlobalSign Root CA - R3 but not
# this intermediate, so the default verification fails with
# "unable to get local issuer certificate".
#
# To verify securely without disabling certificate checking, we bundle the missing
# intermediate below and combine it with certifi's trust store at fetch time.
# This is the "GlobalSign GCC R3 DV TLS CA 2020" intermediate
# (http://secure.globalsign.com/cacert/gsgccr3dvtlsca2020.crt), itself chained to
# the GlobalSign Root CA - R3 that certifi already trusts.
GLOBALSIGN_GCC_R3_DV_TLS_CA_2020 = """-----BEGIN CERTIFICATE-----
MIIEsDCCA5igAwIBAgIQd70OB0LV2enQSdd00CpvmjANBgkqhkiG9w0BAQsFADBM
MSAwHgYDVQQLExdHbG9iYWxTaWduIFJvb3QgQ0EgLSBSMzETMBEGA1UEChMKR2xv
YmFsU2lnbjETMBEGA1UEAxMKR2xvYmFsU2lnbjAeFw0yMDA3MjgwMDAwMDBaFw0y
OTAzMTgwMDAwMDBaMFMxCzAJBgNVBAYTAkJFMRkwFwYDVQQKExBHbG9iYWxTaWdu
IG52LXNhMSkwJwYDVQQDEyBHbG9iYWxTaWduIEdDQyBSMyBEViBUTFMgQ0EgMjAy
MDCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBAKxnlJV/de+OpwyvCXAJ
IcxPCqkFPh1lttW2oljS3oUqPKq8qX6m7K0OVKaKG3GXi4CJ4fHVUgZYE6HRdjqj
hhnuHY6EBCBegcUFgPG0scB12Wi8BHm9zKjWxo3Y2bwhO8Fvr8R42pW0eINc6OTb
QXC0VWFCMVzpcqgz6X49KMZowAMFV6XqtItcG0cMS//9dOJs4oBlpuqX9INxMTGp
6EASAF9cnlAGy/RXkVS9nOLCCa7pCYV+WgDKLTF+OK2Vxw3RUJ/p8009lQeUARv2
UCcNNPCifYX1xIspvarkdjzLwzOdLahDdQbJON58zN4V+lMj0msg+c0KnywPIRp3
BMkCAwEAAaOCAYUwggGBMA4GA1UdDwEB/wQEAwIBhjAdBgNVHSUEFjAUBggrBgEF
BQcDAQYIKwYBBQUHAwIwEgYDVR0TAQH/BAgwBgEB/wIBADAdBgNVHQ4EFgQUDZjA
c3+rvb3ZR0tJrQpKDKw+x3wwHwYDVR0jBBgwFoAUj/BLf6guRSSuTVD6Y5qL3uLd
G7wwewYIKwYBBQUHAQEEbzBtMC4GCCsGAQUFBzABhiJodHRwOi8vb2NzcDIuZ2xv
YmFsc2lnbi5jb20vcm9vdHIzMDsGCCsGAQUFBzAChi9odHRwOi8vc2VjdXJlLmds
b2JhbHNpZ24uY29tL2NhY2VydC9yb290LXIzLmNydDA2BgNVHR8ELzAtMCugKaAn
hiVodHRwOi8vY3JsLmdsb2JhbHNpZ24uY29tL3Jvb3QtcjMuY3JsMEcGA1UdIARA
MD4wPAYEVR0gADA0MDIGCCsGAQUFBwIBFiZodHRwczovL3d3dy5nbG9iYWxzaWdu
LmNvbS9yZXBvc2l0b3J5LzANBgkqhkiG9w0BAQsFAAOCAQEAy8j/c550ea86oCkf
r2W+ptTCYe6iVzvo7H0V1vUEADJOWelTv07Obf+YkEatdN1Jg09ctgSNv2h+LMTk
KRZdAXmsE3N5ve+z1Oa9kuiu7284LjeS09zHJQB4DJJJkvtIbjL/ylMK1fbMHhAW
i0O194TWvH3XWZGXZ6ByxTUIv1+kAIql/Mt29PmKraTT5jrzcVzQ5A9jw16yysuR
XRrLODlkS1hyBjsfyTNZrmL1h117IFgntBA5SQNVl9ckedq5r4RSAU85jV8XK5UL
REjRZt2I6M9Po9QL7guFLu4sPFJpwR1sPJvubS2THeo7SxYoNDtdyBHs7euaGcMa
D/fayQ==
-----END CERTIFICATE-----
"""

PARAM_TRANSLATIONS = {
    "en": {
        "street_name": "Street name",
        "house_number": "House number",
        "commune": "Commune (city)",
    },
    "fr": {
        "street_name": "Nom de rue",
        "house_number": "Numéro",
        "commune": "Commune",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "street_name": "Full street name, e.g. 'Rue Parlier' or 'Avenue de Montpellier'",
        "house_number": "House number (optional but recommended for accurate results)",
        "commune": "Commune name in capitals, e.g. 'MONTPELLIER', 'LATTES'. Helps when a street name appears in multiple communes.",
    },
    "fr": {
        "street_name": "Nom complet de la rue, ex : 'Rue Parlier' ou 'Avenue de Montpellier'",
        "house_number": "Numéro de maison (facultatif mais recommandé)",
        "commune": "Nom de la commune en majuscules, ex : 'MONTPELLIER', 'LATTES'. Utile si la rue existe dans plusieurs communes.",
    },
}


_ca_bundle_path: str | None = None


def _ca_bundle() -> str:
    """Return a CA bundle file combining certifi's roots with the missing intermediate.

    The bundle is written once to a temp file and reused for the process lifetime,
    so concurrent fetches do not each create a new file.
    """
    global _ca_bundle_path
    if _ca_bundle_path is not None and os.path.exists(_ca_bundle_path):
        return _ca_bundle_path

    with open(certifi.where(), encoding="ascii") as f:
        roots = f.read()

    fd, path = tempfile.mkstemp(prefix="montpellier3m_ca_", suffix=".pem")
    with os.fdopen(fd, "w", encoding="ascii") as f:
        f.write(roots)
        f.write("\n")
        f.write(GLOBALSIGN_GCC_R3_DV_TLS_CA_2020)

    _ca_bundle_path = path
    return path


def _normalize_street(name: str) -> str:
    parts = name.upper().strip().split()
    if parts and parts[0] in STREET_TYPE_MAP:
        parts[0] = STREET_TYPE_MAP[parts[0]]
    return " ".join(parts)


def _dates_from_day_code(day_code: str, weeks: int = 8) -> list[date]:
    today = date.today()
    result = []
    for code in day_code:
        if code not in DAY_CODE_MAP:
            continue
        target_wd = DAY_CODE_MAP[code]
        curr_wd = today.weekday()
        diff = (target_wd - curr_wd) % 7
        if diff == 0:
            diff = 7
        for week in range(weeks):
            result.append(today + timedelta(days=diff + week * 7))
    return result


class Source:
    def __init__(
        self,
        street_name: str,
        house_number: int | str | None = None,
        commune: str | None = None,
    ):
        self._street_name = street_name.strip()
        self._house_number = (
            str(house_number).strip() if house_number is not None else None
        )
        self._commune = commune.strip().upper() if commune else None

    def fetch(self) -> list[Collection]:
        response = requests.get(CSV_URL, timeout=120, verify=_ca_bundle())
        response.raise_for_status()

        content = response.content.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(content))

        normalized_input = _normalize_street(self._street_name)

        matching_rows = []
        for row in reader:
            voie = (row.get("nom_voie") or "").strip()
            if not voie:
                continue

            if _normalize_street(voie) != normalized_input:
                continue

            if (
                self._commune
                and row.get("commune", "").strip().upper() != self._commune
            ):
                continue

            if self._house_number is not None:
                row_num = (row.get("numero") or "").strip()
                if row_num != self._house_number:
                    continue

            matching_rows.append(row)

        if not matching_rows:
            raise SourceArgumentNotFound(
                "street_name",
                f"No results found for '{self._street_name}'"
                + (f" in {self._commune}" if self._commune else "")
                + (f" at number {self._house_number}" if self._house_number else ""),
            )

        entries: list[Collection] = []
        seen: set[tuple[str, date]] = set()

        for row in matching_rows:
            for jour_field, typ_field, label in WASTE_TYPES:
                jour = (row.get(jour_field) or "").strip()
                typ_col = (row.get(typ_field) or "").strip()

                if not jour or jour in ("NR", "RDV"):
                    continue
                if typ_col not in ("PAP", "PAV", "DEP"):
                    continue

                for d in _dates_from_day_code(jour):
                    key = (label, d)
                    if key not in seen:
                        seen.add(key)
                        entries.append(
                            Collection(
                                date=d,
                                t=label,
                                icon=ICON_MAP.get(label),
                            )
                        )

        if not entries:
            raise SourceArgumentNotFound(
                "street_name",
                f"Address found but no collection schedule available for '{self._street_name}'",
            )

        return entries
