"""Classification used by tools/check_generated_files.py."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import check_generated_files as guard  # noqa: E402


@pytest.mark.parametrize(
    "path",
    [
        "custom_components/waste_collection_schedule/sources.json",
        "custom_components/waste_collection_schedule/source_metadata.json",
        ".github/source_owners.json",
        "doc/ics/some_provider.md",
    ],
)
def test_fully_generated_paths_are_blocked(path: str) -> None:
    assert guard.classify(path) == "block"


def test_ics_yaml_and_hand_maintained_source_docs_are_allowed() -> None:
    assert guard.classify("doc/ics/yaml/some_provider.yaml") is None
    for name in ("ics.md", "static.md", "multiple.md", "example.md"):
        assert guard.classify(f"doc/source/{name}") is None


def test_legacy_source_doc_is_allowed() -> None:
    # berlin_recycling_de is a legacy source with a hand-written doc.
    assert (ROOT / "doc/source/berlin_recycling_de.md").is_file()
    assert guard.classify("doc/source/berlin_recycling_de.md") is None


def test_pipeline_source_doc_is_blocked() -> None:
    assert (ROOT / "doc/source/koppl_at.md").is_file()
    assert guard.classify("doc/source/koppl_at.md") == "block"


def test_pipeline_doc_with_service_section_is_a_warning() -> None:
    assert guard.classify("doc/source/edpevent_se.md") == "warn"
    assert guard.classify("doc/source/awido_de.md") == "warn"


def test_readme_info_and_translations_are_warnings_only() -> None:
    assert guard.classify("README.md") == "warn"
    assert guard.classify("info.md") == "warn"
    assert (
        guard.classify(
            "custom_components/waste_collection_schedule/translations/en.json"
        )
        == "warn"
    )
    assert guard.classify("translation_templates/fi.json") is None


def test_frontend_bundle_is_exempt() -> None:
    assert (
        guard.classify(
            "custom_components/waste_collection_schedule/frontend/waste-collection-cards.js"
        )
        is None
    )
    assert (
        guard.classify(
            "custom_components/waste_collection_schedule/frontend/THIRD-PARTY-NOTICES.txt"
        )
        is None
    )


def test_ordinary_source_module_is_allowed() -> None:
    assert (
        guard.classify(
            "custom_components/waste_collection_schedule/waste_collection_schedule/source/koppl_at.py"
        )
        is None
    )


def test_classify_paths_splits_blocked_and_warnings() -> None:
    blocked, warnings = guard.classify_paths(
        [
            "README.md",
            "custom_components/waste_collection_schedule/sources.json",
            "doc/source/koppl_at.md",
            "frontend/src/cards.ts",
        ]
    )
    assert blocked == [
        "custom_components/waste_collection_schedule/sources.json",
        "doc/source/koppl_at.md",
    ]
    assert warnings == ["README.md"]


def test_ics_md_path_is_still_blocked_without_diff_status() -> None:
    # Path-only classification does not know whether the change is a deletion.
    assert guard.classify("doc/ics/abfall_hdh_de.md") == "block"
    blocked, warnings = guard.classify_paths(["doc/ics/abfall_hdh_de.md"])
    assert blocked == ["doc/ics/abfall_hdh_de.md"]
    assert warnings == []


def test_paired_ics_yaml_and_md_deletions_are_allowed() -> None:
    md = "doc/ics/abfall_hdh_de.md"
    yaml = "doc/ics/yaml/abfall_hdh_de.yaml"
    blocked, warnings = guard.classify_paths(
        [yaml, md],
        status_by_path={yaml: "D", md: "D"},
    )
    assert blocked == []
    assert warnings == []


@pytest.mark.parametrize(
    "md_status, yaml_status, yaml_path",
    [
        ("M", "D", "doc/ics/yaml/abfall_hdh_de.yaml"),
        ("A", "D", "doc/ics/yaml/abfall_hdh_de.yaml"),
        ("D", "M", "doc/ics/yaml/abfall_hdh_de.yaml"),
        ("D", None, None),
        ("D", "D", "doc/ics/yaml/other_provider.yaml"),
    ],
)
def test_ics_md_change_stays_blocked_without_matching_yaml_deletion(
    md_status: str, yaml_status: str | None, yaml_path: str | None
) -> None:
    md = "doc/ics/abfall_hdh_de.md"
    paths = [md]
    status_by_path = {md: md_status}
    if yaml_path is not None and yaml_status is not None:
        paths.append(yaml_path)
        status_by_path[yaml_path] = yaml_status
    blocked, warnings = guard.classify_paths(paths, status_by_path=status_by_path)
    assert md in blocked
    assert warnings == []


def test_paired_ics_deletion_does_not_exempt_other_blocked_paths() -> None:
    md = "doc/ics/abfall_hdh_de.md"
    yaml = "doc/ics/yaml/abfall_hdh_de.yaml"
    sources = "custom_components/waste_collection_schedule/sources.json"
    blocked, warnings = guard.classify_paths(
        [yaml, md, sources],
        status_by_path={yaml: "D", md: "D", sources: "M"},
    )
    assert blocked == [sources]
    assert warnings == []
