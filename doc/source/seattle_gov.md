# Seattle Public Utilities

Support for schedules provided by [Seattle Public Utilities](https://myutilities.seattle.gov/eportal/#/accountlookup/calendar), serving the city of Seattle, WA, USA.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: seattle_gov
      args:
        street_address: STREET_ADDRESS
        prem_code: PREM_CODE
```

### Configuration Variables

**street_address**<br>
*(string) (required)*

**prem_code**<br>
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: seattle_gov
      args:
        street_address: 600 4th Ave
```

## How to get the source argument

The street_address argument is simply the house mailing address. Road type (eg. St, Ave) and cardinal direction if applicable (eg. N/S/NW) are required, so "501 23rd Ave" and "501 23rd Ave E" will give different results.

If the service cannot be identified based on street address alone (in some multi-family houses, etc), a `prem_code` can be extracted by inspecting the "findAccount" call when looking up your service on the Collection Calendar.