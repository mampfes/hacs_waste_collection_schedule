# Warsaw

Support for schedules provided by [Warsaw](https://warszawa19115.pl).

Source for Warsaw city garbage collection

## Configuration via configuration.yaml

### Using street_address

```yaml
waste_collection_schedule:
  sources:
    - name: warszawa19115_pl
      args:
        street_address: STREET_ADDRESS
```

### Using geolocation_id

```yaml
waste_collection_schedule:
  sources:
    - name: warszawa19115_pl
      args:
        geolocation_id: GEOLOCATION_ID
```

### Configuration Variables

**street_address**  
*(string) (alternative)*

**geolocation_id**  
*(string) (alternative)*

Provide one of: `street_address` or `geolocation_id`.

## Example

### Using street_address

```yaml
waste_collection_schedule:
  sources:
    - name: warszawa19115_pl
      args:
        street_address: "MARSZA\u0141KOWSKA 84/92, 00-514 \u015Ar\xF3dmie\u015Bcie"
```

### Using geolocation_id

```yaml
waste_collection_schedule:
  sources:
    - name: warszawa19115_pl
      args:
        geolocation_id: '27044650'
```

## How to get the source arguments

Enter your address as `street_address`, in the form the [Warsaw 19115 portal](https://warszawa19115.pl/harmonogramy-wywozu-odpadow) suggests it (for example `MARSZAŁKOWSKA 84/92, 00-514 Śródmieście`), or the portal's numeric address point id as `geolocation_id`.
