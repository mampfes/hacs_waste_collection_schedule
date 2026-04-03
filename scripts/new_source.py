#!/usr/bin/env python3
"""Generate a new waste collection source scaffold.

Creates a source .py file and corresponding .md documentation file
with the correct boilerplate structure.

Usage:
    python scripts/new_source.py                           # interactive
    python scripts/new_source.py --title "Example Council" \
        --url "https://example.gov.uk" --country gb        # non-interactive

After generating, run: python update_docu_links.py
"""

import argparse
import os
import re
import sys
import textwrap


def title_to_module_name(title: str, url: str) -> str:
    """Convert a source title/URL to a Python module name."""
    # Prefer deriving from URL domain
    if url:
        from urllib.parse import urlparse

        domain = urlparse(url).netloc or url
        domain = domain.replace("www.", "")
        # Convert dots and hyphens to underscores
        name = re.sub(r"[.\-]", "_", domain)
        # Remove trailing slashes and clean up
        name = re.sub(r"_+", "_", name).strip("_").lower()
        return name

    # Fall back to title
    name = re.sub(r"[^a-zA-Z0-9]+", "_", title).strip("_").lower()
    return name


def generate_source_py(
    title: str, url: str, country: str, module_name: str, params: list[str]
) -> str:
    """Generate the source .py file content."""
    param_init = ""
    param_store = ""
    for p in params:
        param_init += f", {p}: str"
        param_store += f"        self._{p} = {p}\n"

    if not param_store:
        param_store = "        pass\n"

    test_case_params = ", ".join(f'"{p}": ""' for p in params)

    lines = [
        "import requests",
        "from waste_collection_schedule import Collection  # type: ignore[attr-defined]",
        "",
        f'TITLE = "{title}"',
        f'DESCRIPTION = "Source for {title}."',
        f'URL = "{url}"',
        f'COUNTRY = "{country}"',
        "TEST_CASES = {",
        f'    "Test_001": {{{test_case_params}}},',
        "}",
        "",
        "",
        "class Source:",
        f"    def __init__(self{param_init}):",
        param_store.rstrip("\n"),
        "",
        "    def fetch(self) -> list[Collection]:",
        "        # TODO: Implement data fetching",
        "        # The framework auto-detects icons from waste type names.",
        '        # To override an icon, pass icon="mdi:icon-name" to Collection().',
        '        raise NotImplementedError("Source not yet implemented")',
        "",
    ]
    return "\n".join(lines) + "\n"


def generate_source_md(title: str, url: str) -> str:
    """Generate the source .md documentation file content."""
    return textwrap.dedent(f"""\
        # {title}

        Support for schedules provided by [{title}]({url}).

        ## How to get the source arguments

        TODO: Describe how users can find their configuration arguments.

        ## Examples

        ```yaml
        waste_collection_schedule:
          sources:
            - name: {{module_name}}
              args:
                # TODO: add example arguments
        ```
    """)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--title", help="Source title (e.g., 'Example Council')")
    parser.add_argument("--url", help="Website URL")
    parser.add_argument("--country", help="ISO country code (e.g., gb, de, au)")
    parser.add_argument(
        "--params",
        help="Comma-separated parameter names (e.g., uprn,postcode)",
        default="",
    )
    args = parser.parse_args()

    # Interactive mode if args not provided
    title = args.title or input("Source title: ").strip()
    url = args.url or input("Website URL: ").strip()
    country = args.country or input("Country code (e.g., gb, de, au): ").strip()
    params_str = args.params or input(
        "Parameter names (comma-separated, e.g., uprn,postcode): "
    ).strip()
    params = [p.strip() for p in params_str.split(",") if p.strip()]

    module_name = title_to_module_name(title, url)
    print(f"\nModule name: {module_name}")

    source_dir = "custom_components/waste_collection_schedule/waste_collection_schedule/source"
    doc_dir = "doc/source"
    source_path = os.path.join(source_dir, f"{module_name}.py")
    doc_path = os.path.join(doc_dir, f"{module_name}.md")

    if os.path.exists(source_path):
        print(f"ERROR: {source_path} already exists!")
        sys.exit(1)

    source_content = generate_source_py(title, url, country, module_name, params)
    doc_content = generate_source_md(title, url)

    os.makedirs(os.path.dirname(source_path), exist_ok=True)
    os.makedirs(os.path.dirname(doc_path), exist_ok=True)

    with open(source_path, "w") as f:
        f.write(source_content)
    print(f"Created: {source_path}")

    with open(doc_path, "w") as f:
        f.write(doc_content)
    print(f"Created: {doc_path}")

    print("\nNext steps:")
    print(f"  1. Implement the fetch() method in {source_path}")
    print("  2. Fill in test cases with real data")
    print(f"  3. Update the documentation in {doc_path}")
    print("  4. Run: python update_docu_links.py")
    print("  5. Run: python -m pytest tests/")
    print("\nNotes:")
    print("  - ICON_MAP is NOT needed (framework auto-detects icons)")
    print("  - PARAM_TRANSLATIONS is NOT needed for common params")
    print("    (street, address, uprn, postcode, city, house_number, etc.)")
    print("  - Only add PARAM_TRANSLATIONS for source-specific parameter names")


if __name__ == "__main__":
    main()
