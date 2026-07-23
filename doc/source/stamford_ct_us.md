# City of Stamford, CT

Support for schedules provided by [City of Stamford, CT](https://www.stamfordct.gov/government/operations/recycling-and-sanitation/about/recycling-and-garbage-schedule).

This source is for residential properties in Stamford, Connecticut only. It does not
cover condominiums.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: stamford_ct_us
      args:
        street: STREET_NAME
```

### Configuration Variables

**street**
*(string) (required)*

Street name only, without the house number or street suffix (e.g. `Parker` or
`Parker Ave` for `123 Parker Ave`).

**house_number**
*(string or int) (optional)*

Only required if pickup days differ across house-number ranges on this street. If it
is required but missing, the error message raised by the source will list the
available house-number ranges and their pickup days.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: stamford_ct_us
      args:
        street: Parker Ave
```

```yaml
waste_collection_schedule:
  sources:
    - name: stamford_ct_us
      args:
        street: Washington Blvd
        house_number: 200
```

## How to get the source arguments

Use the [City of Stamford Garbage and Recycling
Lookup](https://stamfordapps.org/garbagerecycling/default.asp) to find your street.
Enter just the street name (e.g. `Parker` for `Parker Ave`), leaving out the street
suffix (Ave, St, Rd, etc.) and the house number. If your street has multiple
pickup-day ranges, also provide your house number.

Note: `stamfordapps.org` (the underlying data source) has been reported to only be
reachable from US-based IP addresses. If it appears unreachable, try again from a
US-based network or VPN.
