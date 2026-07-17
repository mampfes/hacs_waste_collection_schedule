# Mildura Rural City Council

Support for schedules provided by [Mildura Rural City Council](https://www.mildura.vic.gov.au/Services/Waste-and-Recycling/My-bins/Find-your-bin-day).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: mildura_vic_gov_au
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
    - name: mildura_vic_gov_au
      args:
        street_address: 1 Stockmans Drive, Irymple VIC 3498
```

## How to get the source arguments

Visit the [Mildura Rural City Council - My Neighbourhood](https://www.mildura.vic.gov.au/Explore/My-Neighbourhood) page and search for your address. The street address used to configure hacs_waste_collection_schedule should match the address shown in the autocomplete suggestions, including suburb and postcode.

## Collection types

The following waste types are returned by this source:

| Type | Icon |
|------|------|
| Organics Waste | mdi:food-apple |
| Landfill Waste | mdi:trash-can |
| Recycling | mdi:recycle |
| Glass | mdi:bottle-soda |
