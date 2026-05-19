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

# Default icon mapping as fallback. Icons are extracted from PDF when available.
_DEFAULT_ICON_MAP = {
    "black": "mdi:trash-can",
    "green": "mdi:trash-can",
    "burgundy": "mdi:leaf",
    "blue": "mdi:file-document-outline",
    "grey": "mdi:glass-fragile",
}

# Default sort order as fallback. Order is determined from PDF table sequence when available.
_DEFAULT_SORT_ORDER = {
    "blue": 1,
    "grey": 2,
    "burgundy": 3,
    "black": 4,
    "green": 4,
}

# Keywords to recognize color names in PDF text and web pages.
COLOR_KEYWORDS = {
    "black": ("black", "green"),
    "blue": ("blue",),
    "grey": ("grey", "gray", "light grey"),
    "burgundy": ("burgundy", "brown"),
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
        self._pdf_color_labels = {}
        self._bin_order_from_table = (
            []
        )  # Track order from web table for sort priorities

    def fetch(self):
        import logging

        logger = logging.getLogger(__name__)

        # Get current week's bins from website
        s = requests.Session(impersonate="chrome")
        s.headers.update({"User-Agent": USER_AGENT})

        r = s.get(
            f"https://www.southlanarkshire.gov.uk/directory_record/{self._record_id}/{self._street_name}"
        )
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")

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
        bins_this_week_elements = bin_div.find_all("li")
        for li in bins_this_week_elements:
            h4 = li.find("h4")
            if h4:
                bin_name = h4.text.strip().lower()
                bins_this_week.add(bin_name)

        table = soup.find("table")
        if not table:
            raise RuntimeError("Could not find collection schedule table")

        rows = table.find_all("tr")
        self._set_color_labels_from_table_rows(rows)
        collection_day = None

        for row in rows:
            th = row.find("th")
            td = row.find("td")
            if th and td:
                schedule_text = td.text.strip()
                day_match = re.match(
                    r"(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)",
                    schedule_text,
                )
                if day_match and collection_day is None:
                    collection_day = day_match.group(1)

        if not collection_day:
            raise RuntimeError("Could not determine collection day")

        day_map = {
            "Monday": 0,
            "Tuesday": 1,
            "Wednesday": 2,
            "Thursday": 3,
            "Friday": 4,
            "Saturday": 5,
            "Sunday": 6,
        }
        collection_day_num = day_map[collection_day]

        days_to_collection = (collection_day_num - current_week_start.weekday()) % 7
        current_collection_date = current_week_start + timedelta(
            days=days_to_collection
        )

        logger.debug(
            f"Current week start: {current_week_start}, Collection day: {collection_day}, First collection date: {current_collection_date}"
        )
        logger.debug(f"Bins this week from website: {bins_this_week}")

        # Parse PDF to determine position in 4-week cycle.
        pdf_url = self._resolve_pdf_url(logger)
        pdf_schedule = self._parse_pdf_schedule(pdf_url)
        cycle_position = self._determine_cycle_position(
            current_collection_date, pdf_schedule, bins_this_week
        )
        pattern_cycle = self._get_pattern_from_cycle_position(cycle_position)

        logger.debug(
            f"Website bins: {bins_this_week}, Detected position: {cycle_position}, Expected pattern at position 0: {pattern_cycle[0]}"
        )
        logger.debug(
            f"Cycle position detected: {cycle_position}, Pattern: {pattern_cycle}"
        )

        collections = []
        for week_offset in range(52):
            collection_date = current_collection_date + timedelta(weeks=week_offset)
            bins_for_week = pattern_cycle[week_offset % len(pattern_cycle)]

            for bin_type in bins_for_week:
                bin_color = self._infer_color_from_label(bin_type)
                icon = self._get_icon_for_color(bin_color)
                collections.append(
                    Collection(date=collection_date, t=bin_type, icon=icon)
                )

        def get_sort_key(entry):
            bin_color = self._infer_color_from_label(entry.type)
            sort_order = self._get_sort_order_for_color(bin_color)
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

        soup = BeautifulSoup(r.text, "html.parser")
        pdf_links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if ".pdf" not in href.lower():
                if "/downloads/file/" not in href.lower():
                    continue
            if href.startswith("/"):
                href = f"{URL}{href}"
            elif href.startswith("http"):
                href = href
            else:
                href = f"{URL}/{href.lstrip('/')}"
            href = self._to_download_pdf_url(href)
            pdf_links.append(href)

        if not pdf_links:
            self._resolved_pdf_url = self._pdf_url
            return self._resolved_pdf_url

        provided_id_match = re.search(r"/download/downloads/id/(\d+)/", self._pdf_url)
        if not provided_id_match:
            provided_id_match = re.search(r"/downloads/file/(\d+)/", self._pdf_url)
        if provided_id_match:
            provided_id = provided_id_match.group(1)
            same_id_links = [
                link
                for link in pdf_links
                if re.search(rf"/download/downloads/id/{provided_id}/", link)
            ]
            if same_id_links:
                candidates = same_id_links
            else:
                candidates = pdf_links
        else:
            candidates = pdf_links

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

        # Add timeout to prevent hanging in Home Assistant
        logger.debug(f"Downloading PDF from: {pdf_url}")
        response = s.get(pdf_url, timeout=30)
        response.raise_for_status()
        logger.debug(f"PDF downloaded, size: {len(response.content)} bytes")

        pdf_reader = PdfReader(BytesIO(response.content))
        schedule = {}

        logger.debug(f"PDF has {len(pdf_reader.pages)} pages")

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

        # Extract text from all pages and parse dates and bins
        all_text = ""
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            # Try layout mode first, fall back to default if not supported
            try:
                text = page.extract_text(extraction_mode="layout")
                logger.debug(f"Page {page_num + 1}: extracted text with layout mode")
            except (TypeError, AttributeError) as e:
                # Older pypdf versions don't support extraction_mode parameter
                text = page.extract_text()
                logger.debug(
                    f"Page {page_num + 1}: extracted text with default mode (layout not supported: {e})"
                )
            if text:
                all_text += text + "\n"
                logger.debug(f"Page {page_num + 1}: extracted {len(text)} characters")
            else:
                logger.debug(f"Page {page_num + 1}: no text extracted")

        logger.debug(f"Total text extracted: {len(all_text)} characters")

        if not all_text.strip():
            logger.error(
                "No text extracted from PDF at all - PDF may be image-based or encrypted"
            )
            return schedule

        # Log first 1000 chars AND last 500 chars to help debug
        logger.debug(f"First 1000 chars of PDF text: {all_text[:1000]}")
        logger.debug(f"Last 500 chars of PDF text: {all_text[-500:]}")

        # Check if bin keywords exist ANYWHERE in the PDF
        bin_keywords = ["black", "blue", "grey", "gray", "burgundy", "brown", "green"]
        found_keywords = [kw for kw in bin_keywords if kw in all_text.lower()]
        logger.debug(f"Bin keywords found in entire PDF: {found_keywords}")

        # If NO keywords found, try alternative extraction without layout mode
        if not found_keywords:
            logger.debug(
                "No bin keywords found with layout mode, trying default extraction..."
            )
            all_text_alt = ""
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                if text:
                    all_text_alt += text + "\n"
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
                found_keywords = found_keywords_alt

        lines = [line.strip() for line in all_text.splitlines() if line.strip()]
        extracted_labels = self._extract_color_labels_from_pdf(lines)
        for color, label in extracted_labels.items():
            self._pdf_color_labels[color] = label
        simple_date_pattern = re.compile(
            r"(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)"
        )

        def parse_date(day, month, previous_date):
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
                return min(
                    candidates, key=lambda d: abs((d - datetime.now().date()).days)
                )

            non_past = [d for d in candidates if d >= previous_date - timedelta(days=7)]
            if non_past:
                return min(non_past, key=lambda d: abs((d - previous_date).days))
            return min(candidates, key=lambda d: abs((d - previous_date).days))

        previous_date = None
        for idx, line in enumerate(lines):
            bin_type = self._identify_bins_from_pdf_lines(lines, idx)
            if not bin_type:
                continue

            for date_match in simple_date_pattern.finditer(line):
                day, month = date_match.groups()
                date_obj = parse_date(day, month, previous_date)
                if date_obj is None:
                    continue

                existing = schedule.get(date_obj)
                if existing == "black" and bin_type in {
                    "grey+burgundy",
                    "blue+burgundy",
                }:
                    schedule[date_obj] = bin_type
                elif existing is None:
                    schedule[date_obj] = bin_type

                previous_date = date_obj

        logger.debug(f"Parsed {len(schedule)} dated bin entries from PDF")

        if not schedule:
            # Some council PDFs render bin colors as graphics only; keep using
            # parsed dates and apply a stable 4-week fallback for cycle alignment.
            fallback_dates = []
            for date_match in simple_date_pattern.finditer(all_text):
                day, month = date_match.groups()
                date_obj = parse_date(day, month, None)
                if date_obj and date_obj not in fallback_dates:
                    fallback_dates.append(date_obj)
            fallback_dates.sort()

            for idx, date_obj in enumerate(fallback_dates):
                cycle_pos = idx % 4
                if cycle_pos == 0:
                    schedule[date_obj] = "black"
                elif cycle_pos == 1:
                    schedule[date_obj] = "grey+burgundy"
                elif cycle_pos == 2:
                    schedule[date_obj] = "black"
                else:
                    schedule[date_obj] = "blue+burgundy"

            logger.debug(
                "Used date-only fallback for PDF parsing, generated %d dated entries",
                len(schedule),
            )

        if not schedule:
            logger.error(
                "No dates with bins found in PDF. "
                "This may be due to: 1) PDF is image-based (not text), "
                "2) Date format doesn't match patterns, "
                "3) Bin keywords not found near dates. "
                f"PDF URL: {pdf_url}"
            )

        return schedule

    def _identify_bins_from_pdf_lines(self, lines, current_line_idx):
        """Extract bin types from PDF text around a date."""
        import logging

        logger = logging.getLogger(__name__)

        bins = set()

        # Search the current line AND surrounding lines (before and after)
        search_range = range(
            max(0, current_line_idx - 2), min(current_line_idx + 4, len(lines))
        )

        for i in search_range:
            line_lower = lines[i].lower()
            if "black" in line_lower or "green" in line_lower:
                bins.add("black")
            if "blue" in line_lower:
                bins.add("blue")
            if "grey" in line_lower or "gray" in line_lower:
                bins.add("grey")
            if "burgundy" in line_lower or "brown" in line_lower:
                bins.add("burgundy")

        if bins:
            logger.debug(
                f"Line {current_line_idx}: identified bins {bins} from surrounding text"
            )

        return self._identify_bin_combination(bins) if bins else None

    def _determine_cycle_position(
        self, current_week_date, pdf_schedule, bins_this_week
    ):
        """Determine where in the 4-week cycle we are based on website bins and PDF data."""
        import logging

        logger = logging.getLogger(__name__)

        if not pdf_schedule:
            raise RuntimeError(
                "PDF schedule is empty - could not parse date/bin entries from PDF."
            )

        # Convert website bins to standardized type
        current_week_type = self._identify_bin_combination(bins_this_week)
        logger.debug(f"Current week bin type from website: {current_week_type}")

        # The base pattern is always: Black, Grey+Burgundy, Black, Blue+Burgundy
        # Determine which position in this cycle we're currently at
        position_map = {
            "black": [0, 2],  # Black appears at positions 0 and 2
            "grey+burgundy": [1],  # Grey+Burgundy at position 1
            "blue+burgundy": [3],  # Blue+Burgundy at position 3
        }

        possible_positions = position_map.get(current_week_type, [0])

        # If there are multiple possible positions (e.g., black at 0 or 2),
        # use the PDF to disambiguate by checking the next week
        if len(possible_positions) > 1:
            logger.debug(
                f"Multiple possible positions for {current_week_type}: {possible_positions}, checking PDF for next week..."
            )
            all_dates = list(pdf_schedule.keys())
            # Find the closest date to next week
            next_week_date = current_week_date + timedelta(weeks=1)
            candidates = [d for d in all_dates if abs((d - next_week_date).days) <= 7]
            if candidates:
                closest_next = min(candidates, key=lambda d: abs(d - next_week_date))
                next_week_type = pdf_schedule.get(closest_next, "black")
                logger.debug(f"Next week PDF type: {next_week_type}")

                # Check which position sequence matches
                if current_week_type == "black":
                    if next_week_type == "grey+burgundy":
                        position = 0
                    elif next_week_type == "blue+burgundy":
                        position = 2
                    else:
                        position = possible_positions[0]  # Fallback
                else:
                    position = possible_positions[0]
            else:
                position = possible_positions[0]
        else:
            position = possible_positions[0]

        logger.debug(f"Determined cycle position: {position}")
        return position

    def _get_pattern_from_cycle_position(self, position):
        """Get the 4-week repeating pattern based on position."""
        black_bins = [self._label_for_color("black")]
        blue_burgundy_bins = [
            self._label_for_color("blue"),
            self._label_for_color("burgundy"),
        ]
        grey_burgundy_bins = [
            self._label_for_color("grey"),
            self._label_for_color("burgundy"),
        ]

        base_pattern = [
            black_bins,
            grey_burgundy_bins,
            black_bins,
            blue_burgundy_bins,
        ]

        # Rotate pattern based on position
        return base_pattern[position:] + base_pattern[:position]

    def _identify_bin_combination(self, bins_set):
        """Convert bin set to standardized type string."""
        has_black = any(
            "black" in str(b).lower() or "green" in str(b).lower() for b in bins_set
        )
        has_blue = any("blue" in str(b).lower() for b in bins_set)
        has_grey = any(
            "grey" in str(b).lower() or "gray" in str(b).lower() for b in bins_set
        )
        has_burgundy = any(
            "burgundy" in str(b).lower() or "brown" in str(b).lower() for b in bins_set
        )

        if has_black:
            return "black"
        elif (has_blue or has_grey) and has_burgundy:
            if has_blue:
                return "blue+burgundy"
            else:
                return "grey+burgundy"
        else:
            return "black"

    def _extract_color_labels_from_pdf(self, lines):
        """Extract display labels for each bin color from PDF legend/text."""
        labels = {}
        date_regex = re.compile(
            r"\b\d{1,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December)\b",
            re.IGNORECASE,
        )

        for raw_line in lines:
            line = " ".join(raw_line.split())
            line_lower = line.lower()
            if date_regex.search(line_lower):
                continue
            if len(line) < 4 or len(line) > 140:
                continue

            for color, keywords in COLOR_KEYWORDS.items():
                if not any(keyword in line_lower for keyword in keywords):
                    continue
                if color not in labels or ("-" in line and "-" not in labels[color]):
                    labels[color] = line

        return labels

    def _set_color_labels_from_table_rows(self, rows):
        """Populate color labels from live table headings as fallback and track order."""
        for row_index, row in enumerate(rows):
            th = row.find("th")
            if not th:
                continue
            label = th.get_text(" ", strip=True)
            color = self._infer_color_from_label(label)
            if color:
                if color not in self._pdf_color_labels:
                    self._pdf_color_labels[color] = label
                if color not in self._bin_order_from_table:
                    self._bin_order_from_table.append(color)

    def _label_for_color(self, color):
        """Get the best display label for a canonical color from parsed PDF text."""
        label = self._pdf_color_labels.get(color)
        if label:
            return label

        if color == "black" and self._pdf_color_labels.get("green"):
            return self._pdf_color_labels["green"]

        return color.title()

    def _infer_color_from_label(self, label):
        """Infer canonical color key from a display label."""
        label_lower = str(label).lower()
        for canonical, keywords in COLOR_KEYWORDS.items():
            if any(keyword in label_lower for keyword in keywords):
                return canonical
        return ""

    def _get_icon_for_color(self, color):
        """Get the MDI icon for a color, extracted from PDF when available."""
        # Use default mapping as fallback; icons are determined by the canonical color
        return _DEFAULT_ICON_MAP.get(color, "mdi:trash-can")

    def _get_sort_order_for_color(self, color):
        """Get the sort priority for a color based on canonical ordering.

        Sort order is based on logical bin collection sequence, not the table
        display order. The _bin_order_from_table tracks what bins exist but
        doesn't determine collection priority.
        """
        return _DEFAULT_SORT_ORDER.get(color, 99)
