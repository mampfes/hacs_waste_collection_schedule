# City of Greater Bendigo

Support for schedules provided by [City of Greater Bendigo](https://www.bendigo.vic.gov.au/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: bendigo_vic_gov_au
      args:
        latitude: LATITUDE
        longitude: LONGITUDE
```

### Configuration Variables

**latitude**  
*(float) (required)*  
Latitude coordinate of your location. Must be between -37.07 and -36.39.

**longitude**  
*(float) (required)*  
Longitude coordinate of your location. Must be between 144.03 and 144.86.

## Examples

```yaml
waste_collection_schedule:
  sources:
    - name: bendigo_vic_gov_au
      args:
        latitude: -36.758540554036315
        longitude: 144.2818129235716
```

## How to get the source arguments

1. Visit the [City of Greater Bendigo bin night](https://www.bendigo.vic.gov.au/residents/general-waste-recycling-and-organics/bin-night) page and search for your address.
2. Use a mapping service (like Google Maps) to get the latitude and longitude coordinates for your location.
3. Enter these coordinates in your configuration.

### Important Notes

- The coordinates must be within the City of Greater Bendigo boundaries (latitude: -37.07 to -36.39, longitude: 144.03 to 144.86).
- If your coordinates are on a boundary between multiple collection zones, you'll receive an error message. In this case:
  - Adjust your coordinates slightly (by 0.0001 degrees or less) in any direction
  - Verify your zone on the [City of Greater Bendigo bin night](https://www.bendigo.vic.gov.au/residents/general-waste-recycling-and-organics/bin-night) page
