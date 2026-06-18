"""Parse a yearly waste calendar published as a single embedded PDF image.

Some providers publish their collection calendar only as a PDF whose page is one
raster image (``pypdf`` text extraction returns nothing). This service reads such
calendars without OCR by detecting the colour-filled day cells of a grid of
monthly mini-calendars.

It is provider-agnostic: a source configures it with the header-bar colour, the
set of colour-to-waste-type bins, and the page layout, then calls ``fetch(url)``.
Grid geometry is detected at runtime from the coloured month-header bands (the
four header tops give the vertical row pitch; the teal runs within each band give
the month-box columns), with calibrated fallbacks for when detection cannot find
the expected structure. The parsed result is validated (minimum count, per-type
weekday consistency, per-month plausibility) so a future layout change fails
loudly instead of returning a handful of silently-wrong dates.
"""

import calendar
import re
from collections import Counter, defaultdict
from datetime import date
from io import BytesIO
from statistics import median
from typing import Callable, Dict, List, NamedTuple, Optional, Tuple

import requests
from PIL import Image
from pypdf import PdfReader

from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentException

RGBMatcher = Callable[[int, int, int], bool]


class ColourBin(NamedTuple):
    """Maps a fill colour to a waste type (and optional icon)."""

    name: str
    icon: Optional[str]
    matches: RGBMatcher


class PdfImageCalendar:
    def __init__(
        self,
        *,
        header_matches: RGBMatcher,
        bins: List[ColourBin],
        box_cols: int = 3,
        grid_cols: int = 7,
        grid_rows: int = 6,
        ref_width: int = 1240,
        fallback_box_x: Tuple[int, ...] = (73, 449, 824),
        fallback_box_w: int = 353,
        row1_ratio: float = 71.0 / 267.0,
        row_pitch_ratio: float = 29.4 / 267.0,
        sample_half_x: int = 11,
        sample_half_y: int = 13,
        fill_threshold: int = 50,
        min_collections: int = 12,
        min_weekday_share: float = 0.5,
        max_per_month: int = 6,
    ):
        self._header_matches = header_matches
        self._bins = bins
        self._box_cols = box_cols
        self._grid_cols = grid_cols
        self._grid_rows = grid_rows
        self._ref_width = ref_width
        self._fallback_box_x = fallback_box_x
        self._fallback_box_w = fallback_box_w
        self._row1_ratio = row1_ratio
        self._row_pitch_ratio = row_pitch_ratio
        self._sample_half_x = sample_half_x
        self._sample_half_y = sample_half_y
        self._fill_threshold = fill_threshold
        self._min_collections = min_collections
        self._min_weekday_share = min_weekday_share
        self._max_per_month = max_per_month

    # -- image / metadata ---------------------------------------------------

    def _extract_image(self, url: str) -> Image.Image:
        try:
            resp = requests.get(url, timeout=60)
            resp.raise_for_status()
        except requests.RequestException as exc:
            raise SourceArgumentException(
                "calendar_url", f"could not download the calendar PDF: {exc}"
            ) from exc

        try:
            reader = PdfReader(BytesIO(resp.content))
            page = reader.pages[0]
            images = page.images
            if not images:
                raise SourceArgumentException(
                    "calendar_url", "the PDF page contains no embedded image"
                )
            img = images[0].image
        except SourceArgumentException:
            raise
        except Exception as exc:
            raise SourceArgumentException(
                "calendar_url", f"could not read the calendar PDF: {exc}"
            ) from exc

        return img.convert("RGB")

    @staticmethod
    def year_from_url(url: str) -> int:
        """Best-effort year for date mapping: a 20xx in the URL, else today."""
        match = re.search(r"20\d\d", url)
        return int(match.group(0)) if match else date.today().year

    # -- geometry detection -------------------------------------------------

    def _header_bands(self, img: Image.Image) -> List[Tuple[int, int]]:
        """Locate the coloured month-header bands (one per box-row)."""
        width, height = img.size
        px = img.load()
        rows = []
        for y in range(height):
            rows.append(
                sum(1 for x in range(0, width, 2) if self._header_matches(*px[x, y]))
            )

        threshold = max(rows) * 0.4
        bands: List[Tuple[int, int]] = []
        start = None
        for y, count in enumerate(rows):
            if count > threshold and start is None:
                start = y
            elif count <= threshold and start is not None:
                if y - start >= 15:  # full header bars are ~28px tall
                    bands.append((start, y))
                start = None
        if start is not None and height - start >= 15:
            bands.append((start, height))

        box_rows = -(-12 // self._box_cols)  # ceil(12 / box_cols)
        if len(bands) != box_rows:
            raise SourceArgumentException(
                "calendar_url",
                f"expected {box_rows} month-header rows in the calendar image, "
                f"found {len(bands)}",
            )
        return bands

    def _box_columns(
        self, img: Image.Image, top: int, bot: int
    ) -> Optional[List[Tuple[int, int]]]:
        """Detect each month-box's (left, width) from a header band.

        A box header is split by its white month name, so a box shows up as two
        or more coloured runs. Runs are grouped into ``box_cols`` boxes by
        cutting at the inter-run gaps nearest the evenly-spaced column
        boundaries. Returns None if the expected structure is not found.
        """
        width, _ = img.size
        px = img.load()
        band_h = bot - top
        threshold = band_h * 0.3
        runs: List[Tuple[int, int]] = []
        start = None
        for x in range(width):
            count = sum(1 for y in range(top, bot) if self._header_matches(*px[x, y]))
            if count > threshold and start is None:
                start = x
            elif count <= threshold and start is not None:
                if x - start >= 25:
                    runs.append((start, x))
                start = None
        if start is not None and width - start >= 25:
            runs.append((start, width))

        if len(runs) < self._box_cols:
            return None

        left, right = runs[0][0], runs[-1][1]
        gap_mids = [(runs[i][1] + runs[i + 1][0]) / 2 for i in range(len(runs) - 1)]
        cuts = set()
        for k in range(1, self._box_cols):
            boundary = left + (right - left) * k / self._box_cols
            cuts.add(
                min(range(len(gap_mids)), key=lambda i: abs(gap_mids[i] - boundary))
            )
        if len(cuts) != self._box_cols - 1:
            return None  # two boundaries collapsed onto one gap -> ambiguous

        boxes: List[Tuple[int, int]] = []
        prev = 0
        for cut in sorted(cuts) + [len(runs) - 1]:
            group = runs[prev : cut + 1]
            box_left = group[0][0]
            boxes.append((box_left, group[-1][1] - box_left))
            prev = cut + 1
        return boxes if len(boxes) == self._box_cols else None

    # -- validation ---------------------------------------------------------

    def _validate(self, raw: List[Tuple[date, str]]) -> None:
        """Guard against a misread layout producing plausible-but-wrong dates."""
        if len(raw) < self._min_collections:
            raise SourceArgumentException(
                "calendar_url",
                f"only {len(raw)} collection(s) detected; the calendar layout "
                "may have changed",
            )

        by_type: Dict[str, List[date]] = defaultdict(list)
        for collection_date, waste_type in raw:
            by_type[waste_type].append(collection_date)

        for waste_type, dates in by_type.items():
            weekdays = Counter(d.weekday() for d in dates)
            _, modal = weekdays.most_common(1)[0]
            if modal / len(dates) < self._min_weekday_share:
                raise SourceArgumentException(
                    "calendar_url",
                    f"detected '{waste_type}' collections fall on inconsistent "
                    "weekdays; the calendar may not have been read correctly",
                )

        per_month = Counter((d.year, d.month, t) for d, t in raw)
        if max(per_month.values()) > self._max_per_month:
            raise SourceArgumentException(
                "calendar_url",
                "implausible number of collections detected in a single month; "
                "the calendar image may have been misread",
            )

    # -- public API ---------------------------------------------------------

    def fetch(self, url: str, year: Optional[int] = None) -> List[Collection]:
        img = self._extract_image(url)
        width, height = img.size
        px = img.load()
        scale = width / self._ref_width
        if year is None:
            year = self.year_from_url(url)

        bands = self._header_bands(img)
        header_tops = [b[0] for b in bands]

        # Vertical row geometry from the measured header-to-header pitch, so it
        # tracks the page layout rather than assuming a fixed pixel spacing.
        box_pitch = median(
            header_tops[i + 1] - header_tops[i] for i in range(len(header_tops) - 1)
        )
        row1_offset = self._row1_ratio * box_pitch
        row_pitch = self._row_pitch_ratio * box_pitch

        # Horizontal box geometry, detected per box-row, with a width-scaled
        # calibrated fallback.
        fallback_boxes = [
            (int(x * scale), int(self._fallback_box_w * scale))
            for x in self._fallback_box_x
        ]
        columns = [
            self._box_columns(img, top, bot) or fallback_boxes for top, bot in bands
        ]

        half_x = max(4, int(self._sample_half_x * scale))
        half_y = max(5, int(self._sample_half_y * scale))
        fill_threshold = max(40, int(self._fill_threshold * scale * scale))

        def cell_bin(cx: int, cy: int) -> Optional[ColourBin]:
            counts = [0] * len(self._bins)
            for x in range(cx - half_x, cx + half_x + 1):
                if x < 0 or x >= width:
                    continue
                for y in range(cy - half_y, cy + half_y + 1):
                    if y < 0 or y >= height:
                        continue
                    rgb = px[x, y]
                    for i, colour_bin in enumerate(self._bins):
                        if colour_bin.matches(*rgb):
                            counts[i] += 1
                            break
            best = max(range(len(counts)), key=lambda i: counts[i])
            if counts[best] > fill_threshold:
                return self._bins[best]
            return None

        raw: List[Tuple[date, str]] = []
        bin_by_name = {b.name: b for b in self._bins}
        for month in range(1, 13):
            box_row = (month - 1) // self._box_cols
            box_col = (month - 1) % self._box_cols
            htop = header_tops[box_row]
            box_left, box_w = columns[box_row][box_col]
            first_weekday, days_in_month = calendar.monthrange(year, month)

            for week in range(self._grid_rows):
                cy = int(htop + row1_offset + week * row_pitch)
                for col in range(self._grid_cols):
                    cx = int(box_left + (col + 0.5) * box_w / self._grid_cols)
                    colour_bin = cell_bin(cx, cy)
                    if colour_bin is None:
                        continue
                    day = week * self._grid_cols + col - first_weekday + 1
                    if not 1 <= day <= days_in_month:
                        # Geometry sanity guard: skip impossible mappings.
                        continue
                    raw.append((date(year, month, day), colour_bin.name))

        if not raw:
            raise SourceArgumentException(
                "calendar_url",
                "no collection days could be detected in the calendar image",
            )

        self._validate(raw)

        return [
            Collection(date=d, t=name, icon=bin_by_name[name].icon) for d, name in raw
        ]
