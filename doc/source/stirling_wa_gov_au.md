# Stirling

Support for schedules provided by [Stirling](https://www.stirling.wa.gov.au/), serving Stirling, Australia.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: stirling_wa_gov_au
      args:
        address: ADDRESS
        
```

### Configuration Variables

**address**  
*(String) (optional)*

**lat**  
*(Float) (optional)*

**lon**  
*(Float) (optional)*

Either `address` or both `lat` and `lon` must be provided.

## Examples

### Using address (recommended)

```yaml
waste_collection_schedule:
    sources:
    - name: stirling_wa_gov_au
      args:
        address: "100 Cedric Street, Stirling, WA, Australia"
        
```

### Using coordinates

```yaml
waste_collection_schedule:
    sources:
    - name: stirling_wa_gov_au
      args:
        lat: -31.9034183
        lon: 115.8320855
        
```

## How to get the source argument

### Using your address (recommended)

Enter your full street address including suburb and state (e.g. `100 Cedric Street, Stirling, WA, Australia`). The address will be geocoded automatically.

### Using coordinates

If address lookup does not work for your location, you can provide coordinates instead:

1. Visit <https://www.stirling.wa.gov.au/waste-and-environment/waste-and-recycling/bin-collections> and search for your address.
2. Open your browser's developer tools (Network tab) and look for the request to `/bincollectioncheck/getresult`.
3. The `fields` header contains the coordinates as `longitude,latitude`. Note the **inverse order**.
4. Enter the latitude and longitude values in the configuration file.
