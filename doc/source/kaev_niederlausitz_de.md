# Kommunaler Abfallentsorgungsverband Niederlausitz

Support for schedules provided by [kaev.de](https://www.kaev.de/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: kaev_niederlausitz
      args:
        abf_suche: SEARCH_STRING
```

### Configuration Variables

**abf_suche**  
*(string) (required)*


## Example

```yaml
waste_collection_schedule:
  sources:
    - name: kaev_niederlausitz
      args:
        abf_suche: "Luckau / OT Zieckau"
```

```yaml
waste_collection_schedule:
  sources:
    - name: kaev_niederlausitz
      args:
        abf_suche: "Luckau / Bersteweg"
```

```yaml
waste_collection_schedule:
  sources:
    - name: kaev_niederlausitz
      args:
        abf_suche: "Staakow"
```


## How to get the source arguments

1. Go to your calendar at 1. Go to your calendar at [https://www.kaev.de/Info-und-Service/Tourenplan/Tourenplan-Abfalltermine.html](https://www.kaev.de/Info-und-Service/Tourenplan/Tourenplan-Abfalltermine.html).
2. Enter your location.
3. Use full string from the search box for the abf_suche value
