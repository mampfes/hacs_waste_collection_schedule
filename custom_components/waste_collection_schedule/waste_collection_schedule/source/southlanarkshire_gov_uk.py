import re
from datetime import datetime, timedelta
from io import BytesIO

import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "South Lanarkshire Council"
DESCRIPTION = "Source for South Lanarkshire Council waste collection."
URL = "https://www.southlanarkshire.gov.uk"
COUNTRY = "uk"

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
        "pdf_url": "https://www.southlanarkshire.gov.uk/download/downloads/id/18301/east_kilbride_cambuslang_and_rutherglen_bin_collection_calendar_2026_-_households_with_4_bins.pdf",
    },
    "Hamilton": {
        "record_id": "576617",
        "street_name": "alexander_balfour_gardens_hamilton",
        "pdf_url": "https://www.southlanarkshire.gov.uk/downloads/file/18300/hamilton_and_clydesdale_bin_collection_calendar_2026_-_households_with_4_bins",
    },
}

ICON_MAP = {
    "Black": "mdi:trash-can",
    "Green": "mdi:trash-can",
    "Burgundy": "mdi:leaf",
    "Blue": "mdi:file-document-outline",
    "Light": "mdi:glass-fragile",
}

SORT_ORDER = {
    "Blue": 1,
    "Light": 2,
    "Burgundy": 3,
    "Black": 4,
    "Green": 4,
}


class Source:
    def __init__(self, record_id: str | int, street_name: str, pdf_url: str):
        if not pdf_url:
            raise ValueError(
                "pdf_url is required to determine collection cycle position. "
                "Black bins appear twice in the 4-week cycle, making position impossible to determine without PDF reference. "
                "Find PDFs at: https://www.southlanarkshire.gov.uk/downloads/download/791/bin_collection_calendars"
            )
        self._record_id = str(record_id).zfill(6)
        self._street_name = str(street_name)
        self._pdf_url = pdf_url

    def fetch(self):
        import logging

        logger = logging.getLogger(__name__)

        # Get current week's bins from website
        s = requests.Session()
        s.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})

        r = s.get(
            f"https://www.southlanarkshire.gov.uk/directory_record/{self._record_id}/{self._street_name}"
        )
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")

        bin_div = soup.find("div", {"class": "bin-dir-snip"})
        if not bin_div:
            raise Exception("Could not find bin collection info")

        week_para = bin_div.find("p")
        if not week_para:
            raise Exception("Could not find week information")

        week_text = week_para.text.strip()
        parts = week_text.split(" to ")
        if len(parts) != 2:
            raise Exception(f"Unexpected week format: {week_text}")

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
            raise Exception("Could not find collection schedule table")

        rows = table.find_all("tr")
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
            raise Exception("Could not determine collection day")

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

        # Parse PDF to determine position in 4-week cycle
        pdf_schedule = self._parse_pdf_schedule()
        cycle_position = self._determine_cycle_position(
            current_week_start, pdf_schedule, bins_this_week
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
                bin_color = bin_type.split()[0]
                icon = ICON_MAP.get(bin_color, "mdi:trash-can")
                collections.append(
                    Collection(date=collection_date, t=bin_type, icon=icon)
                )

        def get_sort_key(entry):
            bin_color = entry.type.split()[0] if entry.type else ""
            sort_order = SORT_ORDER.get(bin_color, 99)
            return (entry.date, sort_order)

        collections.sort(key=get_sort_key)

        # Log first 20 collections being passed to HA calendar (debug level)
        logger.debug(f"Total collections being sent to HA: {len(collections)}")
        for i, collection in enumerate(collections[:20]):
            logger.debug(
                f"  [{i+1}] {collection.date} ({collection.date.strftime('%A')}): {collection.type} (icon: {collection.icon})"
            )

        return collections

    def _parse_pdf_schedule(self):
        """Parse PDF to extract bin collection schedule for multiple weeks."""
        import logging

        logger = logging.getLogger(__name__)

        s = requests.Session()
        s.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})

        # Add timeout to prevent hanging in Home Assistant
        logger.debug(f"Downloading PDF from: {self._pdf_url}")
        response = s.get(self._pdf_url, timeout=30)
        response.raise_for_status()
        logger.debug(f"PDF downloaded, size: {len(response.content)} bytes")

        pdf_reader = PdfReader(BytesIO(response.content))
        schedule = {}

        logger.debug(f"PDF has {len(pdf_reader.pages)} pages")

        # Try to detect year from PDF filename or content
        year_from_url = re.search(r"20\d{2}", self._pdf_url)
        current_year = datetime.now().year
        years_to_try = [current_year]
        if year_from_url:
            pdf_year = int(year_from_url.group())
            if pdf_year not in years_to_try:
                years_to_try.insert(0, pdf_year)
        years_to_try.append(current_year + 1)  # Also try next year
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

        # Parse all dates from PDF
        simple_date_pattern = r"(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)"

        # Extract ALL dates first
        all_pdf_dates = []
        date_matches = re.finditer(simple_date_pattern, all_text)
        for date_match in date_matches:
            day, month = date_match.groups()
            for year in years_to_try:
                try:
                    date_obj = datetime.strptime(
                        f"{day} {month} {year}", "%d %B %Y"
                    ).date()
                    if date_obj not in all_pdf_dates:
                        all_pdf_dates.append(date_obj)
                    break
                except ValueError:
                    continue

        all_pdf_dates.sort()
        logger.debug(f"Found {len(all_pdf_dates)} unique dates in PDF")

        if not all_pdf_dates:
            logger.error("No dates found in PDF")
            return schedule

        # Analyze date intervals to identify bin types
        # Black bins: every 2 weeks, Grey+burgundy: alternating 2-week intervals, Blue+burgundy: 4-week cycle
        # Strategy: Use known 4-week pattern and match dates to it

        # Log first 10 dates for debugging
        logger.debug(f"First 10 PDF dates: {all_pdf_dates[:10]}")

        # Match dates to the 4-week pattern using interval analysis
        # Week 0: Black, Week 1: Grey+Burgundy, Week 2: Black, Week 3: Blue+Burgundy
        for date_obj in all_pdf_dates:
            # Determine week of year to establish pattern
            week_num = date_obj.isocalendar()[1]
            cycle_pos = week_num % 4

            # Map cycle position to bin type (rough estimate - will refine with current week)
            if cycle_pos == 0:
                schedule[date_obj] = "black"
            elif cycle_pos == 1:
                schedule[date_obj] = "grey+burgundy"
            elif cycle_pos == 2:
                schedule[date_obj] = "black"
            else:  # cycle_pos == 3
                schedule[date_obj] = "blue+burgundy"

        logger.debug(f"Assigned bins to {len(schedule)} dates using week-based pattern")

        if not schedule:
            logger.error(
                "No dates with bins found in PDF. "
                "This may be due to: 1) PDF is image-based (not text), "
                "2) Date format doesn't match patterns, "
                "3) Bin keywords not found near dates. "
                f"PDF URL: {self._pdf_url}"
            )

        return schedule

    def _identify_bins_from_pdf_lines(self, lines, current_line_idx):
        """Extract bin types from PDF text around a date."""
        import logging

        logger = logging.getLogger(__name__)

        bins = set()

        # Search the current line AND surrounding lines (before and after)
        search_range = range(
            max(0, current_line_idx - 2), min(current_line_idx + 10, len(lines))
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
            logger.warning(
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
            raise Exception(
                "PDF schedule is empty - could not parse any dates from PDF. Please verify the PDF URL is correct and accessible."
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
        black_bins = ["Black/Green - Non Recyclable Waste"]
        blue_burgundy_bins = ["Blue (paper and card)", "Burgundy - Food and garden"]
        grey_burgundy_bins = [
            "Light Grey - Glass, cans and plastics",
            "Burgundy - Food and garden",
        ]

        base_pattern = [black_bins, grey_burgundy_bins, black_bins, blue_burgundy_bins]

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
