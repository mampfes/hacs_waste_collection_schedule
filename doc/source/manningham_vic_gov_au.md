# City of Manningham

Support for waste collection schedules from the City of Manningham, Victoria, Australia.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: manningham_vic_gov_au
      args:
        street_address: "STREET_ADDRESS"
```

### Configuration Variables

**street_address**
*(string) (required)*

Your street address as it appears on council records. Include the street number and street name. You do not need to include the suburb, state, or postcode, but adding the suburb can help if your street name is ambiguous.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: manningham_vic_gov_au
      args:
        street_address: "10 Harold Street"
```

## How to Find Your Address

1. Visit the [Manningham Bin Collection Days](https://www.manningham.vic.gov.au/waste-and-recycling/bins-and-collections/bin-collection-days) page.
2. Use the address search to look up your property.
3. Use the street number and street name from those results as your `street_address`.

## Waste Types Returned

| Type | Bin | Frequency |
|---|---|---|
| Rubbish | Red lid | Fortnightly |
| Recycling | Yellow lid | Fortnightly |
| Garden Waste | Green lid (FOGO) | Weekly |

Rubbish and recycling collections alternate fortnightly. Garden waste (FOGO — Food and Garden Organics) is collected every week on the same day.
