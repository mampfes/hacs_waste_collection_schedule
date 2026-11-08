"""Offline release packaging checks; no GitHub writes or provider traffic."""

import importlib.util
import json
import subprocess
import zipfile
from pathlib import Path

import pytest
import yaml

SPEC = importlib.util.spec_from_file_location(
    "build_release_package",
    Path(__file__).parents[1] / "tools/build_release_package.py",
)
assert SPEC and SPEC.loader
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


def git(root, *args):
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


def commit(root):
    git(root, "add", ".")
    return git(
        root,
        "-c",
        "user.name=Packaging test",
        "-c",
        "user.email=test@example.invalid",
        "commit",
        "-m",
        "fixture",
    )


@pytest.fixture
def repository(tmp_path):
    root = tmp_path / "repository"
    root.mkdir()
    git(root, "init", "--quiet")
    (root / "hacs.json").write_text(
        json.dumps({"zip_release": True, "filename": builder.FILENAME})
    )
    files = {
        "manifest.json": json.dumps({"version": "3.0.0-beta.10"}),
        "__init__.py": "# integration\n",
        "frontend_registration.py": "# resource registration\n",
        "frontend/waste-collection-cards.js": "/* runtime bundle */",
        "frontend/THIRD-PARTY-NOTICES.txt": "licenses",
        "translations/en.json": "{}",
        "waste_collection_schedule/__init__.py": "# core\n",
        "waste_collection_schedule/service/__init__.py": "",
        "waste_collection_schedule/wizard/__init__.py": "",
        "waste_collection_schedule/test/runtime_helper.py": "# retain runtime subtree\n",
        "waste_collection_schedule/data.json": "{}",
    }
    for name, text in files.items():
        f = root / builder.COMPONENT / name
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text)
    for name in (
        "tests/fixtures/provider.json",
        "doc/source/provider.md",
        "frontend/package.json",
    ):
        f = root / name
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text("not shipped")
    (root / "LICENSE").write_text("MIT license")
    commit(root)
    files["LICENSE"] = "MIT license"
    return root, files


def test_package_exact_contents_reproducible_and_clean(repository, tmp_path):
    root, files = repository
    component = root / builder.COMPONENT
    (component / "untracked.pyc").write_bytes(b"cache")
    (component / "__init__.py").write_text("uncommitted change")
    first, second = tmp_path / "one.zip", tmp_path / "two.zip"
    stats = builder.build_package(root, first, tag="v3.0.0-beta.10")
    builder.build_package(root, second)
    assert first.read_bytes() == second.read_bytes()
    assert stats["files"] == len(files)
    assert stats["zip_bytes"] < builder.MAX_BYTES
    assert stats["expanded_bytes"] < builder.MAX_BYTES
    with zipfile.ZipFile(first) as package:
        assert set(package.namelist()) == set(files)
        assert all(package.read(name) == text.encode() for name, text in files.items())
        # HACS 2.0.5 release ZIP extraction: no wrapper stripping.
        hacs = tmp_path / "hacs"
        package.extractall(hacs)
        # Marketplace release ZIP: limits/path checks, then the same extraction.
        marketplace = tmp_path / "marketplace"
        assert len(package.infolist()) <= 50_000
        assert sum(item.file_size for item in package.infolist()) <= builder.MAX_BYTES
        for name in package.namelist():
            assert (marketplace / name).resolve().is_relative_to(marketplace.resolve())
        package.extractall(marketplace)
    for directory in (hacs, marketplace):
        assert (directory / "manifest.json").is_file()
        assert not (directory / "custom_components").exists()
        assert (
            directory / "waste_collection_schedule/wizard/__init__.py"
        ).read_bytes() == b""
        assert (directory / "frontend/waste-collection-cards.js").read_text() == files[
            "frontend/waste-collection-cards.js"
        ]


@pytest.mark.parametrize("tag", ["v3.0.0-beta.9", "v3.0.0;touch bad", "--help"])
def test_wrong_or_unsafe_release_tag_rejected(repository, tmp_path, tag):
    with pytest.raises(ValueError, match="tag"):
        builder.build_package(repository[0], tmp_path / "bad.zip", tag=tag)


def test_non_sha_revision_rejected(repository, tmp_path):
    with pytest.raises(ValueError, match="revision"):
        builder.build_package(
            repository[0], tmp_path / "bad.zip", revision="--output=bad"
        )


def test_legacy_tag_without_zip_metadata_not_silently_repackaged(repository, tmp_path):
    root, _ = repository
    (root / "hacs.json").write_text("{}")
    commit(root)
    with pytest.raises(ValueError, match=r"hacs\.json"):
        builder.build_package(root, tmp_path / "bad.zip")


@pytest.mark.parametrize("name", ["__pycache__/cached.pyc", "unsafe\\name.py"])
def test_unsafe_or_cache_member_rejected(repository, tmp_path, name):
    root, _ = repository
    f = root / builder.COMPONENT / name
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text("bad")
    commit(root)
    with pytest.raises(ValueError):
        builder.build_package(root, tmp_path / "bad.zip")


def test_symlink_rejected(repository, tmp_path):
    root, _ = repository
    (root / builder.COMPONENT / "link").symlink_to("/etc/passwd")
    commit(root)
    with pytest.raises(ValueError, match="unsafe"):
        builder.build_package(root, tmp_path / "bad.zip")


@pytest.mark.parametrize("limit", [10, 5000])
def test_compressed_and_expanded_size_limits(repository, tmp_path, monkeypatch, limit):
    root, _ = repository
    (root / builder.COMPONENT / "large.txt").write_text("x" * 10000)
    commit(root)
    monkeypatch.setattr(builder, "MAX_BYTES", limit)
    with pytest.raises(ValueError, match="limit"):
        builder.build_package(root, tmp_path / "bad.zip")


def test_existing_output_not_overwritten(repository, tmp_path):
    output = tmp_path / "existing.zip"
    output.write_bytes(b"previous")
    with pytest.raises(FileExistsError):
        builder.build_package(repository[0], output)
    assert output.read_bytes() == b"previous"


def test_workflow_and_manifest_contract():
    root = Path(__file__).parents[1]
    config = json.loads((root / "hacs.json").read_text())
    assert config["filename"] == builder.FILENAME
    assert config["zip_release"] is True
    workflow = yaml.load(
        (root / ".github/workflows/release-package.yaml").read_text(),
        Loader=yaml.BaseLoader,
    )
    assert workflow["on"] == {"release": {"types": ["published"]}}
    assert workflow["permissions"] == {"contents": "read"}
    job = workflow["jobs"]["upload"]
    assert job["permissions"] == {"contents": "write"}
    assert workflow["jobs"]["build"]["steps"][0]["with"]["ref"] == "${{ github.sha }}"
    script = job["steps"][-1]["run"]
    assert "cmp " in script and "--clobber" not in script
    assert builder.FILENAME in script
