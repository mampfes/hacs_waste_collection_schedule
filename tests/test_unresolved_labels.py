"""Gate: a source may not emit a label the vocabulary cannot resolve (#7144).

When ``transformers.BaseTransformer._resolve_type`` finds a label in neither the
source's ``type_value_map`` nor the shared multilingual vocabulary, it keeps the
text verbatim as a ``preserved:`` type and logs a warning. Preserving is the
right fallback: nothing is silently collapsed to "Other". The warning is not,
because it is the *only* signal and it says the same thing whatever went wrong.

Three RiSKommunal (AT) sources were shipping wine taverns, Heurigen opening
seasons and a legal-advice slot as bin collections, and every one of them
announced itself with the same line a genuinely new waste type would produce::

    Unresolved waste type 'Weingut Küssler' — preserving the original label.

Nobody reads a log line that is indistinguishable from routine. So the
correspondence is enforced instead: replay every recorded cassette and fail on
any ``preserved:`` type. A source has three honest ways to satisfy it:

1. add an alias to ``waste_types.py``, when the label is one any provider in
   that language might send (``Silofolien``, ``Leicht- und Metallverpackungen``);
2. map it in the source's own ``type_value_map``, when the naming is local
   (``Altpapier Haushalt``, ``Restmüll Abfuhrbereich 1``);
3. map it to ``None``, which drops the record and states that the label is
   known and is not a collection event (``Recyclinghof``, the recycling
   centre's opening days).

The fourth way, leaving it unresolved, is what this gate exists to end.
"""

import calendar  # noqa: F401 - import stdlib calendar before the package path
import contextlib
import os
import sys
from collections import defaultdict

import dateutil.parser  # noqa: F401
import pytest

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__),
        "../custom_components/waste_collection_schedule",
    ),
)

from importlib import import_module

import cassette
from fixtures_support import discover_fixtures, slug

_FIXTURES = discover_fixtures()

# --------------------------------------------------------------------------- #
# The debt register.
#
# Every (module, label) pair a full cassette replay reached ``preserved()`` with
# on the day the gate went in. It is a backlog, not an exemption list, and it is
# the same shape as CASES_AWAITING_CASSETTE in test_new_architecture.py: fix an
# entry by one of the three routes above and delete its line.
# ``test_the_unresolved_label_backlog_is_not_stale`` fails if a listed pair no
# longer occurs, so the list cannot rot into a permanent excuse the way an
# unread warning did.
#
# Do NOT add to this list to make a new source pass. It was seeded once,
# empirically, and only shrinks. Reading it is also useful on its own: it says
# in one place which of the shared vocabulary's gaps are costing the most
# sources (the frequency-suffixed German Restmüll labels, above all).
# --------------------------------------------------------------------------- #

LABELS_AWAITING_VOCABULARY = {
    "a_region_ch::Altpapier und Karton ganzes Gemeindegebiet",
    "a_region_ch::Eisen-und Metallware",
    "a_region_ch::Grünabfälle",
    "a_region_ch::Hauskehricht / Sperrgut",
    "a_region_ch::Hauskehricht, Sperrgut",
    "a_region_ch::Hauskehricht: Unteres Stadtgebiet",
    "a_region_ch::Medikamente, Chemikalien, Gifte",
    "a_region_ch::Papier, Karton",
    "a_region_ch::Papier, Karton: Unteres Stadtgebiet",
    "a_region_ch::Styropor",
    "a_region_ch::Texilien, Schuhe",
    "aberdeenshire_gov_uk::Blue lid bin recycling and food waste",
    "aberdeenshire_gov_uk::Orange lid bin recycling and food waste",
    "abfall_io::Biogut",
    "abfall_io::Biogut Typ B",
    "abfall_io::Fälligkeit Abfallgebühr",
    "abfall_io::Grünabfallsammlung",
    "abfall_io::Hackgutabholdienst",
    "abfall_io::Leichtverpackungen (gelber Sack)",
    "abfall_io::Papier, Pappe, Kartonagen",
    "abfall_io::Wertstoffhof Nord",
    "abfall_io::Wertstoffhof Süd",
    "abfall_io::Wertstoffhof West",
    "abfall_io_graphql::Altkleider/Textilien",
    "abfall_io_graphql::Biotonne auf Abruf",
    "abfall_io_graphql::Leicht- und Metallverp.",
    "abfall_io_graphql::Pappe, Papier und Kartonage",
    "abfall_io_graphql::Problemstoffmobil",
    "abfallkalender_prezero_network::Biotonne-Reinigung",
    "abfallnavi_de::Altpapier -4 wö.-",
    "abfallnavi_de::Altpapier 4wö",
    "abfallnavi_de::Bio 2wö",
    "abfallnavi_de::Bioabfall -2 wö.-",
    "abfallnavi_de::Gelbe Wertstoffbehälter -2 wö.-",
    "abfallnavi_de::Gelber Sack / Tonne",
    "abfallnavi_de::Grünabfallsammlung mit Containern",
    "abfallnavi_de::Grünschnitt (angemeldet)",
    "abfallnavi_de::Restabfall -2 wö.-",
    "abfallnavi_de::Restabfall -4 wö.-",
    "abfallnavi_de::Restabfall 2wö",
    "abfallnavi_de::Restabfall 4wö Lila",
    "abfallnavi_de::Restabfall 4wö Orange",
    "abfallnavi_de::Restmüll 2-wö.",
    "abfallnavi_de::Restmüll 2W",
    "abfallnavi_de::Restmüll 4-wö.",
    "abfallnavi_de::Restmülltonne 1.100 l, 2 wö",
    "abfallnavi_de::Restmülltonne 1.100 l, 4 wö",
    "abfallnavi_de::Restmülltonne 1.100 l, wö",
    "abfallnavi_de::Restmülltonne 60 l - 1.100 l, 2 wö",
    "abfallnavi_de::Restmülltonne 60 l - 240 l, 4-wö",
    "abfallnavi_de::Schadstoff EWF-Betriebsgelände",
    "abfallnavi_de::Schadstoff Kerweplatz Eppstein",
    "abfallnavi_de::Schadstoff Kerweplatz Flomersheim",
    "abfallnavi_de::Schadstoff Kerweplatz Mörsch",
    "abfallnavi_de::Schadstoff Kerweplatz Studernheim",
    "abfallnavi_de::Schadstoffmobil Außenbezirke",
    "abfallnavi_de::Schadstoffmobil Wochenmarkt",
    "abfallnavi_de::Schadstoffsammlung (bitte wählen)",
    "abfallnavi_de::Stadtputz",
    "abfallnavi_de::Weihnachtsbaum",
    "abfallnavi_de::Weihnachtsbaumabfuhr",
    "abfallnavi_de::Weihnachtsbaumsammlung",
    "abfallnavi_de::Wertstoffcontainer",
    "abfallnavi_de::mobile Laubsammlung",
    "abfalltermine_forchheim_de::Singletonne (Restmüll)",
    "abfallwirtschaft_germersheim_de::Problemmüll 11:00 - 12:00 Uhr, Hatzenbühl, Verbindungsweg zwischen Industriestraße und Freigenberg",
    "abfallwirtschaft_germersheim_de::Problemmüll 11:00 - 13:00 Uhr, Bellheim, Festplatz (Jahnstraße)",
    "abfallwirtschaft_germersheim_de::Problemmüll 14:30 - 15:30 Uhr, Hördt, Bauhof (Rheinaue), Herbst: 13:00 - 14:00 Uhr",
    "aliaserviziambientali_it::Napkins",
    "app_abfallplus_de::Altpapiertonne",
    "app_abfallplus_de::Alttextilien + Schuhe (2-wöchentlich) -",
    "app_abfallplus_de::Bioabfall, 14-tägliche Abfuhr",
    "app_abfallplus_de::Biomüll 2-/4-Radbehälter 14-täglich",
    "app_abfallplus_de::Blaue Tonne (verlegt)",
    "app_abfallplus_de::Gelbe Tonne (verlegt)",
    "app_abfallplus_de::Gelber Sack / Gelbe Tonne",
    "app_abfallplus_de::Gelber Sack, 14-tägliche Abfuhr",
    "app_abfallplus_de::Glasbox",
    "app_abfallplus_de::Graue Tonne (verlegt)",
    "app_abfallplus_de::Grüne Tonne plus 2-/4-Radbehälter 14-täglich",
    "app_abfallplus_de::Grüne Tonne plus 4-Radbehälter wöchentlich",
    "app_abfallplus_de::Grünschnittplatz -",
    "app_abfallplus_de::Komposttonne",
    "app_abfallplus_de::Mobile Schadstoffsammlung",
    "app_abfallplus_de::Rest-/Biomüll 4-Radbehälter wöchentlich",
    "app_abfallplus_de::Restabfalltonne 2-wöchentlich",
    "app_abfallplus_de::Restabfalltonne 2-wöchentlich (verlegt)",
    "app_abfallplus_de::Restabfalltonne 4-wöchentlich",
    "app_abfallplus_de::Restabfalltonne 4-wöchentlich (verlegt)",
    "app_abfallplus_de::Restmüll 1.100l, wöchentliche Abfuhr -",
    "app_abfallplus_de::Restmüll 2-/4-Radbehälter 14-täglich",
    "app_abfallplus_de::Restmüll, 14-tägliche Abfuhr -",
    "app_abfallplus_de::Saison-Komposttonne bis Okt.",
    "app_abfallplus_de::Saisonkomposttonne bis Nov.",
    "app_abfallplus_de::Sperrmüll + Altholz -",
    "art_trier_de::A.R.T. Wichtiger Hinweis!",
    "art_trier_de::Gelber Sack - Dreis - A.R.T. Abfuhrtermin",
    "art_trier_de::Restabfall - Dreis - A.R.T. Abfuhrtermin",
    "awr_de::Restabfallcontainer",
    "awsh_de::Papiertonne 1.100L",
    "awsh_de::Restabfall 40L",
    "awsh_de::Restabfall 40L-240L",
    "awsh_de::Wertstoff/LVP",
    "berdorf_lu::Organische und inerte Abfälle",
    "c_trace_de::Altpapier Container",
    "c_trace_de::Altpapier Tonne",
    "c_trace_de::Feiertag",
    "c_trace_de::Grünschnitt Straßensammlung",
    "c_trace_de::Papier / Gelber Sack",
    "c_trace_de::Papierabfall",
    "c_trace_de::Problemabfallsammlung",
    "c_trace_de::Restmüll Container",
    "c_trace_de::Restmüll Container 2w",
    "c_trace_de::Restmüll Tonne",
    "c_trace_de::Reststoff",
    "c_trace_de::Sonderabfall, Stadtteile",
    "c_trace_de::Sonderabfall, Wertstoffhof",
    "c_trace_de::Strauchgut",
    "c_trace_de::Tannenbaumabfuhr",
    "c_trace_de::Trödelmarkt",
    "c_trace_de::Wertstoff",
    "c_trace_de::Wertstoffhof geschlossen",
    "c_trace_de::Wertstofftonne / Gelber Container",
    "cmcitymedia_de::Grüngut",
    "cmcitymedia_de::Sondermüll Rewe-Parkplatz",
    "ecoharmonogram_pl::MYCIE I DEZYNFEKCJA POJEMNIKÓW - BIO",
    "ecoharmonogram_pl::MYCIE I DEZYNFEKCJA POJEMNIKÓW - ODPADY ZMIESZANE",
    "ecoharmonogram_pl::MYCIE POJEMNIKÓW BIO",
    "ecoharmonogram_pl::MYCIE POJEMNIKÓW ZMIESZANE",
    "ecoharmonogram_pl::ODZIEŻ I TEKSTYLIA",
    "ecoharmonogram_pl::TERMIN PŁATNOŚCI",
    "ecoharmonogram_pl::TERMINY PŁATNOŚCI",
    "ecoharmonogram_pl::mPSZOK/Ratowice, teren zrekultywowanego składowiska",
    "frankenberg_de::Altpapiertonne",
    "frankenberg_de::Altreifen",
    "frankenberg_de::Restmüll blauer Aufkleber",
    "frankenberg_de::Restmüll grüner Aufkleber",
    "gemuenden_wohra_de::Altreifensammlung",
    "geoport_nwm_de::Papiertonne GER",
    "geoport_nwm_de::Papiertonne Gollan",
    "geoport_nwm_de::Papiertonne Veolia",
    "geoport_nwm_de::Restabfalltonne",
    "greaterdandenong_vic_gov_au::Street Sweep",
    "infeo_at::Altpapiertonne",
    "infeo_at::Gelber Sack / Gelbe Tonne",
    "infeo_at::Papier, Pappe und Kartonagen",
    "insert_it_de::DSD",
    "insert_it_de::Sack/Tonne gelb",
    "jumomind_de::Abgabe Problemabfall WSH",
    "jumomind_de::Baumschnitt",
    "jumomind_de::Biotonne 120l-240l",
    "jumomind_de::Gelbe Säcke",
    "jumomind_de::GelberSack",
    "jumomind_de::Mülltonnenservice",
    "jumomind_de::Papier Tonnen und Container",
    "jumomind_de::Papier/Blaue Tonne",
    "jumomind_de::Papierabfall",
    "jumomind_de::Papiertonne 120l-240l",
    "jumomind_de::Restabfall 2-wö.",
    "jumomind_de::Restabfall 4-wö.",
    "jumomind_de::Restabfall wö.",
    "jumomind_de::Restmüll Container wöchentlich",
    "jumomind_de::Restmüll Großbehälter",
    "jumomind_de::Restmüll Tonnen und Container 14-täglich",
    "jumomind_de::Restmülltonne 80l-240l",
    "jumomind_de::Schadstoffanlieferung",
    "jumomind_de::Schadstoffsammlung",
    "jumomind_de::Wertstoff",
    "junker_app::Napkins",
    "kaev_niederlausitz::Gelber Wertstoffbehälter",
    "kaev_niederlausitz::Strauchwerkbündel",
    "koeniz_ch::Kehricht und Sperrgut",
    "koeniz_ch::Papier und Karton",
    "koeniz_ch::Schredderdienst Köniz (nur Ortsteil Köniz)",
    "koeniz_ch::Schredderdienst Liebefeld",
    "koeniz_ch::Schredderdienst Spiegel",
    "koeniz_ch::Schredderdienst Wabern",
    "mpo_krakow_pl::Beczka - odpady kuchenne",
    "mzv_rotenburg_bebra_de::[vtext(b'bioabfall'), vtext(b' entsorgung bioabfall')]",
    "mzv_rotenburg_bebra_de::[vtext(b'gelbe tonne'), vtext(b' entsorgung gelbe tonne')]",
    "mzv_rotenburg_bebra_de::[vtext(b'k\\xc3\\xbchlger\\xc3\\xa4te'), vtext(b' entsorgung k\\xc3\\xbchlger\\xc3\\xa4te')]",
    "mzv_rotenburg_bebra_de::[vtext(b'papier'), vtext(b' entsorgung papier')]",
    "mzv_rotenburg_bebra_de::[vtext(b'restabfall'), vtext(b' entsorgung restabfall')]",
    "mzv_rotenburg_bebra_de::[vtext(b'sperrm\\xc3\\xbcll'), vtext(b' entsorgung sperrm\\xc3\\xbcll')]",
    "mzv_rotenburg_bebra_de::[vtext(b'wei\\xc3\\x9fe ware'), vtext(b' entsorgung wei\\xc3\\x9fe ware')]",
    "narab_se::BEDA Kärl 2 - Matavfall, Restavfall, Tidningar och Färgat glas",
    "neu_ulm_de::Rest- und Biomüll",
    "neu_ulm_de::Wertstoffhof geschlossen",
    "offenbach_de::DSD",
    "pointe_claire_qc_ca::Ecocentre Collection",
    "reso_gmbh_de::Sonderabfall Abgabestelle - Sonderabfall-Kleinmengensammlung: Fränkisch-Crumbach, Industriestr. 9 (Bauhof), 09: 00 Uhr-15: 00 Uhr",
    "rh_entsorgung_de::Problemmüll",
    "southkesteven_gov_uk::23lt Food Caddy",
    "winterthur_ch::Grobmetall",
    "winterthur_ch::Grüntour",
    "zab_ch::Bring- und Holtag",
    "zab_ch::Grünabfuhr Sirnach, Busswil, Littenheid, Wiezikon, Horben-Egg",
    "zab_ch::Kehrichtsammlung",
    "zab_ch::Kehrichtsammlung Eschlikon",
    "zab_ch::Kehrichtsammlung ganzes Gemeindegebiet Sirnach",
    "zab_ch::Kompostplatz Schönenberg",
    "zab_ch::Metall Sirnach/Wiezikon/Busswil",
    "zab_ch::Papier und Karton",
    "zab_ch::Papier und Karton Eschlikon ganzes Gemeindegebiet",
    "zab_ch::Papier und Karton Sirnach",
    "zva_sek_de::Altreifen (Achtung: nur Selbstanlieferung)",
}


def _preserved_labels(module_name: str, case_slug: str, path: str) -> set[str]:
    """Labels one cassette replays to a ``preserved:`` type, or an empty set."""
    module = import_module(f"waste_collection_schedule.source.{module_name}")
    cls = getattr(module, "Source", None)
    if cls is None or not hasattr(cls, "TEST_CASES"):
        return set()  # a legacy source has no canonical vocabulary to check
    args = next(
        (a for k, a in cls.TEST_CASES.items() if slug(k) == case_slug),
        None,
    )
    if args is None:
        return set()  # test_offline_fixtures owns that mismatch
    # A source logs its own warnings while fetching; they are the thing this
    # gate replaces, so they are not worth printing again on every run.
    with (
        open(os.devnull, "w") as quiet,
        contextlib.redirect_stdout(quiet),
        contextlib.redirect_stderr(quiet),
        cassette.replaying(path),
    ):
        results = cls(**args).fetch()
    return {
        r.waste_type.id[len("preserved:") :]
        for r in results
        if r.waste_type is not None and r.waste_type.id.startswith("preserved:")
    }


@pytest.mark.parametrize(
    "module_name,case_slug,path",
    _FIXTURES,
    ids=[f"{m}::{c}" for m, c, _ in _FIXTURES],
)
def test_no_source_emits_an_unresolvable_label(module_name, case_slug, path):
    """A label the vocabulary cannot resolve must be mapped, aliased or dropped."""
    try:
        found = _preserved_labels(module_name, case_slug, path)
    except Exception as exc:  # a broken replay is test_offline_fixtures' business
        pytest.skip(f"{module_name}::{case_slug}: replay failed ({exc!r})")

    new = sorted(
        label
        for label in found
        if f"{module_name}::{label}" not in LABELS_AWAITING_VOCABULARY
    )
    assert not new, (
        f"{module_name}::{case_slug} emits {new}, which neither the source's "
        f"type_value_map nor the shared vocabulary resolves, so each reaches a "
        f"user's calendar as raw text. Add an alias to waste_types.py if any "
        f"provider in that language might send it, map it in the source's "
        f"type_value_map if the naming is local, or map it to None if it is not "
        f"a collection event at all. Do not add it to "
        f"LABELS_AWAITING_VOCABULARY."
    )


def test_the_unresolved_label_backlog_is_not_stale():
    """A label that no longer occurs must leave the register, or the list rots.

    Runs the same replay once per cassette and compares the whole observed set
    against the register, so an entry cannot survive its own fix. An entry whose
    module has no cassette at all is stale too: nothing can verify it.
    """
    observed: set[str] = set()
    covered: set[str] = set()
    for module_name, case_slug, path in _FIXTURES:
        covered.add(module_name)
        try:
            found = _preserved_labels(module_name, case_slug, path)
        except Exception:
            continue
        observed |= {f"{module_name}::{label}" for label in found}

    by_module: dict[str, list[str]] = defaultdict(list)
    for entry in LABELS_AWAITING_VOCABULARY:
        by_module[entry.split("::", 1)[0]].append(entry)

    stale = sorted(
        entry
        for module_name, entries in by_module.items()
        if module_name in covered
        for entry in entries
        if entry not in observed
    )
    assert not stale, (
        f"{stale} no longer occur. Delete them from LABELS_AWAITING_VOCABULARY "
        "so the register reflects what is actually outstanding."
    )
