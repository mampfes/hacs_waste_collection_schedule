# Gemeinde Felixdorf

Support for waste collection schedules provided by [Gemeinde Felixdorf](https://www.felixdorf.gv.at), Lower Austria.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: felixdorf_gv_at
      args:
        zone: Rayon 1  # optional: Rayon 1 or Rayon 2; omit for all zones
```

### Arguments

| Argument | Description |
|---|---|
| `zone` | *(optional)* Collection zone: `Rayon 1` or `Rayon 2`. Omit to receive entries for all zones. |

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: felixdorf_gv_at
      args:
        zone: Rayon 2
```
