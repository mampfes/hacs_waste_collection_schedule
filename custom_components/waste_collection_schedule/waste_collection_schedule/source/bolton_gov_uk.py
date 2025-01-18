import datetime
import re
import ssl
from bs4 import BeautifulSoup
import requests
from urllib3.util.ssl_ import create_urllib3_context
from waste_collection_schedule import Collection

TITLE = "Bolton Council"
DESCRIPTION = "Source for Bolton Council, UK."
URL = "https://www.bolton.gov.uk"
BIN_URL = "https://carehomes.bolton.gov.uk/bins.aspx"

TEST_CASES = {
    "Farnworth": {"postcode": "BL4 7PH", "uprn": "100010914234"},  # Buckley Lane
    "Horwich": {"postcode": "BL1 3BW", "uprn": "200002545501"},  # Winter Hey Lane
    "Westhoughton": {"postcode": "BL5 2AX", "uprn": "100010939810"},  # Church Street
}

ICON_MAP = {
    "Grey bin": "mdi:trash-can",
    "Beige bin": "mdi:newspaper-variant",
    "Burgundy bin": "mdi:bottle-soda",
    "Green bin": "mdi:leaf",
    "Food container": "mdi:food",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-GB,en;q=0.7",
}


class CustomHttpAdapter(requests.adapters.HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        context = create_urllib3_context(
            cert_reqs=ssl.CERT_NONE, ciphers="DEFAULT:@SECLEVEL=1"
        )
        context.options |= 0x4
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.maximum_version = ssl.TLSVersion.TLSv1_2
        kwargs["ssl_context"] = context
        return super().init_poolmanager(*args, **kwargs)


class Source:
    def __init__(self, postcode: str, uprn: str):
        self._postcode = postcode
        self._uprn = uprn

    def fetch(self):
        entries = []
        session = requests.Session()
        session.headers.update(HEADERS)
        session.verify = False

        adapter = CustomHttpAdapter()
        session.mount("https://", adapter)

        try:
            # Get initial form tokens
            r = session.get(BIN_URL, timeout=30)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")

            # Submit postcode
            viewstate = soup.find("input", {"name": "__VIEWSTATE"})["value"]
            viewstategenerator = soup.find("input", {"name": "__VIEWSTATEGENERATOR"})[
                "value"
            ]
            eventvalidation = soup.find("input", {"name": "__EVENTVALIDATION"})["value"]

            r = session.post(
                BIN_URL,
                data={
                    "__VIEWSTATE": viewstate,
                    "__VIEWSTATEGENERATOR": viewstategenerator,
                    "__EVENTVALIDATION": eventvalidation,
                    "txtPostcode": self._postcode,
                    "btnSubmit": "Submit",
                },
                timeout=30,
            )
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")

            # Select address
            viewstate = soup.find("input", {"name": "__VIEWSTATE"})["value"]
            viewstategenerator = soup.find("input", {"name": "__VIEWSTATEGENERATOR"})[
                "value"
            ]
            eventvalidation = soup.find("input", {"name": "__EVENTVALIDATION"})["value"]

            r = session.post(
                BIN_URL,
                data={
                    "__EVENTTARGET": "ddlAddresses",
                    "__EVENTARGUMENT": "",
                    "__LASTFOCUS": "",
                    "__VIEWSTATE": viewstate,
                    "__VIEWSTATEGENERATOR": viewstategenerator,
                    "__EVENTVALIDATION": eventvalidation,
                    "txtPostcode": self._postcode,
                    "ddlAddresses": self._uprn,
                },
                timeout=30,
            )
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")

            # Parse collection dates
            for bin_info in soup.find_all("div", class_="bin-info"):
                strong_tag = bin_info.find("strong")
                if strong_tag:
                    text = strong_tag.text.strip()
                    match = re.match(
                        r"Your next (.*?) collection\(s\) will be on", text
                    )
                    if match:
                        bin_type = match.group(1)
                        for date_p in bin_info.find_all("p", class_="date"):
                            date_text = date_p.find("span").text.strip()
                            try:
                                collection_date = datetime.datetime.strptime(
                                    date_text, "%A %d %B %Y"
                                ).date()
                                entries.append(
                                    Collection(
                                        date=collection_date,
                                        t=bin_type,
                                        icon=ICON_MAP.get(bin_type),
                                    )
                                )
                            except ValueError:
                                continue

        except requests.RequestException as e:
            raise Exception(f"Error fetching data: {e}")

        return entries
