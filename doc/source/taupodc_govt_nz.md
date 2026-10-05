# Taupō District Council

Support for schedules provided by [Taupō District Council](https://www.taupodc.govt.nz).

Source for Taupō District Council kerbside collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: taupodc_govt_nz
      args:
        address: ADDRESS
```

### Configuration Variables

**address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: taupodc_govt_nz
      args:
        address: 9 Richmond Avenue Taupo
```

## How to get the source arguments

Enter the street address as it appears on the Taupō District Council property map, e.g. '9 Richmond Avenue Taupo'.
