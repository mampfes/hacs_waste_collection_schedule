# City of Boroondara

Support for schedules provided by [City of Boroondara](https://www.boroondara.vic.gov.au).

Source for City of Boroondara waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: boroondara_vic_gov_au
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
    - name: boroondara_vic_gov_au
      args:
        address: 211 Mont Albert Road, Surrey Hills
```

## How to get the source arguments

Street address within Boroondara (e.g. '211 Mont Albert Road, Surrey Hills').
