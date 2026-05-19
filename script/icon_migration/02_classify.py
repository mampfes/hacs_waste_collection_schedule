"""Classify each ICON_MAP key into one of the 20 canonical Icons categories.

For every extracted source, decide which `Icons.*` member each `t` string maps
to. Uses a multi-language keyword/regex table as the primary signal and the
existing MDI icon as a secondary tiebreaker. Outputs:

* ``script/icon_migration/classified/<source>.json`` for high-confidence cases
  (the rewriter's input).
* ``script/icon_migration/needs_review/<source>.json`` for low-confidence cases
  (manual review queue).
* ``script/icon_migration/review/classifications.tsv`` — aggregate review
  artefact, one row per ``(source, t_key, old_icon, new_canonical,
  confidence, why)``.

Run from the repo root::

    python script/icon_migration/02_classify.py
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
EXTRACTED_DIR = Path(__file__).resolve().parent / "extracted"
CLASSIFIED_DIR = Path(__file__).resolve().parent / "classified"
REVIEW_DIR = Path(__file__).resolve().parent / "needs_review"
TSV_PATH = Path(__file__).resolve().parent / "review" / "classifications.tsv"

# Canonical Icons enum members, in the same order as icons.py.
CANONICAL = [
    "GENERAL_WASTE",
    "RECYCLING",
    "PLASTIC_PACKAGING",
    "PAPER",
    "NEWSPAPER",
    "GLASS",
    "GLASS_COLORED",
    "METAL",
    "ORGANIC",
    "BIO_KITCHEN",
    "GARDEN",
    "CHRISTMAS_TREE",
    "BULKY",
    "HAZARDOUS",
    "ELECTRONICS",
    "BATTERY",
    "TEXTILE",
    "COMMERCIAL",
    "EVENT",
    "NO_COLLECTION",
]

# Map from MDI icon string to the canonical category that icon most strongly
# implies. Used as a secondary signal when the keyword match is ambiguous, and
# as the *primary* signal when the key itself is a colour code or opaque ID
# (e.g. "C4" in amberg_de).
ICON_TO_CANONICAL: dict[str, str] = {
    "mdi:trash-can": "GENERAL_WASTE",
    "mdi:trash-can-outline": "GENERAL_WASTE",
    "mdi:delete": "GENERAL_WASTE",
    "mdi:delete-empty": "GENERAL_WASTE",
    "mdi:delete-sweep": "GENERAL_WASTE",
    "mdi:delete-variant": "GENERAL_WASTE",
    "mdi:trash-can-outline-": "GENERAL_WASTE",
    "mdi:recycle": "RECYCLING",
    "mdi:recycle-variant": "PLASTIC_PACKAGING",
    "mdi:package-variant": "PAPER",
    "mdi:package-variant-closed": "PAPER",
    "mdi:package": "PAPER",
    "mdi:newspaper": "NEWSPAPER",
    "mdi:newspaper-variant": "NEWSPAPER",
    "mdi:newspaper-variant-multiple": "NEWSPAPER",
    "mdi:newspaper-variant-multiple-outline": "NEWSPAPER",
    "mdi:newspaper-variant-outline": "NEWSPAPER",
    "mdi:bottle-soda": "GLASS",
    "mdi:bottle-soda-outline": "GLASS",
    "mdi:bottle-soda-classic": "GLASS",
    "mdi:bottle-soda-classic-outline": "GLASS",
    "mdi:glass-fragile": "GLASS",
    "mdi:glass-cocktail": "GLASS",
    "mdi:glass-mug": "GLASS",
    "mdi:bottle-wine": "GLASS_COLORED",
    "mdi:bottle-wine-outline": "GLASS_COLORED",
    "mdi:glass-wine": "GLASS_COLORED",
    "mdi:nail": "METAL",
    "mdi:hammer": "METAL",
    "mdi:car-battery": "METAL",
    "mdi:food-apple": "BIO_KITCHEN",
    "mdi:food-apple-outline": "BIO_KITCHEN",
    "mdi:apple": "BIO_KITCHEN",
    "mdi:fruit-watermelon": "BIO_KITCHEN",
    "mdi:food": "BIO_KITCHEN",
    "mdi:silverware-fork-knife": "BIO_KITCHEN",
    "mdi:coffee": "BIO_KITCHEN",
    "mdi:leaf": "ORGANIC",
    "mdi:leaf-maple": "ORGANIC",
    "mdi:sprout": "ORGANIC",
    "mdi:flower": "GARDEN",
    "mdi:flower-outline": "GARDEN",
    "mdi:forest": "GARDEN",
    "mdi:tree": "GARDEN",
    "mdi:tree-outline": "GARDEN",
    "mdi:pine-tree": "CHRISTMAS_TREE",
    "mdi:sofa": "BULKY",
    "mdi:sofa-outline": "BULKY",
    "mdi:truck-remove": "BULKY",
    "mdi:dump-truck": "BULKY",
    "mdi:biohazard": "HAZARDOUS",
    "mdi:chemical-weapon": "HAZARDOUS",
    "mdi:medical-bag": "HAZARDOUS",
    "mdi:flask": "HAZARDOUS",
    "mdi:skull-crossbones": "HAZARDOUS",
    "mdi:skull": "HAZARDOUS",
    "mdi:bottle-tonic-skull": "HAZARDOUS",
    "mdi:bottle-tonic-skull-outline": "HAZARDOUS",
    "mdi:radioactive": "HAZARDOUS",
    "mdi:car-coolant-level": "HAZARDOUS",
    "mdi:oil": "HAZARDOUS",
    "mdi:can": "METAL",
    "mdi:can-outline": "METAL",
    "mdi:hammer": "METAL",
    "mdi:paper-roll": "PAPER",
    "mdi:paper-roll-outline": "PAPER",
    "mdi:file": "PAPER",
    "mdi:file-document": "PAPER",
    "mdi:compost": "BIO_KITCHEN",
    "mdi:hair-dryer": "ELECTRONICS",
    "mdi:hair-dryer-outline": "ELECTRONICS",
    "mdi:flash": "ELECTRONICS",
    "mdi:flash-circle": "ELECTRONICS",
    "mdi:cellphone": "ELECTRONICS",
    "mdi:lightbulb": "ELECTRONICS",
    "mdi:lightbulb-outline": "ELECTRONICS",
    "mdi:lightbulb-cfl": "ELECTRONICS",
    "mdi:sofa-single": "BULKY",
    "mdi:cupboard": "BULKY",
    "mdi:cupboard-outline": "BULKY",
    "mdi:armchair": "BULKY",
    "mdi:bed": "BULKY",
    "mdi:bed-outline": "BULKY",
    "mdi:mattress": "BULKY",
    "mdi:delete-circle": "GENERAL_WASTE",
    "mdi:delete-circle-outline": "GENERAL_WASTE",
    "mdi:sack": "PLASTIC_PACKAGING",
    "mdi:sack-percent": "PLASTIC_PACKAGING",
    "mdi:fire-off": "GENERAL_WASTE",
    "mdi:emoticon-poop": "GENERAL_WASTE",
    "mdi:baby-carriage": "GENERAL_WASTE",
    "mdi:diaper-outline": "GENERAL_WASTE",
    "mdi:microwave": "ELECTRONICS",
    "mdi:desktop-classic": "ELECTRONICS",
    "mdi:desktop-tower": "ELECTRONICS",
    "mdi:television-classic": "ELECTRONICS",
    "mdi:television": "ELECTRONICS",
    "mdi:laptop": "ELECTRONICS",
    "mdi:iron-outline": "ELECTRONICS",
    "mdi:battery": "BATTERY",
    "mdi:battery-20": "BATTERY",
    "mdi:battery-50": "BATTERY",
    "mdi:battery-charging": "BATTERY",
    "mdi:hanger": "TEXTILE",
    "mdi:tshirt-crew": "TEXTILE",
    "mdi:tshirt-crew-outline": "TEXTILE",
    "mdi:factory": "COMMERCIAL",
    "mdi:office-building": "COMMERCIAL",
    "mdi:calendar": "EVENT",
    "mdi:calendar-blank": "EVENT",
    "mdi:calendar-text": "EVENT",
    "mdi:note": "EVENT",
    "mdi:note-multiple": "EVENT",
    "mdi:file-document-outline": "EVENT",
    "mdi:calendar-remove": "NO_COLLECTION",
    "mdi:calendar-remove-outline": "NO_COLLECTION",
    "mdi:cancel": "NO_COLLECTION",
    "mdi:close": "NO_COLLECTION",
    # Second-pass additions from LOW-row review:
    "mdi:fridge": "ELECTRONICS",
    "mdi:fridge-outline": "ELECTRONICS",
    "mdi:bulb": "ELECTRONICS",
    "mdi:archive": "PAPER",
    "mdi:archive-outline": "PAPER",
    "mdi:note-text-outline": "PAPER",
    "mdi:note-text": "PAPER",
    "package-variant": "PAPER",
    "mdi:grass": "GARDEN",
    "mdi:chainsaw": "GARDEN",
    "mdi:shredder": "GARDEN",
    "mdi:flower-tulip": "GARDEN",
    "mdi:flower-poppy": "GARDEN",
    "mdi:clippy": "METAL",
    "mdi:tools": "METAL",
    "mdi:wrench": "METAL",
    "mdi:battery-outline": "BATTERY",
    "mdi:bio": "BIO_KITCHEN",
    "mdi:food-takeout-box": "BIO_KITCHEN",
    "mdi:food-takeout-box-outline": "BIO_KITCHEN",
    "mdi:christmas-tree": "CHRISTMAS_TREE",
    "mdi:hazard-lights": "HAZARDOUS",
    "mdi:water-pump": "HAZARDOUS",
    "mdi:water-opacity": "HAZARDOUS",
    "mdi:toilet": "HAZARDOUS",
    "mdi:valve": "HAZARDOUS",
    "mdi:oil-lamp": "HAZARDOUS",
    "mdi:skull-scan": "HAZARDOUS",
    "mdi:fire": "GENERAL_WASTE",
    "mdi:pot-mix-outline": "BULKY",
    "mdi:sofa-single-outline": "BULKY",
    "mdi:broom": "GENERAL_WASTE",
    "mdi:tanker-truck": "GENERAL_WASTE",
    "mdi:bag-personal": "GENERAL_WASTE",
    "mdi:baby": "GENERAL_WASTE",
    "mdi:glass-pint-outline": "GLASS",
    "mdi:glass-pint": "GLASS",
    "mdi:recycling": "RECYCLING",
    "mdi:recycling-variant": "RECYCLING",
    "mdi:silo": "PLASTIC_PACKAGING",
    "mdi:shopping-outline": "PLASTIC_PACKAGING",
    "mdi:glass": "GLASS",
    "mdi:pot": "BIO_KITCHEN",
    "mdi:pot-outline": "BIO_KITCHEN",
    "mdi:house": "GENERAL_WASTE",
    "mdi:house-outline": "GENERAL_WASTE",
    "mdi:truck": "GENERAL_WASTE",
    "mdi:box-cutter": "GENERAL_WASTE",
    "mdi-calendar-alert": "EVENT",
}

# Manual overrides for genuinely opaque keys that the heuristic can't resolve.
# Keyed by (source_name, t_key) -> canonical category. Use sparingly; prefer
# expanding the regex or icon-hint tables when a pattern affects many sources.
MANUAL_OVERRIDES: dict[tuple[str, str], str] = {
    # narab_se uses Swedish bin-system abbreviations with no expansion in the
    # source. FA = "Farligt Avfall" (hazardous); HAO is a general/other bucket.
    ("narab_se", "FA"): "HAZARDOUS",
    ("narab_se", "FA-H"): "HAZARDOUS",
    # narab_se HAO* stays GENERAL_WASTE (current default is correct).
}


# Keyword rules — order matters (more specific first). Each entry is
# (category, regex). Regexes are case-insensitive; they're matched against the
# normalised key (accent-stripped, lowercased).
RULES: list[tuple[str, re.Pattern[str]]] = [
    # CHRISTMAS_TREE — must come before TREE/GARDEN.
    ("CHRISTMAS_TREE", re.compile(r"\b(christmas|xmas|weihnacht|christbaum|tannenbaum|kerstboom|sapin)\b", re.I)),
    # NEWSPAPER before PAPER.
    ("NEWSPAPER", re.compile(r"\b(newspaper|zeitung)\b", re.I)),
    # GLASS_COLORED before GLASS.
    ("GLASS_COLORED", re.compile(r"\b(coloured|colored|color|grun|gru:n|gruen|brown|braun)\s*glas|buntglas|grunglas|braunglas|coloured\s*glass", re.I)),
    # PLASTIC_PACKAGING — yellow bag/bin or plastic-only.
    ("PLASTIC_PACKAGING", re.compile(r"\b(gelber\s*sack|gelbe\s*tonne|gelber\s*tonne|yellow\s*(bag|bin|sack)|lvp|leichtverpackung|leichte\s*verpackung|leichteverpackung|kunststoff|plastik|plastic\s*packaging)\b", re.I)),
    # PLASTIC_PACKAGING — broad plastic match (less specific, after explicit forms).
    ("PLASTIC_PACKAGING", re.compile(r"\b(plastic|plastics|plast|plasty)\b", re.I)),
    # PAPER (after NEWSPAPER). Includes Italian `cartone`, Danish/Norwegian/Czech `pap`/`papir`.
    ("PAPER", re.compile(r"\b(papier|paper|altpapier|karton|cardboard|cartone|cardbo|pappe|ppk|carta|papel|papper|papír|papirus|papir|pulpable)|\bpap\b", re.I)),
    # GLASS (after GLASS_COLORED).
    ("GLASS", re.compile(r"\b(glas|glass|bottles|botellas|verre|vetro|vidrio|sklo|szkło|szklo|stiklas)\b", re.I)),
    # METAL. Compound-aware: `metallverpackung` etc.
    ("METAL", re.compile(r"\b(metal|metall|metalli|metaler|metales|tin|aluminium|aluminum|cans|konserven|scrap)", re.I)),
    # BATTERY.
    ("BATTERY", re.compile(r"\b(battery|batteries|batterie|batterien|batterij|baterie|baterías|pilas|piles)\b", re.I)),
    # BIO_KITCHEN — kitchen/food.
    ("BIO_KITCHEN", re.compile(r"\b(food|kitchen|kuchen|kuchenne|fogo|brown\s*bin|biotonne|biomull|biomüll|bioabfall|gft|biodegrad|umido|matavfall|matresten|matresterar|alimentaires|ffom|organico|orgánico|essensreste|bac\s*brun)", re.I)),
    # CHRISTMAS_TREE for the German plural we may have missed.
    ("CHRISTMAS_TREE", re.compile(r"weihnachtsbaum", re.I)),
    # GARDEN.
    ("GARDEN", re.compile(r"\b(garden|yard|yardwaste|green\s*waste|grünschnitt|grunschnitt|gartenabfall|hackselgut|häckselgut|hackselservice|häckselservice|hackseldienst|häckseldienst|schredder|schredderdienst|sapinage|déchets\s*verts|dechets\s*verts|sfalci|jardin|trädgård|tradgard|grof\s*tuin|snoeiafval|gartner|ogrod|zahrad|verde|zielone)", re.I)),
    # BULKY. Compound-aware Polish `wielkogabaryt*`, etc.
    ("BULKY", re.compile(r"\b(bulky|hard\s*(rubbish|waste)|sperrmull|sperrmüll|sperrabholung|grof|grofvuil|encombrants|ingombranti|voluminosos|muebles|grovavfall|gabaryt|wielkogabaryt|objemn|oversized|junk\s*waste)", re.I)),
    # HAZARDOUS. Compound-aware: `schadstoff*` etc. matches `Schadstoffsammlung`.
    ("HAZARDOUS", re.compile(r"\b(hazardous|problemmull|problemmüll|problemstoff|sondermull|sondermüll|schadstoff|hhw|chemical|chemisch|toxic|toxique|kca|dds|pericolosi|peligrosos|farligt|nebezpe|skadlig|niebezpiec)", re.I)),
    # ELECTRONICS / WEEE. `electric` (loose), German `elektr*`, Italian RAEE, Polish.
    ("ELECTRONICS", re.compile(r"\b(electron|electric|elektr|elek|e-?waste|weee|computer|deee|raee|fernseh|microwave|elektrosc|elektroniczn)", re.I)),
    # TEXTILE.
    ("TEXTILE", re.compile(r"\b(textile|textilien|kleidung|altkleid|textiel|vetements|vêtements|tessili|abbigliamento|ropa|textil|tekstyl|odzież|odzie)", re.I)),
    # COMMERCIAL.
    ("COMMERCIAL", re.compile(r"\b(commercial|business|gewerbe|geschaft|geschäft|dumpster|skip)\b", re.I)),
    # NO_COLLECTION.
    ("NO_COLLECTION", re.compile(r"\b(no\s*collection|no\s*service|suspended|holiday|keine\s*abholung|keine\s*sammlung|geen\s*inzameling|pas\s*de\s*collecte)\b", re.I)),
    # EVENT.
    ("EVENT", re.compile(r"\b(event|drop-?off|aktion|sammelaktion|recycling\s*event|special\s*collection)\b", re.I)),
    # ORGANIC (umbrella when source doesn't distinguish kitchen vs garden — after BIO_KITCHEN and GARDEN).
    ("ORGANIC", re.compile(r"\b(organic|organics|organique|biodegrad|bio\b|biotonne)\b", re.I)),
    # GENERAL_WASTE (residual / mixed / landfill / household / domestic — last because of broad keywords). Compound-aware.
    ("GENERAL_WASTE", re.compile(r"\b(general\s*waste|general|residual|mixed\s*waste|household|domestic|garbage|trash|rubbish|refuse|landfill|restmull|restmüll|restabfall|hausmull|hausmüll|grossmuell|grossmüll|graue\s*tonne|restafval|restavfall|restaffald|ordures\s*menager|ordures\s*ménager|déchets\s*résiduel|dechets\s*residuel|omr|rifiuti\s*indifferenziati|pannolini|resto|indiferenciados|smesn|směsn|komunaln|niesortowane|unbrennbar|brennbar|brännbar|windel|street\s*sweep|street\s*clean|abfallwirtschaftszentrum)", re.I)),
    # Recycling-ish — generic mixed-recycling fallback. Last general rule.
    ("RECYCLING", re.compile(r"\b(recycl|wertstoff|surowce|surowcow|sbierane|materiali|envases|emballages|raccolta\s*differenziata|multimaterial)\b", re.I)),
]


def _normalise(s: str) -> str:
    """Lowercase, strip accents, collapse whitespace."""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.strip().lower()


def _classify_by_keyword(key: str) -> tuple[str, str] | None:
    """Run the keyword rules; return (category, why) or None."""
    norm = _normalise(key)
    for category, pattern in RULES:
        m = pattern.search(norm)
        if m:
            return category, f"keyword: '{m.group(0)}'"
    return None


def classify_entry(
    key: str, current_icon: str, source: str = ""
) -> tuple[str, str, str]:
    """Return (canonical_category, confidence, why) for one (key, icon) pair.

    Confidence is one of: "high", "medium", "low".
    """
    override = MANUAL_OVERRIDES.get((source, key))
    if override is not None:
        return override, "high", "manual override"

    if current_icon.startswith("Icons."):
        # Already migrated.
        return current_icon[len("Icons.") :], "high", "already Icons reference"

    keyword_match = _classify_by_keyword(key)
    icon_hint = ICON_TO_CANONICAL.get(current_icon)

    if keyword_match is not None and icon_hint is not None:
        cat, why = keyword_match
        if cat == icon_hint:
            return cat, "high", f"{why} + icon agrees"
        # Disagreement — keyword wins for organic/garden splits where the
        # source authors often use mdi:leaf for both kitchen and garden, but
        # the keyword is the more reliable signal. We log "medium" so the
        # reviewer sees the disagreement.
        return cat, "medium", f"{why} (icon hint disagreed: {icon_hint})"

    if keyword_match is not None:
        cat, why = keyword_match
        return cat, "medium", f"{why} (no icon hint)"

    if icon_hint is not None:
        return icon_hint, "medium", f"icon-only: {current_icon} → {icon_hint}"

    # Last-ditch: keep the source's existing icon by falling back to GENERAL_WASTE
    # but flag as low-confidence so the reviewer decides.
    return "GENERAL_WASTE", "low", "no keyword or icon match — defaulted to GENERAL_WASTE"


def main() -> int:
    CLASSIFIED_DIR.mkdir(parents=True, exist_ok=True)
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    TSV_PATH.parent.mkdir(parents=True, exist_ok=True)

    classified_count = 0
    review_count = 0
    rows: list[tuple[str, ...]] = []  # for TSV
    confidence_tally = {"high": 0, "medium": 0, "low": 0}

    for path in sorted(EXTRACTED_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        source = data["source"]
        mapping: dict[str, str] = {}
        per_key_meta: dict[str, dict[str, str]] = {}
        has_low_or_disagree = False

        for key, current_icon in data["icon_map"].items():
            category, confidence, why = classify_entry(key, current_icon, source)
            mapping[key] = category
            per_key_meta[key] = {
                "current_icon": current_icon,
                "category": category,
                "confidence": confidence,
                "why": why,
            }
            confidence_tally[confidence] = confidence_tally.get(confidence, 0) + 1
            if confidence != "high":
                has_low_or_disagree = True
            rows.append(
                (
                    source,
                    data.get("country") or "",
                    key,
                    current_icon,
                    category,
                    confidence,
                    why,
                )
            )

        out_payload = {
            "source": source,
            "title": data.get("title"),
            "country": data.get("country"),
            "mapping": mapping,
            "per_key": per_key_meta,
        }

        if has_low_or_disagree:
            (REVIEW_DIR / f"{source}.json").write_text(
                json.dumps(out_payload, ensure_ascii=False, indent=2, sort_keys=True),
                encoding="utf-8",
            )
            review_count += 1
        # Always write the classified payload too, even for needs-review sources —
        # the rewriter consumes from classified/ and the reviewer's edits
        # supersede the auto-classification.
        (CLASSIFIED_DIR / f"{source}.json").write_text(
            json.dumps(out_payload, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        classified_count += 1

    # Write TSV (one row per key).
    with TSV_PATH.open("w", encoding="utf-8", newline="") as f:
        f.write("source\tcountry\tt_key\told_icon\tnew_canonical\tconfidence\twhy\n")
        for row in rows:
            f.write("\t".join(c.replace("\t", " ").replace("\n", " ") for c in row) + "\n")

    print(f"Classified {classified_count} sources ({len(rows)} key/value pairs).")
    print(
        f"Confidence — high: {confidence_tally['high']}, "
        f"medium: {confidence_tally['medium']}, low: {confidence_tally['low']}."
    )
    print(f"{review_count} sources had at least one medium/low key -> needs_review/.")
    print(f"Review artefact: {TSV_PATH.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
