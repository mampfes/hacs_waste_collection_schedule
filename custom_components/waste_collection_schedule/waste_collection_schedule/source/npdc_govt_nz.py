import datetime
import ssl

import certifi
import requests
from requests.adapters import HTTPAdapter
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "New Plymouth District Council"
DESCRIPTION = "Source for New Plymouth District Council waste collection."
URL = "https://www.npdc.govt.nz"
COUNTRY = "nz"
TEST_CASES = {
    "107 Coronation Avenue (Yellow/Wednesday)": {"address": "107 Coronation Avenue"},
    "5 Rata Street (Blue/Thursday)": {"address": "5 Rata Street"},
    "15 Rata Street (Blue/Wednesday)": {"address": "15 Rata Street"},
}

ICON_MAP = {
    "Glass and Landfill": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
    "Food Scraps": Icons.BIO_KITCHEN,
}

# Day-of-week index mapping (0=Sunday … 6=Saturday) matching the JS _dayArray
_DAY_INDEX = {
    "sunday": 0,
    "monday": 1,
    "tuesday": 2,
    "wednesday": 3,
    "thursday": 4,
    "friday": 5,
    "saturday": 6,
}

# Anchor date from the NPDC bin-collection app JavaScript (refuseMap.js).
# Weeks are counted from this Sunday; odd-numbered weeks are "Blue glass pickup weeks".
_ANCHOR = datetime.date(2015, 6, 28)  # Sunday 28 June 2015

SEARCH_URL = "https://gissearchwebapiproxy.npdcapps.co.nz/api/searchitem/"
COLLECTION_URL = (
    "https://gissearchwebapiproxy.npdcapps.co.nz/api/rubbishdays/ratedrefuseproperties/"
)

# The NPDC API host (gissearchwebapiproxy.npdcapps.co.nz) serves an incomplete /
# mismatched certificate chain: its leaf certificate (CN=*.npdcapps.co.nz) is issued
# by "Sectigo Public Server Authentication CA DV R36", but the server staples a
# stale, unrelated intermediate ("Sectigo RSA Domain Validation Secure Server CA")
# whose subject key identifier does not match the leaf's authority key identifier.
# As a result clients cannot build a trust path to the certifi-trusted Sectigo root,
# and the handshake fails with CERTIFICATE_VERIFY_FAILED (unable to get local issuer
# certificate). We supply the correct R36 intermediate ourselves, alongside the
# standard certifi trust store, so the chain can be validated without disabling
# verification. The intermediate below was fetched from the leaf's AIA caIssuers URL:
# http://crt.sectigo.com/SectigoPublicServerAuthenticationCADVR36.crt
_NPDC_INTERMEDIATE_CERT = """\
-----BEGIN CERTIFICATE-----
MIIGTDCCBDSgAwIBAgIQOXpmzCdWNi4NqofKbqvjsTANBgkqhkiG9w0BAQwFADBf
MQswCQYDVQQGEwJHQjEYMBYGA1UEChMPU2VjdGlnbyBMaW1pdGVkMTYwNAYDVQQD
Ey1TZWN0aWdvIFB1YmxpYyBTZXJ2ZXIgQXV0aGVudGljYXRpb24gUm9vdCBSNDYw
HhcNMjEwMzIyMDAwMDAwWhcNMzYwMzIxMjM1OTU5WjBgMQswCQYDVQQGEwJHQjEY
MBYGA1UEChMPU2VjdGlnbyBMaW1pdGVkMTcwNQYDVQQDEy5TZWN0aWdvIFB1Ymxp
YyBTZXJ2ZXIgQXV0aGVudGljYXRpb24gQ0EgRFYgUjM2MIIBojANBgkqhkiG9w0B
AQEFAAOCAY8AMIIBigKCAYEAljZf2HIz7+SPUPQCQObZYcrxLTHYdf1ZtMRe7Yeq
RPSwygz16qJ9cAWtWNTcuICc++p8Dct7zNGxCpqmEtqifO7NvuB5dEVexXn9RFFH
12Hm+NtPRQgXIFjx6MSJcNWuVO3XGE57L1mHlcQYj+g4hny90aFh2SCZCDEVkAja
EMMfYPKuCjHuuF+bzHFb/9gV8P9+ekcHENF2nR1efGWSKwnfG5RawlkaQDpRtZTm
M64TIsv/r7cyFO4nSjs1jLdXYdz5q3a4L0NoabZfbdxVb+CUEHfB0bpulZQtH1Rv
38e/lIdP7OTTIlZh6OYL6NhxP8So0/sht/4J9mqIGxRFc0/pC8suja+wcIUna0HB
pXKfXTKpzgis+zmXDL06ASJf5E4A2/m+Hp6b84sfPAwQ766rI65mh50S0Di9E3Pn
2WcaJc+PILsBmYpgtmgWTR9eV9otfKRUBfzHUHcVgarub/XluEpRlTtZudU5xbFN
xx/DgMrXLUAPaI60fZ6wA+PTAgMBAAGjggGBMIIBfTAfBgNVHSMEGDAWgBRWc1hk
lfmSGrASKgRieaFAFYghSTAdBgNVHQ4EFgQUaMASFhgOr872h6YyV6NGUV3LBycw
DgYDVR0PAQH/BAQDAgGGMBIGA1UdEwEB/wQIMAYBAf8CAQAwHQYDVR0lBBYwFAYI
KwYBBQUHAwEGCCsGAQUFBwMCMBsGA1UdIAQUMBIwBgYEVR0gADAIBgZngQwBAgEw
VAYDVR0fBE0wSzBJoEegRYZDaHR0cDovL2NybC5zZWN0aWdvLmNvbS9TZWN0aWdv
UHVibGljU2VydmVyQXV0aGVudGljYXRpb25Sb290UjQ2LmNybDCBhAYIKwYBBQUH
AQEEeDB2ME8GCCsGAQUFBzAChkNodHRwOi8vY3J0LnNlY3RpZ28uY29tL1NlY3Rp
Z29QdWJsaWNTZXJ2ZXJBdXRoZW50aWNhdGlvblJvb3RSNDYucDdjMCMGCCsGAQUF
BzABhhdodHRwOi8vb2NzcC5zZWN0aWdvLmNvbTANBgkqhkiG9w0BAQwFAAOCAgEA
YtOC9Fy+TqECFw40IospI92kLGgoSZGPOSQXMBqmsGWZUQ7rux7cj1du6d9rD6C8
ze1B2eQjkrGkIL/OF1s7vSmgYVafsRoZd/IHUrkoQvX8FZwUsmPu7amgBfaY3g+d
q1x0jNGKb6I6Bzdl6LgMD9qxp+3i7GQOnd9J8LFSietY6Z4jUBzVoOoz8iAU84OF
h2HhAuiPw1ai0VnY38RTI+8kepGWVfGxfBWzwH9uIjeooIeaosVFvE8cmYUB4TSH
5dUyD0jHct2+8ceKEtIoFU/FfHq/mDaVnvcDCZXtIgitdMFQdMZaVehmObyhRdDD
4NQCs0gaI9AAgFj4L9QtkARzhQLNyRf87Kln+YU0lgCGr9HLg3rGO8q+Y4ppLsOd
unQZ6ZxPNGIfOApbPVf5hCe58EZwiWdHIMn9lPP6+F404y8NNugbQixBber+x536
WrZhFZLjEkhp7fFXf9r32rNPfb74X/U90Bdy4lzp3+X1ukh1BuMxA/EEhDoTOS3l
7ABvc7BYSQubQ2490OcdkIzUh3ZwDrakMVrbaTxUM2p24N6dB+ns2zptWCva6jzW
r8IWKIMxzxLPv5Kt3ePKcUdvkBU/smqujSczTzzSjIoR5QqQA6lN1ZRSnuHIWCvh
JEltkYnTAH41QJ6SAWO66GrrUESwN/cgZzL4JLEqz1Y=
-----END CERTIFICATE-----
"""


class _NPDCChainAdapter(HTTPAdapter):
    """HTTPAdapter that adds the correct Sectigo R36 intermediate to the trust store.

    NPDC's API host serves a mismatched certificate chain, so we build an SSL context
    seeded with certifi's roots plus the missing intermediate, allowing certificate
    verification to succeed without disabling it.
    """

    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context(cafile=certifi.where())
        ctx.load_verify_locations(cadata=_NPDC_INTERMEDIATE_CERT)
        kwargs["ssl_context"] = ctx
        return super().init_poolmanager(*args, **kwargs)


def _weeks_since_anchor(d: datetime.date) -> int:
    return (d - _ANCHOR).days // 7


def _is_blue_glass_week(weeks_since: int) -> bool:
    """Return True when the week is a Blue-glass/landfill pickup week (odd offset)."""
    return weeks_since % 2 == 1


def _pick_up_date_for_week(weeks_since: int, day_index: int) -> datetime.date:
    """Return the pickup date for the given week offset and day-of-week index."""
    week_start = _ANCHOR + datetime.timedelta(weeks=weeks_since)
    return week_start + datetime.timedelta(days=day_index)


class Source:
    def __init__(self, address: str):
        self._address = address.strip()

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        session.mount("https://", _NPDCChainAdapter())

        # Step 1: Search for the parcel matching the address
        r = session.get(SEARCH_URL, params={"q": self._address}, timeout=30)
        r.raise_for_status()
        results = r.json()

        if not results:
            raise SourceArgumentNotFound("address", self._address)

        # Pick the best match — first result from the API
        parcel = results[0]
        parcel_id = parcel.get("parcelId")
        if not parcel_id:
            raise SourceArgumentNotFound("address", self._address)

        # Step 2: Fetch collection information for the parcel
        r2 = session.get(COLLECTION_URL, params={"parcelId": parcel_id}, timeout=30)
        r2.raise_for_status()
        collection_data = r2.json()

        if not collection_data:
            # The parcel exists but has no collection schedule (commercial, rural, etc.)
            suggestions = [r["address"] for r in results[:5] if r.get("address")]
            if len(suggestions) > 1:
                raise SourceArgumentNotFoundWithSuggestions(
                    "address", self._address, suggestions[1:]
                )
            raise SourceArgumentNotFound("address", self._address)

        record = collection_data[0]
        pick_week_colour = record.get("Week", "").lower()  # "blue" or "yellow"
        collect_day = record.get("CollectDay", "").lower()
        day_index = _DAY_INDEX.get(collect_day)

        if day_index is None or not pick_week_colour:
            raise SourceArgumentNotFound("address", self._address)

        # Step 3: Generate upcoming collection dates for the next 52 weeks
        today = datetime.date.today()
        weeks_today = _weeks_since_anchor(today)

        entries: list[Collection] = []

        # Scan from current week through 52 weeks ahead
        for week_offset in range(weeks_today, weeks_today + 53):
            pickup_date = _pick_up_date_for_week(week_offset, day_index)
            if pickup_date < today:
                continue

            blue_glass_week = _is_blue_glass_week(week_offset)

            # Determine what goes out this fortnightly cycle
            # Blue address → Glass+Landfill on odd (blue glass) weeks
            # Yellow address → Glass+Landfill on even (non-blue glass) weeks
            is_glass_landfill_week = (
                pick_week_colour == "blue"
                and blue_glass_week
                or pick_week_colour == "yellow"
                and not blue_glass_week
            )

            if is_glass_landfill_week:
                waste_type = "Glass and Landfill"
            else:
                waste_type = "Recycling"

            entries.append(
                Collection(
                    date=pickup_date,
                    t=waste_type,
                    icon=ICON_MAP.get(waste_type),
                )
            )

            # Food Scraps go out every week
            entries.append(
                Collection(
                    date=pickup_date,
                    t="Food Scraps",
                    icon=ICON_MAP.get("Food Scraps"),
                )
            )

        return entries
