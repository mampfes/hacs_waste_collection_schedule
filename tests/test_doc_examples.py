"""The worked examples in the documentation are code, so check them like code.

A doc example has twice been the thing that taught a mistake. The `__init__`
skeleton in `new_source_template.py` was the reason 97 sources carried a
redundant constructor, and `alternatives([uprn()], [postcode(), text_field("house")])`
appeared in both the guide and the agent while `house_number()` existed. In each
case a gate was added for real sources and the example that had caused it went on
sitting there, still wrong, until someone happened to read it.

So the same predicates the source gates use run over the examples too, imported
from test_new_architecture rather than reimplemented, because a second copy of a
rule is the problem this file exists to catch.

Only the checks that read text apply. Anything needing the imported class (the
redundant-`__init__` gate, which compares a signature against PARAMS) cannot run
on a snippet, and a snippet is not expected to be importable.
"""

import ast
import calendar  # noqa: F401 - stdlib calendar must be imported FIRST
import os
import pathlib
import re
import sys

import pytest

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__),
        "../custom_components/waste_collection_schedule",
    ),
)

from test_new_architecture import (
    declares_extra_info,
    declares_legacy_translations,
    hand_rolled_registry,
    hand_rolled_standard_fields,
    named_waste_type_imports,
    source_local_retrieval_functions,
    source_local_step_classes,
)

REPO = pathlib.Path(__file__).resolve().parent.parent

# Every file whose fenced python is contributor-facing guidance.
DOCUMENTS = [
    REPO / "doc" / "contributing_source.md",
    REPO / ".claude" / "agents" / "source-implementer.md",
]

# The annotated skeleton is a real .py file, so ruff and pyright already cover its
# syntax; it is included here for the *rule* checks, which they do not do.
TEMPLATES = [REPO / "doc" / "new_source_template.py"]

_FENCE = re.compile(r"```python\n(.*?)```", re.S)


def _blocks():
    """(label, code) for every fenced python block, plus the templates."""
    out = []
    for path in DOCUMENTS:
        text = path.read_text(encoding="utf-8")
        for i, code in enumerate(_FENCE.findall(text)):
            out.append((f"{path.relative_to(REPO)}[{i}]", code))
    for path in TEMPLATES:
        out.append((str(path.relative_to(REPO)), path.read_text(encoding="utf-8")))
    return out


_BLOCKS = _blocks()
# A block declaring a Source class is a whole worked example and gets every check.
_EXAMPLES = [(label, code) for label, code in _BLOCKS if "class Source" in code]


def test_documents_contain_examples():
    """Guard against the fence regex silently matching nothing."""
    assert len(_BLOCKS) >= 10, f"only found {len(_BLOCKS)} python blocks"
    assert len(_EXAMPLES) >= 3, f"only found {len(_EXAMPLES)} full examples"


@pytest.mark.parametrize("label,code", _BLOCKS, ids=[b[0] for b in _BLOCKS])
def test_every_block_parses(label, code):
    """A snippet that does not parse cannot be copied and run."""
    try:
        ast.parse(code)
    except SyntaxError as e:
        pytest.fail(f"{label} does not parse: {e}")


@pytest.mark.parametrize("label,code", _EXAMPLES, ids=[e[0] for e in _EXAMPLES])
def test_examples_do_not_use_extra_info(label, code):
    assert not declares_extra_info(code), (
        f"{label} declares EXTRA_INFO, which is legacy-only. Use REGIONS."
    )


@pytest.mark.parametrize("label,code", _EXAMPLES, ids=[e[0] for e in _EXAMPLES])
def test_examples_do_not_use_legacy_translations(label, code):
    found = declares_legacy_translations(code)
    assert not found, (
        f"{label} declares {found}, which is legacy-only. Labels come from "
        "field_terms via PARAMS; use HOWTO for guidance."
    )


@pytest.mark.parametrize("label,code", _EXAMPLES, ids=[e[0] for e in _EXAMPLES])
def test_examples_import_waste_types_as_a_module(label, code):
    named = named_waste_type_imports(code)
    assert not named, (
        f"{label} imports {named} from waste_types by name. Use "
        "`from waste_collection_schedule import waste_types as wt`."
    )


@pytest.mark.parametrize("label,code", _BLOCKS, ids=[b[0] for b in _BLOCKS])
def test_examples_bind_standard_field_terms(label, code):
    """Applies to every block: a bad PARAMS line is copyable on its own."""
    offenders = hand_rolled_standard_fields(code)
    assert not offenders, (
        f"{label} hand-writes a standard field: {'; '.join(offenders)}. Bind the "
        "concept with its factory or text_field(name, term=TERM). This is the exact "
        "mistake that shipped in two examples before the gate existed."
    )


@pytest.mark.parametrize("label,code", _EXAMPLES, ids=[e[0] for e in _EXAMPLES])
def test_examples_do_not_define_their_own_pipeline_steps(label, code):
    local = source_local_step_classes(code)
    assert not local, (
        f"{label} defines its own step class(es) {local}. An example must compose "
        "shared components, since it is what gets copied."
    )


@pytest.mark.parametrize("label,code", _EXAMPLES, ids=[e[0] for e in _EXAMPLES])
def test_examples_do_not_hand_roll_retrieval(label, code):
    """The function-shaped half of the same rule (#7139).

    An example that reaches for ``source.session`` in a module-level helper
    teaches a Retriever written as a function, which is what let the same vendor
    decoder be hand-rolled twice and drift.
    """
    offenders = source_local_retrieval_functions(code)
    assert not offenders, (
        f"{label} issues HTTP from module-level function(s) {offenders}. An "
        "example must compose a shared retriever, since it is what gets copied."
    )


@pytest.mark.parametrize("label,code", _EXAMPLES, ids=[e[0] for e in _EXAMPLES])
def test_examples_keep_registries_as_data(label, code):
    found = hand_rolled_registry(code)
    assert found is None, (
        f"{label} declares a provider registry in Python: {found}. Use "
        "regions.from_yaml over doc/regions/<source>.yaml."
    )


@pytest.mark.parametrize("label,code", _EXAMPLES, ids=[e[0] for e in _EXAMPLES])
def test_examples_declare_no_redundant_init(label, code):
    """A pass-through __init__ is what the template taught for 97 sources.

    The real gate compares the signature against PARAMS, which needs the imported
    class. On a snippet, checking for the pass-through shape is enough: an
    __init__ whose whole body forwards its arguments to super().
    """
    tree = ast.parse(code)
    cls = next(
        (
            n
            for n in ast.walk(tree)
            if isinstance(n, ast.ClassDef) and n.name == "Source"
        ),
        None,
    )
    if cls is None:
        return
    init = next(
        (
            b
            for b in cls.body
            if isinstance(b, ast.FunctionDef) and b.name == "__init__"
        ),
        None,
    )
    if init is None:
        return
    body = [
        s
        for s in init.body
        if not (
            isinstance(s, ast.Expr)
            and isinstance(s.value, ast.Constant)
            and isinstance(s.value.value, str)
        )
    ]
    is_passthrough = (
        len(body) == 1
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Call)
        and isinstance(body[0].value.func, ast.Attribute)
        and body[0].value.func.attr == "__init__"
    )
    assert not is_passthrough, (
        f"{label} shows an __init__ that only forwards to super(). BaseSource "
        "already applies the PARAMS defaults, validates, and stores them, so the "
        "example must not show one: this is what put a redundant constructor in 97 "
        "sources."
    )
