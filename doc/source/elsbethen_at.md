# Elsbethen

Support for schedules provided by [Elsbethen](https://www.gde-elsbethen.at).

Source for Elsbethen waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: elsbethen_at
      args:
        strasse: STRASSE
        hausnummer: HAUSNUMMER
```

### Configuration Variables

**strasse**  
*(string) (required)*

**hausnummer**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: elsbethen_at
      args:
        strasse: "\xDCberfuhrstra\xDFe"
        hausnummer: '2'
```

## How to get the source arguments

Visit https://www.gde-elsbethen.at/Buergerservice/Abfall-Recycling/Abfallkalender, pick your street and house number from the dropdowns, and use the same values here.
