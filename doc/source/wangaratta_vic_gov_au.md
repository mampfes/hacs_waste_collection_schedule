# Rural City of Wangaratta

Support for schedules provided by [Rural City of Wangaratta](https://www.wangaratta.vic.gov.au).

Source for Rural City of Wangaratta rubbish collection.

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
        street_address: Edwards Street WANGARATTA VIC 3677
```
