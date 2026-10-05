# Mitchell Shire Council

Support for schedules provided by [Mitchell Shire Council](https://www.mitchellshire.vic.gov.au).

Source for Mitchell Shire Council, Victoria, Australia.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: mitchellshire_vic_gov_au
      args:
        lat: LAT
        lon: LON
```

### Configuration Variables

**lat**  
*(float) (required)*

**lon**  
*(float) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: mitchellshire_vic_gov_au
      args:
        lat: -37.4195459
        lon: 144.9592853
```
