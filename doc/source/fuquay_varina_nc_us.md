# Fuquay-Varina, North Carolina

Support for schedules provided by [Fuquay-Varina, NC](https://gis1.fuquay-varina.org/) via their ArcGIS services.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: fuquay_varina_nc_us
      args:
        street_address: STREET_ADDRESS
```

### Configuration Variables

**street_address** _(string) (required)_: Street address of the property

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: fuquay_varina_nc_us
      args:
        street_address: "155 S Main St"
```

## How to find your street address

Use your street address as it appears on official town records. The system will search for matching addresses in the Fuquay-Varina GIS database.

You can verify your address format and pickup schedule by visiting the [Town of Fuquay-Varina Garbage Collection Service page](https://www.fuquay-varina.org/352/Garbage-Collection-Service) where you can search for your address.

Examples of valid formats:
- "155 S Main St" 
- "123 E Vance St"

For best results, use common abbreviations:
- Street types: "St" for Street, "Ave" for Avenue, "Rd" for Road, etc.
- Directions: "N", "S", "E", "W" instead of spelling out directions

The address matching is case-insensitive and uses partial matching, so minor variations in formatting should still work.