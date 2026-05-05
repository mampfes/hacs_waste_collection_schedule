# City of Newcastle

Support for schedules provided by [City of Newcastle](https://www.newcastle.nsw.gov.au/living/waste-and-recycling/collection-services/bin-collection-days).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: newcastle_nsw_gov_au
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
    - name: newcastle_nsw_gov_au
      args:
        address: 1 King Street, Newcastle NSW 2300
```

## How to get the source arguments

Visit the [City of Newcastle Bin Collection Days](https://newcastle.nsw.gov.au/living/waste-and-recycling/collection-services/bin-collection-days) page and search for your address in the map. Use the same address format, e.g. "1 King Street, Newcastle NSW 2300".
