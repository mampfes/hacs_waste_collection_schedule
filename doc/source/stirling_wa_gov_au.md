# Stirling

Support for schedules provided by [Stirling](https://www.stirling.wa.gov.au).

Source for Stirling.

## Configuration via configuration.yaml

### Using address

```yaml
waste_collection_schedule:
  sources:
    - name: stirling_wa_gov_au
      args:
        address: ADDRESS
```

### Using lat and lon

```yaml
waste_collection_schedule:
  sources:
    - name: stirling_wa_gov_au
      args:
        lat: LAT
        lon: LON
```

### Configuration Variables

**address**  
*(string) (alternative)*

**lat**  
*(string) (alternative)*

**lon**  
*(string) (alternative)*

Provide one of: `address` or `lat` + `lon`.

## Example

### Using address

```yaml
waste_collection_schedule:
  sources:
    - name: stirling_wa_gov_au
      args:
        address: 100 Cedric Street, Stirling, WA, Australia
```

### Using lat and lon

```yaml
waste_collection_schedule:
  sources:
    - name: stirling_wa_gov_au
      args:
        lat: -31.9034183
        lon: 115.8320855
```

## How to get the source arguments

Enter your street address including suburb (e.g. '100 Cedric Street, Stirling, WA, Australia'), or provide latitude and longitude coordinates.
