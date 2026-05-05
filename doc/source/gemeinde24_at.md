# Gemeinde24

Support for schedules provided by [Gemeinde24](https://www.gemeinde24.at).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: gemeinde24_at
      args:
        gemeinde: Edelschrott
        strasse: Edelschrott-Ort
```

### Configuration Variables

**gemeinde**
_(string) (optional)_

Municipality name exactly as shown in Gemeinde24.
Required if `gemeinde_id` is not provided.

**strasse**
_(string) (optional)_

Street/local-area name exactly as shown in Gemeinde24.
Required if `street_id` is not provided.

**gemeinde_id**
_(string) (optional)_

Numeric GemeindeID from Gemeinde24.
If set, it is used directly and `gemeinde` is optional.

**street_id**
_(string) (optional)_

Numeric streetID from Gemeinde24.
If set, it is used directly and `strasse` is optional.

## Example using IDs

```yaml
waste_collection_schedule:
  sources:
    - name: gemeinde24_at
      args:
        gemeinde_id: "77"
        street_id: "3753"
```
