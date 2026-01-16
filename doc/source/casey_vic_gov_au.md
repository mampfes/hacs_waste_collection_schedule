# City of Casey

Support for schedules provided by [City of Casey](https://www.casey.vic.gov.au/find-your-bin-collection-day).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: casey_vic_gov_au
      args:
        street_address: STREET_ADDRESS
```

### Configuration Variables

**street_address**
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: casey_vic_gov_au
      args:
        street_address: 55 Victor Crescent NARRE WARREN VIC 3805
```

## How to get the source arguments

Visit the [City of Casey](https://www.casey.vic.gov.au/find-your-bin-collection-day) page and search for your address. There are typically no commas and the suburb / state are in capitals. The arguments should exactly match the full street address after selecting the autocomplete result.
