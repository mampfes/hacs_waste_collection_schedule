# Elsbethen

Support for schedules provided by [Elsbethen](https://www.gde-elsbethen.at).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: elsbethen_at
      args:
        strasse: Überfuhrstraße
        hausnummer: "2"
```

### Configuration Variables

**strasse**
*(string) (required)*
Street name as listed in the Elsbethen waste calendar.

**hausnummer**
*(string) (required)*
House number as listed in the Elsbethen waste calendar.

## How to get the arguments

Visit [https://www.gde-elsbethen.at/Buergerservice/Abfall-Recycling/Abfallkalender](https://www.gde-elsbethen.at/Buergerservice/Abfall-Recycling/Abfallkalender), pick your street and house number from the dropdowns, and use the same values here.
