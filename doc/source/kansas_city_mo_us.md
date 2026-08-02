# Kansas City, MO

Support for schedules provided by [Kansas City, MO](https://www.kcmo.gov/city-hall/trash).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: kansas_city_mo_us
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
    - name: kansas_city_mo_us
      args:
        address: 4632 Paseo, Kansas City, MO 64110
```

## How to get the source arguments

Use your full street address including city, state, and ZIP code (e.g. "4632 Paseo, Kansas City, MO 64110"). The source geocodes the address via the ArcGIS World Geocoder and then queries the city's "Trash Route Boundary" layer to determine your weekly collection day.

Note: Kansas City collects trash and unlimited recycling on the same weekly day, so both are reported together. Holiday-shifted collection dates are not accounted for, since the city's GIS data does not expose holiday schedule information.
