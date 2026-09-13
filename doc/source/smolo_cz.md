# SMOLO a.s. (Třinec)

Support for waste collection schedules provided by [SMOLO a.s.](https://www.smolo.cz/sluzby/odpadove-hospodarstvi/informace-pro-domacnosti/) for the town of Třinec, Moravskoslezský kraj, Czech Republic.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: smolo_cz
      args:
        district: "Nebory"
```

### Configuration Variables

**district**
*(string) (required)*

The town district / part of town ("část města") exactly as it appears in the SMOLO Třinec collection schedule, e.g. `Staré Město`, `Lyžbice`, `Nebory`, `Karpentná`.

**street**
*(string) (optional)*

Some districts (e.g. `Staré Město`, `Oldřichovice`, `Lyžbice`) appear on multiple rows of the schedule table with different street lists and, in some cases, different collection weekdays. If `district` alone is ambiguous, provide one street name from the matching row's locality ("LOKALITA") list to disambiguate.

## How to find your `district` / `street`

1. Open the SMOLO household-waste page: <https://www.smolo.cz/sluzby/odpadove-hospodarstvi/informace-pro-domacnosti/>.
2. In the Třinec section, open the current "HARMONOGRAM … (SKO. BIO, SEP)" PDF (the source follows this link automatically on every fetch, so the exact PDF filename does not matter and is not hardcoded).
3. On page 1 ("HARMONOGRAM SVOZU SMĚSNÉHO KOMUNÁLNÍHO A BIOLOGICKÉHO ODPADU"), find your street under the "LOKALITA" column and note the "ČÁST MĚSTA" (district) value in the same row.
4. If that district name appears in more than one row, also copy one of the street names from your row into the `street` argument.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: smolo_cz
      args:
        district: "Staré Město"
        street: "Husova"
```

## Bin types returned

| Provider description (Czech) | Returned type | Icon |
|---|---|---|
| Směsný komunální odpad (SKO) | Směsný komunální odpad | `Icons.GENERAL_WASTE` |
| Biologický odpad (BIO) | Biologický odpad | `Icons.ORGANIC` |
| Tříděný odpad, pytle/240L nádoby (SEP, mixed) | Tříděný odpad (pytle/240L nádoby) | `Icons.RECYCLING` |
| Tříděný odpad, žluté pytle/nádoby (SEP, plast) | Tříděný odpad - plast (žluté pytle/nádoby) | `Icons.RECYCLING` |
| Tříděný odpad, modré pytle/nádoby (SEP, papír) | Tříděný odpad - papír (modré pytle/nádoby) | `Icons.PAPER` |

## Notes and known limitations

- The schedule PDF is discovered dynamically each fetch by scraping the landing page for the "Třinec – komunální..." link, since SMOLO has changed the PDF's URL/filename between years in the past.
- SKO (general waste) and BIO (biowaste) dates on page 1 of the PDF are *computed* from a weekly weekday + odd/even ISO-week rule, not read as explicit dates. BIO normally follows the same weekday as SKO, except for a handful of districts flagged `(BIO* svoz v pondělí)` in the source PDF, whose BIO collection is on Monday regardless of their SKO weekday — this per-district override is applied, but a finer, per-street `*` marking used within some mixed districts is not (all streets in an overridden district are treated the same).
- BIO collection only occurs once a month in January, February and December. The source tries to parse the exact ISO week numbers used for this from the PDF's explanatory text; if that text can't be parsed, it falls back to "every even week" in those three months and logs a warning.
- Holiday shifts (e.g. a collection day that falls on 1 January or 25 December moving to the next day) are parsed from the PDF's explanatory text on a best-effort basis; if the sentence can't be parsed, the shift is skipped for that run and a warning is logged instead of failing the whole fetch.
- SEP (sorted waste / pytle+240L nádoby) dates on page 2 of the PDF are explicit date lists and are used as-is (year taken from the "PLATNÝ OD" page header).
