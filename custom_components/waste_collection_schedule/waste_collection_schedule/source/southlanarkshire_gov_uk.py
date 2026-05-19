import calendar
import re
from datetime import datetime, timedelta
from io import BytesIO

from bs4 import BeautifulSoup
from curl_cffi import requests
from pypdf import PdfReader
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentRequired,
)

TITLE = "South Lanarkshire Council"
DESCRIPTION = "Source for South Lanarkshire Council waste collection."
URL = "https://www.southlanarkshire.gov.uk"
COUNTRY = "uk"
CALENDAR_INDEX_URL = "https://www.southlanarkshire.gov.uk/downloads/download/791/bin_collection_calendars"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
YEAR_PATTERN = r"20\d{2}"

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Find your street on the South Lanarkshire website. The URL format is `.../directory_record/574605/clincarthill_road_rutherglen`. Record ID is `574605` and Street Name is `clincarthill_road_rutherglen`.",
}

PARAM_TRANSLATIONS = {
    "en": {
        "record_id": "Directory Record ID",
        "street_name": "Street Name",
        "pdf_url": "Collection Calendar PDF URL",
    }
}

PARAM_DESCRIPTIONS = {
    "en": {
        "record_id": "The 6-digit number in your URL (e.g., 574605).",
        "street_name": "The text at the end of your URL (e.g., clincarthill_road_rutherglen).",
        "pdf_url": "REQUIRED: Full URL to council's bin collection calendar PDF. This is essential for determining your exact position in the 4-week collection cycle, as black bins appear twice per cycle. Find PDFs at https://www.southlanarkshire.gov.uk/downloads/download/791/bin_collection_calendars",
    }
}

TEST_CASES = {
    "Rutherglen": {
        "record_id": "574605",
        "street_name": "clincarthill_road_rutherglen",
        "pdf_url": "https://www.southlanarkshire.gov.uk/download/downloads/id/18301/east_kilbride_cambuslang_and_rutherglen_bin_collection_calendar_2026.pdf",
    },
    "Hamilton": {
        "record_id": "576617",
        "street_name": "alexander_balfour_gardens_hamilton",
        "pdf_url": "https://www.southlanarkshire.gov.uk/download/downloads/id/18300/hamilton_and_clydesdale_bin_collection_calendar_2026.pdf",
    },
    "Lesmahagow": {
        "record_id": "579971",
        "street_name": "abbeygreen_road_lesmahagow",
        "pdf_url": "https://www.southlanarkshire.gov.uk/download/downloads/id/18302/hamilton_and_clydesdale_bin_collection_calendar_2026_-_households_with_food_and_garden_waste_collected_on_the_same_week_as_general_waste.pdf",
    },
}


class Source:
    def __init__(self, record_id: str | int, street_name: str, pdf_url: str):
        if not pdf_url:
            raise SourceArgumentRequired(
                "pdf_url",
                "it is required to determine 4-week cycle position for black bins. "
                f"Find available calendars at {CALENDAR_INDEX_URL}",
            )
        self._record_id = str(record_id).zfill(6)
        self._street_name = str(street_name)
        self._pdf_url = pdf_url
        self._resolved_pdf_url = ""
        self._known_labels = []

    def fetch(self):
        import logging

        logger = logging.getLogger(__name__)
        # Keep label discovery scoped to each fetch run.
        self._known_labels = []

        soup = self._fetch_street_page_soup()
        self._validate_bin_details_present(soup)

        table = soup.find("table")
        if not table:
            raise RuntimeError("Could not find collection schedule table")

        rows = table.find_all("tr")
        self._set_known_labels_from_table_rows(rows)

        current_collection_date, bins_this_week = self._extract_current_week_context(
            soup, rows
        )

        logger.debug(f"Bins this week from website: {bins_this_week}")

        # Parse the PDF for dated collections and use the live page to fill the
        # current week if the PDF extraction misses it.
        pdf_url = self._resolve_pdf_url(logger)
        pdf_schedule = self._parse_pdf_schedule(pdf_url)
        self._merge_current_week_if_missing(
            pdf_schedule, current_collection_date, bins_this_week, logger
        )

        if not pdf_schedule:
            raise RuntimeError(
                "Could not derive a dated collection schedule from the PDF."
            )

        return self._build_collections(pdf_schedule, current_collection_date, logger)

    def _validate_bin_details_present(self, soup):
        if soup.find("div", {"class": "bin-dir-snip"}):
            return
        raise SourceArgumentNotFound(
            "record_id",
            self._record_id,
            "the street page did not contain bin collection details; please verify record_id and street_name.",
        )

    def _fetch_street_page_soup(self):
        s = requests.Session(impersonate="chrome")
        s.headers.update({"User-Agent": USER_AGENT})

        r = s.get(
            f"https://www.southlanarkshire.gov.uk/directory_record/{self._record_id}/{self._street_name}",
            timeout=30,
        )
        r.raise_for_status()
        return BeautifulSoup(r.text, "html.parser")

    def _extract_current_week_context(self, soup, rows):
        import logging

        logger = logging.getLogger(__name__)
        bin_div = soup.find("div", {"class": "bin-dir-snip"})
        if not bin_div:
            raise SourceArgumentNotFound(
                "record_id",
                self._record_id,
                "the street page did not contain bin collection details; please verify record_id and street_name.",
            )

        week_para = bin_div.find("p")
        if not week_para:
            raise RuntimeError("Could not find week information on the street page")

        week_text = week_para.text.strip()
        parts = week_text.split(" to ")
        if len(parts) != 2:
            raise RuntimeError(f"Unexpected week format: {week_text}")

        start_date_str = parts[0].strip()
        current_week_start = datetime.strptime(start_date_str, "%A %d %B %Y").date()

        bins_this_week = set()
        for li in bin_div.find_all("li"):
            h4 = li.find("h4")
            if h4:
                bin_name = h4.text.strip().lower()
                bins_this_week.add(bin_name)

        collection_day = self._extract_collection_day(rows)

        if not collection_day:
            raise RuntimeError("Could not determine collection day")

        collection_day_num = list(calendar.day_name).index(collection_day)

        days_to_collection = (collection_day_num - current_week_start.weekday()) % 7
        current_collection_date = current_week_start + timedelta(
            days=days_to_collection
        )

        logger.debug(
            f"Current week start: {current_week_start}, Collection day: {collection_day}, First collection date: {current_collection_date}"
        )
        return current_collection_date, bins_this_week

    def _extract_collection_day(self, rows):
        for row in rows:
            th = row.find("th")
            td = row.find("td")
            if not th or not td:
                continue

            day_match = re.match(
                r"(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)",
                td.text.strip(),
            )
            if day_match:
                return day_match.group(1)
        return None

    def _merge_current_week_if_missing(
        self, pdf_schedule, current_collection_date, bins_this_week, logger
    ):
        current_week_labels = self._extract_labels_from_texts(bins_this_week)
        if not current_week_labels:
            return

        existing_labels = list(pdf_schedule.get(current_collection_date, ()))
        for label in current_week_labels:
            if label not in existing_labels:
                existing_labels.append(label)

        pdf_schedule[current_collection_date] = tuple(existing_labels)
        logger.debug(
            "Merged current website week into PDF schedule: %s -> %s",
            current_collection_date,
            pdf_schedule[current_collection_date],
        )

    def _build_collections(self, pdf_schedule, current_collection_date, logger):
        collections = []
        horizon_end = current_collection_date + timedelta(weeks=52)
        for collection_date in sorted(pdf_schedule):
            if (
                collection_date < current_collection_date
                or collection_date >= horizon_end
            ):
                continue

            for bin_type in pdf_schedule[collection_date]:
                icon = self._get_icon_for_label(bin_type)
                collections.append(
                    Collection(date=collection_date, t=bin_type, icon=icon)
                )

        def get_sort_key(entry):
            sort_order = self._get_sort_order_for_label(entry.type)
            return (entry.date, sort_order)

        collections.sort(key=get_sort_key)

        # Log first 20 collections being passed to HA calendar (debug level)
        logger.debug(f"Total collections being sent to HA: {len(collections)}")
        for i, collection in enumerate(collections[:20]):
            logger.debug(
                f"  [{i+1}] {collection.date} ({collection.date.strftime('%A')}): {collection.type} (icon: {collection.icon})"
            )

        return collections

    def _resolve_pdf_url(self, logger):
        """Return a currently valid PDF URL for the selected calendar.

        The user-supplied URL usually contains a year. We try to match the same
        calendar in the listing page and prefer the latest available year.
        """
        if self._resolved_pdf_url:
            return self._resolved_pdf_url

        s = requests.Session(impersonate="chrome")
        s.headers.update({"User-Agent": USER_AGENT})

        try:
            r = s.get(CALENDAR_INDEX_URL, timeout=30)
            r.raise_for_status()
        except requests.RequestException:
            self._resolved_pdf_url = self._pdf_url
            return self._resolved_pdf_url

        pdf_links = self._collect_pdf_links(r.text)

        if not pdf_links:
            self._resolved_pdf_url = self._pdf_url
            return self._resolved_pdf_url

        candidates = self._filter_pdf_candidates(pdf_links)

        provided_norm = re.sub(YEAR_PATTERN, "YEAR", self._pdf_url.lower())
        same_calendar_links = [
            link
            for link in candidates
            if re.sub(YEAR_PATTERN, "YEAR", link.lower()) == provided_norm
        ]
        candidates = same_calendar_links if same_calendar_links else candidates

        def _year_key(link):
            year_match = re.search(YEAR_PATTERN, link)
            return int(year_match.group(0)) if year_match else 0

        best = max(candidates, key=_year_key)
        if best != self._pdf_url:
            logger.debug(
                "Updated PDF URL from listing page: %s -> %s", self._pdf_url, best
            )
        self._resolved_pdf_url = best
        return self._resolved_pdf_url

    def _collect_pdf_links(self, html):
        soup = BeautifulSoup(html, "html.parser")
        links = []
        for anchor in soup.find_all("a", href=True):
            href = anchor["href"]
            if ".pdf" not in href.lower() and "/downloads/file/" not in href.lower():
                continue

            if href.startswith("/"):
                href = f"{URL}{href}"
            elif not href.startswith("http"):
                href = f"{URL}/{href.lstrip('/')}"

            links.append(self._to_download_pdf_url(href))
        return links

    def _filter_pdf_candidates(self, pdf_links):
        provided_id_match = re.search(r"/download/downloads/id/(\d+)/", self._pdf_url)
        if not provided_id_match:
            provided_id_match = re.search(r"/downloads/file/(\d+)/", self._pdf_url)
        if not provided_id_match:
            return pdf_links

        provided_id = provided_id_match.group(1)
        same_id_links = [
            link
            for link in pdf_links
            if re.search(rf"/download/downloads/id/{provided_id}/", link)
        ]
        return same_id_links or pdf_links

    def _to_download_pdf_url(self, url):
        """Normalize listing/file URLs to direct PDF download URLs."""
        if "/download/downloads/id/" in url:
            return url

        match = re.search(r"/downloads/file/(\d+)/(.*)$", url)
        if not match:
            return url

        file_id = match.group(1)
        slug = match.group(2).rstrip("/")
        if not slug.lower().endswith(".pdf"):
            slug = f"{slug}.pdf"

        return f"{URL}/download/downloads/id/{file_id}/{slug}"

    def _parse_pdf_schedule(self, pdf_url=None):
        """Parse PDF to extract date -> bin-type entries used for cycle disambiguation."""
        import logging

        logger = logging.getLogger(__name__)

        if pdf_url is None:
            pdf_url = self._pdf_url

        s = requests.Session(impersonate="chrome")
        s.headers.update({"User-Agent": USER_AGENT})

        schedule = {}

        pdf_reader = self._download_pdf_reader(s, pdf_url, logger)
        all_text = self._extract_pdf_text(pdf_reader, logger)

        # Try to detect year from PDF filename or content
        year_from_url = re.search(YEAR_PATTERN, pdf_url)
        current_year = datetime.now().year
        years_to_try = [current_year]
        if year_from_url:
            pdf_year = int(year_from_url.group())
            if pdf_year not in years_to_try:
                years_to_try.insert(0, pdf_year)
        years_to_try.append(current_year + 1)
        logger.debug(f"Will try years: {years_to_try}")

        if not all_text.strip():
            logger.error(
                "No text extracted from PDF at all - PDF may be image-based or encrypted"
            )
            return schedule

        # Log first 1000 chars AND last 500 chars to help debug
        logger.debug(f"First 1000 chars of PDF text: {all_text[:1000]}")
        logger.debug(f"Last 500 chars of PDF text: {all_text[-500:]}")

        if not self._known_labels:
            self._bootstrap_known_labels_from_pdf(
                lines=[line.strip() for line in all_text.splitlines() if line.strip()]
            )

        # Check if any known label tokens exist ANYWHERE in the PDF
        bin_keywords = self._known_label_tokens()
        found_keywords = [kw for kw in bin_keywords if kw in all_text.lower()]
        logger.debug(f"Bin keywords found in entire PDF: {found_keywords}")

        # If NO keywords found, try alternative extraction without layout mode
        if not found_keywords:
            logger.debug(
                "No bin keywords found with layout mode, trying default extraction..."
            )
            all_text_alt = self._extract_pdf_text(
                pdf_reader, logger, force_default=True
            )
            logger.debug(f"Alternative extraction: {len(all_text_alt)} characters")
            logger.debug(f"Alternative first 1000 chars: {all_text_alt[:1000]}")

            # Check keywords again
            found_keywords_alt = [
                kw for kw in bin_keywords if kw in all_text_alt.lower()
            ]
            logger.debug(f"Alternative extraction bin keywords: {found_keywords_alt}")

            # Use alternative text if it has more keywords
            if len(found_keywords_alt) > len(found_keywords):
                logger.debug("Using alternative extraction as it has more bin keywords")
                all_text = all_text_alt

        lines = [line.strip() for line in all_text.splitlines() if line.strip()]
        if not self._known_labels:
            self._bootstrap_known_labels_from_pdf(lines)
        self._add_pdf_schedule_entries(schedule, lines, years_to_try)

        schedule = {
            collection_date: tuple(colors)
            for collection_date, colors in schedule.items()
            if colors
        }

        logger.debug(f"Parsed {len(schedule)} dated bin entries from PDF")

        if not schedule:
            logger.error(
                "No dates with bins found in PDF. "
                "This may be due to: 1) PDF is image-based (not text), "
                "2) Date format doesn't match patterns, "
                "3) Bin keywords not found near dates. "
                f"PDF URL: {pdf_url}"
            )

        return schedule

    def _download_pdf_reader(self, session, pdf_url, logger):
        logger.debug(f"Downloading PDF from: {pdf_url}")
        response = session.get(pdf_url, timeout=30)
        response.raise_for_status()
        logger.debug(f"PDF downloaded, size: {len(response.content)} bytes")
        pdf_reader = PdfReader(BytesIO(response.content))
        logger.debug(f"PDF has {len(pdf_reader.pages)} pages")
        return pdf_reader

    def _extract_pdf_text(self, pdf_reader, logger, force_default=False):
        all_text = ""
        for page_num, page in enumerate(pdf_reader.pages, start=1):
            text = ""
            if not force_default:
                try:
                    text = page.extract_text(extraction_mode="layout") or ""
                    logger.debug(f"Page {page_num}: extracted text with layout mode")
                except (TypeError, AttributeError) as error:
                    logger.debug(
                        f"Page {page_num}: layout mode not supported ({error}), using default"
                    )
            if not text:
                text = page.extract_text() or ""
                logger.debug(f"Page {page_num}: extracted text with default mode")

            if text:
                all_text += text + "\n"
                logger.debug(f"Page {page_num}: extracted {len(text)} characters")
            else:
                logger.debug(f"Page {page_num}: no text extracted")

        logger.debug(f"Total text extracted: {len(all_text)} characters")
        return all_text

    def _known_label_tokens(self):
        return sorted(
            {
                token
                for label in self._known_labels
                for token in self._label_match_tokens(label)
            }
        )

    def _add_pdf_schedule_entries(self, schedule, lines, years_to_try):
        simple_date_pattern = re.compile(
            r"(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)"
        )

        previous_date = None
        for idx, line in enumerate(lines):
            week_labels = self._identify_bins_from_pdf_lines(lines, idx)
            if not week_labels:
                continue

            for date_match in simple_date_pattern.finditer(line):
                day, month = date_match.groups()
                date_obj = self._parse_collection_date(
                    day, month, years_to_try, previous_date
                )
                if date_obj is None:
                    continue

                existing = schedule.setdefault(date_obj, [])
                for label in week_labels:
                    if label not in existing:
                        existing.append(label)

                previous_date = date_obj

    def _parse_collection_date(self, day, month, years_to_try, previous_date):
        candidates = []
        for year in years_to_try:
            try:
                candidates.append(
                    datetime.strptime(f"{day} {month} {year}", "%d %B %Y").date()
                )
            except ValueError:
                continue

        if not candidates:
            return None

        if previous_date is None:
            return min(candidates, key=lambda d: abs((d - datetime.now().date()).days))

        non_past = [d for d in candidates if d >= previous_date - timedelta(days=7)]
        if non_past:
            return min(non_past, key=lambda d: abs((d - previous_date).days))
        return min(candidates, key=lambda d: abs((d - previous_date).days))

    def _identify_bins_from_pdf_lines(self, lines, current_line_idx):
        """Extract known bin labels from PDF text around a date."""
        import logging

        logger = logging.getLogger(__name__)

        date_regex = re.compile(
            r"\b\d{1,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December)\b",
            re.IGNORECASE,
        )

        search_lines = []
        line_idx = current_line_idx - 1
        while line_idx >= 0:
            if date_regex.search(lines[line_idx]):
                break
            search_lines.append(lines[line_idx])
            line_idx -= 1

        bins = self._extract_labels_from_texts(reversed(search_lines))

        if bins:
            logger.debug(
                f"Line {current_line_idx}: identified bins {bins} from surrounding text"
            )

        return bins if bins else None

    def _extract_labels_from_texts(self, labels):
        """Infer known bin labels from one or more text fragments."""
        matches = []

        for label in labels:
            label_tokens = self._tokenize_label(label)
            if not label_tokens:
                continue

            for known_label in self._known_labels:
                match_tokens = self._label_match_tokens(known_label)
                if label_tokens & match_tokens and known_label not in matches:
                    matches.append(known_label)

        return tuple(matches)

    def _bootstrap_known_labels_from_pdf(self, lines):
        """Seed known labels from PDF legend-like lines when table rows are unavailable."""
        date_regex = re.compile(
            r"\b\d{1,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December)\b",
            re.IGNORECASE,
        )
        ignore_regex = re.compile(
            r"\b(permit required|collection calendar|food waste collected)\b",
            re.IGNORECASE,
        )

        for raw_line in lines:
            line = " ".join(raw_line.split())
            if date_regex.search(line):
                continue
            if len(line) < 4 or len(line) > 140:
                continue
            if ignore_regex.search(line):
                continue

            if "-" not in line and "(" not in line:
                continue
            if len(self._tokenize_label(line)) < 2:
                continue

            if line not in self._known_labels:
                self._known_labels.append(line)

    def _set_known_labels_from_table_rows(self, rows):
        """Populate known bin labels from live table headings."""
        for row in rows:
            th = row.find("th")
            td = row.find("td")
            if not th or not td:
                continue

            schedule_text = td.get_text(" ", strip=True)
            if not re.search(r"\((Fortnightly|4 Weekly)\)", schedule_text):
                continue

            label = th.get_text(" ", strip=True)
            if label not in self._known_labels:
                self._known_labels.append(label)

    def _tokenize_label(self, label):
        return {
            token
            for token in re.findall(r"[a-z]+", str(label).lower())
            if len(token) >= 3
        }

    def _label_match_tokens(self, label):
        all_tokens = self._tokenize_label(label)
        token_counts = {}
        for known_label in self._known_labels:
            for token in self._tokenize_label(known_label):
                token_counts[token] = token_counts.get(token, 0) + 1

        unique_tokens = {token for token in all_tokens if token_counts.get(token) == 1}
        return unique_tokens or all_tokens

    def _get_icon_for_label(self, label):
        """Get the MDI icon for a label extracted from upstream content."""
        label_lower = str(label).lower()

        if "non recyclable" in label_lower or "general waste" in label_lower:
            return "mdi:trash-can"
        if "food" in label_lower:
            return "mdi:food-apple"
        if "garden" in label_lower or "green waste" in label_lower:
            return "mdi:leaf"
        if any(
            token in label_lower
            for token in ["recycl", "paper", "card", "glass", "cans", "plastic"]
        ):
            return "mdi:recycle"

        return "mdi:trash-can"

    def _get_sort_order_for_label(self, label):
        """Get sort priority based on the live table label order."""
        try:
            return self._known_labels.index(label)
        except ValueError:
            return 99
