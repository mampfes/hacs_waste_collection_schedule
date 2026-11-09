"""Build a HACS/Marketplace ZIP from a committed integration subtree only."""

import argparse
import io
import json
import re
import stat
import subprocess
import zipfile
from pathlib import Path, PurePosixPath

COMPONENT = "custom_components/waste_collection_schedule"
FILENAME = "waste_collection_schedule.zip"
MAX_BYTES = 100 * 1024 * 1024


def build_package(
    root: Path, output: Path, revision: str = "HEAD", tag: str | None = None
) -> dict:
    """Archive committed bytes, never local caches or untracked development files."""
    if revision != "HEAD" and not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("revision must be HEAD or a full commit SHA")
    commit = subprocess.check_output(
        ["git", "rev-parse", "--verify", f"{revision}^{{commit}}"], cwd=root, text=True
    ).strip()
    config = json.loads(
        subprocess.check_output(["git", "show", f"{commit}:hacs.json"], cwd=root)
    )
    if config.get("zip_release") is not True or config.get("filename") != FILENAME:
        raise ValueError("release commit must enable the matching ZIP in hacs.json")
    source = subprocess.check_output(
        ["git", "archive", "--format=zip", commit, COMPONENT, "LICENSE"], cwd=root
    )
    buffer = io.BytesIO()
    with (
        zipfile.ZipFile(io.BytesIO(source)) as original,
        zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as package,
    ):
        for member in sorted(original.infolist(), key=lambda item: item.filename):
            if member.is_dir():
                continue
            name = member.filename.removeprefix(f"{COMPONENT}/")
            if name == member.filename and name != "LICENSE":
                raise ValueError("file outside integration subtree")
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = member.external_attr
            package.writestr(info, original.read(member), compresslevel=9)
    archive = buffer.getvalue()
    if len(archive) > MAX_BYTES:
        raise ValueError("compressed archive exceeds Marketplace's 100 MiB limit")
    with zipfile.ZipFile(io.BytesIO(archive)) as package:
        members = package.infolist()
        names = {item.filename for item in members}
        required = {
            "LICENSE",
            "manifest.json",
            "__init__.py",
            "waste_collection_schedule/__init__.py",
        }
        if not required <= names:
            raise ValueError(
                "archive must have the integration files directly at its root"
            )
        for item in members:
            path = PurePosixPath(item.filename)
            if (
                path.is_absolute()
                or ".." in path.parts
                or "\\" in item.filename
                or stat.S_ISLNK(item.external_attr >> 16)
            ):
                raise ValueError("unsafe archive member")
            if any(
                part in {".git", "__pycache__", ".pytest_cache"} for part in path.parts
            ):
                raise ValueError("development cache in committed integration")
        expanded = sum(item.file_size for item in members)
        if expanded > MAX_BYTES or len(members) > 50_000:
            raise ValueError("expanded archive exceeds Marketplace limits")
        manifest = json.loads(package.read("manifest.json"))
        if tag is not None and (
            not re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?", tag)
            or manifest["version"] != tag[1:]
        ):
            raise ValueError("release tag must match manifest version")
        if package.testzip() is not None:
            raise ValueError("archive CRC validation failed")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as destination:
        destination.write(archive)
    return {
        "commit": commit,
        "files": sum(not item.is_dir() for item in members),
        "zip_bytes": len(archive),
        "expanded_bytes": expanded,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--revision", default="HEAD")
    parser.add_argument("--tag")
    args = parser.parse_args()
    print(json.dumps(build_package(Path.cwd(), args.output, args.revision, args.tag)))


if __name__ == "__main__":
    main()
