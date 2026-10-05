# City of Sydney

Support for schedules provided by [City of Sydney](https://www.cityofsydney.nsw.gov.au).

Source for City of Sydney (NSW) bin collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: cityofsydney_nsw_gov_au
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
    - name: cityofsydney_nsw_gov_au
      args:
        address: 17 Junction Street, Forest Lodge
```

## How to get the source arguments

Enter your street address including suburb (e.g. '17 Junction Street, Forest Lodge'), as it would appear on the council's [find my bin collection day](https://www.cityofsydney.nsw.gov.au/waste-recycling-services/find-my-bin-collection-day) page.
