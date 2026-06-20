"""Pipeline components for waste calendars published as a single PDF image.

Some providers publish their collection calendar only as a PDF whose page is one
raster image (``pypdf`` text extraction returns nothing). This module reads such
calendars without OCR by detecting the colour-filled day cells of a grid of
monthly mini-calendars.

It is split into two reusable pipeline steps so it composes with the BaseSource
architecture (retrieve -> parse -> transform):

* :class:`PdfImageRetriever` (the ``retrieve`` step) downloads the PDF and
  extracts its embedded image. Pillow and pypdf are imported lazily here, so the
  image-handling dependency is only touched when such a source actually runs.
* :class:`ColourGridCalendarParser` (the ``parse`` step) detects the month grid,
  samples each day cell, and emits ``(date, label)`` records. A source configures
  it with the header-bar colour matcher, the colour-to-label bins, and the page
  layout.

The label each cell maps to is a plain string; the source's transformer
(typically ``ICSTransformer``) maps those labels to canonical ``WasteType`` values,
so the icon and multilingual names come from the shared vocabulary rather than
being declared here.

Grid geometry is detected at runtime from the coloured month-header bands (the
header tops give the vertical row pitch; the coloured runs within each band give
the month-box columns), with an optional width-scaled fallback for providers
whose detection cannot find the expected structure. The parsed result is
validated (minimum count, per-label weekday consistency, per-month plausibility)
so a future layout change fails loudly instead of returning silently-wrong dates.
"""

from __future__ import annotations

import calendar
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date
from io import BytesIO
from statistics import median
from typing import TYPE_CHECKING, Any, Callable, List, NamedTuple, Optional, Tuple

from waste_collection_schedule.exceptions import SourceArgumentException
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc

if TYPE_CHECKING:
    from PIL import Image

    from waste_collection_schedule.base_source import BaseSource

RGBMatcher = Callable[[int, int, int], bool]

DEFAULT_URL_PARAM = "calendar_url"


class ColourBin(NamedTuple):
    """Maps a fill colour to a label string emitted for matching day cells.

    ``label`` is resolved to a canonical ``WasteType`` by the source's
    transformer (e.g. ``ICSTransformer(type_value_map={label: WASTE_TYPE})``).
    """

    label: str
    matches: RGBMatcher


@dataclass(frozen=True)
class CalendarImage:
    """An extracted calendar page image plus the URL it came from.

    The URL travels with the image so the parser can derive the calendar year
    from it without needing to know the source's parameter names.
    """

    image: "Image.Image"
    url: str


def year_from_url(url: str) -> int:
    """Best-effort year for date mapping: a 20xx in the URL, else this year."""
    match = re.search(r"20\d\d", url)
    return int(match.group(0)) if match else date.today().year


class PdfImageRetriever(RetrieverFunc):
    """Download a calendar PDF and extract its embedded page image.

    Reads the PDF URL from ``source.params[url_param]``, fetches it with the
    shared (curl_cffi) session so Cloudflare-protected providers work, and
    returns the largest embedded raster image of the first page as a
    :class:`CalendarImage`. Pillow and pypdf are imported lazily.

    Args:
        url_param: ``source.params`` field holding the calendar PDF URL.
        timeout:   Download timeout in seconds.
    """

    def __init__(self, url_param: str = DEFAULT_URL_PARAM, timeout: int = 60):
        self.url_param = url_param
        self.timeout = timeout

    def __call__(self, source: "BaseSource") -> CalendarImage:
        from pypdf import PdfReader

        url = source.params[self.url_param]
        try:
            resp = source.session.get(url, timeout=self.timeout)
            resp.raise_for_status()
        except Exception as exc:
            raise SourceArgumentException(
                self.url_param, f"could not download the calendar PDF: {exc}"
            ) from exc

        try:
            reader = PdfReader(BytesIO(resp.content))
            images = reader.pages[0].images
            if not images:
                raise SourceArgumentException(
                    self.url_param, "the PDF page contains no embedded image"
                )

            # The page may carry small logos alongside the calendar; the
            # calendar is the largest image by pixel area.
            def _area(embedded: Any) -> int:
                pic = embedded.image
                return 0 if pic is None else pic.width * pic.height

            pil_image = max(images, key=_area).image
            if pil_image is None:
                raise SourceArgumentException(
                    self.url_param, "the PDF page image could not be decoded"
                )
            image = pil_image.convert("RGB")
        except SourceArgumentException:
            raise
        except Exception as exc:
            raise SourceArgumentException(
                self.url_param, f"could not read the calendar PDF: {exc}"
            ) from exc

        return CalendarImage(image=image, url=url)


class ColourGridCalendarParser(Parser["List[Tuple[date, str]]"]):
    """Detect a grid of monthly mini-calendars and read colour-filled day cells.

    Consumes the :class:`CalendarImage` from :class:`PdfImageRetriever` and emits
    ``(date, label)`` records for each coloured day cell, for use with an
    ``ICSTransformer`` that maps each label to a canonical ``WasteType``.

    The vertical geometry (first-row offset, row pitch) is expressed as a ratio
    of the measured header-to-header pitch, so it tracks the page scale rather
    than assuming fixed pixel spacing. Horizontal month-box positions are
    detected per header band; ``fallback_box_x``/``fallback_box_w`` supply a
    width-scaled fallback only when detection fails (leave ``fallback_box_x``
    ``None`` to require clean detection).

    Args:
        header_matches: RGB matcher for the coloured month-header bands.
        bins:           Colour-to-label bins, tried in order per cell.
        url_param:      Field name used in error messages (and to read the URL
                        if the retrieved image lacks one).
        crop:           Optional ``(left, top, right, bottom)`` as fractions of
                        the image (0..1). Restricts detection to the month grid
                        for pages that wrap it in banners, legends or text
                        panels. ``None`` uses the whole image.
        box_cols:       Month boxes per row (3 for a 3x4 grid, 4 for 4x3).
        grid_cols/grid_rows: Day-cell grid within each month box (7x6).
        ref_width:      Reference image width the pixel constants were tuned at.
        fallback_box_x/fallback_box_w: Optional calibrated horizontal fallback.
        row1_ratio:     First day-row offset as a fraction of the box pitch.
        row_pitch_ratio: Day-row pitch as a fraction of the box pitch.
        sample_half_x/sample_half_y: Half-size of the cell colour sample window.
        fill_threshold: Minimum matching pixels for a cell to count as filled.
        min_collections/min_weekday_share/max_per_month: Validation thresholds.
    """

    def __init__(
        self,
        *,
        header_matches: RGBMatcher,
        bins: List[ColourBin],
        url_param: str = DEFAULT_URL_PARAM,
        crop: Optional[Tuple[float, float, float, float]] = None,
        box_cols: int = 3,
        grid_cols: int = 7,
        grid_rows: int = 6,
        ref_width: int = 1240,
        fallback_box_x: Optional[Tuple[int, ...]] = None,
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
        self._url_param = url_param
        self._crop = crop
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

    # -- geometry detection -------------------------------------------------

    def _header_bands(self, img: "Image.Image") -> List[Tuple[int, int]]:
        """Locate the coloured month-header bands (one per box-row)."""
        width, height = img.size
        px: Any = img.load()
        rows = [
            sum(1 for x in range(0, width, 2) if self._header_matches(*px[x, y]))
            for y in range(height)
        ]

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
                self._url_param,
                f"expected {box_rows} month-header rows in the calendar image, "
                f"found {len(bands)}",
            )
        return bands

    def _box_columns(
        self, img: "Image.Image", top: int, bot: int
    ) -> Optional[List[Tuple[int, int]]]:
        """Detect each month-box's (left, width) from a header band.

        A box header is split by its white month name, so a box shows up as two
        or more coloured runs. Runs are grouped into ``box_cols`` boxes by
        cutting at the inter-run gaps nearest the evenly-spaced column
        boundaries. Returns None if the expected structure is not found.
        """
        width, _ = img.size
        px: Any = img.load()
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
                self._url_param,
                f"only {len(raw)} collection(s) detected; the calendar layout "
                "may have changed",
            )

        by_label: dict[str, List[date]] = defaultdict(list)
        for collection_date, label in raw:
            by_label[label].append(collection_date)

        for label, dates in by_label.items():
            weekdays = Counter(d.weekday() for d in dates)
            _, modal = weekdays.most_common(1)[0]
            if modal / len(dates) < self._min_weekday_share:
                raise SourceArgumentException(
                    self._url_param,
                    f"detected '{label}' collections fall on inconsistent "
                    "weekdays; the calendar may not have been read correctly",
                )

        per_month = Counter((d.year, d.month, t) for d, t in raw)
        if max(per_month.values()) > self._max_per_month:
            raise SourceArgumentException(
                self._url_param,
                "implausible number of collections detected in a single month; "
                "the calendar image may have been misread",
            )

    # -- parse --------------------------------------------------------------

    def __call__(
        self, retrieved: CalendarImage, source: "BaseSource | None" = None
    ) -> List[Tuple[date, str]]:
        img = retrieved.image
        if self._crop is not None:
            full_w, full_h = img.size
            left, top, right, bottom = self._crop
            img = img.crop(
                (
                    int(left * full_w),
                    int(top * full_h),
                    int(right * full_w),
                    int(bottom * full_h),
                )
            )
        width, height = img.size
        px: Any = img.load()
        scale = width / self._ref_width
        year = year_from_url(retrieved.url)

        bands = self._header_bands(img)
        header_tops = [b[0] for b in bands]

        # Vertical row geometry from the measured header-to-header pitch, so it
        # tracks the page layout rather than assuming a fixed pixel spacing.
        box_pitch = median(
            header_tops[i + 1] - header_tops[i] for i in range(len(header_tops) - 1)
        )
        row1_offset = self._row1_ratio * box_pitch
        row_pitch = self._row_pitch_ratio * box_pitch

        # Horizontal box geometry, detected per box-row, with an optional
        # width-scaled calibrated fallback.
        fallback_boxes = (
            [
                (int(x * scale), int(self._fallback_box_w * scale))
                for x in self._fallback_box_x
            ]
            if self._fallback_box_x is not None
            else None
        )
        columns = []
        for top, bot in bands:
            detected = self._box_columns(img, top, bot)
            if detected is None:
                if fallback_boxes is None:
                    raise SourceArgumentException(
                        self._url_param,
                        "could not detect the month-box columns in the calendar "
                        "image; the layout may have changed",
                    )
                detected = fallback_boxes
            columns.append(detected)

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
                    raw.append((date(year, month, day), colour_bin.label))

        if not raw:
            raise SourceArgumentException(
                self._url_param,
                "no collection days could be detected in the calendar image",
            )

        self._validate(raw)
        return raw
