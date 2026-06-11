# Bundaberg Regional Council

Support for schedules provided by [Bundaberg Regional Council](https://www.bundaberg.qld.gov.au/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: bundaberg_qld_gov_au
      args:
        street_number: STREET_NUMBER
        street_name: STREET_NAME
        suburb: SUBURB
```

### Configuration Variables

**street_number**  
*(string) (required)*

**street_name**  
*(string) (required)*

**suburb**  
*(string) (optional)*  
Required only if your street name is not unique across the council area (e.g. the same street name exists in multiple suburbs). Use uppercase (e.g. `AVENELL HEIGHTS`).

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: bundaberg_qld_gov_au
      args:
        street_number: "10"
        street_name: Maynard
        suburb: AVENELL HEIGHTS
```

## How to get the source arguments

Visit the [Bundaberg Regional Council Bin Day Finder](https://microapps.bundaberg.qld.gov.au/bin_dates/binCollection.html) and start typing your address. Use the street number and street name (without the street type, e.g. "Maynard" not "Maynard St"). If your search returns multiple results for different suburbs, add the `suburb` argument to select the correct one.
