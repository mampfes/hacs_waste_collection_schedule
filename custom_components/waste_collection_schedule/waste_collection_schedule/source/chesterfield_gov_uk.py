from typing import ClassVar, final

from waste_collection_schedule import date_parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.service.SalesforceAuraApex import (
    AuraApexRetriever,
    AuraServiceUnitsParser,
)
from waste_collection_schedule.transformers import RowTransformer

# myaccount.chesterfield.gov.uk sends its leaf certificate without the issuing
# intermediate, so certifi alone cannot verify it. This is the "GlobalSign GCC
# R3 EV TLS CA 2025" intermediate
# (http://secure.globalsign.com/cacert/gsgccr3evtlsca2025.crt), itself chained to
# the GlobalSign Root CA - R3 that certifi already trusts. It expires 2027-07-16.
_GLOBALSIGN_GCC_R3_EV_TLS_CA_2025 = """-----BEGIN CERTIFICATE-----
MIIElzCCA3+gAwIBAgIRAIPahmyfUtUakxi40OfAMWkwDQYJKoZIhvcNAQELBQAw
TDEgMB4GA1UECxMXR2xvYmFsU2lnbiBSb290IENBIC0gUjMxEzARBgNVBAoTCkds
b2JhbFNpZ24xEzARBgNVBAMTCkdsb2JhbFNpZ24wHhcNMjUwNzE2MDMwNTQ2WhcN
MjcwNzE2MDAwMDAwWjBTMQswCQYDVQQGEwJCRTEZMBcGA1UEChMQR2xvYmFsU2ln
biBudi1zYTEpMCcGA1UEAxMgR2xvYmFsU2lnbiBHQ0MgUjMgRVYgVExTIENBIDIw
MjUwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQDEG4l4CpUk556CyXIA
B3ihV2b8sWMNGwnW0wCpuaHHA5rlXpSWE1AD6r9hyGhQOrc45nPOj6Fvsqw8dFZw
FpAJzlk6FxhYP1ve8KPJvIpt6f5v28jOlzfs8c7dJ8ZmqKHB0Zj6RbAvA9vAl2A3
j0mu+ooXN3/QaFvVihDV/SRyOfFBlhPAsRk8y97tLPWx7/4YzfE6NSLKsU1yF+tf
BTttbaXTH/cWY/KQE3ZHTFRo6XouemjPBP9CDXeTR11tm37Bgn3QOj93FHdi1JJp
eNBGEOGvM8qhTV/77kDiUyOvsp4jZOhas6kIRn8nWK7fCPNdFJYi1Ctvd7gnQ1gB
lW71AgMBAAGjggFrMIIBZzAOBgNVHQ8BAf8EBAMCAYYwHQYDVR0lBBYwFAYIKwYB
BQUHAwEGCCsGAQUFBwMCMBIGA1UdEwEB/wQIMAYBAf8CAQAwHQYDVR0OBBYEFGMQ
f+QoM5r4R2BZUn5XEMdN+BcWMB8GA1UdIwQYMBaAFI/wS3+oLkUkrk1Q+mOai97i
3Ru8MHsGCCsGAQUFBwEBBG8wbTAuBggrBgEFBQcwAYYiaHR0cDovL29jc3AyLmds
b2JhbHNpZ24uY29tL3Jvb3RyMzA7BggrBgEFBQcwAoYvaHR0cDovL3NlY3VyZS5n
bG9iYWxzaWduLmNvbS9jYWNlcnQvcm9vdC1yMy5jcnQwNgYDVR0fBC8wLTAroCmg
J4YlaHR0cDovL2NybC5nbG9iYWxzaWduLmNvbS9yb290LXIzLmNybDAtBgNVHSAE
JjAkMAcGBWeBDAEBMAwGCisGAQQBoDIKAQEwCwYJKwYBBAGgMgEBMA0GCSqGSIb3
DQEBCwUAA4IBAQCtcTjIgw+tiW7E+sCTJ36nrC0IOxMpwE+nTaUG1xQJb+QE18vF
cPvEiqv8OonEBkQJFQ1N5YdDu9kydDYXBmIheYD9Z//TlUBnLL7HBje1ugplB0xE
jpU52q0XLxe6nHfeEKnslZ/Q/eDEsjZKxwF51SlGO6ap+09hfdbfMXDkTsfa+yXg
dIxZRCud0QEBTZAow0iCs3rf5wVALhhh2ePEwqxEm1LkUhvkJMLSCobYcJ+vXprK
JijbpPM602H1kqxNcD/nE7aCNm7g5GTaT04SCGYiQJ32r9mhx34peuYz05pY+AA3
aVB22PDvfoNyGZyClRtNt4KKg8dGJlYEhc3D
-----END CERTIFICATE-----
"""

_TYPE_MAP = {
    "Domestic Refuse": wt.GENERAL_WASTE,
    "Domestic Recycling": wt.RECYCLABLES,
    "Domestic Food": wt.FOOD_WASTE,
    "Domestic Paid Garden": wt.GARDEN_WASTE,
}


@final
class Source(BaseSource):
    TITLE = "Chesterfield Borough Council"
    DESCRIPTION = (
        "Source for waste collection services for Chesterfield Borough Council"
    )
    URL = "https://www.chesterfield.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"uprn": 74023685},
        "Test_002": {"uprn": "74009625"},
        "Test_003": {"uprn": "74035689"},
        "Test_004": {"uprn": "74020930"},
    }

    PARAMS = (uprn(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "An easy way to discover your Unique Property Reference Number (UPRN) "
            "is by going to [FindMyAddress.co.uk](https://www.findmyaddress.co.uk/) "
            "and entering your address details."
        ),
    }

    retrieve = AuraApexRetriever(
        "myaccount.chesterfield.gov.uk",
        app="cbc_VE_CollectionDaysLO",
        page_uri="/bins-and-recycling/bin-collections/check-bin-collections.aspx",
        classname="CBC_VE_CollectionDays",
        method="getServicesByUPRN",
        params=lambda uprn, **_: {
            "propertyUprn": str(uprn),
            "executedFrom": "Main Website",
        },
        ca_certs=_GLOBALSIGN_GCC_R3_EV_TLS_CA_2025,
    )
    parse = AuraServiceUnitsParser()
    transform = RowTransformer(
        parse_date=date_parsers.in_timezone("Europe/London"),
        clean=lambda label: label.removeprefix("Collect "),
        type_value_map=_TYPE_MAP,
    )
