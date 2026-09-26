# Mildura Rural City Council

Support for schedules provided by [Mildura Rural City Council](https://www.mildura.vic.gov.au).

Source for Mildura Rural City Council waste collection.

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

Go to <https://www.mildura.vic.gov.au/Explore/My-Neighbourhood> and make sure your address matches the auto-complete suggestions.
