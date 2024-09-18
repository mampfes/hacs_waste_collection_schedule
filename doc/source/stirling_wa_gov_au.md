# Stirling

Support for schedules provided by [Stirling](https://www.stirling.wa.gov.au/), serving Stirling, Australia.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: stirling_wa_gov_au
      args:
        lat: LATITUDE
        lon: LONGITUDE
        
```

### Configuration Variables

**lat**  
*(Float) (required)*

**lon**  
*(Float) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: stirling_wa_gov_au
      args:
        lat: -31.9034183
        lon: 115.8320855
        
```

## How to get the source argument

### Using your address coordinates

1. Find the coordinates of your address using any map service like Google Maps. (the coordinates should be in decimal format with 7 decimal places)
2. Write the coordinates in the configuration file.

### Inspecting network requests of the Stirling website

Visit <https://www.stirling.wa.gov.au/waste-and-environment/waste-and-recycling/residential-bin-collections> and open the developer tools of your browser. Go to the network tab and filter. search for your address in the websites search bar and click on you address. In your network tab look for a GET request to https://www.stirling.wa.gov.au/aapi/map. Click on that request and look for the Request Headers. The `fields` value of the Request Headers is latitude and longitude **in inverse order!!!** (longitude,latitude). Write the coordinates in the configuration file.
