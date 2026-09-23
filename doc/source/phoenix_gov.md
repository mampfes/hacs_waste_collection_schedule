# Phoenix, AZ

Support for schedules provided by [City of Phoenix, AZ](https://www.phoenix.gov/publicworks/garbage/trashschedule/find-your-day-of-collection).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: phoenix_gov
      args:
        address: ADDRESS
```

### Configuration Variables

**address**
*(string) (required)*

Full street address including city and state.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: phoenix_gov
      args:
        address: 4750 S 48th St, Phoenix, AZ 85040
```

## How to get the source arguments

Use your full street address including city, state, and ZIP code (e.g. "4750 S 48th St, Phoenix, AZ 85040"). The source geocodes the address via the ArcGIS World Geocoder and then queries the city's public "GarbagePickUp" map service to determine your trash and recycling collection day.

Returned collection types:

- **Trash** — weekly, for all city residential customers.
- **Recycling** — weekly, only for addresses eligible for city recycling service. Addresses without city recycling (e.g. some multi-family or commercial buildings) will not show recycling.

Note: Trash and recycling are reported as a fixed weekly pickup day and do not account for holiday shifts (Thanksgiving Day, Christmas Day and New Year's Day all shift the schedule).
