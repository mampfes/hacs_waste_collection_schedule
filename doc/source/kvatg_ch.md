# KVA Thurgau, Switzerland

Support for schedules provided by [KVA Thurgau (Kehrichtverwertungsanlage Thurgau)](https://www.kvatg.ch), covering the 70 municipalities of the canton of Thurgau and neighbouring communities (including some in the cantons of Schaffhausen and St. Gallen) that publish their disposal plan ("Entsorgungsplan") through KVA Thurgau.

The source downloads the current disposal-plan PDF of your community from [kvatg.ch](https://www.kvatg.ch/fuer-private/entsorgungsplaene-1/) and extracts all collections it contains:

- **Kehricht** (household waste): expanded weekly from the collection weekday stated in the plan ("Abfuhrtag: Dienstag"). Holiday shifts ("Verschiebedaten") are *not* applied — check [kvatg.ch](https://www.kvatg.ch) around public holidays.
- **Papier / Karton**: the printed collection dates, including per-village zones and separate paper/cardboard tours where the plan splits them.
- **Grüngut** (green waste): printed dates, per-district date grids (e.g. Kreuzlingen), weekly summer collections ("Von Anfang März bis Ende November"), and calendar-week rotations (e.g. Frauenfeld).
- **Kleinsperrgut**, **Kunststoff**, **Metalle**, **Häckseldienst**, **Christbaum** collections where the plan lists street-collection dates.

Communities whose plan offers a waste type only via drop-off points or private subscription produce no calendar entries for that type.

**Kreuzlingen special case:** the KVA plan for Kreuzlingen contains no Kehricht dates — the city publishes its own zone plan on [kreuzlingen.ch](https://www.kreuzlingen.ch/wir-fuer-sie/entsorgung). For Kreuzlingen, the source additionally fetches that plan and generates weekly Kehricht collections for its three city zones (`Süd & Tägerwilen` = Montag, `Nord und Ost` = Donnerstag, `Zentrum` = Freitag). Because these are a different zone system than the Grüngut districts, they are selected via the separate `kehricht_zone` argument.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: kvatg_ch
      args:
        community: COMMUNITY
        zone: ZONE  # optional
        kehricht_zone: KEHRICHT_ZONE  # optional, Kreuzlingen only
```

### Configuration Variables

**community**
*(string) (required)*

Community name exactly as listed on the [Entsorgungspläne page](https://www.kvatg.ch/fuer-private/entsorgungsplaene-1/), e.g. `Kreuzlingen`, `Sulgen`, `Stein am Rhein`.

**zone**
*(string) (optional)*

Collection zone / district within the community, for plans that split a collection by area — for example the Grüngut districts `Bernrain`, `Ost`, `Süd`, `Nord` in Kreuzlingen, the villages in multi-village municipalities (e.g. `Pfyn` or `Dettighofen`), or the weekday zones in Frauenfeld (`Zone Dienstag`, ...).

If omitted, all zones are included and zoned collections are suffixed with their zone name, e.g. `Grüngut (Ost)`. If a zone is supplied that does not exist, the error message lists the valid zone names found in the plan.

**kehricht_zone**
*(string) (optional, Kreuzlingen only)*

Household-waste zone from the city of Kreuzlingen's own Kehricht zone plan: `Süd & Tägerwilen`, `Nord und Ost`, or `Zentrum` (partial names like `Zentrum` or `Nord` work). If omitted, all three zones are included with their zone name as suffix. Supplying it for any other community raises an error.

## Examples

```yaml
waste_collection_schedule:
  sources:
    - name: kvatg_ch
      args:
        community: Kreuzlingen
        zone: Ost
        kehricht_zone: Zentrum
```

```yaml
waste_collection_schedule:
  sources:
    - name: kvatg_ch
      args:
        community: Sulgen
```

## How to get the source arguments

Open the [Entsorgungspläne listing](https://www.kvatg.ch/fuer-private/entsorgungsplaene-1/) and use your community name as `community`. Open your community's PDF to see whether any collection is split by zone; if so, use the zone name as printed in the plan (left of the date grid) as `zone`.

## Known limitations

- The schedule year comes from the current PDF ("Gültig ab 1. Januar ..."), so dates for the following year only appear once KVA Thurgau publishes the new plans (usually in December).
- Kehricht holiday shifts are applied where the plan lists explicit replacement dates; otherwise they are announced on [kvatg.ch](https://www.kvatg.ch/) and in the local press only, and the calendar shows the regular weekday in those weeks.
- A few communities (e.g. Egnach) have no street collection for Kehricht (underground containers only) — no Kehricht entries are generated there.
- The Kreuzlingen city Kehricht plan follows the city's own publication rhythm; its weekday rules are expanded for the current KVA schedule year.
