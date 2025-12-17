from urllib.parse import parse_qs, urlparse

import cloudscraper
from bs4 import BeautifulSoup
from dateutil import parser
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "East Renfrewshire Council"
DESCRIPTION = "Source for eastrenfrewshire.gov.uk services for East Renfrewshire"
URL = "https://eastrenfrewshire.gov.uk"  # apex host (no www)
FORM_PAGE = f"{URL}/bin-days"

TEST_CASES = {
    "Test_001": {"postcode": "G78 2TJ", "uprn": "131016859"},
    "Test_002": {"postcode": "g775ar", "uprn": 131019331},
    "Test_003": {"postcode": "g78 3er", "uprn": "000131020112"},
}

ICON_MAP = {
    "Grey": "mdi:trash-can",
    "Brown": "mdi:leaf",
    "Green": "mdi:glass-fragile",
    "Blue": "mdi:note",
}


class Source:
    def __init__(self, postcode, uprn):
        if not postcode or not uprn:
            raise ValueError("Both 'postcode' and 'uprn' must be provided.")
        self._postcode = postcode
        self._uprn = str(uprn).zfill(12)

    def fetch(self):
        # Cloudflare-aware session
        session = cloudscraper.create_scraper(
            browser={"browser": "chrome", "platform": "windows", "mobile": False}
        )
        session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/129.0.0.0 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-GB,en;q=0.9",
            }
        )

        address_page = self.__get_address_page(session, self._postcode)
        bin_collection_info_page = self.__get_bin_collection_info_page(
            session, address_page, self._uprn
        )
        return self.__get_bin_collection_info(bin_collection_info_page)

    def __get_address_page(self, s, postcode):
        r = s.get(FORM_PAGE, timeout=30)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        form = soup.find(id="BINDAYSV2_FORM")
        if not form or not form.has_attr("action"):
            raise Exception(
                "Form with id 'BINDAYSV2_FORM' and 'action' attribute not found on PAGE1."
            )

        # Prefer hidden inputs if present; fallback to action query params
        def _val(name):
            el = form.find("input", attrs={"name": name})
            return el["value"] if el and el.has_attr("value") else ""

        page_session_id = _val("BINDAYSV2_PAGESESSIONID")
        session_id = _val("BINDAYSV2_SESSIONID")
        nonce = _val("BINDAYSV2_NONCE")
        if not (page_session_id and session_id and nonce):
            goss_ids = self.__get_goss_form_ids(form["action"])
            page_session_id = page_session_id or goss_ids["page_session_id"]
            session_id = session_id or goss_ids["session_id"]
            nonce = nonce or goss_ids["nonce"]

        r = s.post(
            form["action"],
            headers={"Origin": URL, "Referer": FORM_PAGE},
            data={
                "BINDAYSV2_PAGESESSIONID": page_session_id,
                "BINDAYSV2_SESSIONID": session_id,
                "BINDAYSV2_NONCE": nonce,
                "BINDAYSV2_VARIABLES": "e30=",
                "BINDAYSV2_PAGENAME": "PAGE1",
                "BINDAYSV2_PAGEINSTANCE": "0",
                "BINDAYSV2_PAGE1_POSTCODE": postcode,
                "BINDAYSV2_FORMACTION_NEXT": "BINDAYSV2_PAGE1_FIELD290",
            },
            timeout=30,
        )
        r.raise_for_status()
        return r.text

    def __get_bin_collection_info_page(self, session, address_page, uprn):
        soup = BeautifulSoup(address_page, "html.parser")
        form = soup.find(id="BINDAYSV2_FORM")
        if not form or not form.has_attr("action"):
            raise Exception(
                "Form with id 'BINDAYSV2_FORM' and 'action' attribute not found on PAGE2."
            )

        def _val(name):
            el = form.find("input", attrs={"name": name})
            return el["value"] if el and el.has_attr("value") else ""

        page_session_id = _val("BINDAYSV2_PAGESESSIONID")
        session_id = _val("BINDAYSV2_SESSIONID")
        nonce = _val("BINDAYSV2_NONCE")
        if not (page_session_id and session_id and nonce):
            goss_ids = self.__get_goss_form_ids(form["action"])
            page_session_id = page_session_id or goss_ids["page_session_id"]
            session_id = session_id or goss_ids["session_id"]
            nonce = nonce or goss_ids["nonce"]

        r = session.post(
            form["action"],
            headers={"Origin": URL, "Referer": FORM_PAGE},
            data={
                "BINDAYSV2_PAGESESSIONID": page_session_id,
                "BINDAYSV2_SESSIONID": session_id,
                "BINDAYSV2_NONCE": nonce,
                "BINDAYSV2_VARIABLES": "e30=",
                "BINDAYSV2_PAGENAME": "PAGE2",
                "BINDAYSV2_PAGEINSTANCE": "0",
                "BINDAYSV2_PAGE2_FIELD293": "true",
                "BINDAYSV2_PAGE2_UPRN": uprn,
                "BINDAYSV2_FORMACTION_NEXT": "BINDAYSV2_PAGE2_FIELD294",
                "BINDAYSV2_PAGE2_FIELD295": "false",
                "BINDAYSV2_PAGE2_FIELD297": "false",
            },
            timeout=30,
        )
        r.raise_for_status()
        return r.text

    def __get_bin_collection_info(self, html_page):
        soup = BeautifulSoup(html_page, "html.parser")
        table_div = soup.find("div", id="BINDAYSV2_RESULTS_NEXTCOLLECTIONLISTV4")
        if not table_div:
            raise Exception("Could not find bin collection results table.")

        rows = table_div.find_all("tr")[1:]  # skip header
        entries = []

        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 3:
                continue

            date_str = cols[0].get_text(strip=True)
            bin_types_html = cols[2]

            try:
                date = parser.parse(date_str, dayfirst=True).date()
            except Exception:
                continue

            for img in bin_types_html.find_all("img"):
                color = img.get("alt", "").split()[0]
                entries.append(
                    Collection(
                        date=date,
                        t=color,
                        icon=ICON_MAP.get(color),
                    )
                )

        return entries

    def __get_goss_form_ids(self, url):
        parsed = urlparse(url)
        qs = parse_qs(parsed.query)
        return {
            "page_session_id": qs.get("pageSessionId", [""])[0],
            "session_id": qs.get("fsid", [""])[0],
            "nonce": qs.get("fsn", [""])[0],
        }
