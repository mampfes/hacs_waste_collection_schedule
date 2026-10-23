# Gmina Osielsko

Support for schedules provided by [Gmina Osielsko](https://osielsko.pl).

Source for Gmina Osielsko, Poland.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: osielsko_pl
      args:
        rejon: REJON
        multi_family: MULTI_FAMILY
```

### Configuration Variables

**rejon**  
*(string) (required)*

**multi_family**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: osielsko_pl
      args:
        rejon: '8'
```

## How to get the source arguments

Enter your collection area number (rejon, 1-9) as listed on https://osielsko.pl/odpady-komunalne.html (e.g. '8' for Żołędowo, Strzelce Leśne and Bożenkowo). Tick 'multi_family' for a multi-family building (zabudowa wielorodzinna).
