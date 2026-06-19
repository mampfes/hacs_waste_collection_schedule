# Herzogsdorf

Support for waste collection schedules provided by [Gemeinde Herzogsdorf](https://www.herzogsdorf.ooe.gv.at), Upper Austria.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: herzogsdorf_ooe_gv_at
```

### Configuration Variables

No arguments required — the source fetches the municipality-wide calendar automatically.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: herzogsdorf_ooe_gv_at
```
