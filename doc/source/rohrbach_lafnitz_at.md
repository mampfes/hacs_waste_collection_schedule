# Rohrbach an der Lafnitz

Support for schedules provided by [Rohrbach an der Lafnitz](https://www.rohrbach-lafnitz.at/Buergerservice/Muellkalender), Austria.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: rohrbach_lafnitz_at
```

No configuration parameters required. The source automatically fetches all waste types (Biomüll, Leichtverpackungen, Restmüll, Sperrmüll & Heckenschnitt).

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: rohrbach_lafnitz_at
```
