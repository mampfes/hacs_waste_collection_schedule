"""Lines of Python per layer, counted properly, for one or two git refs.

`wc -l` cannot answer "did the v3 work make the sources smaller", because a
source that shrank from 200 lines of hand-rolled fetching to 40 lines of
declaration plus a 30-line docstring explaining the provider has not grown its
*code*. So every line is classified before it is counted:

* **code**      - anything the interpreter executes. A line with a trailing
                  comment counts as code, since the code is what is there.
* **docstring** - module, class and function docstrings, located with ``ast``
                  rather than guessed at, so a multi-line string used as data
                  is not miscounted as prose.
* **comment**   - a line whose only content is a ``#`` comment.
* **blank**     - whitespace only.

Files are read out of the git object store, so any ref can be measured without
checking it out or touching the working tree.

    python tools/loc_report.py                       # working tree
    python tools/loc_report.py release/3.0.0         # one ref
    python tools/loc_report.py master release/3.0.0  # compare two

With two refs the second is the "after": a negative delta means it shrank.

``--migrated`` narrows the comparison to the sources that are on the pipeline
in the "after" ref and already existed in the "before" ref. The whole-tree
table averages those in with hundreds of untouched legacy sources, which
understates the per-source effect considerably; this isolates it.
"""

from __future__ import annotations

import argparse
import ast
import io
import re
import subprocess
import sys
import token as token_module
import tokenize
from collections import defaultdict
from dataclasses import dataclass, fields
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

PACKAGE = "custom_components/waste_collection_schedule"
LIBRARY = f"{PACKAGE}/waste_collection_schedule"

# First match wins, so the specific paths come before the general ones.
LAYERS: tuple[tuple[str, str], ...] = (
    ("Sources", f"{LIBRARY}/source/"),
    ("Services", f"{LIBRARY}/service/"),
    ("Wizard", f"{LIBRARY}/wizard/"),
    ("Test helpers", f"{LIBRARY}/test/"),
    ("Core library", f"{LIBRARY}/"),
    ("HA integration", f"{PACKAGE}/"),
    ("Tests", "tests/"),
    ("Tools", "tools/"),
)


@dataclass
class Counts:
    code: int = 0
    docstring: int = 0
    comment: int = 0
    blank: int = 0
    files: int = 0

    @property
    def total(self) -> int:
        return self.code + self.docstring + self.comment + self.blank

    def add(self, other: "Counts") -> None:
        for field in fields(self):
            setattr(self, field.name, getattr(self, field.name) + getattr(other, field.name))


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout


def _list_python_files(ref: str | None) -> list[str]:
    if ref is None:
        out = _git("ls-files", "*.py")
    else:
        out = _git("ls-tree", "-r", "--name-only", ref)
    return [line for line in out.splitlines() if line.endswith(".py")]


class BlobReader:
    """Stream file contents out of one ref.

    A ``git show`` per file spawns a process per file, which on this repository
    is a few thousand of them and takes minutes. ``git cat-file --batch`` keeps
    one process open and answers on a pipe instead.
    """

    def __init__(self, ref: "str | None"):
        self.ref = ref
        self.proc = None
        if ref is not None:
            self.proc = subprocess.Popen(
                ["git", "cat-file", "--batch"],
                cwd=REPO_ROOT,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
            )

    def read(self, path: str) -> "str | None":
        if self.proc is None:
            try:
                return (REPO_ROOT / path).read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                return None

        assert self.proc.stdin is not None and self.proc.stdout is not None
        self.proc.stdin.write(f"{self.ref}:{path}\n".encode())
        self.proc.stdin.flush()
        header = self.proc.stdout.readline().decode("utf-8", errors="replace")
        if not header or header.rstrip().endswith(("missing", "ambiguous")):
            return None
        size = int(header.split()[-1])
        body = self.proc.stdout.read(size)
        self.proc.stdout.read(1)  # the trailing newline git adds
        return body.decode("utf-8", errors="replace")

    def close(self) -> None:
        if self.proc is not None and self.proc.stdin is not None:
            self.proc.stdin.close()
            self.proc.wait()


def _docstring_lines(tree: ast.AST) -> set[int]:
    """Every line covered by a module/class/function docstring."""
    lines: set[int] = set()
    holders = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
    for node in ast.walk(tree):
        if not isinstance(node, holders):
            continue
        body = getattr(node, "body", None)
        if not body:
            continue
        first = body[0]
        if not isinstance(first, ast.Expr):
            continue
        value = first.value
        if not (isinstance(value, ast.Constant) and isinstance(value.value, str)):
            continue
        end = value.end_lineno or value.lineno
        lines.update(range(value.lineno, end + 1))
    return lines


def _own_line_comments(source: str) -> set[int]:
    """Lines whose only content is a comment (a trailing one stays code)."""
    lines: set[int] = set()
    try:
        tokens = tokenize.generate_tokens(io.StringIO(source).readline)
        for tok in tokens:
            if tok.type != token_module.COMMENT:
                continue
            if not tok.line[: tok.start[1]].strip():
                lines.add(tok.start[0])
    except (tokenize.TokenError, IndentationError, SyntaxError):
        pass
    return lines


def classify(source: str) -> Counts:
    counts = Counts(files=1)
    try:
        tree = ast.parse(source)
    except SyntaxError:
        # Unparsable on this ref: count it flatly rather than dropping it.
        for line in source.splitlines():
            if line.strip():
                counts.code += 1
            else:
                counts.blank += 1
        return counts

    docstrings = _docstring_lines(tree)
    comments = _own_line_comments(source)

    for number, line in enumerate(source.splitlines(), start=1):
        if not line.strip():
            counts.blank += 1
        elif number in docstrings:
            counts.docstring += 1
        elif number in comments:
            counts.comment += 1
        else:
            counts.code += 1
    return counts


# A pipeline source declares its steps on a BaseSource subclass; a legacy one is
# a plain class with a hand-written fetch(). Read from the text so any ref can be
# measured without importing, but follow the base class rather than matching
# ``class Source(BaseSource)`` literally: a handful of sources subclass *another
# source*, and three of those reach BaseSource that way (offenbach_de via
# insert_it_de, rh_entsorgung_de via jumomind_de, stadt_kerpen_de via abfall_io).
# Matching the literal text counted those as legacy and understated the
# migration. Seven others also subclass another source but inherit from a legacy
# parent, so following the chain keeps excluding them, correctly.
_CLASS_SOURCE_RE = re.compile(r"^class Source\(\s*([A-Za-z_][\w.]*)", re.MULTILINE)


def _source_base(text: str) -> str | None:
    """The base class name of this module's ``Source``, or None if it has none."""
    match = _CLASS_SOURCE_RE.search(text)
    return match.group(1) if match else None


def _base_module(text: str, base: str) -> str | None:
    """The source module a base class name was imported from, if it was.

    Handles both the absolute and the relative import spellings the sources use::

        from waste_collection_schedule.source.jumomind_de import Source as JumomindSource
        from .edpevent_se import Source as EdpEventSource
    """
    pattern = (
        r"from\s+(?:waste_collection_schedule\.source\.|\.)([a-z0-9_]+)\s+import\s+"
        r"(?:\(\s*)?Source\s+as\s+" + re.escape(base)
    )
    match = re.search(pattern, text)
    return match.group(1) if match else None


def is_pipeline_source(text: str, sources: dict[str, str]) -> bool:
    """Does this module's ``Source`` reach ``BaseSource`` through its bases?

    ``sources`` maps module stem to file text, so a base that is another source
    can be followed. A base imported from anywhere else (a ``service`` module,
    say) is not followed: ``RiSKommunalSource`` is a plain class, so a source
    subclassing it is legacy.
    """
    seen: set[str] = set()
    while True:
        base = _source_base(text)
        if base is None:
            return False
        if base == "BaseSource":
            return True
        stem = _base_module(text, base)
        if stem is None or stem in seen or stem not in sources:
            return False
        seen.add(stem)
        text = sources[stem]


def _is_source(path: str) -> bool:
    return path.startswith(f"{LIBRARY}/source/") and not path.endswith("__init__.py")


def report_migrated(before_ref: str, after_ref: str) -> None:
    """Just the sources that reached the pipeline, before against after."""
    before_reader, after_reader = BlobReader(before_ref), BlobReader(after_ref)
    try:
        before_paths = {p for p in _list_python_files(before_ref) if _is_source(p)}
        after_paths = [p for p in _list_python_files(after_ref) if _is_source(p)]

        # Read every source on the "after" ref first: resolving whether a source
        # is on the pipeline may have to follow its base class into another
        # module, so the whole set has to be in hand before deciding any of them.
        after_texts: dict[str, str] = {}
        for path in after_paths:
            text = after_reader.read(path)
            if text is not None:
                after_texts[path] = text
        by_stem = {Path(p).stem: t for p, t in after_texts.items()}

        rows: list[tuple[str, Counts, Counts]] = []
        for path, after_source in after_texts.items():
            if path not in before_paths:
                continue
            if not is_pipeline_source(after_source, by_stem):
                continue
            before_source = before_reader.read(path)
            if before_source is None:
                continue
            rows.append((path, classify(before_source), classify(after_source)))
    finally:
        before_reader.close()
        after_reader.close()

    if not rows:
        print("\nNo migrated sources found on both refs.\n")
        return

    before_total, after_total = Counts(), Counts()
    for _path, b, a in rows:
        before_total.add(b)
        after_total.add(a)

    n = len(rows)
    print(f"\n{before_ref}  ->  {after_ref}   ({n} migrated sources, present on both)\n")
    table = [
        [
            "Migrated sources",
            f"{before_total.code:,} -> {after_total.code:,}",
            _delta(before_total.code, after_total.code),
            f"{before_total.docstring:,} -> {after_total.docstring:,}",
            _delta(before_total.docstring, after_total.docstring),
            f"{before_total.comment:,} -> {after_total.comment:,}",
            _delta(before_total.comment, after_total.comment),
        ],
        [
            "Mean per source",
            f"{before_total.code / n:,.1f} -> {after_total.code / n:,.1f}",
            f"{(after_total.code - before_total.code) / n:+,.1f}",
            f"{before_total.docstring / n:,.1f} -> {after_total.docstring / n:,.1f}",
            f"{(after_total.docstring - before_total.docstring) / n:+,.1f}",
            f"{before_total.comment / n:,.1f} -> {after_total.comment / n:,.1f}",
            f"{(after_total.comment - before_total.comment) / n:+,.1f}",
        ],
    ]
    _print_table(
        table,
        ["", "Code", "Δ code", "Docstr", "Δ docstr", "Comment", "Δ comment"],
    )

    shrank = sum(1 for _p, b, a in rows if a.code < b.code)
    grew = sum(1 for _p, b, a in rows if a.code > b.code)
    print(f"\n  {shrank} shrank, {grew} grew, {n - shrank - grew} unchanged (code lines)")

    rows.sort(key=lambda r: r[2].code - r[1].code)
    print("\n  Biggest reductions:")
    for path, b, a in rows[:5]:
        print(f"    {Path(path).name:<34} {b.code:>5,} -> {a.code:<5,} ({a.code - b.code:+,})")


def _layer_for(path: str) -> str | None:
    for name, prefix in LAYERS:
        if path.startswith(prefix):
            return name
    return None


def measure(ref: str | None) -> dict[str, Counts]:
    totals: dict[str, Counts] = defaultdict(Counts)
    reader = BlobReader(ref)
    try:
        for path in _list_python_files(ref):
            layer = _layer_for(path)
            if layer is None:
                continue
            source = reader.read(path)
            if source is None:
                continue
            totals[layer].add(classify(source))
    finally:
        reader.close()
    return totals


ORDER = [name for name, _ in LAYERS]
COLUMNS = ("files", "code", "docstring", "comment", "blank", "total")


def _row(name: str, counts: Counts) -> list[str]:
    return [name, *(f"{getattr(counts, c) if c != 'total' else counts.total:,}" for c in COLUMNS)]


def _print_table(rows: list[list[str]], header: list[str]) -> None:
    widths = [
        max(len(header[i]), max((len(r[i]) for r in rows), default=0))
        for i in range(len(header))
    ]
    def line(cells: list[str]) -> str:
        return "  ".join(
            cell.ljust(widths[i]) if i == 0 else cell.rjust(widths[i])
            for i, cell in enumerate(cells)
        )
    print(line(header))
    print("  ".join("-" * w for w in widths))
    for row in rows:
        print(line(row))


def report_single(ref: str | None) -> None:
    totals = measure(ref)
    grand = Counts()
    rows = []
    for name in ORDER:
        if name not in totals:
            continue
        rows.append(_row(name, totals[name]))
        grand.add(totals[name])
    rows.append(_row("TOTAL", grand))
    print(f"\n{ref or 'working tree'}\n")
    _print_table(rows, ["Layer", "Files", "Code", "Docstr", "Comment", "Blank", "Total"])


def _delta(before: int, after: int) -> str:
    change = after - before
    if change == 0:
        return "0"
    return f"{change:+,}"


def report_compare(before_ref: str, after_ref: str) -> None:
    before = measure(before_ref)
    after = measure(after_ref)

    print(f"\n{before_ref}  ->  {after_ref}\n")
    header = ["Layer", "Files", "Code", "Δ code", "Docstr", "Δ docstr", "Comment", "Δ comment"]
    rows = []
    grand_before, grand_after = Counts(), Counts()
    for name in ORDER:
        b = before.get(name, Counts())
        a = after.get(name, Counts())
        if b.total == 0 and a.total == 0:
            continue
        grand_before.add(b)
        grand_after.add(a)
        rows.append(
            [
                name,
                f"{b.files:,} -> {a.files:,}",
                f"{b.code:,} -> {a.code:,}",
                _delta(b.code, a.code),
                f"{b.docstring:,} -> {a.docstring:,}",
                _delta(b.docstring, a.docstring),
                f"{b.comment:,} -> {a.comment:,}",
                _delta(b.comment, a.comment),
            ]
        )
    rows.append(
        [
            "TOTAL",
            f"{grand_before.files:,} -> {grand_after.files:,}",
            f"{grand_before.code:,} -> {grand_after.code:,}",
            _delta(grand_before.code, grand_after.code),
            f"{grand_before.docstring:,} -> {grand_after.docstring:,}",
            _delta(grand_before.docstring, grand_after.docstring),
            f"{grand_before.comment:,} -> {grand_after.comment:,}",
            _delta(grand_before.comment, grand_after.comment),
        ]
    )
    _print_table(rows, header)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("refs", nargs="*", help="zero, one or two git refs")
    parser.add_argument(
        "--migrated",
        action="store_true",
        help="only the sources that reached the pipeline (needs two refs)",
    )
    args = parser.parse_args(argv)

    if args.migrated:
        if len(args.refs) != 2:
            parser.error("--migrated needs two refs")
        report_migrated(args.refs[0], args.refs[1])
        print()
        return 0

    if len(args.refs) == 0:
        report_single(None)
    elif len(args.refs) == 1:
        report_single(args.refs[0])
    elif len(args.refs) == 2:
        report_compare(args.refs[0], args.refs[1])
    else:
        parser.error("give at most two refs")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
