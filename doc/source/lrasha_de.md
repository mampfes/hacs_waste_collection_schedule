# Landkreis Schwäbisch Hall

Support for schedules provided by [Landkreis Schwäbisch Hall](https://www.lrasha.de) located in Baden-Württemberg, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: lrasha_de
      args:
        location: "68329"
```

### Configuration Variables

**location**
*(string) (required)*

## How to get the source arguments

Visit [Abfallkalender](https://www.lrasha.de/de/buergerservice/abfallwirtschaft/abfallkalender), select your location and click on import. Now you see a link to import the calendar. The number after `SecondCategoryIds=` has to be entered in the configuration.
