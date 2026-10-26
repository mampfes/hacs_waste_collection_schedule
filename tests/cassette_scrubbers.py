"""Per-source trimming of a cassette at record time.

Some providers answer with one feed for every customer and offer no way to ask
for less (``sica_lu``'s ``/pickup-date`` lists every commune's collections,
about 7 MB). Recording that verbatim makes a multi-megabyte cassette per test
case. A scrubber registered here is run by ``record_fixtures.py`` on the live
interactions before they are written, and cuts such a response down to what the
test case actually reads, so re-recording reproduces the same trimmed cassette.

A scrubber only *removes* records or unused document pages from a recorded
response; it never invents collection data. Register one only for a feed that
cannot be filtered server side.
"""

from __future__ import annotations

import base64
import datetime
import json
import re
from collections.abc import Callable
from typing import Any

Scrubber = Callable[[list[dict], dict[str, Any], str], None]


def _json(interaction: dict) -> Any:
    return json.loads(base64.b64decode(interaction["content_b64"]))


def _set_json(interaction: dict, value: Any) -> None:
    raw = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    interaction["content_b64"] = base64.b64encode(raw.encode("utf-8")).decode("ascii")


def _dardanup_wa_gov_au(
    interactions: list[dict], args: dict[str, Any], today: str
) -> None:
    """Retain all calendar pages and their dated colour grids, without photos."""
    from io import BytesIO

    from pypdf import PdfReader, PdfWriter
    from pypdf.constants import ImageType

    for interaction in interactions:
        if ".pdf" not in interaction["url"].lower():
            continue
        reader = PdfReader(BytesIO(base64.b64decode(interaction["content_b64"])))
        writer = PdfWriter()
        for page in reader.pages:
            text = page.extract_text() or ""
            if re.search(r"[23]-BIN SERVICE", text) and "202" in text:
                writer.add_page(page)
        if len(writer.pages) != 5:
            raise ValueError(
                "Expected all five Dardanup calendar pages before trimming"
            )
        writer.remove_images(ImageType.XOBJECT_IMAGES | ImageType.INLINE_IMAGES)
        for page in writer.pages:
            page.compress_content_streams()
        writer.compress_identical_objects()
        output = BytesIO()
        writer.write(output)
        interaction["content_b64"] = base64.b64encode(output.getvalue()).decode("ascii")


def _sica_lu(interactions: list[dict], args: dict[str, Any], today: str) -> None:
    """Keep the configured commune's collections from the recording day on."""
    wanted = str(args["municipality"]).lower()
    ids = {
        item["name"]["en"].lower(): item["id"]
        for interaction in interactions
        if interaction["url"].endswith("/community")
        for community in _json(interaction).get("data", [])
        for item in [community, *community.get("children", [])]
        if not item["isDisabled"] and not item.get("children", [])
    }
    for interaction in interactions:
        if interaction["url"].endswith("/pickup-date"):
            _set_json(
                interaction,
                [
                    entry
                    for entry in _json(interaction)
                    if not entry["isDisabled"]
                    and entry["community_id"] == ids.get(wanted)
                    and entry["date"][:10] >= today
                ],
            )


def _luxembourg_lu(interactions: list[dict], args: dict[str, Any], today: str) -> None:
    """Keep the rows of the configured commune, locality and street, from today on."""
    import csv
    import datetime

    wanted = [
        str(args.get(key) or "").strip() for key in ("commune", "localite", "rue")
    ]
    for interaction in interactions:
        if "data.public.lu" not in interaction["url"]:
            continue
        text = base64.b64decode(interaction["content_b64"]).decode("utf-8-sig")
        kept = []
        for number, line in enumerate(text.splitlines()):
            if number == 0:
                kept.append(line)
                continue
            date, _, commune, locality, street = next(csv.reader([line], delimiter=";"))
            day = datetime.datetime.strptime(date, "%d/%m/%Y").date().isoformat()
            if (
                commune == wanted[0]
                and day >= today
                and locality in ("", wanted[1])
                and street in ("", "Toutes les rues", wanted[2])
            ):
                kept.append(line)
        raw = "\n".join(kept) + "\n"
        interaction["content_b64"] = base64.b64encode(raw.encode("utf-8-sig")).decode(
            "ascii"
        )


def _chesterfield_gov_uk(
    interactions: list[dict], args: dict[str, Any], today: str
) -> None:
    """Keep only the Aura ``context`` of the Lightning Out bootstrap (~450 KB)."""
    for interaction in interactions:
        if interaction["url"].endswith(".app"):
            context = _json(interaction)["auraConfig"]["context"]
            _set_json(interaction, {"auraConfig": {"context": context}})


def _afvalstoffendienst_nl(
    interactions: list[dict], args: dict[str, Any], today: str
) -> None:
    """Keep only the waste streams the calendars refer to (each carries an SVG)."""
    used = {
        entry["afvalstroom_id"]
        for interaction in interactions
        if "/kalender/" in interaction["url"]
        for entry in _json(interaction)
    }
    for interaction in interactions:
        if interaction["url"].endswith("/afvalstromen"):
            _set_json(interaction, [s for s in _json(interaction) if s["id"] in used])


def _cem_ambiente_it(
    interactions: list[dict], args: dict[str, Any], today: str
) -> None:
    """Keep only the configured municipality and street of the two index lists.

    ``listComuni`` carries every municipality's full profile (~400 KB) and
    ``listVie`` every street; the schedule request is the only thing a replay
    needs besides the two rows that resolve the arguments.
    """
    wanted = {"listComuni": args["city"], "listVie": args["street"]}
    for interaction in interactions:
        endpoint = interaction["url"].rsplit("/", 1)[-1]
        if endpoint in wanted:
            data = _json(interaction)
            name = str(wanted[endpoint]).strip().casefold()
            data["body"] = [
                row for row in data["body"] if str(row["nome"]).casefold() == name
            ]
            _set_json(interaction, data)


def _czystyregion_pl(
    interactions: list[dict], args: dict[str, Any], today: str
) -> None:
    """Cut each page of the cascade (~250 KB of site chrome apiece) to what is read.

    The form page keeps its CSRF token, the commune dropdown and the ``regiony``
    list, the result page its schedule table, the schedule page its ``events``.
    """
    patterns = (
        r'name="_token" value="[^"]*"',
        r'id="gminy"[^>]*>.*?</select>',
        r"var regiony = \[.*?\];",
        r'<table id="harmonogramy".*?</table>',
        r"events:\s*JSON\.parse\(`.*?`\)",
    )
    for interaction in interactions:
        text = base64.b64decode(interaction["content_b64"]).decode("utf-8")
        kept = [
            match.group(0)
            for pattern in patterns
            for match in [re.search(pattern, text, re.S)]
            if match
        ]
        raw = "<html><body>" + "\n".join(kept) + "</body></html>"
        interaction["content_b64"] = base64.b64encode(raw.encode("utf-8")).decode(
            "ascii"
        )


_PLAIN_DAY = re.compile(
    r'\s*<td data-date="[^"]*" class="(?![^"]*highlighted)[^"]*">\d+</td>'
)


def _gmina_sroda_slaska_pl(
    interactions: list[dict], args: dict[str, Any], today: str
) -> None:
    """Drop the calendar cells that are not collection days, and page chrome."""
    for interaction in interactions:
        html = base64.b64decode(interaction["content_b64"]).decode("utf-8")
        html = _PLAIN_DAY.sub("", html)
        html = re.sub(r"[^\n]*data:image/[^\n]*\n", "", html)
        html = re.sub(r'<ul class="nav-bar vertical">.*?</ul>', "", html, flags=re.S)
        html = re.sub(r"<script.*?</script>", "", html, flags=re.S)
        interaction["content_b64"] = base64.b64encode(html.encode("utf-8")).decode(
            "ascii"
        )


def _smiecioplan_pl(interactions: list[dict], args: dict[str, Any], today: str) -> None:
    """Drop the ICS export's reminder alarms and events before the recording day."""
    day = today.replace("-", "")
    for interaction in interactions:
        if not interaction["url"].endswith("/export/ics"):
            continue
        text = base64.b64decode(interaction["content_b64"]).decode("utf-8")
        text = re.sub(r"BEGIN:VALARM.*?END:VALARM\r?\n", "", text, flags=re.S)
        text = re.sub(
            r"BEGIN:VEVENT(?:(?!END:VEVENT).)*?DTSTART;VALUE=DATE:(\d{8})"
            r"(?:(?!END:VEVENT).)*?END:VEVENT\r?\n",
            lambda m: m.group(0) if m.group(1) >= day else "",
            text,
            flags=re.S,
        )
        interaction["content_b64"] = base64.b64encode(text.encode("utf-8")).decode(
            "ascii"
        )


def _valorlux_lu(interactions: list[dict], args: dict[str, Any], today: str) -> None:
    """Keep only the configured commune of the all-communes calendar (~80 KB)."""
    for interaction in interactions:
        if interaction["url"].endswith("/api/calendar/all"):
            cities = _json(interaction)["cities"]
            commune = args["commune"]
            _set_json(interaction, {"cities": {commune: cities[commune]}})


def _potsdam_de(interactions: list[dict], args: dict[str, Any], today: str) -> None:
    """Keep only the configured street of the 17 MB all-streets page data."""

    def norm(value: Any) -> str:
        return str(value or "").lower().strip()

    for interaction in interactions:
        if not interaction["url"].endswith("page-data.json"):
            continue
        payload = _json(interaction)
        dbapi = payload["result"]["data"]["dbapi"]
        region = dbapi["allRegionen"][0]["regionen"][0]
        region["ortsteile"] = [
            {
                **district,
                "strassen": [
                    street
                    for street in district["strassen"]
                    if norm(street["name"]) == norm(args["strasse"])
                ],
            }
            for district in region["ortsteile"]
            if norm(district["name"]) == norm(args["ortsteil"])
        ]
        dbapi["allFeiertage"] = []
        _set_json(interaction, payload)


def _eth_erd_hu(interactions: list[dict], args: dict[str, Any], today: str) -> None:
    """Keep the configured street's assignments from the city-wide JS feed."""
    pattern = re.compile(r"telep === '([^']+)'(.+?)(?=telep === '|\Z)", re.S)
    for interaction in interactions:
        if "telepvegleges" not in interaction["url"]:
            continue
        text = base64.b64decode(interaction["content_b64"]).decode("utf-8")
        matches = list(pattern.finditer(text))
        if any(m.group(1) == args["street"] for m in matches):
            text = pattern.sub(
                lambda m: m.group(0) if m.group(1) == args["street"] else "", text
            )
            interaction["content_b64"] = base64.b64encode(text.encode()).decode()


def _aksd_hu(interactions: list[dict], args: dict[str, Any], today: str) -> None:
    """Keep only the requested street's published recurrence rules."""
    from waste_collection_schedule.service.AksdCalendar import _normalize

    wanted = _normalize(args["street"])
    pattern = re.compile(r"const wasteCalendarStreets = (\[.*?\]);\s*\n", re.S)
    for interaction in interactions:
        text = base64.b64decode(interaction["content_b64"]).decode("utf-8")
        match = pattern.search(text)
        if not match:
            continue
        streets = json.loads(match.group(1))
        kept = [
            street
            for street in streets
            if wanted == _normalize(street["label"])
            or wanted in [_normalize(value) for value in street.get("searchValues", [])]
        ]
        if kept:
            text = (
                text[: match.start(1)]
                + json.dumps(kept, ensure_ascii=False)
                + text[match.end(1) :]
            )
            interaction["content_b64"] = base64.b64encode(text.encode()).decode()


def _vattenmiljoresurs_se(
    interactions: list[dict], args: dict[str, Any], today: str
) -> None:
    """Keep the address rows used by the Sitevision widget's calendar."""
    from waste_collection_schedule.service.SitevisionGarbageCalendar import (
        _address_matches,
    )

    for interaction in interactions:
        if "/allAddresses" not in interaction["url"]:
            continue
        payload = _json(interaction)
        payload["allAddresses"] = [
            entry
            for entry in payload.get("allAddresses", [])
            if _address_matches(args["street_address"], entry.get("hamtstalle", ""))
        ]
        _set_json(interaction, payload)


def _data_montpellier3m_fr(
    interactions: list[dict], args: dict[str, Any], today: str
) -> None:
    """Keep only matching property rows from the metropolitan CSV reference."""
    import csv
    import io

    from waste_collection_schedule.service.MontpellierCollectionReference import (
        _normalize_street,
    )

    wanted = _normalize_street(args["street_name"])
    for interaction in interactions:
        if "MMM_MMM_ReferentielCollecte.csv" not in interaction["url"]:
            continue
        text = base64.b64decode(interaction["content_b64"]).decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        rows = [
            row
            for row in reader
            if _normalize_street((row.get("nom_voie") or "").strip()) == wanted
            and (
                not args.get("commune")
                or row.get("commune", "").strip().upper()
                == args["commune"].strip().upper()
            )
            and (
                args.get("house_number") is None
                or (row.get("numero") or "").strip()
                == str(args["house_number"]).strip()
            )
        ]
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=reader.fieldnames or [])
        writer.writeheader()
        writer.writerows(rows)
        interaction["content_b64"] = base64.b64encode(
            output.getvalue().encode("utf-8-sig")
        ).decode()


def _nwrrr_com_au(interactions: list[dict], args: dict[str, Any], today: str) -> None:
    """Drop zone geometry from the unfiltered all-councils feed; retain every property."""
    for interaction in interactions:
        if interaction["url"].endswith("/assets/all_councils.geojson"):
            payload = _json(interaction)
            for feature in payload.get("features", []):
                feature.pop("geometry", None)
                feature.pop("bbox", None)
            _set_json(interaction, payload)


def _awb_bad_kreuznach_de(
    interactions: list[dict], args: dict[str, Any], today: str
) -> None:
    """Keep the configured address's options and the calendars' rules, not the lists.

    Every ``filterRegion`` answer lists all 121 cities; the calendar answer
    carries the stations and holidays lists besides the rules the source reads.
    """

    def same(name: Any, wanted: Any) -> bool:
        def norm(value: Any) -> str:
            return str(value).lower().replace(" ", "").replace("-", "")

        return norm(name) == norm(wanted)

    levels = {
        "citys": "ort",
        "partOfCitys": "stadtteil",
        "streets": "strasse",
        "houseNumbers": "nummer",
    }
    for interaction in interactions:
        if "filterRegion" in interaction["url"]:
            payload = _json(interaction)
            for key, argument in levels.items():
                options = payload["data"].get(key)
                if not options:
                    continue
                # An unset level is not read at that step (the city answer
                # also lists up to 1000 streets and house numbers).
                payload["data"][key] = [
                    option
                    for option in options
                    if args.get(argument) is not None
                    and same(option["name"], args[argument])
                ]
            _set_json(interaction, payload)
        elif "getAllGarbageCalendar" in interaction["url"]:
            payload = _json(interaction)
            for key in ("stations", "holidays"):
                payload["data"].pop(key, None)
            # The source reads moves within its one-year window; the list repeats
            # each holiday once per tour (the shift is the same for every tour).
            first = datetime.date.fromisoformat(today) - datetime.timedelta(days=3)
            last = first + datetime.timedelta(days=370)
            kept: dict[tuple, dict] = {}
            for view in payload["data"].get("holidayViews", []):
                day = datetime.datetime.fromtimestamp(
                    view["holiday"] / 1000, datetime.UTC
                ).date()
                if first <= day <= last:
                    kept.setdefault((view["holiday"], view["shiftTo"]), view)
            payload["data"]["holidayViews"] = list(kept.values())
            _set_json(interaction, payload)


def _segreguj_gliwice_eu(
    interactions: list[dict], args: dict[str, Any], today: str
) -> None:
    """Keep the download page's file links and the configured street's rows.

    The page is ~120 KB of site chrome around the links ``yearly_links`` reads;
    the workbook has a row per street (~600) on each of its sheets. Each sheet
    keeps its header row and the rows of the configured street, or of the
    streets it is the bare name of ("Rolników" for "Rolników od nr 237 ...").
    """
    import io
    import zipfile

    from lxml import etree

    ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    wanted = " ".join(str(args.get("street", "")).split()).casefold()

    def keep(name: str) -> bool:
        name = " ".join(name.split()).casefold()
        return name == wanted or name.startswith(wanted + " ")

    for interaction in interactions:
        content = base64.b64decode(interaction["content_b64"])
        if not zipfile.is_zipfile(io.BytesIO(content)):
            links = re.findall(
                r"<a\b[^>]*\.(?:xlsx|pdf)\"[^>]*>.*?</a>", content.decode("utf-8"), re.S
            )
            raw = ("<html><body>" + "\n".join(links) + "</body></html>").encode("utf-8")
        else:
            out = io.BytesIO()
            with (
                zipfile.ZipFile(io.BytesIO(content)) as src,
                zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as dst,
            ):
                shared = [
                    "".join(t.text or "" for t in si.iter(f"{ns}t"))
                    for si in etree.fromstring(src.read("xl/sharedStrings.xml"))
                ]
                for info in src.infolist():
                    data = src.read(info)
                    if info.filename.startswith("xl/worksheets/sheet"):
                        sheet = etree.fromstring(data)
                        for row in list(sheet.iter(f"{ns}row")):
                            first = row.find(f"{ns}c")
                            value = first.find(f"{ns}v") if first is not None else None
                            name = (
                                shared[int(value.text)]
                                if value is not None and first.get("t") == "s"
                                else ""
                            )
                            if row.get("r") != "1" and not keep(name):
                                row.getparent().remove(row)
                        data = etree.tostring(
                            sheet,
                            xml_declaration=True,
                            encoding="UTF-8",
                            standalone=True,
                        )
                    dst.writestr(info, data)
            raw = out.getvalue()
        interaction["content_b64"] = base64.b64encode(raw).decode("ascii")


def _montreal_ca(interactions: list[dict], args: dict[str, Any], today: str) -> None:
    """Keep the configured sectors' features, without their geometry.

    The five city-wide GeoJSON files hold every sector with its map polygon.
    """
    sectors = {
        args[field]
        for field in ("sector", "recycling", "bulky", "food", "green")
        if args.get(field)
    }
    for interaction in interactions:
        if interaction["url"].endswith(".geojson"):
            payload = _json(interaction)
            payload["features"] = [
                {key: value for key, value in feature.items() if key != "geometry"}
                for feature in payload["features"]
                if feature["properties"]["SECTEUR"] in sectors
            ]
            _set_json(interaction, payload)


def _wastenet_org_nz(
    interactions: list[dict], args: dict[str, Any], today: str
) -> None:
    """Keep address matches and the fallback suggestions, not the whole registry."""
    wanted = (
        str(args["address"]).replace(" INVERCARGILL", ", Invercargill").strip().lower()
    )
    for interaction in interactions:
        if interaction["url"].endswith("/address-list"):
            rows = _json(interaction)
            _set_json(
                interaction,
                [
                    row
                    for index, row in enumerate(rows)
                    if index < 5 or wanted in row["address"].lower()
                ],
            )


def _ritl_ca(interactions: list[dict], args: dict[str, Any], today: str) -> None:
    """Keep the annual calendar page; remove the unrelated information pages.

    The source's PDF parser is explicitly configured for page zero. Preserve
    its vector marks, fonts and printed dates rather than rasterising the PDF.
    """
    from io import BytesIO

    from pypdf import PdfReader, PdfWriter

    for interaction in interactions:
        if ".pdf" not in interaction["url"].lower():
            continue
        reader = PdfReader(BytesIO(base64.b64decode(interaction["content_b64"])))
        writer = PdfWriter()
        writer.add_page(reader.pages[0])
        writer.compress_identical_objects()
        writer.pages[0].compress_content_streams()
        output = BytesIO()
        writer.write(output)
        interaction["content_b64"] = base64.b64encode(output.getvalue()).decode("ascii")


SCRUBBERS: dict[str, Scrubber] = {
    "ritl_ca": _ritl_ca,
    "wastenet_org_nz": _wastenet_org_nz,
    "montreal_ca": _montreal_ca,
    "dardanup_wa_gov_au": _dardanup_wa_gov_au,
    "awb_bad_kreuznach_de": _awb_bad_kreuznach_de,
    "segreguj_gliwice_eu": _segreguj_gliwice_eu,
    "eth_erd_hu": _eth_erd_hu,
    "aksd_hu": _aksd_hu,
    "vattenmiljoresurs_se": _vattenmiljoresurs_se,
    "data_montpellier3m_fr": _data_montpellier3m_fr,
    "potsdam_de": _potsdam_de,
    "valorlux_lu": _valorlux_lu,
    "smiecioplan_pl": _smiecioplan_pl,
    "afvalstoffendienst_nl": _afvalstoffendienst_nl,
    "cem_ambiente_it": _cem_ambiente_it,
    "czystyregion_pl": _czystyregion_pl,
    "gmina_sroda_slaska_pl": _gmina_sroda_slaska_pl,
    "sica_lu": _sica_lu,
    "nwrrr_com_au": _nwrrr_com_au,
    "luxembourg_lu": _luxembourg_lu,
    "chesterfield_gov_uk": _chesterfield_gov_uk,
}


def for_case(
    module_name: str, args: dict[str, Any], today: str
) -> Callable[[list[dict]], None] | None:
    """The scrubber for one test case of ``module_name``, if it has one."""
    scrubber = SCRUBBERS.get(module_name)
    if scrubber is None:
        return None
    return lambda interactions: scrubber(interactions, args, today)
