"""Character-positioned words, lines and filled vectors for PDF calendars.

Use when text matrices lose positions or line extraction merges adjacent grid
cells. This layer contains no calendar, locality or recurrence rules.
"""

from io import BytesIO
from typing import NamedTuple

from pdfminer.high_level import extract_pages
from pdfminer.layout import LAParams, LTChar, LTContainer, LTCurve, LTTextLineHorizontal

from waste_collection_schedule import response_shape
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.parsers import Parser, PdfTextFragment, PdfVector


class PdfWordLayout(NamedTuple):
    lines: list[PdfTextFragment]
    words: list[PdfTextFragment]
    vectors: list[PdfVector]


def _colour(value) -> tuple[float, ...] | None:
    if isinstance(value, (float, int)):
        return (float(value),) * 3
    return tuple(value) if isinstance(value, (tuple, list)) else None


def _parse_pdf(response, source: BaseSource | None = None) -> PdfWordLayout:
    """Retain individual word centres even when lines span several grid cells."""
    lines, words, vectors = [], [], []

    def visit(item, page):
        if isinstance(item, LTTextLineHorizontal):
            lines.append(
                PdfTextFragment(
                    page,
                    " ".join(item.get_text().split()),
                    (item.x0 + item.x1) / 2,
                    (item.y0 + item.y1) / 2,
                )
            )
            chars = []

            def flush():
                if chars:
                    words.append(
                        PdfTextFragment(
                            page,
                            "".join(c.get_text() for c in chars),
                            (chars[0].x0 + chars[-1].x1) / 2,
                            (chars[0].y0 + chars[0].y1) / 2,
                        )
                    )
                    chars.clear()

            for char in item:
                if isinstance(char, LTChar) and not char.get_text().isspace():
                    chars.append(char)
                else:
                    flush()
            flush()
        elif isinstance(item, LTContainer):
            for child in item:
                visit(child, page)
        elif isinstance(item, LTCurve) and item.fill:
            vectors.append(
                PdfVector(
                    page,
                    item.x0,
                    item.y0,
                    item.x1,
                    item.y1,
                    _colour(item.stroking_color),
                    _colour(item.non_stroking_color),
                )
            )

    for page, layout in enumerate(
        extract_pages(BytesIO(response.content), laparams=LAParams())
    ):
        visit(layout, page)
    return PdfWordLayout(lines, words, vectors)


class PdfWordLayoutParser(Parser[list[PdfWordLayout]]):
    """Return one document with word/line centres and filled vector geometry.

    Coordinates use the PDF origin at bottom left and zero-based page numbers.
    Scalar greyscale fills are normalised to RGB triples for comparison with RGB
    legends. An optional minimum word/vector count detects empty or changed
    documents. The one-item list composes with ``parsers.EachResponse``.
    """

    def __init__(self, *, min_words: int = 1, min_vectors: int = 0):
        self.min_words = min_words
        self.min_vectors = min_vectors

    def __call__(
        self, response, source: BaseSource | None = None
    ) -> list[PdfWordLayout]:
        layout = _parse_pdf(response, source)
        response_shape.expect(
            len(layout.words) >= self.min_words
            and len(layout.vectors) >= self.min_vectors,
            source_name=response_shape.source_name(source),
            detail="PDF has too few positioned words or filled vectors (image-only or changed layout?)",
            raw=str(layout.lines[:10]),
        )
        return [layout]
