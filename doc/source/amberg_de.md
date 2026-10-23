# Amberg

Support for schedules provided by [Amberg](https://www.amberg.de).

Source for the city of Amberg (Bavaria), Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: amberg_de
      args:
        street: STREET
        zone: ZONE
```

### Configuration Variables

**street**  
*(string) (optional)*

**zone**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: amberg_de
      args:
        street: Adalbert-Stifter-Str.
```

## How to get the source arguments

Visit https://amberg.de/abfallberatung/abfuhrkalender-2026, look up your street in the table, and note the zone code (e.g. A1). You can then use either the street name or the zone code directly.
