"""Generic ICS (iCalendar) source.

The raw-passthrough ICS engine behind ~178 YAML providers (doc/ics/yaml/*.yaml,
served through config_flow's ICS-YAML mechanism) and usable directly for any
other provider that only publishes an .ics feed. Unlike every other pipeline
source this one has no fixed vocabulary to map onto WasteTypes: the feed's own
VEVENT summary becomes the collection title verbatim (the legacy
``Collection(date, t=...)`` raw-string form), so ``classify()`` builds that
directly instead of declaring a transformer.

Demonstrates: ``config_params.integer``/``boolean``/``raw_object``, the three
widget kinds added alongside this conversion so a source with genuinely
arbitrary numeric/boolean/dict fields (``offset``, ``verify_ssl``, extra POST
``params``, extra ``headers``) needs no config-flow UI compromise.
"""

from pathlib import Path
from typing import Any, ClassVar, final

from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    alternatives,
    boolean,
    dropdown,
    integer,
    raw_object,
    text_field,
)
from waste_collection_schedule.regions import Region
from waste_collection_schedule.service.ICS import (
    IcsConfiguredParser,
    IcsConfiguredRetriever,
    IcsEvent,
)

# Kept as module-level constants (rather than moved onto the class) so that
# test_source_components.py's "hasattr(module, name) counts even when falsy"
# rule keeps accepting URL = None: this is a generic engine with no single
# provider site, exactly as under the legacy module-level contract.
TITLE = "ICS"
DESCRIPTION = "Source for ICS based schedules."
URL = None
TEST_CASES = {
    "Esslingen, Bahnhof": {
        "url": "https://api.abfall.io/?kh=DaA02103019b46345f1998698563DaAd&t=ics&s=1a862df26f6943997cef90233877a4fe"
    },
    "Test File": {
        # Path is used here to allow to call the Source from any location.
        # This is not required in a yaml configuration!
        "file": str(Path(__file__).resolve().parents[1].joinpath("test/test.ics"))
    },
    "Test File (recurring)": {
        # Path is used here to allow to call the Source from any location.
        # This is not required in a yaml configuration!
        "file": str(Path(__file__).resolve().parents[1].joinpath("test/recurring.ics"))
    },
    "München, Bahnstr. 11": {
        "url": "https://www.awm-muenchen.de/entsorgen/abfuhrkalender?tx_awmabfuhrkalender_abfuhrkalender%5Bhausnummer%5D=11&tx_awmabfuhrkalender_abfuhrkalender%5Bleerungszyklus%5D%5BB%5D=1%2F2%3BU&tx_awmabfuhrkalender_abfuhrkalender%5Bleerungszyklus%5D%5BP%5D=1%2F2%3BG&tx_awmabfuhrkalender_abfuhrkalender%5Bleerungszyklus%5D%5BR%5D=001%3BU&tx_awmabfuhrkalender_abfuhrkalender%5Bsection%5D=ics&tx_awmabfuhrkalender_abfuhrkalender%5Bsinglestandplatz%5D=false&tx_awmabfuhrkalender_abfuhrkalender%5Bstandplatzwahl%5D=true&tx_awmabfuhrkalender_abfuhrkalender%5Bstellplatz%5D%5Bbio%5D=70024507&tx_awmabfuhrkalender_abfuhrkalender%5Bstellplatz%5D%5Bpapier%5D=70024507&tx_awmabfuhrkalender_abfuhrkalender%5Bstellplatz%5D%5Brestmuell%5D=70024507&tx_awmabfuhrkalender_abfuhrkalender%5Bstrasse%5D=bahnstr.&tx_awmabfuhrkalender_abfuhrkalender%5Byear%5D={%Y}",
        "version": 1,
    },
    #    "Hausmüllinfo: ASR Chemnitz": {
    #        "url": "https://asc.hausmuell.info/ics/ics.php",
    #        "method": "POST",
    #        "params": {
    #            "hidden_id_egebiet": 439087,
    #            "input_ort": "Chemnitz",
    #            "input_str": "Straße der Nationen",
    #            "input_hnr": 2,
    #            "hidden_send_btn": "ics",
    #            # "hiddenYear": 2021,
    #            "hidden_id_ort": 10,
    #            "hidden_id_ortsteil": 0,
    #            "hidden_id_str": 17814,
    #            "hidden_id_hnr": 5538100,
    #            "hidden_kalenderart": "privat",
    #            "showBinsBio": "on",
    #            "showBinsRest": "on",
    #            "showBinsRest_rc": "on",
    #            "showBinsPapier": "on",
    #            "showBinsOrganic": "on",
    #            "showBinsXmas": "on",
    #            "showBinsDsd": "on",
    #            "showBinsProb": "on",
    #        },
    #        "year_field": "hiddenYear",
    #    },
    "Abfall Zollernalbkreis, Ebingen": {
        "url": "https://www.abfallkalender-zak.de",
        "params": {
            "city": "2,3,4",
            "street": "3",
            "types[]": [
                "restmuell",
                "gelbersack",
                "papiertonne",
                "biomuell",
                "gruenabfall",
                "schadstoffsammlung",
                "altpapiersammlung",
                "schrottsammlung",
                "weihnachtsbaeume",
                "elektrosammlung",
            ],
            "go_ics": "Download",
        },
        "year_field": "year",
    },
    "ReCollect, Ottawa": {
        "url": "https://recollect.a.ssl.fastly.net/api/places/BCCDF30E-578B-11E4-AD38-5839C200407A/services/208/events.en.ics",
        "split_at": "\\, (?:and )?|(?: and )",
    },
    "ReCollect, Simcoe County": {
        "url": "https://recollect.a.ssl.fastly.net/api/places/08E862E8-8190-11E2-A8A6-C758AE7205AF/services/226/events.en.ics",
        "split_at": "\\, (?:and )?|(?: and )",
    },
    "Erlensee, Am Haspel": {
        "url": "https://sperrmuell.erlensee.de/?type=reminder",
        "method": "POST",
        "params": {
            "street": 8,
            "eventType[]": [27, 23, 19, 20, 21, 24, 22, 25, 26],
            "timeframe": 23,
            "download": "ical",
        },
    },
    "UTF-8-SIG (UTF-8 with BOM)": {
        "url": "https://servicebetrieb.koblenz.de/abfallwirtschaft/entsorgungstermine-digital/entsorgungstermine-2023-digital/altstadt-2023.ics?cid=2ui7",
    },
}


def _normalize_ics_codeowners(owners: Any) -> "list[str]":
    """Normalise a YAML ``codeowners:`` value into a sorted list of @handles.

    Mirrors update_docu_links.py's private ``_normalize_owners`` exactly, so
    the ``.github/source_owners.json`` entries this produces (via REGIONS)
    are unchanged from the ones the old ``browse_ics_yaml()`` listing path
    produced. Duplicated rather than imported: this module is the standalone,
    HA-runtime-importable core library and must not depend on the repo-root
    maintainer script.
    """
    if not owners:
        return []
    if isinstance(owners, str):
        owners = [owners]
    result: list[str] = []
    for entry in owners:
        if not isinstance(entry, str) or not entry.strip():
            continue
        handle = entry.strip()
        if not handle.startswith("@"):
            handle = f"@{handle}"
        result.append(handle)
    return sorted(set(result))


def _load_ics_yaml_regions() -> "list[Region]":
    """Build the Region listing for the ICS YAML providers (doc/ics/yaml/*.yaml).

    Build-time only: called by update_docu_links.py (via the generic
    REGIONS handling in get_source_by_file()) to generate the README /
    sources.json / source_owners.json listings and the per-provider
    doc/ics/<stem>.md pages. Never read at HA runtime -- a HACS install only
    ships custom_components/, not the repo's doc/ tree -- hence the
    directory-existence guard below returning [] rather than raising.

    Mirrors, region for region, the listing expansion the now doc-generation-
    only update_docu_links.py:browse_ics_yaml() used to perform directly: one
    Region per YAML file, plus one additional Region per each of that file's
    optional ``regions:`` entries, so folding this into ics.REGIONS changes
    nothing about the generated output.
    """
    yaml_dir = Path(__file__).resolve().parents[4] / "doc" / "ics" / "yaml"
    if not yaml_dir.is_dir():
        return []

    import yaml as _yaml

    regions: list[Region] = []
    for f in yaml_dir.glob("*.yaml"):
        with open(f, encoding="utf-8") as stream:
            data = _yaml.safe_load(stream)
        regions.extend(_regions_from_definition(data, stem=f.stem))
    return regions


def _regions_from_definition(data: dict, stem: str = "") -> "list[Region]":
    """The Regions one ICS yaml definition covers: the file itself, then its own.

    ``regions:`` lists the further providers a single definition covers, each
    becoming its own discoverable listing pointing at this file's generated page.

    That key was called ``extra_info:`` until 2026-08, which named it after the
    deprecated Python ``EXTRA_INFO`` attribute it has nothing to do with: this key
    has always fed ``ics.REGIONS``, the current path, while ``EXTRA_INFO`` is the
    legacy form that ``regions.from_extra_info()`` adapts for legacy Python
    sources. The old spelling is still read so an in-flight contribution keeps
    working; ``regions:`` wins if somehow both are present.
    """
    howto_raw = data["howto"]
    howto = {"en": howto_raw} if isinstance(howto_raw, str) else howto_raw

    country = data.get("country", stem.split("_")[-1] if stem else None)
    params = data.get("default_params", {})
    doc_filename = f"/doc/ics/{stem}.md" if stem else None
    source_owners = _normalize_ics_codeowners(data.get("codeowners", []))

    out = [
        Region(
            title=data["title"],
            params=params,
            url=data["url"],
            country=country,
            doc_filename=doc_filename,
            howto=howto,
            source_owners=source_owners,
        )
    ]
    for entry in data.get("regions", data.get("extra_info", [])):
        out.append(
            Region(
                title=entry.get("title", data["title"]),
                params=params,
                url=entry.get("url", data["url"]),
                country=entry.get("country", country),
                doc_filename=doc_filename,
                howto=howto,
                source_owners=source_owners,
            )
        )
    return out


@final
class Source(BaseSource):
    TEST_CASES: ClassVar[dict] = TEST_CASES

    # Callable (rather than an inline list): the ~178 ICS YAML providers
    # (doc/ics/yaml/*.yaml) are a large external registry, loaded lazily from
    # those files at doc-generation time only. Never read at HA runtime.
    REGIONS = _load_ics_yaml_regions

    PARAMS = (
        alternatives(
            [text_field("url", label="URL", optional=True)],
            [text_field("file", label="File", optional=True)],
        ),
        text_field("year_field", label="Year field", optional=True),
        dropdown("method", ["GET", "POST"], label="Method", optional=True),
        text_field("regex", label="Regular expression", optional=True),
        text_field(
            "title_template", label="Title template", default="{{date.summary}}"
        ),
        text_field("split_at", label="Split at", optional=True),
        text_field(
            "impersonate",
            label="Browser to impersonate (e.g. 'chrome') to pass TLS-fingerprinting WAFs",
            optional=True,
        ),
        integer("offset", label="Offset"),
        boolean("verify_ssl", label="Verify SSL", default=True),
        raw_object("params", label="Parameters"),
        raw_object("headers", label="Headers"),
        # Deprecated, kept only so existing YAML configs (and this source's
        # own "München" TEST_CASE) that still set it don't break: retrieve()
        # logs a warning and otherwise ignores it. Declared as a real PARAM
        # (rather than handled via a custom __init__) so this source keeps
        # relying on BaseSource.__init__ -- overriding __init__ would make
        # test_source_components.py fall back to introspecting the
        # **kwargs-only signature instead of PARAMS for its mandatory-args
        # check, which breaks for every source using this pattern.
        integer(
            "version",
            label="(Deprecated) Version, has no effect anymore",
            optional=True,
        ),
    )

    # The platform's own retriever and converter: every request and conversion
    # detail comes from the PARAMS above rather than from this module, so the
    # ~178 YAML providers folded in here reach them through service/ICS.py.
    retrieve = IcsConfiguredRetriever()
    parse = IcsConfiguredParser()

    def classify(self, record: IcsEvent) -> Collection:
        return Collection(
            date=record.date,
            t=record.title,
            location=record.location,
            description=record.description,
        )
