# Entsorgung + Recycling Stadt Bern

Support for schedules provided by [Entsorgung + Recycling Stadt Bern](https://www.bern.ch/themen/umwelt-natur-und-energie/abfall-und-recycling).

Source for waste collection in the city of Bern, Switzerland.

## Configuration via configuration.yaml

### Using strasse and hnr

```yaml
waste_collection_schedule:
  sources:
    - name: bern_ch
      args:
        strasse: STRASSE
        hnr: HNR
```

### Using key

```yaml
waste_collection_schedule:
  sources:
    - name: bern_ch
      args:
        key: KEY
```

### Configuration Variables

**strasse**  
*(string) (alternative)*

**hnr**  
*(string) (alternative)*

**key**  
*(string) (alternative)*

Provide one of: `strasse` + `hnr` or `key`.

## Example

### Using strasse and hnr

```yaml
waste_collection_schedule:
  sources:
    - name: bern_ch
      args:
        strasse: Bundesplatz
        hnr: 1
```

### Using key

```yaml
waste_collection_schedule:
  sources:
    - name: bern_ch
      args:
        key: DC46354136EE5531B312A864FA2C4604
```

## How to get the source arguments

Enter street and house number as shown on https://bernentsorgung.glue.ch/erb/web/index, e.g. street 'Bundesplatz' and house number '1'. House numbers with a suffix are written as '3a'. Alternatively, paste the key from the iCalendar link (…/ical?key=…) directly into the 'key' field.
