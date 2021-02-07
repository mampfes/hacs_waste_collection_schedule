# Seattle Public Utilities

Support for schedules provided by [Seattle Public Utilities](https://myutilities.seattle.gov/eportal/#/accountlookup/calendar), serving the city of Seattle, WA, USA.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: seattle_gov
      args:
        street_address: STREET_ADDRESS
```

### Configuration Variables

**street_address**<br>
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: seattle_gov
      args:
        street_address: 600 4th Ave
```

## How to get the source argument

The source argument is simply the house mailing address. Road type (eg. St, Ave) and cardinal direction if applicable (eg. N/S/NW) are required, so "501 23rd Ave" and "501 23rd Ave E" will give different results.