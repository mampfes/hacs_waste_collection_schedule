# Entsorgung + Recycling Stadt Bern

Support for schedules provided by [Entsorgung + Recycling Stadt Bern (ERB)](https://www.bern.ch/themen/umwelt-natur-und-energie/abfall-und-recycling), serving the city of Bern, Switzerland.

Collections are read from the city's public iCalendar feed and cover Hauskehricht (household waste), Grünabfuhr (organic waste, kitchen and garden combined) and Altpapiersammlung (paper).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: bern_ch
      args:
        strasse: STRASSE
        hnr: HNR
        key: KEY  # optional
```

### Configuration Variables

**strasse**
*(string) (required if `key` is not set)*

Street name exactly as listed on the [ERB collection-dates page](https://bernentsorgung.glue.ch/erb/web/index), e.g. `Bundesplatz`. Spaces and umlauts are kept as shown; multi-word names are usually hyphenated (e.g. `Von-Werdt-Passage`).

**hnr**
*(string or integer) (required if `key` is not set)*

House number, e.g. `1`. Numbers with a letter suffix are written without a space, e.g. `3a`. The suffix is matched case-insensitively, so `3a` and `3A` both work.

**key**
*(string) (optional)*

The address key from your personal iCalendar link. If set, `strasse` and `hnr` are ignored and the key is used directly.

This is an escape hatch: the source normally derives the key itself, but if ERB ever changes how the key is built, you can paste the key from your own link and keep working without waiting for a new release.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: bern_ch
      args:
        strasse: Bundesplatz
        hnr: 1
```

Using the key directly instead:

```yaml
waste_collection_schedule:
  sources:
    - name: bern_ch
      args:
        key: DC46354136EE5531B312A864FA2C4604
```

## How to get the source arguments

Open the [ERB collection-dates page](https://bernentsorgung.glue.ch/erb/web/index) and start typing your street into the search field. Pick your address from the suggestion list — that is the exact spelling to use for `strasse` and `hnr`.

If the address search does not find your street, or you would rather pin the address permanently, use the `key` argument instead:

1. Search for your address on the page above.
2. Click **Import iKalender**.
3. Copy the `key` parameter out of the resulting link:

   ```text
   https://bernentsorgung.glue.ch/erb/web/ical?key=DC46354136EE5531B312A864FA2C4604
                                                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   ```

4. Use that value as the `key` argument.

## Notes

The feed covers the current calendar year only, so the number of returned collections shrinks as the year goes on. ERB publishes the next year's dates in December.

Public holidays are already excluded by the service and are therefore not reported as collection days.

The number of collections differs by address: collection weekdays vary by district, and Altpapiersammlung is weekly in some streets and fortnightly in others.
