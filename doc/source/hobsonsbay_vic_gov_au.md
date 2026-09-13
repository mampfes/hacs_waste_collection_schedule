# Hobsons Bay City Council

Support for schedules provided by [Hobsons Bay City Council](https://www.hobsonsbay.vic.gov.au).

Hobsons Bay moved its bin collection lookup to [Impact Apps](https://impactapps.com.au/), so this source now reads from `hobsons-bay.waste-info.com.au`. The `street_address` argument is unchanged, so existing configurations keep working.

The collection types come from Impact Apps and are named `waste`, `recycle`, `organic`, `glass` and `special`. If you previously used `customize` with the old names (`Rubbish`, `Commingled Recycling`, `Food and Garden`, `Glass`), update them to the new ones.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: hobsonsbay_vic_gov_au
      args:
        street_address: STREET_ADDRESS
```

### Configuration Variables

**street_address**  
*(string) (required)*

The street number, street name and suburb, in the form `<number> <street>, <suburb>`. The comma is optional.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: hobsonsbay_vic_gov_au
      args:
        street_address: 399 Queen St, Altona Meadows
```

## How to get the source arguments

Look up your address on the council's [bin collection calendar](https://www.hobsonsbay.vic.gov.au/Services/Waste-and-recycling/When-will-my-bins-be-collected) and use the street number, street name and suburb exactly as the calendar shows them — for example `20 Merrett Dr Williamstown`, where the street is abbreviated to `Dr` rather than `Drive`.

If the street name or number is not recognised, the error message lists the values the council accepts for that street and suburb.

As an alternative, the [Impact Apps source](impactapps_com_au.md) can be used directly with `service: hobsons-bay` and either a `property_id` or a `suburb`/`street_name`/`street_number` combination.
