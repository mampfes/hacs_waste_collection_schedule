"""Recognise outlined numerals by path topology and scale-independent moments.

Some PDF exports convert their calendar's numerals to paths, so there are no
characters for a text extractor to return. These are still vector data: the
path commands and geometric moments identify a glyph independently of position
and scale. Unknown shapes fail rather than guessing a date. This is template
matching for a known printed font, without rendering, OCR or a font dependency.
"""

from collections.abc import Mapping, Sequence
from statistics import mean, pstdev

Glyph = tuple[str, tuple[float, ...]]

# Tahoma Bold numerals as outlined in the council's public calendar. Only
# topology and five aggregate measurements are stored, not font outlines.
TAHOMA_BOLD: dict[str, Glyph] = {
    "0": ("mcccccccccccccccc", (0.74068, 0.52997, 0.49986, 0.37906, 0.35303)),
    "1": ("mllllllcccclll", (0.65912, 0.36329, 0.54682, 0.33996, 0.38577)),
    "2": ("mllccccccccccllccccccccl", (0.72069, 0.4316, 0.56333, 0.32261, 0.30821)),
    "3": (
        "mccccccllcccccccccclllccccccccccccllcccccccclcccc",
        (0.71246, 0.51708, 0.51877, 0.29544, 0.28478),
    ),
    "4": ("mllllllllll", (0.81513, 0.63127, 0.38099, 0.33879, 0.32273)),
    "5": (
        "mccccccllccccccccccccccllllllcccccc",
        (0.71774, 0.48729, 0.40198, 0.32045, 0.25843),
    ),
    "6": ("mccccccccccccllcccccccccc", (0.73514, 0.57606, 0.58836, 0.32078, 0.30654)),
    "7": ("mllllll", (0.73539, 0.44436, 0.63197, 0.41699, 0.40754)),
    "8": ("mcccccccccclcccccccccccclcc", (0.75657, 0.5169, 0.50468, 0.37058, 0.32755)),
    "9": (
        "mccccccllcccccccccccccccccccc",
        (0.73515, 0.44729, 0.42891, 0.31785, 0.31222),
    ),
}


def signature(shape) -> Glyph:
    path = [part for part in shape.original_path if part[0] != "h"]
    xs = [(part[-1][0] - shape.x0) / shape.width for part in path]
    ys = [(part[-1][1] - shape.y0) / shape.height for part in path]
    return (
        "".join(part[0] for part in path),
        (shape.width / shape.height, mean(xs), mean(ys), pstdev(xs), pstdev(ys)),
    )


class VectorDigits:
    """Decode a row of outlined digits, rejecting unknown or overlapping glyphs."""

    def __init__(self, templates: Mapping[str, Glyph], *, tolerance: float = 0.003):
        self.templates = dict(templates)
        self.tolerance = tolerance

    def read(self, shapes: Sequence) -> int:
        digits = []
        last_x = None
        for shape in sorted(shapes, key=lambda s: s.x0):
            topology, moments = signature(shape)
            matches = [
                digit
                for digit, (
                    expected_topology,
                    expected_moments,
                ) in self.templates.items()
                if topology == expected_topology
                and all(
                    abs(actual - expected) <= self.tolerance
                    for actual, expected in zip(moments, expected_moments, strict=True)
                )
            ]
            if len(matches) != 1 or (last_x is not None and shape.x0 < last_x - 0.1):
                raise ValueError("Unknown or overlapping outlined calendar numeral")
            last_x = shape.x1
            digits.append(matches[0])
        if not 1 <= len(digits) <= 2:
            raise ValueError("A calendar cell must contain one or two outlined digits")
        return int("".join(digits))
