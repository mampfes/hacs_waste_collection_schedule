# Landkreis Schwäbisch Hall

Support for schedules provided by [Landkreis Schwäbisch Hall](https://www.lrasha.de) located in Baden Württemberg, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: lrasha_de
      args:
        location: "97"
```

### Configuration Variables

**location**<br>
*(string) (required)*

## How to get the source arguments

Visit [Abfallkalender](https://www.lrasha.de/de/buergerservice/abfallwirtschaft/abfallkalender), select your location and click on search. Now copy the download link and paste it somewhere to see it. The number after `location=` has to be entered in the configuration.
