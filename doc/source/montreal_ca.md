# Montreal

Waste collection schedules provided by [Info Collecte Montreal](https://montreal.ca/info-collectes/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: montreal_ca
      args:
        address: ADDRESS
```

### Configuration Variables

**address**
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: montreal_ca
      args:
        address: 2812, rue Monsabre
```

