# Saalfelden am Steinernen Meer

Support for schedules provided by [Saalfelden am Steinernen Meer](https://www.saalfelden.at).

Source for Saalfelden am Steinernen Meer waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: saalfelden_at
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
    - name: saalfelden_at
      args:
        strasse: Achenweg
        hausnummer: 1
```

## How to get the source arguments

Visit https://www.saalfelden.at/Buergerservice/Abfallkalender, pick your street and house number from the dropdowns, and use the same values here.
