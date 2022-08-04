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

Visit [Abfallkalender](https://www.lrasha.de/de/buergerservice/abfallwirtschaft/abfallkalender) and search for your location. The `city` and `street` argument should exactly match the autocomplete result.
