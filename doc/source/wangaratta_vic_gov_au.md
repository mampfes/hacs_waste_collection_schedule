# Rural City of Wangaratta Council

Support for schedules provided by [Rural City of Wangaratta Council](https://www.wangaratta.vic.gov.au/Services/Waste-Recycling/Kerbside-Collection/Check-your-bin-day).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: wangaratta_vic_gov_au
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
    - name: wangaratta_vic_gov_au
      args:
        street_address: 23-27 Ryley St, Wangaratta
```

## How to get the source arguments

Visit the [Rural City of Wangaratta waste and recycling](https://www.wangaratta.vic.gov.au/Services/Waste-Recycling/Kerbside-Collection/Check-your-bin-day) page and search for your address. The arguments should exactly match the street address shown in the autocomplete result.
