# Amberg

Support for schedules provided by [Stadt Amberg](https://www.amberg.de), serving the city of Amberg, Bavaria, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: amberg_de
      args:
        street: STREET       # use street name OR zone, not both
        # zone: ZONE
```

### Configuration Variables

**street**
*(String) (optional)*

Street name as it appears in the city's street directory (e.g. `Adalbert-Stifter-Str.`). Either `street` or `zone` must be provided.

**zone**
*(String) (optional)*

Zone code in the form `<letter><number>`, e.g. `A1` or `C4`. Either `street` or `zone` must be provided.

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: amberg_de
      args:
        street: Adalbert-Stifter-Str.
```

```yaml
waste_collection_schedule:
    sources:
    - name: amberg_de
      args:
        zone: A1
```

## How to get the source arguments

1. Visit [https://amberg.de/abfallberatung/abfuhrkalender-2026](https://amberg.de/abfallberatung/abfuhrkalender-2026).
2. Use the street search table to find your street.
3. Note the zone code shown (e.g. `A1`, `C4`) — you can use either the exact street name or the zone code directly in the configuration.
