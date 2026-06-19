# Kronstorf

Support for waste collection schedules provided by [Marktgemeinde Kronstorf](https://www.kronstorf.at), Austria.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: kronstorf_at
```

### Configuration Variables

No arguments required — the source fetches the municipality-wide calendar automatically.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: kronstorf_at
```
