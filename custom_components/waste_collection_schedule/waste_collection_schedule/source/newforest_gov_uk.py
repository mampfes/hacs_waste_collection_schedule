import http.client
from urllib.parse import urlencode

from bs4 import BeautifulSoup
from dateutil import parser as dateutil_parser
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (  # type: ignore[attr-defined]
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "New Forest District Council"
DESCRIPTION = "Source for newforest.gov.uk services for New Forest District Council."
URL = "https://www.newforest.gov.uk"
COUNTRY = "uk"
FORM_HOST = "forms.newforest.gov.uk"
FORM_PATH = "/ufs/FIND_MY_BIN_BAR.eb"
FORM_BASE_URL = f"https://{FORM_HOST}/ufs"

TEST_CASES = {
    "1 Oleander Drive, Totton": {"postcode": "SO40 8XX", "uprn": 100060514912},
    "49 Salisbury Road, Totton": {"postcode": "SO40 3HX", "uprn": "100060518013"},
    "12 Hawkins Close, Ringwood": {"postcode": "BH24 1UQ", "uprn": "100060495458"},
}

ICON_MAP = {
    "Food": Icons.BIO_KITCHEN,
    "Garden": Icons.GARDEN,
    "General": Icons.GENERAL_WASTE,
    "Glass": Icons.GLASS,
    "Recycle": Icons.RECYCLING,
}

PARAM_TRANSLATIONS = {
    "en": {
        "postcode": "Postcode",
        "uprn": "Unique Property Reference Number (UPRN)",
    }
}

PARAM_DESCRIPTIONS = {
    "en": {
        "postcode": "Your property's postcode, e.g. SO40 8XX",
        "uprn": "Your Unique Property Reference Number. Find it at https://www.findmyaddress.co.uk/",
    }
}


class Source:
    def __init__(self, postcode: str, uprn: str | int):
        self._postcode = str(postcode).strip()
        self._uprn = str(uprn).strip()

    def fetch(self) -> list[Collection]:
        conn = http.client.HTTPSConnection(FORM_HOST, timeout=30)
        try:
            jsessionid, ebs, formstack = self._init_session(conn)
            ebs2 = self._submit_postcode(conn, jsessionid, ebs, formstack)
            html = self._submit_uprn(conn, jsessionid, ebs2, formstack)
        finally:
            conn.close()

        return self._parse_collections(html)

    def _get(
        self,
        conn: http.client.HTTPSConnection,
        path: str,
        jsessionid: str | None = None,
    ) -> tuple[int, list[tuple[str, str]], str]:
        headers: dict[str, str] = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        if jsessionid:
            headers["Cookie"] = f"JSESSIONID={jsessionid}"
        conn.request("GET", path, headers=headers)
        resp = conn.getresponse()
        body = resp.read().decode("utf-8")
        # Return raw header list to preserve duplicates (server sends two Set-Cookie headers)
        return resp.status, resp.getheaders(), body

    def _post(
        self, conn: http.client.HTTPSConnection, path: str, data: dict, jsessionid: str
    ) -> tuple[int, list[tuple[str, str]]]:
        encoded = urlencode(data)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Content-Type": "application/x-www-form-urlencoded",
            "Content-Length": str(len(encoded.encode("utf-8"))),
            "Origin": FORM_BASE_URL,
            "Cookie": f"JSESSIONID={jsessionid}",
        }
        conn.request("POST", path, body=encoded, headers=headers)
        resp = conn.getresponse()
        resp.read()
        return resp.status, resp.getheaders()

    @staticmethod
    def _header(raw_headers: list[tuple[str, str]], name: str) -> str | None:
        """Return the first value for a header name (case-insensitive)."""
        name_lower = name.lower()
        for k, v in raw_headers:
            if k.lower() == name_lower:
                return v
        return None

    def _init_session(self, conn: http.client.HTTPSConnection) -> tuple[str, str, str]:
        """Perform the initial GET (following two redirects) to establish a session."""
        # First GET: server returns 302 with JSESSIONID in the first Set-Cookie header.
        # The server sends two Set-Cookie headers; the second is a malformed "Secure; HttpOnly"
        # that would overwrite JSESSIONID in a dict.  We use raw header iteration instead.
        status, raw_headers, _ = self._get(conn, FORM_PATH)
        jsessionid = None
        for k, v in raw_headers:
            if k.lower() == "set-cookie" and "JSESSIONID=" in v:
                jsessionid = v.split("JSESSIONID=")[1].split(";")[0]
                break
        if not jsessionid:
            raise Exception(
                "Could not obtain session cookie from New Forest form server."
            )

        # Second GET: follows the location from the 302
        loc1 = self._header(raw_headers, "location") or FORM_PATH
        status, raw_headers, _ = self._get(conn, f"/ufs/{loc1}", jsessionid)

        # Third GET: follows to the parameterised form URL (ebd=0&ebp=10&ebz=...)
        loc2 = self._header(raw_headers, "location") or loc1
        status, raw_headers, body = self._get(conn, f"/ufs/{loc2}", jsessionid)

        soup = BeautifulSoup(body, "html.parser")
        form = soup.find("form")
        if not form:
            raise Exception("Could not find the collection schedule form.")
        ebs = form.find("input", {"name": "ebs"})["value"]
        formstack = form.find("input", {"name": "formstack"})["value"]
        return jsessionid, ebs, formstack

    def _submit_postcode(
        self,
        conn: http.client.HTTPSConnection,
        jsessionid: str,
        ebs: str,
        formstack: str,
    ) -> str:
        """Submit the postcode and return the updated ebs for page 2."""
        status, raw_headers = self._post(
            conn,
            f"{FORM_PATH}?ebz={ebs}",
            {
                "formid": "/Forms/FIND_MY_BIN_BAR",
                "ebs": ebs,
                "origrequrl": f"{FORM_BASE_URL}/FIND_MY_BIN_BAR.eb",
                "formstack": formstack,
                "PAGE:E.h": "",
                "PAGE:B.h": "",
                "PAGE:N.h": "",
                "PAGE:S.h": "",
                "PAGE:R.h": "",
                "PAGE:D": "",
                "PAGE:H": "",
                "PAGE:X": "0",
                "PAGE:Y": "0",
                "PAGE:F": "CTID-EBTnjgwK-_",
                "ufsEndUser*": "1",
                "pageSeq": "1",
                "pageId": "Page_1",
                "formStateId": "1",
                "$USERVAR1": "",
                "$USERVAR2": "",
                "$USERVAR3": "",
                "CTRL:JmLqCKl2:_:A": self._postcode,
                "CTRL:JmLqCKl2:_:B.h": "",
                "HID:inputs": "ICTRL:JmLqCKl2:_:A,ACTRL:JmLqCKl2:_:B.h,ACTRL:EBTnjgwK:_,APAGE:E.h,APAGE:B.h,APAGE:N.h,APAGE:S.h,APAGE:R.h",
                "CTRL:EBTnjgwK:_": "Submit",
            },
            jsessionid,
        )
        loc = self._header(raw_headers, "location")
        if not loc:
            raise Exception(
                f"Postcode lookup did not redirect (status {status}). Check the postcode is valid."
            )

        # Follow redirect to page 2 (address selection)
        _, _, body = self._get(conn, f"/ufs/{loc}", jsessionid)
        soup = BeautifulSoup(body, "html.parser")

        # Validate that our UPRN is in the address list
        options = soup.find_all("option")
        available_uprns = [opt.get("value") for opt in options if opt.get("value")]
        if not available_uprns:
            raise Exception(f"No addresses found for postcode '{self._postcode}'.")
        if self._uprn not in available_uprns:
            raise SourceArgumentNotFoundWithSuggestions(
                "uprn",
                self._uprn,
                available_uprns,
            )

        form = soup.find("form")
        return form.find("input", {"name": "ebs"})["value"]

    def _submit_uprn(
        self,
        conn: http.client.HTTPSConnection,
        jsessionid: str,
        ebs: str,
        formstack: str,
    ) -> str:
        """Submit the UPRN and return the results page HTML."""
        status, raw_headers = self._post(
            conn,
            f"{FORM_PATH}?ebz={ebs}",
            {
                "formid": "/Forms/FIND_MY_BIN_BAR",
                "ebs": ebs,
                "origrequrl": f"{FORM_BASE_URL}/FIND_MY_BIN_BAR.eb",
                "formstack": formstack,
                "PAGE:E.h": "",
                "PAGE:B.h": "",
                "PAGE:N.h": "",
                "PAGE:S.h": "",
                "PAGE:R.h": "",
                "PAGE:D": "",
                "PAGE:H": "",
                "PAGE:X": "0",
                "PAGE:Y": "0",
                "PAGE:F": "",
                "ufsEndUser*": "1",
                "pageSeq": "2",
                "pageId": "Page_1",
                "formStateId": "1",
                "$USERVAR1": "",
                "$USERVAR2": "",
                "$USERVAR3": "",
                "CTRL:KOeKcmrC:_:A": self._uprn,
                "CTRL:KOeKcmrC:_:B.h": "",
                "HID:inputs": "ICTRL:KOeKcmrC:_:A,ACTRL:KOeKcmrC:_:B.h,ACTRL:QxB4NyYs:_,ACTRL:Ggx8Z7ze:_,APAGE:E.h,APAGE:B.h,APAGE:N.h,APAGE:S.h,APAGE:R.h",
                "CTRL:QxB4NyYs:_": "Submit",
            },
            jsessionid,
        )
        loc = self._header(raw_headers, "location")
        if not loc:
            raise Exception(f"UPRN submission did not redirect (status {status}).")

        _, _, body = self._get(conn, f"/ufs/{loc}", jsessionid)
        return body

    def _parse_collections(self, html: str) -> list[Collection]:
        soup = BeautifulSoup(html, "html.parser")

        # Find the "Future collections" table — it has a class containing "tableContent"
        # and exactly two column headers: "Collection date" and "Container type".
        collection_table = None
        for table in soup.find_all("table", class_=True):
            classes = " ".join(table.get("class", []))
            if "tableContent" not in classes:
                continue
            thead = table.find("thead")
            if not thead:
                continue
            th_tags = thead.find_all("th")
            header_texts = [th.get_text(strip=True) for th in th_tags]
            if header_texts == ["Collection date", "Container type"]:
                collection_table = table
                break

        if not collection_table:
            raise Exception(
                "Could not find the collection schedule table in the response."
            )

        entries = []
        for row in collection_table.find_all("tr")[1:]:  # skip header row
            cells = row.find_all("td")
            if len(cells) < 2:
                continue
            date_str = cells[0].get_text(strip=True)
            waste_type = cells[1].get_text(strip=True)
            if not date_str or not waste_type:
                continue
            try:
                date = dateutil_parser.parse(date_str).date()
            except Exception:
                continue

            # Map icon by the first word of the waste type (e.g. "Food", "General", etc.)
            icon = ICON_MAP.get(waste_type.split()[0] if waste_type else "")
            entries.append(Collection(date=date, t=waste_type, icon=icon))

        return entries
